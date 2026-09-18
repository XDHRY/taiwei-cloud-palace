import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import {
  API_TIMEOUT_MS,
  TASK_DEADLINE_MS,
  TASK_ROOT,
  BASE,
  ImageError,
  isCancelled,
  isTerminal,
  listTaskIds,
  readTask,
  requestJson,
  saveImageItem,
  sleep,
  updateTask,
  validateOutputs,
  formatError,
  writeManifest,
  nodeExecutable,
} from "./core.mjs";

function envNumber(name, fallback, min, max) {
  const raw = process.env[name];
  const value = raw == null || raw === "" ? fallback : Number(raw);
  if (!Number.isFinite(value)) return fallback;
  return Math.min(max, Math.max(min, value));
}

const DEFAULT_CONCURRENCY = envNumber("IMAGE_RUNNER_CONCURRENCY", 4, 1, 8);
const SCAN_MS = envNumber("IMAGE_RUNNER_SCAN_MS", 1000, 250, 60000);
const LEASE_MS = envNumber("IMAGE_RUNNER_LEASE_MS", 900000, 30000, 86400000);
const MAX_ATTEMPTS = Math.floor(envNumber("IMAGE_SUBMIT_ATTEMPTS", 3, 1, 10));
const LOCK_FILE = path.join(TASK_ROOT, "runner.lock");
const THIS_FILE = fileURLToPath(import.meta.url);
const THIS_DIR = path.dirname(THIS_FILE);

function nowIso() { return new Date().toISOString(); }

function readLock() {
  try { return JSON.parse(fs.readFileSync(LOCK_FILE, "utf8")); } catch { return null; }
}

const LOCK_TOKEN = `${process.pid}-${Math.random().toString(16).slice(2)}-${Date.now()}`;
let lockLeaseUntil = null;

function lockOwnedByThisProcess(lock) {
  return lock?.pid === process.pid && lock?.token === LOCK_TOKEN;
}

function acquireLock() {
  fs.mkdirSync(TASK_ROOT, { recursive: true });
  const lock = {
    pid: process.pid,
    token: LOCK_TOKEN,
    acquired_at: nowIso(),
    lease_until: new Date(Date.now() + LEASE_MS).toISOString(),
  };
  for (let attempt = 0; attempt < 8; attempt++) {
    const tmp = `${LOCK_FILE}.${LOCK_TOKEN}.tmp`;
    try {
      fs.writeFileSync(tmp, JSON.stringify(lock, null, 2), "utf8");
      try {
        // Hard-link publication is atomic and refuses an existing target on Windows;
        // unlike rename, it cannot replace another live owner's lock.
        fs.linkSync(tmp, LOCK_FILE);
        fs.rmSync(tmp, { force: true });
        lockLeaseUntil = Date.parse(lock.lease_until);
        return true;
      } catch (error) {
        fs.rmSync(tmp, { force: true });
        if (error.code !== "EEXIST" && error.code !== "EPERM" && error.code !== "EACCES") return false;
        throw Object.assign(new Error("runner lock exists"), { code: "EEXIST" });
      }
    } catch (error) {
      fs.rmSync(tmp, { force: true });
      if (error.code !== "EEXIST") return false;
      const current = readLock();
      if (!current?.token || !current?.pid) {
        const until = Date.now() + Math.min(50, 5 * (attempt + 1));
        while (Date.now() < until) { /* creator may still be publishing lock JSON */ }
        continue;
      }
      try { process.kill(current.pid, 0); return false; }
      catch { /* dead owner: stale lock may be replaced */ }
      try {
        const observed = readLock();
        if (observed?.token === current.token) fs.rmSync(LOCK_FILE, { force: true });
      } catch {
        return false;
      }
    }
  }
  return false;
}

function refreshLock() {
  // The lock record is intentionally immutable. Live PID ownership is authoritative
  // in acquireLock, and replacing this file would create a window for a second runner.
  const current = readLock();
  return lockOwnedByThisProcess(current);
}

function releaseLock() {
  const current = readLock();
  if (lockOwnedByThisProcess(current)) fs.rmSync(LOCK_FILE, { force: true });
}

function recoverExpired() {
  for (const taskId of listTaskIds()) {
    try {
      const state = readTask(taskId);
      if (isTerminal(state.status)) continue;
      if (state.lease_until && Date.parse(state.lease_until) <= Date.now()) {
        const uncertain = ["submitting", "provider_processing", "downloading"].includes(state.status);
        updateTask(taskId, {
          status: uncertain ? "submission_unknown" : "queued",
          lease_until: null,
          error: uncertain ? { code: "LEASE_EXPIRED", message: "runner 租约过期，无法安全确认上游状态；为避免重复计费不自动重提", unknown_submission: true } : state.error,
        }, { type: "lease_expired" });
      }
    } catch (error) {
      process.stderr.write(`[runner] recovery: ${error.message}\n`);
    }
  }
}

function retryable(error) {
  return error?.code === "NETWORK_ERROR" || error?.code === "REQUEST_TIMEOUT" || error?.status === 408 || error?.status === 429 || error?.status >= 500;
}

function retryDelay(error, attempt) {
  const retryAfter = Number(error?.retryAfterMs || 0);
  if (retryAfter > 0) return Math.min(retryAfter, 60000);
  return Math.min(30000, 1000 * (2 ** Math.max(0, attempt - 1)) + Math.floor(Math.random() * 500));
}

async function processTask(taskId) {
  let state = readTask(taskId);
  if (isTerminal(state.status) || isCancelled(taskId)) {
    if (!isTerminal(state.status)) updateTask(taskId, { status: "cancelled", cancel_requested: true, completed_at: nowIso(), error: { code: "CANCELLED", message: "任务已取消" } }, { type: "cancelled" });
    return;
  }
  if (Date.parse(state.deadline_at) <= Date.now()) {
    updateTask(taskId, { status: "failed", completed_at: nowIso(), error: { code: "TASK_DEADLINE", message: "任务超过总截止时间" } }, { type: "deadline" });
    return;
  }

  const leaseUntil = new Date(Date.now() + LEASE_MS).toISOString();
  state = updateTask(taskId, { status: "submitting", attempt: Number(state.attempt || 0) + 1, lease_until: leaseUntil, started_at: state.started_at || nowIso(), error: null }, { type: "submitting" });
  const controller = new AbortController();
  const cancelWatcher = setInterval(() => {
    if (isCancelled(taskId)) controller.abort(new Error("cancelled"));
  }, 250);
  const leaseWatcher = setInterval(() => {
    try {
      const current = readTask(taskId);
      if (!isTerminal(current.status) && current.lease_until) {
        updateTask(taskId, { lease_until: new Date(Date.now() + LEASE_MS).toISOString() });
      }
    } catch { /* task may have reached a terminal state */ }
  }, Math.max(1000, Math.floor(LEASE_MS / 3)));
  const ensureBudget = () => {
    if (Date.parse(readTask(taskId).deadline_at) <= Date.now()) throw new ImageError("任务超过总截止时间", "TASK_DEADLINE");
    if (controller.signal.aborted || isCancelled(taskId)) throw new ImageError("任务已取消", "CANCELLED");
  };
  try {
    let response;
    let lastError;
    for (let attempt = state.attempt; attempt <= MAX_ATTEMPTS; attempt++) {
      ensureBudget();
      try {
        response = await requestJson("/images/generations", state.request, { timeoutMs: Math.min(API_TIMEOUT_MS, Math.max(1000, Date.parse(state.deadline_at) - Date.now())), signal: controller.signal });
        break;
      } catch (error) {
        lastError = error;
        if (error.code === "CANCELLED") throw error;
        if (error.unknownSubmission) {
          throw new ImageError(
            "提交请求已进入无法确认状态；为避免重复计费，任务未自动重试",
            "SUBMISSION_UNKNOWN",
            { unknownSubmission: true, cause_code: error.code }
          );
        }
        if (!retryable(error) || attempt >= MAX_ATTEMPTS) throw error;
        const delay = retryDelay(error, attempt);
        await sleep(Math.min(delay, Math.max(0, Date.parse(state.deadline_at) - Date.now())));
      }
    }
    ensureBudget();
    if (!response) throw lastError || new ImageError("上游无响应", "EMPTY_RESPONSE");
    let items = Array.isArray(response.data) ? response.data : [];
    if (!items.length) throw new ImageError("上游响应无 data 图片", "EMPTY_DATA");
    if (items.length > state.request.n) throw new ImageError(`上游返回 ${items.length}/${state.request.n} 张图片`, "COUNT_MISMATCH");
    state = updateTask(taskId, { status: "provider_processing", provider_response_at: nowIso(), provider_count: items.length, provider_expected_count: state.request.n, lease_until: new Date(Date.now() + LEASE_MS).toISOString() }, { type: "provider_succeeded", provider_count: items.length });
    const outputs = [];
    for (let i = 0; i < items.length; i++) {
      ensureBudget();
      state = updateTask(taskId, { status: "downloading", lease_until: new Date(Date.now() + LEASE_MS).toISOString() }, { type: "downloading", index: i + 1 });
      outputs.push(await saveImageItem(items[i], state, i + 1, controller.signal));
      state = updateTask(taskId, { outputs: [...outputs] }, { type: "artifact_saved", index: i + 1 });
    }
    while (outputs.length < state.request.n) {
      const missing = state.request.n - outputs.length;
      ensureBudget();
      const supplementRequest = { ...state.request, n: missing };
      let supplement;
      try {
        supplement = await requestJson("/images/generations", supplementRequest, { timeoutMs: Math.min(API_TIMEOUT_MS, Math.max(1000, Date.parse(state.deadline_at) - Date.now())), signal: controller.signal });
      } catch (error) {
        if (error.code === "CANCELLED") throw error;
        if (error.unknownSubmission) {
          throw new ImageError("补足请求已进入无法确认状态；为避免重复计费，任务未自动重试", "SUBMISSION_UNKNOWN", { unknownSubmission: true, cause_code: error.code, completed_count: outputs.length, expected_count: state.request.n });
        }
        throw error;
      }
      const supplementItems = Array.isArray(supplement?.data) ? supplement.data : [];
      if (!supplementItems.length || supplementItems.length > missing) {
        throw new ImageError(`补足请求返回 ${supplementItems.length}/${missing} 张图片`, "COUNT_MISMATCH", { completed_count: outputs.length, expected_count: state.request.n });
      }
      items = items.concat(supplementItems);
      for (const item of supplementItems) {
        ensureBudget();
        const index = outputs.length + 1;
        state = updateTask(taskId, { status: "downloading", lease_until: new Date(Date.now() + LEASE_MS).toISOString() }, { type: "downloading", index });
        outputs.push(await saveImageItem(item, state, index, controller.signal));
        state = updateTask(taskId, { outputs: [...outputs], provider_count: items.length, provider_expected_count: state.request.n }, { type: "artifact_saved", index });
      }
    }
    ensureBudget();
    if (isCancelled(taskId)) throw new ImageError("任务已取消", "CANCELLED");
    const verified = validateOutputs({ ...state, outputs });
    if (verified.length !== state.request.n) throw new ImageError(`落盘校验失败：${verified.length}/${state.request.n} 张有效图片`, "OUTPUT_INCOMPLETE");
    state = updateTask(taskId, { status: "completed", outputs: verified, lease_until: null, completed_at: nowIso(), error: null }, { type: "completed" });
    writeManifest(state);
  } catch (error) {
    const code = error.code || "IMAGE_ERROR";
    const status = code === "CANCELLED" ? "cancelled" : code === "SUBMISSION_UNKNOWN" ? "submission_unknown" : "failed";
    const detail = formatError(error);
    updateTask(taskId, { status, lease_until: null, completed_at: nowIso(), error: detail, outputs: validateOutputs(state) }, { type: status, error: detail });
  } finally {
    clearInterval(cancelWatcher);
    clearInterval(leaseWatcher);
  }
}

async function run() {
  if (!acquireLock()) return;
  let stopping = false;
  const active = new Set();
  const concurrency = DEFAULT_CONCURRENCY;
  const onSignal = () => { stopping = true; };
  process.on("SIGTERM", onSignal);
  process.on("SIGINT", onSignal);
  try {
    recoverExpired();
    const once = process.env.IMAGE_RUNNER_ONCE === "1";
    while (!stopping) {
      if (!refreshLock()) {
        stopping = true;
        process.stderr.write("[runner] lock ownership lost; stopping\n");
        break;
      }
      recoverExpired();
      const batchActive = new Map();
      for (const activeId of active) {
        try {
          const activeState = readTask(activeId);
          if (activeState.batch_id) batchActive.set(activeState.batch_id, (batchActive.get(activeState.batch_id) || 0) + 1);
        } catch { /* task may have been removed after completion */ }
      }
      for (const taskId of listTaskIds()) {
        if (active.size >= concurrency) break;
        if (active.has(taskId)) continue;
        try {
          const state = readTask(taskId);
          if (isTerminal(state.status) || ["submitting", "provider_processing", "downloading"].includes(state.status)) continue;
          const batchLimit = state.batch_concurrency || concurrency;
          if (state.batch_id && (batchActive.get(state.batch_id) || 0) >= batchLimit) continue;
          active.add(taskId);
          if (state.batch_id) batchActive.set(state.batch_id, (batchActive.get(state.batch_id) || 0) + 1);
          processTask(taskId).catch((error) => process.stderr.write(`[runner] ${taskId}: ${error.stack || error}\n`)).finally(() => active.delete(taskId));
        } catch (error) {
          process.stderr.write(`[runner] scan ${taskId}: ${error.message}\n`);
        }
      }
      if (once) {
        while (active.size) await sleep(100);
        const remaining = listTaskIds().some((id) => {
          try {
            const state = readTask(id);
            return !isTerminal(state.status) && !["submitting", "provider_processing", "downloading"].includes(state.status) && !isCancelled(id);
          } catch { return false; }
        });
        if (!remaining) break;
        continue;
      }
      await sleep(SCAN_MS);
    }
    while (active.size) await sleep(100);
  } finally {
    releaseLock();
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(THIS_FILE)) {
  run().catch((error) => { process.stderr.write(`[runner] fatal: ${error.stack || error}\n`); releaseLock(); process.exitCode = 1; });
}

export { processTask, recoverExpired, run };

export function ensureRunner() {
  fs.mkdirSync(TASK_ROOT, { recursive: true });
  const lock = readLock();
  if (lock?.pid) {
    try {
      process.kill(lock.pid, 0);
      // A live owner is authoritative even when its lease is near/just past expiry;
      // starting another child would only create a loser and can race recovery.
      return { started: false, pid: lock.pid, lease_until: lock.lease_until || null, owner_live: true };
    } catch { /* stale/dead owner: child may recover the lock */ }
  }
  const runnerPath = path.join(THIS_DIR, "runner.mjs");
  const child = spawn(nodeExecutable(), [runnerPath], { detached: true, stdio: "ignore", windowsHide: true, cwd: path.dirname(runnerPath), env: { ...process.env } });
  child.unref();
  return { started: true, pid: child.pid };
}
