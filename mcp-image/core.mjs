import crypto from "node:crypto";
import dns from "node:dns/promises";
import fs from "node:fs";
import net from "node:net";
import path from "node:path";

export const OUT_ROOT = path.resolve(process.env.IMAGE_OUT_DIR || "E:/UserData/xdrhh/.openclaw/workspace/image-runs");
export const TASK_ROOT = path.join(OUT_ROOT, ".image-tasks");
export const BASE = (process.env.IMAGE_BASE_URL || "https://code.mmkg.cloud/v1").replace(/\/+$/, "");
const configuredModel = (process.env.IMAGE_MODEL || "").trim();
export const DEFAULT_MODEL = (!configuredModel || configuredModel === "gpt-image-2" || configuredModel === "gpt-image-2.0") ? "gpt-image-2.5-flare" : configuredModel;
function envNumber(name, fallback, min, max) {
  const raw = process.env[name];
  const value = raw == null || raw === "" ? fallback : Number(raw);
  if (!Number.isFinite(value)) return fallback;
  return Math.min(max, Math.max(min, value));
}

export const API_TIMEOUT_MS = envNumber("IMAGE_API_TIMEOUT_MS", 300000, 1000, 1800000);
export const DOWNLOAD_TIMEOUT_MS = envNumber("IMAGE_DOWNLOAD_TIMEOUT_MS", 180000, 1000, 1800000);
export const TASK_DEADLINE_MS = envNumber("IMAGE_TASK_DEADLINE_MS", 1800000, 1000, 86400000);
export const POLL_MS = envNumber("IMAGE_POLL_MS", 700, 50, 60000);
export const MAX_IMAGE_BYTES = envNumber("IMAGE_MAX_BYTES", 50 * 1024 * 1024, 1024, 512 * 1024 * 1024);
export const MAX_RESPONSE_BYTES = envNumber("IMAGE_MAX_RESPONSE_BYTES", 20 * 1024 * 1024, 4096, 512 * 1024 * 1024);
export const MAX_PROMPT_CHARS = envNumber("IMAGE_MAX_PROMPT_CHARS", 10000, 1, 1000000);

export function nodeExecutable() {
  const candidates = [process.env.NODE_REAL_PATH, process.execPath];
  const nvmRoot = process.env.NVM_HOME || path.join(process.env.LOCALAPPDATA || "", "nvm");
  if (nvmRoot && fs.existsSync(nvmRoot)) {
    for (const entry of fs.readdirSync(nvmRoot).sort().reverse()) candidates.push(path.join(nvmRoot, entry, "node.exe"));
  }
  return candidates.find((candidate) => candidate && fs.existsSync(candidate) && path.basename(candidate).toLowerCase() === "node.exe") || process.execPath;
}

const USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) mcp-image/2.0";
const TERMINAL = new Set(["completed", "failed", "cancelled", "submission_unknown"]);
const TASK_ID_RE = /^img-[A-Za-z0-9_-]+$/;
const BATCH_ID_RE = /^batch-[A-Za-z0-9_-]+$/;

export class ImageError extends Error {
  constructor(message, code = "IMAGE_ERROR", extra = {}) {
    super(message);
    this.name = "ImageError";
    this.code = code;
    Object.assign(this, extra);
  }
}

export class HttpError extends ImageError {
  constructor(status, body, retryAfterMs = 0) {
    const unknownSubmission = status === 408 || status === 429 || status >= 500;
    super(`HTTP ${status}: ${String(body || "").slice(0, 500)}`, "HTTP_ERROR", { status, body: String(body || ""), retryAfterMs, unknownSubmission });
  }
}

function iso(ms = Date.now()) {
  return new Date(ms).toISOString();
}

function stamp() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`;
}

function randomId(prefix) {
  return `${prefix}-${stamp()}-${crypto.randomBytes(5).toString("hex")}`;
}

function stableValue(value) {
  if (Array.isArray(value)) return value.map(stableValue);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.keys(value).sort().map((key) => [key, stableValue(value[key])]));
  }
  return value;
}

function stableJson(value) {
  return JSON.stringify(stableValue(value));
}

function ensureRoots() {
  fs.mkdirSync(OUT_ROOT, { recursive: true });
  fs.mkdirSync(TASK_ROOT, { recursive: true });
}

function atomicWrite(file, value) {
  const dir = path.dirname(file);
  fs.mkdirSync(dir, { recursive: true });
  const tmp = `${file}.${process.pid}.${crypto.randomBytes(4).toString("hex")}.tmp`;
  const backup = `${file}.bak`;
  const text = typeof value === "string" ? value : JSON.stringify(value, null, 2);
  fs.writeFileSync(tmp, text, "utf8");
  let lastError;
  for (let attempt = 0; attempt < 20; attempt++) {
    try {
      fs.renameSync(tmp, file);
      try { fs.rmSync(backup, { force: true }); } catch { /* backup cleanup is best effort */ }
      return;
    } catch (error) {
      lastError = error;
      if (!["EEXIST", "EPERM", "EBUSY", "EACCES"].includes(error.code)) break;
      try {
        if (fs.existsSync(file)) {
          try { fs.rmSync(backup, { force: true }); } catch { /* retry below */ }
          fs.renameSync(file, backup);
        }
        fs.renameSync(tmp, file);
        try { fs.rmSync(backup, { force: true }); } catch { /* stale backup is recoverable */ }
        return;
      } catch (replacementError) {
        lastError = replacementError;
        if (!fs.existsSync(file) && fs.existsSync(backup)) {
          try { fs.renameSync(backup, file); } catch { /* preserve backup for read recovery */ }
        }
        if (!["EPERM", "EBUSY", "EACCES", "EEXIST"].includes(replacementError.code)) break;
      }
      const until = Date.now() + Math.min(50, 5 * (attempt + 1));
      while (Date.now() < until) { /* retry Windows file-share replacement */ }
    }
  }
  fs.rmSync(tmp, { force: true });
  throw lastError;
}

function atomicBinaryWrite(file, bytes) {
  const dir = path.dirname(file);
  fs.mkdirSync(dir, { recursive: true });
  const tmp = `${file}.${process.pid}.${crypto.randomBytes(4).toString("hex")}.part`;
  const backup = `${file}.bak`;
  fs.writeFileSync(tmp, bytes);
  let lastError;
  for (let attempt = 0; attempt < 20; attempt++) {
    try {
      fs.renameSync(tmp, file);
      try { fs.rmSync(backup, { force: true }); } catch { /* backup cleanup is best effort */ }
      return;
    } catch (error) {
      lastError = error;
      if (!["EEXIST", "EPERM", "EBUSY", "EACCES"].includes(error.code)) break;
      try {
        if (fs.existsSync(file)) {
          try { fs.rmSync(backup, { force: true }); } catch { /* retry below */ }
          fs.renameSync(file, backup);
        }
        fs.renameSync(tmp, file);
        try { fs.rmSync(backup, { force: true }); } catch { /* stale backup is recoverable */ }
        return;
      } catch (replacementError) {
        lastError = replacementError;
        if (!fs.existsSync(file) && fs.existsSync(backup)) {
          try { fs.renameSync(backup, file); } catch { /* preserve backup for read recovery */ }
        }
        if (!["EPERM", "EBUSY", "EACCES", "EEXIST"].includes(replacementError.code)) break;
      }
      const until = Date.now() + Math.min(50, 5 * (attempt + 1));
      while (Date.now() < until) { /* retry Windows file-share replacement */ }
    }
  }
  fs.rmSync(tmp, { force: true });
  throw lastError;
}

function publishExclusive(tmp, target) {
  try {
    // Hard links provide an atomic create-if-absent operation on Windows.
    fs.linkSync(tmp, target);
    fs.rmSync(tmp, { force: true });
  } catch (error) {
    fs.rmSync(tmp, { force: true });
    throw error;
  }
}

function appendEvent(taskDir, event) {
  fs.appendFileSync(path.join(taskDir, "events.jsonl"), `${JSON.stringify({ at: iso(), ...event })}\n`, "utf8");
}

function isWithin(root, candidate) {
  const rel = path.relative(root, candidate);
  return rel === "" || (rel && !rel.startsWith("..") && !path.isAbsolute(rel));
}

function canonicalPath(candidate) {
  let probe = candidate;
  const missing = [];
  while (!fs.existsSync(probe)) {
    const parent = path.dirname(probe);
    if (parent === probe) break;
    missing.unshift(path.basename(probe));
    probe = parent;
  }
  let resolved = fs.realpathSync.native(probe);
  for (const part of missing) resolved = path.join(resolved, part);
  return path.resolve(resolved);
}

function resolveOutputBase(requested) {
  const candidate = path.resolve(requested ? (path.isAbsolute(requested) ? requested : path.join(OUT_ROOT, requested)) : OUT_ROOT);
  const canonicalRoot = canonicalPath(OUT_ROOT);
  const canonicalCandidate = canonicalPath(candidate);
  if (process.env.IMAGE_ALLOW_EXTERNAL_OUTPUT !== "1" && !isWithin(canonicalRoot, canonicalCandidate)) {
    throw new ImageError("output_dir 必须位于 IMAGE_OUT_DIR 内（如需外部目录请显式设置 IMAGE_ALLOW_EXTERNAL_OUTPUT=1）", "INVALID_OUTPUT_DIR");
  }
  if (canonicalCandidate.split(path.sep).includes(".image-tasks")) {
    throw new ImageError("output_dir 不能指向任务内部目录", "INVALID_OUTPUT_DIR");
  }
  return candidate;
}

function taskDir(taskId) {
  if (!TASK_ID_RE.test(taskId)) throw new ImageError("task_id 格式无效", "INVALID_TASK_ID");
  return path.join(TASK_ROOT, taskId);
}

function batchDir(batchId) {
  if (!BATCH_ID_RE.test(batchId)) throw new ImageError("batch_id 格式无效", "INVALID_BATCH_ID");
  return path.join(OUT_ROOT, ".image-batches", batchId);
}

function stateFile(taskId) {
  return path.join(taskDir(taskId), "state.json");
}

function readJson(file) {
  let lastError;
  for (let attempt = 0; attempt < 20; attempt++) {
    try {
      return JSON.parse(fs.readFileSync(file, "utf8"));
    } catch (error) {
      lastError = error;
      if (!(["ENOENT", "EBUSY", "EPERM"].includes(error.code) || error instanceof SyntaxError)) break;
      const until = Date.now() + 5;
      while (Date.now() < until) { /* allow Windows rename replacement to finish */ }
    }
  }
  throw new ImageError(`无法读取 JSON：${file}（${lastError?.message || "未知错误"}）`, "CORRUPT_STATE");
}

export function readTask(taskId) {
  const file = stateFile(taskId);
  for (let attempt = 0; attempt < 20; attempt++) {
    if (fs.existsSync(file)) return readJson(file);
    const until = Date.now() + 5;
    while (Date.now() < until) { /* allow Windows rename replacement to finish */ }
  }
  throw new ImageError(`任务不存在：${taskId}`, "TASK_NOT_FOUND");
}

export function listTaskIds() {
  ensureRoots();
  return fs.readdirSync(TASK_ROOT, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && TASK_ID_RE.test(entry.name))
    .map((entry) => entry.name);
}

export function isTerminal(status) {
  return TERMINAL.has(status);
}

export function isCancelled(taskId) {
  return fs.existsSync(path.join(taskDir(taskId), "cancel.request"));
}

function taskLockFile(taskId) {
  return path.join(taskDir(taskId), "update.lock");
}

function withTaskLock(taskId, fn) {
  const file = taskLockFile(taskId);
  for (let attempt = 0; attempt < 100; attempt++) {
    const token = `${process.pid}-${crypto.randomBytes(8).toString("hex")}`;
    const tmp = `${file}.${token}.tmp`;
    try {
      atomicWrite(tmp, { pid: process.pid, token, at: iso() });
      try { publishExclusive(tmp, file); }
      catch (error) {
        fs.rmSync(tmp, { force: true });
        if (error.code !== "EEXIST" && error.code !== "EPERM" && error.code !== "EACCES") throw error;
        throw Object.assign(new Error("lock exists"), { code: "EEXIST" });
      }
      try { return fn(); }
      finally {
        try {
          const holder = JSON.parse(fs.readFileSync(file, "utf8"));
          if (holder?.pid === process.pid && holder?.token === token) fs.rmSync(file, { force: true });
        } catch { /* another process may have recovered the lock */ }
      }
    } catch (error) {
      fs.rmSync(tmp, { force: true });
      if (error.code !== "EEXIST") throw error;
      let stale = false;
      let observedToken = null;
      try {
        const holder = JSON.parse(fs.readFileSync(file, "utf8"));
        observedToken = holder?.token || null;
        try { process.kill(holder.pid, 0); } catch { stale = true; }
      } catch { /* incomplete publication: wait, do not delete */ }
      if (stale && observedToken) {
        try {
          const current = JSON.parse(fs.readFileSync(file, "utf8"));
          if (current?.token === observedToken) fs.rmSync(file, { force: true });
        } catch { /* creator may be replacing it */ }
      } else {
        const until = Date.now() + 5;
        while (Date.now() < until) { /* serialize cross-process state updates */ }
      }
    }
  }
  throw new ImageError("任务状态正在被另一个进程更新", "TASK_UPDATE_BUSY");
}

export function updateTask(taskId, patch, event = {}) {
  return withTaskLock(taskId, () => {
    const dir = taskDir(taskId);
    const current = readTask(taskId);
    const next = { ...current, ...patch, updated_at: iso() };
    atomicWrite(path.join(dir, "state.json"), next);
    if (event.type || patch.status && patch.status !== current.status) {
      appendEvent(dir, { type: event.type || "state", from: current.status, to: next.status, ...event });
    }
    if (next.output_dir) writeManifest(next);
    return next;
  });
}

export function writeManifest(state) {
  if (!state.output_dir) return;
  const manifest = {
    version: 2,
    task_id: state.task_id,
    batch_id: state.batch_id || null,
    operation_id: state.operation_id,
    status: state.status,
    request: state.request,
    expected_count: state.request?.n || 1,
    files: state.outputs || [],
    error: state.error || null,
    created_at: state.created_at,
    updated_at: state.updated_at,
    completed_at: state.completed_at || null,
  };
  atomicWrite(path.join(state.output_dir, "manifest.json"), manifest);
}

export function normaliseRequest(args) {
  const prompt = String(args.prompt || "").trim();
  if (!prompt) throw new ImageError("prompt 不能为空", "INVALID_PROMPT");
  if (prompt.length > MAX_PROMPT_CHARS) throw new ImageError(`prompt 超过 ${MAX_PROMPT_CHARS} 个字符`, "PROMPT_TOO_LONG");
  const n = Number(args.n || 1);
  if (!Number.isInteger(n) || n < 1 || n > 10) throw new ImageError("n 必须是 1-10 的整数", "INVALID_N");
  let model = String(args.model || DEFAULT_MODEL).trim();
  if (model === "gpt-image-2" || model === "gpt-image-2.0" || model === "gpt-image-2.5") {
    model = "gpt-image-2.5-flare";
  }
  if (!model || model.length > 200) throw new ImageError("model 无效", "INVALID_MODEL");
  const size = String(args.size || "1024x1024");
  if (!["auto", "1024x1024", "1536x1024", "1024x1536"].includes(size)) throw new ImageError("size 必须是 auto、1024x1024、1536x1024 或 1024x1536", "INVALID_SIZE");
  const request = { model, prompt, n, size };
  if (args.quality) {
    const quality = String(args.quality);
    if (!["auto", "low", "medium", "high"].includes(quality)) throw new ImageError("quality 必须是 auto、low、medium 或 high", "INVALID_QUALITY");
    request.quality = quality;
  }
  if (args.background) {
    const background = String(args.background);
    if (!["auto", "transparent", "opaque"].includes(background)) throw new ImageError("background 必须是 auto、transparent 或 opaque", "INVALID_BACKGROUND");
    request.background = background;
  }
  return request;
}

function displayJobId(job, index) {
  return String(job.id || `job-${String(index + 1).padStart(3, "0")}`);
}

export function prepareBatchJobs(jobs) {
  if (!Array.isArray(jobs) || !jobs.length || jobs.length > 200) {
    throw new ImageError("jobs 必须是 1-200 项数组", "INVALID_JOBS");
  }
  const seenIds = new Set();
  const seenOperations = new Set();
  return jobs.map((job, index) => {
    if (!job || typeof job !== "object") throw new ImageError(`第 ${index + 1} 项 job 无效`, "INVALID_JOB");
    const id = displayJobId(job, index);
    if (seenIds.has(id)) throw new ImageError(`job id 重复：${id}`, "DUPLICATE_JOB_ID");
    seenIds.add(id);
    const request = normaliseRequest(job);
    const operation_id = job.operation_id ? String(job.operation_id) : null;
    if (operation_id && operation_id.length > 500) throw new ImageError(`第 ${index + 1} 项 operation_id 无效`, "INVALID_OPERATION_ID");
    if (operation_id && seenOperations.has(operation_id)) throw new ImageError(`operation_id 重复：${operation_id}`, "DUPLICATE_OPERATION_ID");
    if (operation_id) seenOperations.add(operation_id);
    const fingerprint = crypto.createHash("sha256").update(stableJson({ id, request, operation_id })).digest("hex");
    return { index, id, request, operation_id, fingerprint };
  });
}

export function batchInputFingerprint(preparedJobs) {
  const jobs = (preparedJobs || []).map(({ id, request, operation_id, fingerprint }) => ({ id, request, operation_id, fingerprint }));
  return crypto.createHash("sha256").update(stableJson(jobs)).digest("hex");
}

function findOperation(operationId) {
  if (!operationId) return null;
  for (const id of listTaskIds()) {
    try {
      const state = readTask(id);
      if (state.operation_id === operationId) return state;
    } catch {
      // A partially created task is ignored; the next call can repair it.
    }
  }
  return null;
}

function operationLockFile(operationId) {
  const digest = crypto.createHash("sha256").update(operationId).digest("hex");
  return path.join(TASK_ROOT, `.operation-${digest}.lock`);
}

function acquireOperationLock(operationId) {
  const file = operationLockFile(operationId);
  for (let attempt = 0; attempt < 40; attempt++) {
    const token = `${process.pid}-${crypto.randomBytes(8).toString("hex")}`;
    const tmp = `${file}.${token}.tmp`;
    try {
      atomicWrite(tmp, { pid: process.pid, token, operation_id: operationId, at: iso() });
      try { publishExclusive(tmp, file); }
      catch (error) {
        fs.rmSync(tmp, { force: true });
        if (error.code !== "EEXIST" && error.code !== "EPERM" && error.code !== "EACCES") throw error;
        throw Object.assign(new Error("lock exists"), { code: "EEXIST" });
      }
      return { file, token };
    } catch (error) {
      fs.rmSync(tmp, { force: true });
      if (error.code !== "EEXIST") throw error;
      const existing = findOperation(operationId);
      if (existing) return null;
      let stale = false;
      let observedToken = null;
      try {
        const holder = JSON.parse(fs.readFileSync(file, "utf8"));
        observedToken = holder?.token || null;
        if (!holder?.pid) stale = false;
        else { try { process.kill(holder.pid, 0); } catch { stale = true; } }
      } catch { /* incomplete publication: wait, do not delete */ }
      if (stale && observedToken) {
        try {
          const current = JSON.parse(fs.readFileSync(file, "utf8"));
          if (current?.token === observedToken) fs.rmSync(file, { force: true });
        } catch { /* creator may be replacing it */ }
      } else {
        const until = Date.now() + 5;
        while (Date.now() < until) { /* wait for creator to publish state */ }
      }
    }
  }
  throw new ImageError("operation_id 正在被另一个请求创建", "OPERATION_BUSY");
}

function releaseOperationLock(lock) {
  if (!lock) return;
  const file = typeof lock === "string" ? lock : lock.file;
  const token = typeof lock === "string" ? null : lock.token;
  try {
    const current = JSON.parse(fs.readFileSync(file, "utf8"));
    if (!token || current?.token === token) fs.rmSync(file, { force: true });
  } catch {
    // Do not remove an unreadable or already-replaced lock.
  }
}

export function createTask(args, options = {}) {
  ensureRoots();
  const request = normaliseRequest(args);
  const operationId = String(args.operation_id || options.operation_id || randomId("op"));
  const base = resolveOutputBase(args.output_dir || options.output_dir);
  const batchId = options.batch_id || args.batch_id || null;
  const requestFingerprint = crypto.createHash("sha256").update(JSON.stringify({ request, batch_id: batchId, output_base: base })).digest("hex");
  const lock = acquireOperationLock(operationId);
  if (!lock) {
    const existing = findOperation(operationId);
    if (!existing) throw new ImageError("operation_id 已被占用但任务尚未可读", "OPERATION_BUSY");
    if (existing.request_fingerprint !== requestFingerprint) throw new ImageError("operation_id 已用于不同请求", "OPERATION_CONFLICT");
    return { state: existing, reused: true };
  }
  try {
    const existing = findOperation(operationId);
    if (existing) {
      if (existing.request_fingerprint !== requestFingerprint) throw new ImageError("operation_id 已用于不同请求", "OPERATION_CONFLICT");
      return { state: existing, reused: true };
    }

    const taskId = randomId("img");
    const dir = taskDir(taskId);
    const outputDir = path.join(base, taskId);
    fs.mkdirSync(dir, { recursive: true });
    fs.mkdirSync(outputDir, { recursive: true });
    const now = Date.now();
    const state = {
      version: 2,
      task_id: taskId,
      batch_id: batchId,
      operation_id: operationId,
      request_fingerprint: requestFingerprint,
      status: "queued",
      request,
      output_dir: outputDir,
      outputs: [],
      attempt: 0,
      created_at: iso(now),
      updated_at: iso(now),
      deadline_at: iso(now + TASK_DEADLINE_MS),
      lease_until: null,
      error: null,
      cancel_requested: false,
      batch_concurrency: options.concurrency ? Math.max(1, Math.min(Number(options.concurrency) || 4, 8)) : null,
    };
    atomicWrite(path.join(dir, "request.json"), { operation_id: operationId, request, created_at: state.created_at });
    atomicWrite(path.join(dir, "state.json"), state);
    appendEvent(dir, { type: "created", status: "queued" });
    writeManifest(state);
    return { state, reused: false };
  } finally {
    releaseOperationLock(lock);
  }
}

export function requestCancel(taskId) {
  return withTaskLock(taskId, () => {
    const state = readTask(taskId);
    if (isTerminal(state.status)) return state;
    const dir = taskDir(taskId);
    atomicWrite(path.join(dir, "cancel.request"), { task_id: taskId, requested_at: iso() });
    const now = iso();
    const patch = state.status === "queued"
      ? { status: "cancelled", cancel_requested: true, completed_at: now, error: { code: "CANCELLED", message: "任务在开始前被取消" } }
      : { cancel_requested: true };
    const next = { ...state, ...patch, updated_at: now };
    atomicWrite(path.join(dir, "state.json"), next);
    appendEvent(dir, {
      type: state.status === "queued" ? "cancelled" : "cancel_requested",
      from: state.status,
      to: next.status,
    });
    if (next.output_dir) writeManifest(next);
    return next;
  });
}

export function validateOutputs(state) {
  const outputs = Array.isArray(state.outputs) ? state.outputs : [];
  const valid = [];
  for (const item of outputs) {
    if (!item?.file || !item?.sidecar) continue;
    try {
      const stat = fs.statSync(item.file);
      if (!stat.isFile() || stat.size <= 0) continue;
      const sidecar = readJson(item.sidecar);
      if (path.resolve(sidecar.file) !== path.resolve(item.file)) continue;
      if (sidecar.task_id !== state.task_id || sidecar.operation_id !== state.operation_id) continue;
      if (Number(sidecar.bytes) !== stat.size || !/^[a-f0-9]{64}$/i.test(String(sidecar.sha256 || ""))) continue;
      const digest = crypto.createHash("sha256").update(fs.readFileSync(item.file)).digest("hex");
      if (digest.toLowerCase() !== String(sidecar.sha256).toLowerCase()) continue;
      valid.push({ ...item, bytes: stat.size, sha256: digest });
    } catch {
      // Invalid or partial artifacts are never reported as completed.
    }
  }
  return valid;
}

export function repairTask(taskId) {
  const state = readTask(taskId);
  const valid = validateOutputs(state);
  if (state.status === "completed" && valid.length !== state.request.n) {
    return updateTask(taskId, { status: "failed", outputs: valid, error: { code: "OUTPUT_INCOMPLETE", message: `已落盘 ${valid.length}/${state.request.n} 张图片` } }, { type: "repaired_incomplete" });
  }
  if (state.status !== "completed" && valid.length === state.request.n && !state.error) {
    return updateTask(taskId, { status: "completed", outputs: valid, completed_at: iso() }, { type: "repaired_completed" });
  }
  return state;
}

const RESPONSE_CONTROL = Symbol("mcpImageResponseControl");

export async function fetchWithTimeout(url, init = {}, timeoutMs = API_TIMEOUT_MS, externalSignal) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(new Error("timeout")), timeoutMs);
  const onAbort = () => controller.abort(new Error("cancelled"));
  const cleanup = () => {
    clearTimeout(timer);
    externalSignal?.removeEventListener("abort", onAbort);
  };
  if (externalSignal) {
    if (externalSignal.aborted) onAbort();
    else externalSignal.addEventListener("abort", onAbort, { once: true });
  }
  try {
    const response = await fetch(url, { ...init, signal: controller.signal });
    Object.defineProperty(response, RESPONSE_CONTROL, { value: { controller, cleanup }, configurable: true });
    return response;
  } catch (error) {
    cleanup();
    if (controller.signal.aborted) {
      const reason = controller.signal.reason?.message || "请求中止";
      throw new ImageError(reason === "cancelled" ? "任务已取消" : `请求超时（${timeoutMs / 1000}s）`, reason === "cancelled" ? "CANCELLED" : "REQUEST_TIMEOUT", { unknownSubmission: true });
    }
    throw new ImageError(`网络请求失败：${error.message}`, "NETWORK_ERROR", { unknownSubmission: true });
  }
}

export async function readResponseBody(response, mode = "text", options = {}) {
  const control = response?.[RESPONSE_CONTROL];
  const maxBytes = options.maxBytes || MAX_RESPONSE_BYTES;
  const bodyTimeoutMs = Number(options.timeoutMs || 0);
  const bodyTimer = bodyTimeoutMs > 0 && control?.controller
    ? setTimeout(() => control.controller.abort(new Error("body timeout")), bodyTimeoutMs)
    : null;
  try {
    const length = Number(response?.headers?.get?.("content-length") || 0);
    if (length > maxBytes) throw new ImageError(`响应体超过 ${maxBytes} 字节上限`, "RESPONSE_TOO_LARGE", { unknownSubmission: options.unknownSubmission !== false });
    if (!response?.body) {
      const raw = mode === "arrayBuffer" ? Buffer.from(await response.arrayBuffer()) : Buffer.from(await response.text(), "utf8");
      if (raw.length > maxBytes) throw new ImageError(`响应体超过 ${maxBytes} 字节上限`, "RESPONSE_TOO_LARGE", { unknownSubmission: options.unknownSubmission !== false });
      return mode === "arrayBuffer" ? raw.buffer.slice(raw.byteOffset, raw.byteOffset + raw.byteLength) : raw.toString("utf8");
    }
    const chunks = [];
    let total = 0;
    for await (const chunk of response.body) {
      const part = Buffer.from(chunk);
      total += part.length;
      if (total > maxBytes) {
        control?.controller.abort(new Error("response too large"));
        throw new ImageError(`响应体超过 ${maxBytes} 字节上限`, "RESPONSE_TOO_LARGE", { unknownSubmission: options.unknownSubmission !== false });
      }
      chunks.push(part);
    }
    const raw = Buffer.concat(chunks);
    return mode === "arrayBuffer" ? raw.buffer.slice(raw.byteOffset, raw.byteOffset + raw.byteLength) : raw.toString("utf8");
  } catch (error) {
    if (error instanceof ImageError) throw error;
    if (control?.controller.signal.aborted) {
      const reason = control.controller.signal.reason?.message || "请求中止";
      throw new ImageError(reason === "cancelled" ? "任务已取消" : `响应体读取超时（${options.timeoutMs || ""}）`, reason === "cancelled" ? "CANCELLED" : (options.timeoutCode || "REQUEST_TIMEOUT"), { unknownSubmission: options.unknownSubmission !== false });
    }
    throw new ImageError(`响应体读取失败：${error.message}`, options.errorCode || "RESPONSE_BODY_ERROR", { unknownSubmission: options.unknownSubmission !== false });
  } finally {
    if (bodyTimer) clearTimeout(bodyTimer);
    control?.cleanup();
  }
}

export function releaseResponse(response) {
  response?.[RESPONSE_CONTROL]?.cleanup();
}

export async function requestJson(endpoint, body, options = {}) {
  const key = process.env.IMAGE_API_KEY || "";
  if (!key) throw new ImageError("未配置 IMAGE_API_KEY 环境变量", "MISSING_API_KEY");
  const timeoutMs = options.timeoutMs || API_TIMEOUT_MS;
  const res = await fetchWithTimeout(`${BASE}${endpoint}`, {
    method: body ? "POST" : "GET",
    headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json", "User-Agent": USER_AGENT, ...(options.headers || {}) },
    body: body ? JSON.stringify(body) : undefined,
  }, timeoutMs, options.signal);
  const text = await readResponseBody(res, "text", { timeoutMs, unknownSubmission: body != null });
  if (!res.ok) {
    const retryAfter = res.headers.get("retry-after");
    const retryAfterMs = retryAfter && /^\d+(?:\.\d+)?$/.test(retryAfter)
      ? Number(retryAfter) * 1000
      : retryAfter ? Math.max(0, Date.parse(retryAfter) - Date.now()) : 0;
    throw new HttpError(res.status, text, retryAfterMs);
  }
  try {
    return JSON.parse(text);
  } catch {
    throw new ImageError("上游返回了非 JSON 响应", "INVALID_JSON_RESPONSE", { unknownSubmission: body != null });
  }
}

function isPrivateHost(hostname) {
  const host = String(hostname || "").toLowerCase().replace(/[\[\]]/g, "");
  if (host === "localhost" || host.endsWith(".localhost") || host === "0.0.0.0" || host === "::1") return true;
  if (/^127\./.test(host) || /^10\./.test(host) || /^192\.168\./.test(host) || /^169\.254\./.test(host)) return true;
  const match = host.match(/^172\.(\d+)\./);
  if (match && Number(match[1]) >= 16 && Number(match[1]) <= 31) return true;
  if (net.isIP(host) === 6 && (host === "::" || host.startsWith("fc") || host.startsWith("fd") || host.startsWith("fe8") || host.startsWith("fe9") || host.startsWith("fea") || host.startsWith("feb"))) return true;
  return false;
}

async function resolvesToPrivateHost(hostname) {
  if (net.isIP(hostname)) return isPrivateHost(hostname);
  try {
    const records = await dns.lookup(hostname, { all: true, verbatim: true });
    return records.some((record) => isPrivateHost(record.address));
  } catch {
    return false;
  }
}

function validateImageUrl(url) {
  let parsed;
  try { parsed = new URL(url); } catch { throw new ImageError("图片 URL 无效", "INVALID_IMAGE_URL"); }
  if (!/^https?:$/.test(parsed.protocol)) throw new ImageError("图片 URL 必须使用 http 或 https", "INVALID_IMAGE_URL");
  return parsed;
}

async function downloadBytes(url, signal) {
  const parsed = validateImageUrl(url);
  const allowedHost = new URL(BASE).hostname;
  if (parsed.hostname !== allowedHost && process.env.IMAGE_ALLOW_EXTERNAL_IMAGE_HOSTS === "0") throw new ImageError("图片 URL 主机不是配置的图片服务主机", "IMAGE_HOST_NOT_ALLOWED");
  if (await resolvesToPrivateHost(parsed.hostname) && parsed.hostname !== allowedHost) throw new ImageError("图片 URL 不允许指向本机或私有网络", "IMAGE_HOST_NOT_ALLOWED");
  const res = await fetchWithTimeout(parsed.href, { headers: { "User-Agent": USER_AGENT }, redirect: "manual" }, DOWNLOAD_TIMEOUT_MS, signal);
  if (res.status >= 300 && res.status < 400) {
    const location = res.headers.get("location");
    releaseResponse(res);
    throw new ImageError(`图片下载重定向被拒绝${location ? `：${location}` : ""}`, "IMAGE_REDIRECT_REJECTED");
  }
  const contentType = (res.headers.get("content-type") || "").toLowerCase();
  if (!res.ok) {
    const text = await readResponseBody(res, "text", { timeoutMs: DOWNLOAD_TIMEOUT_MS, maxBytes: MAX_RESPONSE_BYTES, unknownSubmission: false });
    throw new HttpError(res.status, text, 0);
  }
  if (!contentType || (!contentType.startsWith("image/") && !contentType.includes("octet-stream"))) {
    releaseResponse(res);
    throw new ImageError(`图片下载返回了非图片 Content-Type：${contentType || "缺失"}`, "INVALID_IMAGE_CONTENT_TYPE");
  }
  const bytes = Buffer.from(await readResponseBody(res, "arrayBuffer", { timeoutMs: DOWNLOAD_TIMEOUT_MS, maxBytes: MAX_IMAGE_BYTES, unknownSubmission: false }));
  if (!bytes.length) throw new ImageError("图片下载为空", "EMPTY_IMAGE");
  const validMagic = (bytes[0] === 0x89 && bytes[1] === 0x50 && bytes[2] === 0x4e && bytes[3] === 0x47)
    || (bytes[0] === 0xff && bytes[1] === 0xd8)
    || (bytes[0] === 0x52 && bytes[1] === 0x49 && bytes[2] === 0x46 && bytes[3] === 0x46);
  if (!validMagic) throw new ImageError("图片下载内容不是可识别的 PNG/JPEG/WebP", "INVALID_IMAGE_FORMAT");
  const ext = contentType.includes("jpeg") ? "jpg" : contentType.includes("webp") ? "webp" : "png";
  return { bytes, ext, sourceUrl: parsed.href, contentType };
}

export async function saveImageItem(item, state, index, signal) {
  let bytes;
  let ext = "png";
  let sourceUrl = null;
  let contentType = "image/png";
  if (item?.b64_json) {
    const encoded = String(item.b64_json);
    if (encoded.length > Math.ceil(MAX_IMAGE_BYTES * 4 / 3) + 16) throw new ImageError(`第 ${index} 张图片超过 ${MAX_IMAGE_BYTES} 字节上限`, "IMAGE_TOO_LARGE");
    if (!/^[A-Za-z0-9+/]*={0,2}$/.test(encoded) || encoded.length % 4 === 1) throw new ImageError(`第 ${index} 张图片 base64 无效`, "INVALID_IMAGE_BASE64");
    bytes = Buffer.from(encoded, "base64");
    if (!bytes.length) throw new ImageError(`第 ${index} 张图片 base64 为空`, "EMPTY_IMAGE");
    if (bytes.length > MAX_IMAGE_BYTES) throw new ImageError(`第 ${index} 张图片超过 ${MAX_IMAGE_BYTES} 字节上限`, "IMAGE_TOO_LARGE");
    if (!(bytes[0] === 0x89 && bytes[1] === 0x50 && bytes[2] === 0x4e && bytes[3] === 0x47) && !(bytes[0] === 0xff && bytes[1] === 0xd8) && !(bytes[0] === 0x52 && bytes[1] === 0x49 && bytes[2] === 0x46 && bytes[3] === 0x46)) {
      throw new ImageError(`第 ${index} 张图片格式无法识别`, "INVALID_IMAGE_FORMAT");
    }
  } else if (item?.url) {
    ({ bytes, ext, sourceUrl, contentType } = await downloadBytes(item.url, signal));
  } else {
    throw new ImageError(`第 ${index} 张响应中既无 b64_json 也无 url`, "INVALID_IMAGE_RESPONSE");
  }
  const name = `img-${String(index).padStart(2, "0")}`;
  const file = path.join(state.output_dir, `${name}.${ext}`);
  const sidecar = path.join(state.output_dir, `${name}.json`);
  const sha256 = crypto.createHash("sha256").update(bytes).digest("hex");
  atomicBinaryWrite(file, bytes);
  const meta = {
    version: 2,
    task_id: state.task_id,
    operation_id: state.operation_id,
    request: state.request,
    base_url: BASE,
    created: iso(),
    file,
    bytes: bytes.length,
    sha256,
    content_type: contentType,
    revised_prompt: item.revised_prompt || null,
    source_url: sourceUrl,
  };
  atomicWrite(sidecar, meta);
  return { index, file, sidecar, bytes: bytes.length, sha256, revised_prompt: item.revised_prompt || null, source_url: sourceUrl };
}

export function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function waitForTask(taskId, seconds = 0) {
  const budget = Math.max(0, Math.min(Number(seconds) || 0, 25)) * 1000;
  const end = Date.now() + budget;
  let state = repairTask(taskId);
  while (!isTerminal(state.status) && Date.now() < end) {
    await sleep(Math.min(POLL_MS, Math.max(50, end - Date.now())));
    state = repairTask(taskId);
  }
  return state;
}

export function listTasks(filter = {}) {
  const rows = [];
  for (const id of listTaskIds()) {
    try {
      const state = repairTask(id);
      if (filter.status && state.status !== filter.status) continue;
      if (filter.batch_id && state.batch_id !== filter.batch_id) continue;
      rows.push({ task_id: id, status: state.status, batch_id: state.batch_id, operation_id: state.operation_id, outputs: state.outputs || [], output_dir: state.output_dir, error: state.error, updated_at: state.updated_at });
    } catch {
      // Ignore incomplete task directories in list output.
    }
  }
  return rows.sort((a, b) => String(b.updated_at).localeCompare(String(a.updated_at))).slice(0, Math.max(1, Math.min(Number(filter.limit) || 50, 200)));
}

function batchLockFile(batchId) {
  return path.join(batchDir(batchId), "update.lock");
}

function withBatchLock(batchId, fn) {
  const file = batchLockFile(batchId);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  for (let attempt = 0; attempt < 100; attempt++) {
    const token = `${process.pid}-${crypto.randomBytes(8).toString("hex")}`;
    const tmp = `${file}.${token}.tmp`;
    try {
      atomicWrite(tmp, { pid: process.pid, token, at: iso() });
      try {
        publishExclusive(tmp, file);
      } catch (error) {
        fs.rmSync(tmp, { force: true });
        if (!["EEXIST", "EPERM", "EACCES"].includes(error.code)) throw error;
        throw Object.assign(new Error("batch lock exists"), { code: "EEXIST" });
      }
      try {
        return fn();
      } finally {
        try {
          const holder = JSON.parse(fs.readFileSync(file, "utf8"));
          if (holder?.pid === process.pid && holder?.token === token) fs.rmSync(file, { force: true });
        } catch {
          // A replacement owner must not be removed by an older waiter.
        }
      }
    } catch (error) {
      fs.rmSync(tmp, { force: true });
      if (error.code !== "EEXIST") throw error;
      let stale = false;
      let observedToken = null;
      try {
        const holder = JSON.parse(fs.readFileSync(file, "utf8"));
        observedToken = holder?.token || null;
        if (holder?.pid) {
          try { process.kill(holder.pid, 0); } catch { stale = true; }
        }
      } catch {
        // Incomplete publication: wait, do not delete.
      }
      if (stale && observedToken) {
        try {
          const current = JSON.parse(fs.readFileSync(file, "utf8"));
          if (current?.token === observedToken) fs.rmSync(file, { force: true });
        } catch {
          // The creator may be completing publication.
        }
      } else {
        const until = Date.now() + Math.min(50, 5 * (attempt + 1));
        while (Date.now() < until) { /* serialize batch manifest updates */ }
      }
    }
  }
  throw new ImageError("批次状态正在被另一个进程更新", "BATCH_UPDATE_BUSY");
}

export function createBatch(jobs, concurrency = 4) {
  const prepared = prepareBatchJobs(jobs);
  const batchId = randomId("batch");
  const dir = batchDir(batchId);
  fs.mkdirSync(dir, { recursive: true });
  return withBatchLock(batchId, () => {
    const safeConcurrency = Math.max(1, Math.min(Number(concurrency) || 4, 8));
    const manifestFile = path.join(dir, "manifest.json");
    const manifest = {
      version: 3,
      batch_id: batchId,
      concurrency: safeConcurrency,
      created_at: iso(),
      input_fingerprint: batchInputFingerprint(prepared),
      input_count: prepared.length,
      jobs: [],
      error: null
    };
    atomicWrite(manifestFile, manifest);
    try {
      for (const item of prepared) {
        const cleaned = item.id.replace(/[^A-Za-z0-9_-]/g, "_").slice(0, 80) || `job-${item.index + 1}`;
        const suffix = crypto.createHash("sha256").update(`${item.id}\0${item.index}`).digest("hex").slice(0, 10);
        const taskLabel = `${cleaned}-${String(item.index + 1).padStart(3, "0")}-${suffix}`;
        const operationId = item.operation_id || `${batchId}:${taskLabel}`;
        const state = createTask(
          { ...item.request, output_dir: dir, operation_id: operationId },
          { batch_id: batchId, output_dir: dir, concurrency: safeConcurrency }
        ).state;
        manifest.jobs.push({
          id: item.id,
          index: item.index,
          fingerprint: item.fingerprint,
          request_fingerprint: state.request_fingerprint,
          operation_id: state.operation_id,
          request: state.request,
          task_id: state.task_id,
          status: state.status,
          output_dir: state.output_dir,
          expected_count: state.request.n,
          outputs: [],
          error: null
        });
        atomicWrite(manifestFile, manifest);
      }
    } catch (error) {
      manifest.error = formatError(error);
      manifest.failed_at = iso();
      atomicWrite(manifestFile, manifest);
      throw error;
    }
    return {
      batch_id: batchId,
      manifest_path: manifestFile,
      concurrency: safeConcurrency,
      input_fingerprint: manifest.input_fingerprint,
      tasks: manifest.jobs.map(({ id, task_id, status, fingerprint }) => ({ id, task_id, status, fingerprint }))
    };
  });
}


export function batchStatus(batchId) {
  return withBatchLock(batchId, () => {
    const file = path.join(batchDir(batchId), "manifest.json");
    if (!fs.existsSync(file)) throw new ImageError(`批次不存在：${batchId}`, "BATCH_NOT_FOUND");
    const manifest = readJson(file);
    if (!Array.isArray(manifest.jobs)) throw new ImageError("批次 manifest.jobs 无效", "CORRUPT_BATCH_MANIFEST");
    const jobs = manifest.jobs.map((job) => {
      try {
        const state = repairTask(job.task_id);
        const stateFingerprint = state.request_fingerprint || null;
        if (job.request_fingerprint && stateFingerprint && job.request_fingerprint !== stateFingerprint) {
          throw new ImageError(`批次任务 ${job.id} 的 request_fingerprint 不一致`, "CORRUPT_BATCH_MANIFEST");
        }
        const verified = state.status === "completed" ? validateOutputs(state) : [];
        return {
          ...job,
          status: state.status,
          request_fingerprint: stateFingerprint || job.request_fingerprint || null,
          operation_id: state.operation_id,
          request: state.request,
          expected_count: state.request?.n || job.expected_count || 1,
          outputs: state.outputs || [],
          verified_files: verified,
          output_dir: state.output_dir,
          error: state.error,
          attempt: state.attempt || 0,
          created_at: state.created_at,
          completed_at: state.completed_at || null,
          updated_at: state.updated_at
        };
      } catch (error) {
        const detail = formatError(error);
        return {
          ...job,
          status: "failed",
          outputs: [],
          verified_files: [],
          error: { ...detail, code: detail.code === "IMAGE_ERROR" ? "CORRUPT_TASK" : detail.code },
          updated_at: iso()
        };
      }
    });
    const counts = Object.fromEntries([...new Set([...jobs.map((j) => j.status), "queued", "submitting", "provider_processing", "downloading", "completed", "failed", "cancelled", "submission_unknown"])].map((status) => [status, jobs.filter((j) => j.status === status).length]));
    const verifiedFiles = jobs.flatMap((job) => job.verified_files || []);
    const next = { ...manifest, updated_at: iso(), counts, verified_files: verifiedFiles, files: verifiedFiles, jobs };
    atomicWrite(file, next);
    return next;
  });
}

export function formatError(error) {
  return { code: error.code || "IMAGE_ERROR", message: error.message || String(error), status: error.status || null, unknown_submission: Boolean(error.unknownSubmission) };
}
