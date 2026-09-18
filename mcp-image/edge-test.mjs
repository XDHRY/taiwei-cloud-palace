import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { createServer } from "node:http";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const NODE = process.env.NODE_REAL_PATH || "C:\\Users\\xdrhh\\AppData\\Local\\nvm\\v22.14.0\\node.exe";
const PNG = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=", "base64");
const root = fs.mkdtempSync(path.join(os.tmpdir(), "mcp-image-edge-"));
let generationCount = 0;
const upstream = createServer((req, res) => {
  if (req.url === "/v1/images/generations" && req.method === "POST") {
    generationCount += 1;
    res.statusCode = 500;
    res.setHeader("Content-Type", "text/plain");
    res.end("temporary upstream failure");
    return;
  }
  if (req.url === "/v1/image.png") {
    res.setHeader("Content-Type", "image/png");
    res.end(PNG);
    return;
  }
  if (req.url === "/v1/redirect") {
    res.statusCode = 302;
    res.setHeader("Location", "/v1/image.png");
    res.end();
    return;
  }
  if (req.url === "/v1/not-image") {
    res.setHeader("Content-Type", "text/plain");
    res.end("not an image");
    return;
  }
  if (req.url === "/v1/stall") {
    res.setHeader("Content-Type", "image/png");
    res.flushHeaders();
    const timer = setInterval(() => res.write(PNG.subarray(0, 1)), 250);
    setTimeout(() => { clearInterval(timer); res.destroy(); }, 1800);
    return;
  }
  res.statusCode = 404;
  res.end("not found");
});
function listen(server) {
  return new Promise((resolve) => server.listen(0, "127.0.0.1", () => resolve(server.address().port)));
}
function runMcp(env) {
  return new Promise((resolve, reject) => {
    const child = spawn(NODE, [path.join(HERE, "server.js")], { cwd: HERE, env, stdio: ["pipe", "pipe", "pipe"], windowsHide: true });
    let stdout = "";
    let stderr = "";
    const pending = new Map();
    let nextId = 1;
    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
      for (const line of stdout.split("\n").slice(0, -1)) {
        try {
          const message = JSON.parse(line);
          const item = pending.get(message.id);
          if (item) { pending.delete(message.id); clearTimeout(item.timer); item.resolve(message); }
        } catch { /* wait for a complete line */ }
      }
      stdout = stdout.slice(stdout.lastIndexOf("\n") + 1);
    });
    child.stderr.on("data", (chunk) => { stderr += chunk.toString(); });
    child.on("error", reject);
    child.on("exit", (code) => { if (code && pending.size) reject(new Error(`server exited ${code}: ${stderr}`)); });
    function call(method, params) {
      return new Promise((resolveCall, rejectCall) => {
        const id = nextId++;
        const timer = setTimeout(() => { pending.delete(id); rejectCall(new Error(`timeout ${method}`)); }, 10000);
        pending.set(id, { resolve: resolveCall, reject: rejectCall, timer });
        child.stdin.write(`${JSON.stringify({ jsonrpc: "2.0", id, method, params })}\n`);
      });
    }
    resolve({ child, call, getStderr: () => stderr });
  });
}
function tool(message) {
  assert.ok(message.result, JSON.stringify(message));
  const text = message.result.content?.find((item) => item.type === "text")?.text;
  return JSON.parse(text);
}
async function waitFor(fn, timeout = 10000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) {
    const value = await fn();
    if (value) return value;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error("condition timeout");
}

const port = await listen(upstream);
const env = {
  ...process.env,
  IMAGE_API_KEY: "mock-only",
  IMAGE_BASE_URL: `http://127.0.0.1:${port}/v1`,
  IMAGE_OUT_DIR: root,
  IMAGE_API_TIMEOUT_MS: "1000",
  IMAGE_DOWNLOAD_TIMEOUT_MS: "1000",
  IMAGE_TASK_DEADLINE_MS: "5000",
  IMAGE_RUNNER_SCAN_MS: "250",
  IMAGE_RUNNER_CONCURRENCY: "1",
  IMAGE_RUNNER_ONCE: "1",
};
for (const [key, value] of Object.entries(env)) process.env[key] = value;
let mcp;
try {
  mcp = await runMcp(env);
  await mcp.call("initialize", { protocolVersion: "2024-11-05", capabilities: {}, clientInfo: { name: "edge-test", version: "1" } });
  const created = tool(await mcp.call("tools/call", { name: "create-image", arguments: { prompt: "unknown submission test", operation_id: "edge-unknown" } }));
  assert.equal(created.ok, true);
  const unknown = await waitFor(async () => {
    const status = tool(await mcp.call("tools/call", { name: "image-task-status", arguments: { task_id: created.task_id } }));
    return status.status === "submission_unknown" ? status : null;
  });
  assert.equal(generationCount, 1, "uncertain HTTP failure must never be blindly retried");
  assert.equal(unknown.error.code, "SUBMISSION_UNKNOWN");

  const { readTask, saveImageItem, validateOutputs } = await import("./core.mjs");
  const state = readTask(created.task_id);
  const saved = await saveImageItem({ url: `http://127.0.0.1:${port}/v1/image.png` }, state, 1);
  const withOutput = { ...state, outputs: [saved], request: { ...state.request, n: 1 }, status: "queued" };
  assert.equal(validateOutputs(withOutput).length, 1, "same-host PNG URL should validate");
  await assert.rejects(() => saveImageItem({ url: `http://127.0.0.1:${port}/v1/redirect` }, state, 1), /重定向被拒绝/);
  await assert.rejects(() => saveImageItem({ url: `http://127.0.0.1:${port}/v1/not-image` }, state, 1), /非图片 Content-Type/);
  await assert.rejects(() => saveImageItem({ url: `http://127.0.0.1:${port}/v1/stall` }, state, 1), /响应体读取超时|下载/);
  process.env.IMAGE_ALLOW_EXTERNAL_IMAGE_HOSTS = "0";
  await assert.rejects(() => saveImageItem({ url: "https://example.com/image.png" }, state, 1), /主机不是配置的图片服务主机/);
  delete process.env.IMAGE_ALLOW_EXTERNAL_IMAGE_HOSTS;
  const sidecar = saved.sidecar;
  fs.writeFileSync(sidecar, JSON.stringify({ ...JSON.parse(fs.readFileSync(sidecar, "utf8")), sha256: "0".repeat(64) }), "utf8");
  assert.equal(validateOutputs(withOutput).length, 0, "tampered sidecar must not validate");
  console.log(JSON.stringify({ ok: true, generation_count: generationCount, unknown_status: unknown.status }));
} finally {
  try { mcp?.child.stdin.end(); mcp?.child.kill(); } catch { /* bounded test cleanup */ }
  await new Promise((resolve) => upstream.close(resolve));
  for (let attempt = 0; attempt < 20; attempt++) {
    try { fs.rmSync(root, { recursive: true, force: true }); break; } catch { await new Promise((resolve) => setTimeout(resolve, 100)); }
  }
}
