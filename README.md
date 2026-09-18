# 太微云宫 · 工程库

> 2026-09-18 起转为公开仓库（转公前已移除含个人操作信息的 `docs/history/` 与 `docs/handoff/`，并重建 Git 历史）。主人是先生。代理自称「素」。

目标产物：一部 **30 秒电影级仙宫短片**（燕云十六声的细腻 + 黑神话悟空 CG 的沉郁光），零操作桌面交付。构图、留白、光，比堆构件重要。

本库按分类收口 2026-09-17 的全部可复现进展。720 帧序列、超分结果、备份 blend 体积超过 GitHub 免费账号额度，只进清单，不进 Git。

## 目录

| 路径 | 内容 |
|---|---|
| `blender/src/` | 场景真源 `taiwei_cloud_palace_generator.py` + HIGH 重建 bat |
| `blender/tools/` | 巡航、生命系统、720 渲、MCP 客户端、审美审计脚本 |
| `blender/mcp-for-blender/` | Codex 2026-09-17 下载的 ahujasid `mcp-for-blender` 源码副本 |
| `blender/scripts-scene/` | 燕云材质、氛围、测量、导出 |
| `blender/scripts-rebuild/` | Wukong HIGH 独立档的悬浮审计 / 验收渲 |
| `scenes/current/` | 现役工作档 `TaiWei_Wukong_HIGH.blend`（可覆盖重建） |
| `scenes/protected/` | **禁清空** 三档：Video / YanYun / Align_HIGH |
| `assets/textures_wukong/` | 悟空燕云 PBR 贴图（生成器绑定目录） |
| `assets/asset_library/` | 组件资产库 + 目录 |
| `assets/guides_wukong/` | 形制扫描参考图 |
| `assets/asset_library/` | 组件目录 `ASSET_CATALOG.md` + 氛围参考图（贴图/形制图与上两栏去重，未重复入库） |
| `evidence/` | G19 审计帧、Codex 四帧、工程图鉴、UE5 样张、氛围参考 |
| `films/` | 桌面 30 秒 H264 正片（G17 时代；H265 同内容未收） |
| `desktop/01-入口/` | 桌面双击入口 + `taiwei_web.glb` |
| `mcp-image/` | 生图 MCP 源码 + 任务契约 skill（**不含 API key**） |
| `ue-pipeline/` | UE5 MRQ 管线笔记（已结案，非主战场） |
| `docs/plans/` | `PLAN_LIVE` 与各转向计划 |

> 注：`docs/history/`（项目史记忆档案）与 `docs/handoff/`（接手文档）含个人操作信息，2026-09-18 转公有时已从仓库及全部 Git 历史移除（本地保留，见 `docs/OMITTED.md`）。

## 当前断点（2026-09-17 晚）

- 现役档：`scenes/current/TaiWei_Wukong_HIGH.blend`（约 191MB，1196 对象，EEVEE Next 1080P / TAA 16 / 720 帧巡航已注入）。
- Codex 已用 `mcp-for-blender` 开 GUI、改仪门开合 78°、改巡航路径（自称 G19），并渲了 140/380/504/720。
- 桌面 30 秒 H264/H265 **仍是 9/16 下午 G17 成片**，不是 G18/G19。
- `frames_720/` 里 720 张 PNG 也是 G17。正片管线「文件 >100KB 则跳过」——重渲前必须先改名，否则会把旧片再压一遍。
- 审美审计已拍 14 张固定机位 + 人视补拍，清单尚未写成桌面刀法文档（本轮改推送，审计暂停）。

## 绝对禁写

这三档是成片对照，清空或覆盖等于毁片：

- `scenes/protected/TaiWei_Video.blend`
- `scenes/protected/TaiWei_YanYun.blend`
- `scenes/protected/TaiWei_Align_HIGH.blend`

生成器 `CLEAR_SCENE=1` **只允许**打 `TaiWei_Wukong_HIGH.blend`。

## 机器铁律

- GPU：MX450 2GB。同时只开 **一个** Blender。
- 正片引擎：`BLENDER_EEVEE_NEXT`，`taa_render_samples = 16`。Cycles 160 sample 在这台机器上约 1 小时/帧，是死路。
- 无 Tensor Core，没有 DLSS5。离线超分走 Real-ESRGAN `x4plus`，串行 `-g 1 -j 1:1:1`。不要用 `animevideov3`。
- GUI 退出会静默把内存里的旧场景覆盖刚写到磁盘的新 blend。无头重建 / 720 渲期间禁止开 GUI。
- 桌面真身是 `E:\zhuomian`（注册表重定向），不是 `C:\Users\xdrhh\Desktop`。

## 生图 MCP

源码在 `mcp-image/`。默认模型 `gpt-image-2.5-flare`。`create-image` 返回的 `task_id` **不等于完成**；以 `completed` + 磁盘文件为准。

`submission_unknown` 禁止盲重试。对账确认上游没接到任务后，换新 `operation_id` 再提。密钥只走环境变量 `IMAGE_API_KEY`，本库不收 `.env`。

## 本库故意没收的东西

见 [`docs/OMITTED.md`](docs/OMITTED.md)。主要是：

- `taiwei_video/frames_720`（2.4GB，G17 旧帧）
- `taiwei_video/frames_upscaled`（2.2GB）
- 多份季节 / 备份 blend（Align 春冬、`.blend1`、`_backup_*`）
- 生图落盘 `C:\Users\xdrhh\.zcode\image-runs`（309MB，含计费产物，不入库）
- 桌面 H265 正片（与 H264 重复，H264 已收）

本地原件都还在工作区，没有删除。

## 复现（HIGH 重建）

本机 Blender：`D:\blender-portable\blender.exe`

```bat
taiwei_wukong_rebuild_v2.bat
```

重建后必须再注入巡航 + 生命，否则只有静态场景。脚本在 `blender/tools/`。

## 许可

公开归档，供参考学习；blend 场景与贴图资产的再分发需经先生允许。仓库不含任何密钥。
