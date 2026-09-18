# mcp-image

可恢复的 OpenAI-compatible 图片生成 MCP 服务。`create-image` 只负责创建本地任务，后台 detached runner 负责提交、下载、校验和落盘，因此约 30 秒的 MCP 宿主前台边界不会丢失结果；前台 `wait_seconds` 硬上限为 25 秒。

## 工具契约

- `create-image`: 返回 `task_id`、状态、manifest 路径；`wait_seconds` 最多 25 秒；中转站若忽略 `n` 导致首响应少图，会自动按缺口补足并在状态中报告 `provider_count`/`completed_count`。
- `image-task-status`: 查询任务并验证每张图片与 sidecar。
- `image-task-wait`: 有限轮询；超时不会停止 runner。
- `image-task-list`: 按状态或 batch 列出任务。
- `image-task-cancel`: 写入取消请求。
- `image-batch-create` / `image-batch-status`: 持久化批次，服务端并发硬上限 8，默认 4。
- `image-models`: 免费列出上游模型。

创建响应中的 `task_id` 不代表图片已完成。最终成功必须同时存在图片、同名 sidecar 和 `manifest.json`，并且状态为 `completed`。每张已验证图片都在 `files` 中返回绝对路径。

任务文件位于 `IMAGE_OUT_DIR/.image-tasks/<task_id>/`；批次清单位于 `.image-batches/<batch_id>/`。输出目录按任务隔离，使用 `.part` 文件和原子重命名，避免半文件被误报成功。提交阶段发生无法确认的网络中断、408、429 或 5xx 会进入 `submission_unknown`，不会盲目重发造成重复计费；这类任务必须先人工对账。runner 或 MCP 重启后会从磁盘扫描恢复，未知提交阶段不会自动重提。

批量 CLI 支持 `node batch.mjs --resume <batch_id> [jobs.json] [等待秒]`：它复用已保存的 task_id、输入指纹和已完成产物，不重新创建成功任务；只有通过 state、sidecar、SHA-256 和 manifest 校验的文件才会作为链接返回。下载有独立超时，响应体和图片大小也有上限。

## 环境变量

服务使用 `IMAGE_API_KEY`、`IMAGE_BASE_URL`、`IMAGE_MODEL`、`IMAGE_OUT_DIR`。默认模型为 `gpt-image-2.5-flare`（全面替代 2.0；同时支持 `gpt-image-2.5` 智能别名映射与 `gpt-image-2.5-sunburst`），默认 API 地址为 `https://code.mmkg.cloud/v1`。中转站返回的图片 URL 默认允许下载；如需恢复严格同主机限制，设置 `IMAGE_ALLOW_EXTERNAL_IMAGE_HOSTS=0`。时间预算可用 `IMAGE_API_TIMEOUT_MS`、`IMAGE_DOWNLOAD_TIMEOUT_MS`、`IMAGE_TASK_DEADLINE_MS` 调整。不要把 key 写入代码、任务 state、events 或 sidecar。

## 本地命令

```text
npm test
npm run smoke
node batch.mjs jobs.json 4 25
```

默认测试完全使用本地 mock HTTP 服务，不消耗真实图片额度。真实回归应先运行 `image-models`，再只提交一张低成本图片，随后用 `image-task-wait` 或 `image-task-status` 查询并核对磁盘文件。
