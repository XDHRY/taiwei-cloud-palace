// smoke-mcp.mjs - protocol smoke for the persistent image MCP.
// Usage: node smoke-mcp.mjs [tools|models|gen "prompt" [size] [quality] [output_dir]]
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { nodeExecutable, POLL_MS } from "./core.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const srv = spawn(nodeExecutable(), [path.join(HERE, "server.js")], { cwd: HERE, stdio: ["pipe", "pipe", "pipe"], env: { ...process.env }, windowsHide: true });
let buffer = "";
let nextId = 1;
let stderr = "";
let closed = false;
const pending = new Map();
srv.stderr.on("data", (chunk) => { stderr += chunk.toString(); });
srv.stdout.on("data", (chunk) => {
  buffer += chunk.toString();
  let index;
  while ((index = buffer.indexOf("\n")) >= 0) {
    const line = buffer.slice(0, index).trim(); buffer = buffer.slice(index + 1);
    if (!line) continue;
    let message;
    try { message = JSON.parse(line); } catch (error) { rejectAll(new Error(`MCP stdout 不是 JSON：${error.message}`)); continue; }
    const item = pending.get(message.id);
    if (!item) continue;
    pending.delete(message.id); clearTimeout(item.timer);
    if (message.error) item.reject(new Error(`JSON-RPC ${message.error.code}: ${message.error.message}`)); else item.resolve(message);
  }
});
function rejectAll(error) { for (const item of pending.values()) { clearTimeout(item.timer); item.reject(error); } pending.clear(); }
srv.on("error", (error) => { closed = true; rejectAll(error); });
srv.on("exit", (code) => { closed = true; rejectAll(new Error(`MCP server exited ${code}: ${stderr}`)); });
function call(method, params, timeoutMs = 30000) {
  if (closed) return Promise.reject(new Error("MCP server 已关闭"));
  return new Promise((resolve, reject) => {
    const id = nextId++;
    const timer = setTimeout(() => { pending.delete(id); reject(new Error(`MCP 调用超时：${method}`)); }, timeoutMs);
    pending.set(id, { resolve, reject, timer });
    srv.stdin.write(`${JSON.stringify({ jsonrpc: "2.0", id, method, params })}\n`);
  });
}
function decode(message) {
  if (message.error) throw new Error(`JSON-RPC ${message.error.code}: ${message.error.message}`);
  const response = message.result;
  if (!response) throw new Error("MCP 响应缺少 result");
  const text = response.content?.find((item) => item.type === "text")?.text;
  let value; try { value = JSON.parse(text || "{}"); } catch { throw new Error(`MCP 工具返回非 JSON：${text || "<empty>"}`); }
  if (response.isError || value.ok === false) throw new Error(value.error?.message || "MCP 工具失败");
  return value.result || value;
}
async function tool(name, args = {}) { return decode(await call("tools/call", { name, arguments: args })); }
try {
  decode(await call("initialize", { protocolVersion: "2024-11-05", capabilities: {}, clientInfo: { name: "smoke", version: "2" } }));
  srv.stdin.write(`${JSON.stringify({ jsonrpc: "2.0", method: "notifications/initialized", params: {} })}\n`);
  const listedMessage = await call("tools/list", {});
  if (listedMessage.error || !listedMessage.result?.tools) throw new Error("tools/list 响应无 tools");
  const names = listedMessage.result.tools.map((tool) => tool.name);
  const required = ["create-image", "image-task-status", "image-task-wait", "image-task-list", "image-task-cancel", "image-batch-create", "image-batch-status", "image-models"];
  if (!required.every((name) => names.includes(name))) throw new Error(`工具注册不完整：${required.filter((name) => !names.includes(name)).join(", ")}`);
  console.log(JSON.stringify({ ok: true, tools: names }, null, 2));
  const mode = process.argv[2] || "tools";
  if (mode === "models") console.log(JSON.stringify(await tool("image-models"), null, 2));
  if (mode === "gen") {
    const args = { prompt: process.argv[3] };
    if (!args.prompt) throw new Error("gen 需要 prompt");
    if (process.argv[4]) args.size = process.argv[4];
    if (process.argv[5]) args.quality = process.argv[5];
    if (process.argv[6]) args.output_dir = process.argv[6];
    args.wait_seconds = 20;
    console.log(JSON.stringify(await tool("create-image", args), null, 2));
  }
} catch (error) { console.error(error.stack || error.message || error); process.exitCode = 1; }
finally { srv.stdin.end(); setTimeout(() => { if (!srv.killed) srv.kill(); }, 500); }
