# 本库故意没收的本地原件

GitHub 免费账号：**仓库建议 <1GB，LFS 存储 1GB / 月流量 1GB，单文件普通 Git 上限 100MB**。
下面这些还在本机，没有删除，只是不进 Git。

工作区根：`E:\UserData\xdrhh\.openclaw\workspace`

| 本地路径 | 大约体积 | 为什么没收 |
|---|---|---|
| `taiwei_video/frames_720/` | 2.4 GB / 720 PNG | G17 旧正片帧。管线「>100KB 则跳过」，G18/G19 重渲前应改名为 `frames_720_g17` |
| `taiwei_video/frames_upscaled/` | 2.2 GB | Real-ESRGAN 超分缓存 |
| `taiwei_video/frames_540p/` | 562 MB | 540p 中间帧 |
| `taiwei_video/frames_yy_1080p/` + `frames_yy_540p/` | 694 MB | 燕云验证片帧 |
| `taiwei_video/upscaled/` | 543 MB | 另一份超分 |
| `taiwei_video/diag/` | 525 MB | 诊断截图堆 |
| `taiwei_video/preview/` `showcase_frames/` `closeup/` `survey/` | ~320 MB | 过程预览 |
| `taiwei_video/TaiWei_Align/*.blend` 春/冬/bak + `.blend1` | ~1.3 GB | 只收现行 `TaiWei_Align_HIGH.blend`；季节档与自动备份不入库 |
| `taiwei_video/_backup_20260915_wukong_yanyun/` | 350 MB | 转向前备份 |
| `taiwei_video/TaiWei_WukongRebuild/TaiWei_Wukong_STUDY.blend` | 69 MB | STUDY 档，可重建 |
| `taiwei_video/*.blend1` | 与正档等大 | Blender 自动备份 |
| `E:\zhuomian\太微云宫3D\05-样片成片\*H265*.mp4` | 104 MB | 与已收 H264 同内容 |
| `E:\zhuomian\太微云宫3D\04-验收截图\` | 368 MB / 103 文件 | 历史迭代截图；工程图鉴 + 本轮审计帧已收。清单见 `docs/omitted-acceptance-shots.txt` |
| `E:\zhuomian\太微云宫3D\02-贴图材质\` | 164 MB | 与 `assets/textures_wukong` 重复 |
| `C:\Users\xdrhh\.zcode\image-runs\` | 309 MB / 988 文件 | 生图计费产物，不入库。MCP 源码已收 |
| `tools/.blender-mcp-venv/` | 本机 venv | 用 `blender/mcp-for-blender` 自行安装 |
| `docs/history/`（21 个记忆档案）+ `docs/handoff/`（2 份接手文档） | ~200 KB | 含个人操作信息（渠道清单、key 编号、工作流细节），2026-09-18 转公有时从仓库及全部 Git 历史移除；本地备份在 `workspace/taiwei-private-docs-backup/` |

取回方式：在本机按上表路径复制。不要为了「补全」强行 LFS 上传，会把免费额度打爆，以后 blend 也推不上去。
