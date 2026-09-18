# 太微云宫进展年表（收口到 2026-09-17）

更细的闸门表仍以 `docs/plans/PLAN_LIVE.md` 为准。本文件补上 PLAN_LIVE 停更之后的 G12–G19 与审美审计中断点。

## 主线战场变迁

1. **2.5D 图组 + three.js**（`xiangong` / palace3d）→ 先生 9/3 判「太拉了」，降级存档。史见 `docs/history/xiangong-3d-palace-project.md`、`agentmore-v4-xianxiao-palace.md`。
2. **AgentMore V4 雲霄仙宫** → 贴图槽换完后无头渲染失败，改为先生真机验收。非本库主战场。
3. **Blender 白模 100 卡**（whitemode / listener 9877）→ 研究与体块阶段。史见 `xiangong-blender-dual-purpose-v3.md`。
4. **Blender EEVEE 影视长卷**（现行）→ `taiwei_cloud_palace_generator.py` 程序化生成，工作档 `TaiWei_Wukong_HIGH.blend`。
5. **UE5 MRQ**（9/12）→ 黑帧/白爆结案，交付过 7.5 秒样片；MX450 无 DLSS5。**不是**现行主战场。笔记在 `ue-pipeline/` 与 `docs/history/taiwei-ue5-mrq-pipeline-status-2026-09-12.md`。
6. **Unity** → 评估后否决（HDRP 爆显存 / URP 不如 EEVEE）。见 `unity-vs-blender-rendering-eval-2026-09-12.md`。

## 闸门 G0–G19

| 闸 | 状态 | 一句话 |
|---|---|---|
| G0–G11 | 见 `PLAN_LIVE.md` | 封缝、燕云形制、悟空套件、KIT 开关、独立 HIGH 档 |
| G12–G16 | DONE（记忆） | 构件精修、贴图绑定、1221 件量级、牌坊/九龙壁/石狮/日晷/铜鹤 |
| G17 | DONE 9/16 下午 | 720 帧 1080P EEVEE 正片；桌面 H264/H265 **就是这一版** |
| G18 | 写入 blend，正片未重渲 | 匾额、九龙壁壁画独立、铺地、远山 BOX 映射尺度、苔藓地面；22:43 注入巡航+生命 |
| G19 | Codex 2026-09-17 | GUI + `mcp-for-blender`；仪门开 78°；巡航路径改写；渲了 140/380/504/720。**未**重渲 30 秒正片 |

## 2026-09-17 审美审计（中断，未写成刀法文档）

先生令：当燕云级策划，列审美缺陷 + 布局/营造法式逻辑清单，先审后刀。推送任务插入后暂停。

已做：

- 复制 Codex 的 `mcp-for-blender` 到 `blender/mcp-for-blender/`
- 自建客户端 `blender/tools/taiwei_mcp.py`（端口 9876）
- 场景普查：EEVEE Next / 1920×1080 / TAA 16 / 1196 对象 / 1051 mesh / 10 相机 / 17 灯
- 批次一 8 张固定机位 + 批次二 6 张人视，在 `evidence/audit-2026-09-17/`
- Codex 四帧在 `evidence/g19-codex-frames/`

肉眼已坐实、尚未写成分级刀法的问题（供接手人接着写）：

1. **正脊金葫芦 / 重阁宝刹**：歇山正殿不该立喇嘛塔式宝顶。源码 `finial.lathe` 在 `hall("太微正殿", …)` 之后。
2. **正脊中段白带**：上檐歇山山花/博风在俯视变成一条白板，G19 frame 380 与 A7 都在。
3. **鸱吻尺度**：正吻高过正脊太多，近看是玩具龙，不是扫描级鱼龙。A4 / A8 刺眼。
4. **走兽**：垂脊走兽像金钉阵列，不是仙人走兽。
5. **远山**：圆锥糖塔，横岚是白雾条（A4 右侧一条白烟），岛像切出来的圆饼（A1、G19-720）。
6. **九龙壁**：壁画糊成印象派色块；壁顶蓝瓦错台；壁前栏杆像玩具；壁在岛缘/水上，不是宫门内的影壁制度。G19-504、B3。
7. **外岛放射廊桥**：俯视像自行车轮，不是因势随形的水院。A1。
8. **北崖栈道**：断头板桥 + 白线「绳」；相机名「北崖飞瀑」但画面没有瀑。A6。有对象 `飞瀑水口与飞珠`，机位没拍到或被藏了。
9. **斗栱**：源码是两跳华栱+下昂，人视几乎看不见铺作层，只见红柱撑蓝顶。
10. **开间**：正殿 `width=14.4` → 约 7 间，合「九五」不足；仪门开 78° 后中轴对正殿，但这是 Codex 改 mesh，生成器重跑会丢。
11. **灯**：106 盏六角绢宫灯 + 33 根云廊灯柱，夜景没问题，白天是仪仗阵列。
12. **贴图平涂**：远山 BOX mapping 尺度仍偏平面；水面塑料绿；铺地从空中看仍是平色。
13. **天空**：AgX + 灰蓝无云无层次，World Background 强度 0.32。
14. **营造法式已有、画面读不出**：侧脚/生起/卷杀在 `hall()` 里（`cejiao_delta` / `shengqi_scale` / `ENTASIS_*`），远景被屋面和灯盖住。

刀法方向（先生已授权删）：远山改剪影或直接删糖塔；外岛廊桥减到东西南北四向或随岸；撤宝刹；九龙壁要么做成合格影壁要么移出中轴电影镜头；正片重渲前先改名 `frames_720`。

## 生图 MCP

`mcp-image/` 是 2026-09-15 切到 GPT image 2.5 后的 task/batch 架构。契约见该目录 `SKILL.md` 与 `docs/history/iterative-image-gen-task-contract.md`。
