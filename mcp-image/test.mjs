import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { createServer } from "node:http";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import { nodeExecutable } from "./core.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const NODE = nodeExecutable();
const PNG = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=", "base64");
const root = fs.mkdtempSync(path.join(os.tmpdir(), "mcp-image-test-"));
let generationCount = 0;
let partialN2Served = false;
let active = 0;
let maxActive = 0;
const upstream = createServer((req, res) => {
  if (req.url === "/v1/models" && req.method === "GET") {
    res.setHeader("Content-Type", "application/json");
    res.end(JSON.stringify({ data: [{ id: "gpt-image-1" }, { id: "gpt-image-1.5" }, { id: "gpt-image-2" }] }));
    return;
  }
  if (req.url === "/v1/images/generations" && req.method === "POST") {
    generationCount += 1;
    active += 1;
    maxActive = Math.max(maxActive, active);
    let body = "";
    req.on("data", (chunk) => { body += chunk; });
    req.on("end", () => {
      setTimeout(() => {
        active -= 1;
        let input = {};
        try { input = JSON.parse(body); } catch { /* test fixture */ }
        const count = Number(input.n || 1) === 2 && !partialN2Served ? (partialN2Served = true, 1) : Number(input.n || 1);
        const data = Array.from({ length: count }, () => ({ b64_json: PNG.toString("base64"), revised_prompt: "mock revised" }));
        res.setHeader("Content-Type", "application/json");
        res.end(JSON.stringify({ data }));
      }, 60);
    });
    return;
  }
  res.statusCode = 404;
  res.end("not found");
});

function listen(server) {
  return new Promise((resolve) => server.listen(0, "127.0.0.1", () => resolve(server.address().port)));
}

const port = await listen(upstream);
const env = {
  ...process.env,
  IMAGE_API_KEY: "test-key",
  IMAGE_BASE_URL: `http://127.0.0.1:${port}/v1`,
  IMAGE_OUT_DIR: root,
  IMAGE_API_TIMEOUT_MS: "3000",
  IMAGE_DOWNLOAD_TIMEOUT_MS: "3000",
  IMAGE_TASK_DEADLINE_MS: "20000",
  IMAGE_RUNNER_SCAN_MS: "30",
  IMAGE_RUNNER_CONCURRENCY: "2",
  IMAGE_RUNNER_ONCE: "1",
};
const server = spawn(NODE, [path.join(HERE, "server.js")], { cwd: HERE, env, stdio: ["pipe", "pipe", "pipe"], windowsHide: true });
let buffer = "";
let nextId = 1;
const pending = new Map();
let stderr = "";
server.stderr.on("data", (chunk) => { stderr += chunk.toString(); });
server.stdout.on("data", (chunk) => {
  buffer += chunk.toString();
  let index;
  while ((index = buffer.indexOf("\n")) >= 0) {
    const line = buffer.slice(0, index).trim();
    buffer = buffer.slice(index + 1);
    if (!line) continue;
    const message = JSON.parse(line);
    const item = pending.get(message.id);
    if (item) { pending.delete(message.id); clearTimeout(item.timer); item.resolve(message); }
  }
});
server.on("exit", (code) => {
  for (const item of pending.values()) { clearTimeout(item.timer); item.reject(new Error(`server exited ${code}`)); }
  pending.clear();
});
function call(method, params, timeout = 10000) {
  return new Promise((resolve, reject) => {
    const id = nextId++;
    const timer = setTimeout(() => { pending.delete(id); reject(new Error(`timeout ${method}`)); }, timeout);
    pending.set(id, { resolve, reject, timer });
    server.stdin.write(`${JSON.stringify({ jsonrpc: "2.0", id, method, params })}\n`);
  });
}
function tool(message) {
  assert.ok(message.result, JSON.stringify(message));
  assert.equal(message.result.isError, undefined, JSON.stringify(message));
  const text = message.result.content?.find((item) => item.type === "text")?.text;
  return JSON.parse(text);
}
async function toolCall(name, args = {}) {
  return tool(await call("tools/call", { name, arguments: args }));
}
async function waitUntil(fn, timeout = 10000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) {
    const value = await fn();
    if (value) return value;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error("condition timeout");
}

try {
  const init = await call("initialize", { protocolVersion: "2024-11-05", capabilities: {}, clientInfo: { name: "test", version: "1" } });
  assert.ok(init.result);
  const list = await call("tools/list", {});
  const names = list.result.tools.map((item) => item.name);
  for (const name of ["create-image", "image-task-status", "image-task-wait", "image-task-list", "image-task-cancel", "image-batch-create", "image-batch-status", "image-models"]) assert.ok(names.includes(name), name);

  const models = await toolCall("image-models");
  assert.deepEqual(models.models, ["gpt-image-1", "gpt-image-1.5", "gpt-image-2"]);

  const created = await toolCall("create-image", { prompt: "mock phoenix", n: 2, size: "1024x1024", operation_id: "test-op-1" });
  assert.equal(created.ok, true);
  assert.match(created.task_id, /^img-/);
  const done = await waitUntil(async () => {
    const status = await toolCall("image-task-status", { task_id: created.task_id });
    return status.status === "completed" ? status : null;
  });
  assert.equal(done.files.length, 2);
  assert.equal(done.provider_count, 2);
  for (const file of done.files) {
    assert.ok(fs.statSync(file.file).size > 0);
    assert.ok(fs.existsSync(file.sidecar));
    assert.ok(fs.existsSync(path.join(done.output_dir, "manifest.json")));
  }
  const reused = await toolCall("create-image", { prompt: "mock phoenix", n: 2, size: "1024x1024", operation_id: "test-op-1" });
  assert.equal(reused.task_id, created.task_id);
  assert.equal(reused.reused, true);
  const conflict = await call("tools/call", { name: "create-image", arguments: { prompt: "different text", operation_id: "test-op-1" } });
  assert.equal(conflict.result.isError, true);
  assert.match(JSON.parse(conflict.result.content[0].text).error.code, /OPERATION_CONFLICT/);

  const duplicateIds = await call("tools/call", { name: "image-batch-create", arguments: { jobs: [{ id: "duplicate", prompt: "one" }, { id: "duplicate", prompt: "two" }] } });
  assert.equal(duplicateIds.result.isError, true);
  assert.equal(JSON.parse(duplicateIds.result.content[0].text).error.code, "DUPLICATE_JOB_ID");
  const duplicateOperations = await call("tools/call", { name: "image-batch-create", arguments: { jobs: [{ id: "one", prompt: "one", operation_id: "duplicate-op" }, { id: "two", prompt: "two", operation_id: "duplicate-op" }] } });
  assert.equal(duplicateOperations.result.isError, true);
  assert.equal(JSON.parse(duplicateOperations.result.content[0].text).error.code, "DUPLICATE_OPERATION_ID");

  const batch = await toolCall("image-batch-create", { concurrency: 2, jobs: [{ id: "a", prompt: "a" }, { id: "b", prompt: "b" }, { id: "c", prompt: "c" }] });
  assert.match(batch.batch_id, /^batch-/);
  let lastBatchStatus;
  const batchDone = await waitUntil(async () => {
    lastBatchStatus = await toolCall("image-batch-status", { batch_id: batch.batch_id });
    return lastBatchStatus.jobs.every((job) => job.status === "completed") ? lastBatchStatus : null;
  }).catch((error) => { throw new Error(`${error.message}: ${JSON.stringify(lastBatchStatus)}`); });
  assert.equal(batchDone.counts.completed, 3);
  assert.ok(maxActive <= 2, `mock upstream concurrency ${maxActive}`);

  const cancel = await toolCall("create-image", { prompt: "to cancel", operation_id: "test-cancel" });
  const cancelled = await toolCall("image-task-cancel", { task_id: cancel.task_id });
  assert.ok(["cancelled", "queued", "submitting"].includes(cancelled.status));
  const cancelDone = await waitUntil(async () => {
    const status = await toolCall("image-task-status", { task_id: cancel.task_id });
    return ["cancelled", "completed", "failed"].includes(status.status) ? status : null;
  });
  assert.equal(cancelDone.status, "cancelled");

  const all = await toolCall("image-task-list", { limit: 100 });
  assert.ok(all.tasks.length >= 5);
  console.log(JSON.stringify({ ok: true, generation_count: generationCount, max_upstream_concurrency: maxActive, task_root: path.join(root, ".image-tasks") }));
} catch (error) {
  console.error(stderr);
  throw error;
} finally {
  server.stdin.end();
  server.kill();
  await new Promise((resolve) => upstream.close(resolve));
  const lock = path.join(root, ".image-tasks", "runner.lock");
  const deadline = Date.now() + 5000;
  while (fs.existsSync(lock) && Date.now() < deadline) await new Promise((resolve) => setTimeout(resolve, 100));
  for (let attempt = 0; attempt < 10; attempt++) {
    try { fs.rmSync(root, { recursive: true, force: true }); break; }
    catch { await new Promise((resolve) => setTimeout(resolve, 100)); }
  }
}
