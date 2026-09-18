// 可恢复批量驱动：创建持久化 batch 后轮询 manifest，不让 MCP 长请求承担生图时间。
// 用法：node batch.mjs jobs.json [并发=4] [等待秒=25]
//      node batch.mjs --resume batch-id [jobs.json] [等待秒=25]
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  POLL_MS,
  batchInputFingerprint,
  prepareBatchJobs,
  readTask,
  validateOutputs,
  nodeExecutable,
} from "./core.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SERVER = path.join(HERE, "server.js");
const argv = process.argv.slice(2);
const resumeIndex = argv.indexOf("--resume");
const isResume = resumeIndex >= 0;
const resumeBatchId = isResume ? argv[resumeIndex + 1] : null;
const BATCH_ID_RE = /^batch-[A-Za-z0-9_-]+$/;

function numeric(value) {
  return value != null && value !== "" && Number.isFinite(Number(value));
}

function boundedNumber(value, fallback, min, max, label) {
  const result = value == null || value === "" ? fallback : Number(value);
  if (!Number.isFinite(result) || result < min || result > max) {
    throw new Error(`${label} 必须是 ${min}-${max} 之间的数字`);
  }
  return result;
}

if (isResume && (!resumeBatchId || !BATCH_ID_RE.test(resumeBatchId))) {
  throw new Error("用法：node batch.mjs --resume batch-id [jobs.json] [等待秒=25]");
}
if (!isResume && argv.length < 1) {
  throw new Error("用法：node batch.mjs jobs.json [并发=4] [等待秒=25]");
}

let jobsFile = null;
let concurrency = 4;
let waitSeconds = 25;
if (isResume) {
  const candidate = argv[resumeIndex + 2];
  if (candidate && !numeric(candidate)) {
    jobsFile = candidate;
    waitSeconds = boundedNumber(argv[resumeIndex + 3], 25, 0, 25, "等待秒");
  } else {
    waitSeconds = boundedNumber(candidate, 25, 0, 25, "等待秒");
  }
} else {
  jobsFile = argv[0];
  concurrency = boundedNumber(argv[1], 4, 1, 8, "并发");
  waitSeconds = boundedNumber(argv[2], 25, 0, 25, "等待秒");
}

let jobs = null;
let preparedJobs = null;
if (jobsFile) {
  jobs = JSON.parse(fs.readFileSync(path.resolve(jobsFile), "utf8"));
  preparedJobs = prepareBatchJobs(jobs);
}

const srv = spawn(nodeExecutable(), [SERVER], {
  stdio: ["pipe", "pipe", "inherit"],
  env: { ...process.env },
  cwd: HERE,
  windowsHide: true,
});
let buf = "";
let nextId = 1;
let closed = false;
const pending = new Map();

function rejectAll(error) {
  for (const item of pending.values()) {
    clearTimeout(item.timer);
    item.reject(error);
  }
  pending.clear();
}

srv.stdout.on("data", (data) => {
  buf += data.toString();
  let index;
  while ((index = buf.indexOf("\n")) >= 0) {
    const line = buf.slice(0, index).trim();
    buf = buf.slice(index + 1);
    if (!line) continue;
    let message;
    try {
      message = JSON.parse(line);
    } catch (error) {
      rejectAll(new Error(`MCP stdout 不是 JSON：${error.message}`));
      continue;
    }
    if (message.id == null || !pending.has(message.id)) continue;
    const item = pending.get(message.id);
    clearTimeout(item.timer);
    pending.delete(message.id);
    if (message.error) {
      item.reject(new Error(`JSON-RPC ${message.error.code}: ${message.error.message}`));
    } else {
      item.resolve(message);
    }
  }
});
srv.on("error", (error) => {
  closed = true;
  rejectAll(new Error(`MCP server 启动失败：${error.message}`));
});
srv.on("exit", (code, signal) => {
  closed = true;
  rejectAll(new Error(`MCP server 已退出 code=${code} signal=${signal || ""}`));
});

function call(method, params, timeoutMs = 60000) {
  if (closed) return Promise.reject(new Error("MCP server 已关闭"));
  return new Promise((resolve, reject) => {
    const id = nextId++;
    const timer = setTimeout(() => {
      if (pending.delete(id)) reject(new Error(`MCP 调用超时：${method}（任务状态仍应通过 manifest 查询）`));
    }, timeoutMs);
    pending.set(id, { resolve, reject, timer });
    try {
      srv.stdin.write(`${JSON.stringify({ jsonrpc: "2.0", id, method, params })}\n`);
    } catch (error) {
      clearTimeout(timer);
      pending.delete(id);
      reject(error);
    }
  });
}

function parseToolResponse(message) {
  if (message.error) throw new Error(`JSON-RPC ${message.error.code}: ${message.error.message}`);
  const result = message.result;
  if (!result) throw new Error("MCP 响应缺少 result");
  const text = result.content?.find((item) => item.type === "text")?.text;
  let value;
  try {
    value = JSON.parse(text || "{}");
  } catch {
    throw new Error(`MCP 工具返回非 JSON：${text || "<empty>"}`);
  }
  if (result.isError || value.ok === false) {
    const detail = value.error?.code ? `${value.error.code}: ` : "";
    throw new Error(`${detail}${value.error?.message || "MCP 工具失败"}`);
  }
  return value.result || value;
}

async function initialize() {
  const response = await call("initialize", {
    protocolVersion: "2024-11-05",
    capabilities: {},
    clientInfo: { name: "mcp-image-batch", version: "2.1" },
  }, 10000);
  if (response.error) throw new Error(`JSON-RPC initialize ${response.error.code}: ${response.error.message}`);
  srv.stdin.write(`${JSON.stringify({ jsonrpc: "2.0", method: "notifications/initialized", params: {} })}\n`);
}

async function createOrResumeBatch() {
  if (resumeBatchId) return { batch_id: resumeBatchId, resumed: true };
  const response = await call("tools/call", {
    name: "image-batch-create",
    arguments: { jobs, concurrency },
  });
  return parseToolResponse(response);
}

async function getStatus(batchId) {
  const response = await call("tools/call", {
    name: "image-batch-status",
    arguments: { batch_id: batchId },
  });
  return parseToolResponse(response);
}

function terminal(status) {
  return ["completed", "failed", "cancelled", "submission_unknown"].includes(status);
}

function verifyManifest(status) {
  if (!status || !Array.isArray(status.jobs)) {
    throw new Error("批次 manifest 无效：缺少 jobs");
  }
  if (!BATCH_ID_RE.test(String(status.batch_id || ""))) {
    throw new Error("CORRUPT_BATCH_MANIFEST: batch_id 无效");
  }
  if (
    status.version < 3 ||
    !/^[a-f0-9]{64}$/i.test(String(status.input_fingerprint || "")) ||
    !Number.isInteger(Number(status.input_count)) ||
    Number(status.input_count) < 1 ||
    Number(status.input_count) > 200 ||
    status.jobs.length !== Number(status.input_count)
  ) {
    throw new Error("CORRUPT_BATCH_MANIFEST: 版本、输入指纹或任务数量无效");
  }
  if (preparedJobs) {
    const expected = batchInputFingerprint(preparedJobs);
    if (expected !== status.input_fingerprint) {
      throw new Error(`BATCH_INPUT_MISMATCH: 输入 jobs 指纹不匹配（批次 ${status.input_fingerprint}，输入 ${expected}）`);
    }
    if (Number(status.input_count) !== preparedJobs.length) {
      throw new Error("BATCH_INPUT_MISMATCH: 输入项数量不匹配");
    }
  }

  const seenTasks = new Set();
  const seenIds = new Set();
  const seenIndexes = new Set();
  for (const [position, job] of status.jobs.entries()) {
    if (!job || typeof job !== "object" || !job.task_id || !/^img-[A-Za-z0-9_-]+$/.test(job.task_id)) {
      throw new Error(`CORRUPT_BATCH_MANIFEST: job ${job?.id || position + 1} task_id 无效`);
    }
    if (seenTasks.has(job.task_id)) throw new Error(`CORRUPT_BATCH_MANIFEST: task_id 重复 ${job.task_id}`);
    seenTasks.add(job.task_id);
    if (typeof job.id !== "string" || !job.id || seenIds.has(job.id)) throw new Error(`CORRUPT_BATCH_MANIFEST: job id 重复或无效 ${job.id || position + 1}`);
    seenIds.add(job.id);
    if (!Number.isInteger(job.index) || job.index < 0 || job.index >= Number(status.input_count) || seenIndexes.has(job.index)) {
      throw new Error(`CORRUPT_BATCH_MANIFEST: job index 重复或越界 ${job.index}`);
    }
    seenIndexes.add(job.index);
    if (!/^[a-f0-9]{64}$/i.test(String(job.fingerprint || ""))) throw new Error(`CORRUPT_BATCH_MANIFEST: job ${job.id} fingerprint 无效`);
    const state = readTask(job.task_id);
    if (state.batch_id !== status.batch_id) throw new Error(`CORRUPT_BATCH_MANIFEST: job ${job.id} 不属于该 batch`);
    if (job.operation_id !== state.operation_id) throw new Error(`CORRUPT_BATCH_MANIFEST: job ${job.id} operation_id 不一致`);
    if (!job.request || typeof job.request !== "object") throw new Error(`CORRUPT_BATCH_MANIFEST: job ${job.id} request 缺失`);
    if (job.request_fingerprint !== state.request_fingerprint) throw new Error(`CORRUPT_BATCH_MANIFEST: job ${job.id} 请求指纹不一致`);
    if (preparedJobs) {
      const expected = preparedJobs[job.index];
      if (!expected || expected.id !== job.id || expected.fingerprint !== job.fingerprint || (expected.operation_id && expected.operation_id !== job.operation_id)) {
        throw new Error(`BATCH_INPUT_MISMATCH: job ${job.id} 与输入项不一致`);
      }
    }
    if (state.status === "completed") {
      const valid = validateOutputs(state);
      if (valid.length !== (state.request?.n || 1)) throw new Error(`OUTPUT_INCOMPLETE: job ${job.id} 的已完成产物未通过磁盘校验`);
    }
  }
  if (seenIndexes.size !== Number(status.input_count)) throw new Error("CORRUPT_BATCH_MANIFEST: job index 不完整");
  return status;
}

function verifiedFiles(status) {
  return status.jobs.flatMap((job) => {
    if (job.status !== "completed") return [];
    const state = readTask(job.task_id);
    const files = validateOutputs(state);
    if (files.length !== (state.request?.n || 1)) {
      throw new Error(`OUTPUT_INCOMPLETE: job ${job.id} 的文件未通过最终校验`);
    }
    return files;
  });
}

async function closeMcp() {
  if (closed) return;
  closed = true;
  try {
    srv.stdin.end();
  } catch {
    // stdin may already be closed
  }
  await new Promise((resolve) => {
    const timer = setTimeout(() => {
      if (!srv.killed) srv.kill();
      resolve();
    }, 1500);
    srv.once("exit", () => {
      clearTimeout(timer);
      resolve();
    });
  });
}

const started = Date.now();
let batch;
let failed = false;
let unfinished = false;
try {
  await initialize();
  batch = await createOrResumeBatch();
  const status = await getStatus(batch.batch_id);
  verifyManifest(status);
  batch = {
    ...batch,
    input_fingerprint: status.input_fingerprint,
    input_count: status.input_count,
  };
  console.log(JSON.stringify({ event: isResume ? "batch_resumed" : "batch_created", ...batch }, null, 2));

  let current = status;
  while (current.jobs.some((job) => !terminal(job.status)) && Date.now() - started < waitSeconds * 1000) {
    await new Promise((resolve) => setTimeout(resolve, Math.min(POLL_MS, 700)));
    current = await getStatus(batch.batch_id);
    verifyManifest(current);
  }

  const files = verifiedFiles(current);
  console.log(JSON.stringify({ event: "batch_status", ...current }, null, 2));
  if (files.length) console.log(JSON.stringify({ event: "verified_files", files }, null, 2));
  unfinished = current.jobs.some((job) => !terminal(job.status));
  failed = current.jobs.some((job) => ["failed", "cancelled", "submission_unknown"].includes(job.status));
  if (unfinished) console.log(`任务仍在后台运行；请用 image-batch-status 查询 ${batch.batch_id}`);
  if (current.jobs.some((job) => job.status === "submission_unknown")) console.log(`存在 submission_unknown；禁止盲目重提，请先对账 ${batch.batch_id}`);
} catch (error) {
  failed = true;
  console.error(error.stack || error.message || String(error));
} finally {
  await closeMcp();
}
process.exitCode = failed ? 1 : unfinished ? 2 : 0;
