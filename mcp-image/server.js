import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import {
  BASE,
  DEFAULT_MODEL,
  POLL_MS,
  batchStatus,
  createBatch,
  createTask,
  formatError,
  listTasks,
  repairTask,
  requestCancel,
  requestJson,
  waitForTask,
} from "./core.mjs";
import { ensureRunner } from "./runner.mjs";

const server = new McpServer({ name: "mcp-image", version: "2.0.0" });
const json = (value) => JSON.stringify(value, null, 2);

function result(value) {
  return { content: [{ type: "text", text: json(value) }] };
}

function errorResult(error) {
  return { content: [{ type: "text", text: json({ ok: false, error: formatError(error) }) }], isError: true };
}

async function safe(fn) {
  try { return result({ ok: true, ...(await fn()) }); }
  catch (error) { return errorResult(error); }
}

function taskSummary(state, extra = {}) {
  return {
    task_id: state.task_id,
    batch_id: state.batch_id || null,
    operation_id: state.operation_id,
    status: state.status,
    output_dir: state.output_dir,
    manifest_path: state.output_dir ? `${state.output_dir}/manifest.json` : null,
    expected_count: state.request?.n || 1,
    provider_count: state.provider_count || null,
    completed_count: Array.isArray(state.outputs) ? state.outputs.length : 0,
    files: state.outputs || [],
    error: state.error || null,
    attempt: state.attempt || 0,
    created_at: state.created_at,
    updated_at: state.updated_at,
    completed_at: state.completed_at || null,
    poll_after_ms: POLL_MS,
    ...extra,
  };
}

const createSchema = {
  prompt: z.string().min(1).describe("完整图片提示词"),
  model: z.string().optional().describe(`模型，默认 ${DEFAULT_MODEL}`),
  n: z.number().int().min(1).max(10).optional().describe("生成张数，默认 1"),
  size: z.string().optional().describe("尺寸，如 1024x1024 / 1536x1024 / 1024x1536"),
  quality: z.string().optional().describe("质量：low / medium / high"),
  background: z.string().optional().describe("透明背景等上游支持的背景参数"),
  output_dir: z.string().optional().describe("输出目录名或 IMAGE_OUT_DIR 内的绝对路径"),
  operation_id: z.string().optional().describe("稳定操作 ID；重复调用会复用同一任务"),
  wait_seconds: z.number().min(0).max(25).optional().describe("最多短等待多少秒，默认 0；返回 task_id 后可查询"),
};

server.tool(
  "create-image",
  "创建图片生成任务并立即返回 task_id。默认不长时间等待；用 image-task-status 或 image-task-wait 获取最终图片文件。任务会在 MCP 请求断开后继续运行。",
  createSchema,
  (args) => safe(async () => {
    const created = createTask(args);
    const runner = ensureRunner();
    const state = args.wait_seconds ? await waitForTask(created.state.task_id, args.wait_seconds) : repairTask(created.state.task_id);
    return taskSummary(state, { reused: created.reused, runner });
  }),
);

server.tool(
  "image-task-status",
  "查询图片任务状态，并核对已落盘图片、sidecar 和 manifest。",
  { task_id: z.string().describe("create-image 返回的 task_id") },
  (args) => safe(async () => taskSummary(repairTask(args.task_id))),
);

server.tool(
  "image-task-wait",
  "短轮询图片任务；最多等待 25 秒，超时返回当前状态，不让 MCP 调用长时间挂起。",
  {
    task_id: z.string().describe("任务 ID"),
    wait_seconds: z.number().min(0).max(25).optional().describe("等待秒数，最多 25"),
  },
  (args) => safe(async () => taskSummary(await waitForTask(args.task_id, args.wait_seconds ?? 10))),
);

server.tool(
  "image-task-list",
  "列出本地图片任务，可按状态或 batch_id 过滤。",
  {
    status: z.string().optional().describe("状态过滤：queued/submitting/provider_processing/downloading/completed/failed/cancelled/submission_unknown"),
    batch_id: z.string().optional().describe("批次 ID"),
    limit: z.number().int().min(1).max(200).optional().describe("最多返回多少项，默认 50"),
  },
  (args) => safe(async () => ({ tasks: listTasks(args) })),
);

server.tool(
  "image-task-cancel",
  "请求取消图片任务。排队任务立即取消，运行中的任务会在下一个取消检查点停止。",
  { task_id: z.string().describe("任务 ID") },
  (args) => safe(async () => taskSummary(requestCancel(args.task_id))),
);

server.tool(
  "image-batch-create",
  "创建批量图片任务。服务端硬限制并发不超过 8，每个 job 独立追踪并写入 batch manifest。",
  {
    jobs: z.array(z.object({
      id: z.string().optional(),
      prompt: z.string().min(1),
      model: z.string().optional(),
      n: z.number().int().min(1).max(10).optional(),
      size: z.string().optional(),
      quality: z.string().optional(),
      background: z.string().optional(),
      operation_id: z.string().optional(),
    })).min(1).max(200).describe("任务列表"),
    concurrency: z.number().int().min(1).max(8).optional().describe("批量并发，默认 4，硬上限 8"),
  },
  (args) => safe(async () => {
    const batch = createBatch(args.jobs, args.concurrency);
    const runner = ensureRunner();
    return { ...batch, runner };
  }),
);

server.tool(
  "image-batch-status",
  "查询批次汇总、每项状态和全部已落盘图片路径。",
  { batch_id: z.string().describe("批次 ID") },
  (args) => safe(async () => {
    const runner = ensureRunner();
    return { ...batchStatus(args.batch_id), runner };
  }),
);

server.tool(
  "image-models",
  "列出图像中转站可用模型。用于确认 gpt-image-2.5-flare、gpt-image-2.5-sunburst 等是否可用。",
  {},
  () => safe(async () => {
    const response = await requestJson("/models", null);
    const models = (response.data || []).map((item) => item.id).filter(Boolean).sort();
    return { base_url: BASE, count: models.length, models };
  }),
);

const transport = new StdioServerTransport();
await server.connect(transport);
