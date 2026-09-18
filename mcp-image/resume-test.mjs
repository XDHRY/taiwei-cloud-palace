import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { createServer } from "node:http";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const root = fs.mkdtempSync(path.join(os.tmpdir(), "mcp-image-resume-"));
process.env.IMAGE_OUT_DIR = root;
const { nodeExecutable } = await import("./core.mjs");
const NODE = nodeExecutable();
const BATCH = path.join(HERE, "batch.mjs");
const PNG = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=", "base64");
const jobsFile = path.join(root, "jobs.json");
let generationCount = 0;
let active = 0;
let maxActive = 0;

const upstream = createServer((req, res) => {
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
        try { input = JSON.parse(body); } catch { /* request fixture */ }
        const n = Number(input.n || 1);
        res.setHeader("Content-Type", "application/json");
        res.end(JSON.stringify({ data: Array.from({ length: n }, () => ({ b64_json: PNG.toString("base64"), revised_prompt: "resume mock" })) }));
      }, 80);
    });
    return;
  }
  if (req.url === "/v1/models" && req.method === "GET") {
    res.setHeader("Content-Type", "application/json");
    res.end(JSON.stringify({ data: [{ id: "gpt-image-2" }] }));
    return;
  }
  res.statusCode = 404;
  res.end("not found");
});

function listen(server) {
  return new Promise((resolve) => server.listen(0, "127.0.0.1", () => resolve(server.address().port)));
}

function runCli(args, env) {
  return new Promise((resolve) => {
    const child = spawn(NODE, [BATCH, ...args], { cwd: HERE, env, stdio: ["ignore", "pipe", "pipe"], windowsHide: true });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => { stdout += chunk.toString(); });
    child.stderr.on("data", (chunk) => { stderr += chunk.toString(); });
    child.on("error", (error) => resolve({ code: -1, stdout, stderr: `${stderr}${error.stack || error.message}` }));
    child.on("exit", (code, signal) => resolve({ code: code ?? -1, signal, stdout, stderr }));
  });
}

async function waitFor(predicate, timeoutMs = 10000) {
  const end = Date.now() + timeoutMs;
  while (Date.now() < end) {
    if (predicate()) return;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error("等待条件超时");
}

async function removeTree(dir) {
  for (let attempt = 0; attempt < 30; attempt += 1) {
    try {
      fs.rmSync(dir, { recursive: true, force: true });
      return;
    } catch {
      await new Promise((resolve) => setTimeout(resolve, 100));
    }
  }
  throw new Error(`无法清理测试目录：${dir}`);
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
  IMAGE_RUNNER_SCAN_MS: "50",
  IMAGE_RUNNER_CONCURRENCY: "2",
  IMAGE_RUNNER_ONCE: "1",
};
for (const [key, value] of Object.entries(env)) process.env[key] = value;
const jobs = [
  { id: "one", prompt: "one", n: 1, size: "1024x1024" },
  { id: "two", prompt: "two", n: 2, size: "1024x1024" },
];
fs.writeFileSync(jobsFile, JSON.stringify(jobs, null, 2), "utf8");

try {
  const first = await runCli([jobsFile, "2", "25"], env);
  assert.equal(first.code, 0, `首次批量失败\nstdout=${first.stdout}\nstderr=${first.stderr}`);
  const batchMatch = first.stdout.match(/"batch_id":\s*"(batch-[A-Za-z0-9_-]+)"/);
  assert.ok(batchMatch, `首次输出缺少 batch_id：${first.stdout}`);
  const batchId = batchMatch[1];
  assert.match(first.stdout, /"event":\s*"verified_files"/);
  assert.equal(generationCount, 2, `首次应提交 2 个 provider 请求，实际 ${generationCount}`);
  assert.ok(maxActive <= 2, `上游并发超过 batch 限制：${maxActive}`);

  const batchDir = path.join(root, ".image-batches", batchId);
  const manifestFile = path.join(batchDir, "manifest.json");
  const manifest = JSON.parse(fs.readFileSync(manifestFile, "utf8"));
  assert.equal(manifest.version, 3);
  assert.equal(manifest.input_count, jobs.length);
  assert.match(manifest.input_fingerprint, /^[a-f0-9]{64}$/);
  assert.equal(manifest.jobs.length, jobs.length);
  const taskIds = manifest.jobs.map((job) => job.task_id);
  assert.equal(new Set(taskIds).size, jobs.length);
  const taskDirs = fs.readdirSync(path.join(root, ".image-tasks"), { withFileTypes: true }).filter((entry) => entry.isDirectory() && entry.name.startsWith("img-")).map((entry) => entry.name);
  assert.deepEqual(new Set(taskDirs), new Set(taskIds));
  await waitFor(() => !fs.existsSync(path.join(root, ".image-tasks", "runner.lock")));

  const resumed = await runCli(["--resume", batchId, jobsFile, "5"], env);
  assert.equal(resumed.code, 0, `resume 失败\nstdout=${resumed.stdout}\nstderr=${resumed.stderr}`);
  assert.match(resumed.stdout, /"event":\s*"batch_resumed"/);
  assert.match(resumed.stdout, /"event":\s*"verified_files"/);
  assert.equal(generationCount, 2, "resume 不得重新提交已完成任务");
  const resumedManifest = JSON.parse(fs.readFileSync(manifestFile, "utf8"));
  assert.deepEqual(resumedManifest.jobs.map((job) => job.task_id), taskIds);
  assert.equal(resumedManifest.counts.completed, jobs.length);
  await waitFor(() => !fs.existsSync(path.join(root, ".image-tasks", "runner.lock")));

  const mismatchedJobsFile = path.join(root, "mismatch.json");
  fs.writeFileSync(mismatchedJobsFile, JSON.stringify([{ ...jobs[0], prompt: "different" }, jobs[1]], null, 2), "utf8");
  const mismatch = await runCli(["--resume", batchId, mismatchedJobsFile, "0"], env);
  assert.notEqual(mismatch.code, 0);
  assert.match(`${mismatch.stdout}\n${mismatch.stderr}`, /BATCH_INPUT_MISMATCH/);
  assert.equal(generationCount, 2, "输入指纹不匹配不得触发 provider 请求");

  const { readTask, validateOutputs } = await import("./core.mjs");
  for (const taskId of taskIds) {
    const state = readTask(taskId);
    assert.equal(state.status, "completed");
    assert.equal(validateOutputs(state).length, state.request.n);
    for (const output of validateOutputs(state)) {
      assert.ok(fs.statSync(output.file).size > 0);
      assert.ok(fs.existsSync(output.sidecar));
    }
  }
  console.log(JSON.stringify({ ok: true, batch_id: batchId, generation_count: generationCount, task_count: taskIds.length, max_upstream_concurrency: maxActive }));
} finally {
  await new Promise((resolve) => upstream.close(resolve));
  try { await waitFor(() => !fs.existsSync(path.join(root, ".image-tasks", "runner.lock")), 5000); } catch { /* cleanup below remains bounded */ }
  await removeTree(root);
}
