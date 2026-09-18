# 图片生成 MCP 改造进度

- 时间：2026-09-04（北京）
- 持久化 task/batch 核心、独立 runner、stdio MCP 八工具、批量客户端、mock 与协议 smoke 已完成基础闭环。
- 本轮完成：runner lock 采用 hard-link 独占发布；锁刷新不再替换共享 lock 文件，丢失 PID/token 所有权时 runner 立即停止；task update、operation、batch manifest 均使用 token 化 hard-link 锁并按 token 释放；createBatch/batchStatus 的 manifest 读改写已纳入 batch 锁；`submission_unknown` 对 HTTP 408/429/5xx 与请求未知状态统一止损，不盲目重试；package.json 保持 Node >=18 约束；新增 edge-test 覆盖未知提交、同主机 URL、重定向、非图片 Content-Type、sidecar 篡改。
- 已验证：core.mjs、runner.mjs、server.js、batch.mjs、edge-test.mjs Node syntax checks 通过；npm.cmd test 通过（generation_count=4、batch generation_count=2、edge generation_count=1 且 unknown_status=submission_unknown）；基础 mock upstream 最大并发=2。
- 文档已对齐：mcp-image README、iterative-image-gen、media-forge 已改为实际 `https://code.mmkg.cloud/v1` 默认端点/环境变量、25 秒前台等待、约 30 秒宿主边界、detached runner、resume、逐文件校验、取消、外链兼容和未知提交语义。
- 历史基础验证：core.mjs、runner.mjs、server.js、batch.mjs、edge-test.mjs Node syntax checks 通过；基础 mock、resume、MCP smoke 已通过。
- 生产实测（2026-09-04/05，本轮）：真实配置通过 ZCode `config.json` 的 `mcp.servers.image.env` 注入到隔离子进程；`image-models` 成功返回 27 个模型，实际端点为 `https://code.mmkg.cloud/v1`。第一轮单图 `n=2` 只返回 1 张，正确终止为 `COUNT_MISMATCH`；第二轮默认外链保护正确拒绝上游返回的外部图片 URL（`IMAGE_HOST_NOT_ALLOWED`）；第三轮仅在隔离进程显式开启 `IMAGE_ALLOW_EXTERNAL_IMAGE_HOSTS=1` 后完成真实 `n=1` 单图和 batch 3 项测验：单图 1/1 成功，batch 1/3 成功、1 项上游 404、1 项下载响应体超时（180s），均无盲目重试或半文件误报。成功图片已做 SHA-256、bytes、sidecar、manifest 核验并通过视觉检查。
- 优化回归（2026-09-05）：基于真实反馈完成多轮修正：默认端点改为实际 `https://code.mmkg.cloud/v1`；默认兼容中转站正常外链图片返回（可用 `IMAGE_ALLOW_EXTERNAL_IMAGE_HOSTS=0` 恢复严格同主机）；`n>1` 首响应少图时保留已成功产物并按缺口自动补足；状态新增 `provider_count`/`completed_count`；batch 创建前拒绝重复 job id/operation_id；`batchStatus` 顶层返回 `files`/`verified_files`，坏 task 按 job 隔离报告；sidecar 保存完整 source URL。
- 优化后自动测试：Node syntax、`npm.cmd test`、MCP smoke 全绿；mock 已新增首个 `n=2` 响应只返回 1 张、第二次按缺口补足，实测 generation_count=5、最大并发=2；重复 batch ID/operation 预检通过；unknown submission、URL、body timeout、sidecar 篡改测试继续通过。
- 优化后真实测试目录：`E:\zhuomian\mcp-image-real-optimized-20260905-010859`。真实 `image-models` 返回 27 个模型；真实 batch 3/3 完成（并发 2）；真实 `n=2` 专项完成 2/2，文件为 `n2\img-20260905-011756-0343fef0cf\img-01.png`（2,253,067 bytes）与 `img-02.png`（2,031,846 bytes），均有 sidecar/manifest 且 SHA-256 匹配；两张视觉抽查通过。
