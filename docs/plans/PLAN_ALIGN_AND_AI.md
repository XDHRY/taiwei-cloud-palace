# 太微云宫 · 构件对齐 + 真·AI 重构 计划（2026-09-14）

先生原话口径：
1. 渲染里**没有**用上 DLSS 5 的 AI 能力；动漫 ESRGAN 不算。
2. 墙 / 屋檐 / 房顶分离是基本构件关系错误，**先对齐再谈精致**。
3. 先规划、实测、摸清，再试启用 DLSS 5 的真正能力。

---

## 0. 先讲清楚：DLSS 5 在这台机器上是什么

| 说法 | 事实 |
|---|---|
| 官方 DLSS 5 / Ray Reconstruction / Transformer | 硬锁 RTX Tensor Core。MX450 = Turing TU117，**Tensor Core = 0**。`nvngx_dlssnr.dll` 第一帧会走 `mma.sync`，非法指令或 TDR。 |
| 磁盘上的 `dlss5oneclick.exe` + OptiScaler | **不是** NVIDIA 官方 DLSS 5。是 ReShade Feeder + OptiScaler + FSR/XeSS 的包装。`SKIP_GPU_CHECK=1` 只能骗过菜单，骗不过硅片。 |
| OptiScaler 挂钩 UE MRQ / Blender 离线 PNG | **钩不到**。它吃的是 `IDXGISwapChain::Present()`。离线渲染写磁盘，不 Present。UE Win64 目录里现在也没有 dxgi/fakenvapi 注入。 |
| 上一轮 `realesr-animevideov3-x2` | 真是神经网络，但是**动漫去网点模型**，会抹平 3A 微结构。先生否决成立。 |
| 本机**真正能跑的 AI 重构** | ① `realesrgan-x4plus`（写实 RRDB，已在 `D:\dev-tools\esrgan\models\`）② Intel XeSS DP4a（TU117 有 INT8 点积）③ 更重的 SUPIR/Topaz 可走 CPU+24GB，单帧分钟级。 |

**结论（不装糊涂）：** 这台 MX450 跑不了官方 DLSS 5。要的「3A 那种 AI 大幅改画质」只能走**离线神经重构**。今天必须做的对照：同一帧 × 三次——原图 / 旧动漫模型 / 写实 x4plus。同时把 `dlss5oneclick --help` 跑出真输出，把「注入轨」钉死为失败或伪装，不再口头说。

调研全文：`research/dlss5_real_capability_2026-09-14.md`

---

## 1. 构件分离：根因（已对源码，行号可点）

生成器 `taiwei_cloud_palace_generator.py` 的 `hall()`：

- 墙 = 平顶盒子，顶标高 `top = 0.43 + height`（L1370–1371）
- 前后梁在 `top+0.26`，梁顶 `top+0.37`（L1440）；**山面没有梁、没有斗拱**（L1412 只循环 `yy=±depth*.445`）
- 屋面基准 `local_roof_z = top+0.56`（L1476），比梁顶再悬空 **19cm**
- 屋面是四坡起拱：正殿墙顶到屋底，前檐净空约 **1.6m**，山面约 **2.1m**
- 古建该有的**额枋垫板 / 山花板 / 博风**全部没做 → 看起来就是「墙和房顶分成两截」

同类病：回廊屋面比梁顶高 11.5cm；八角亭 8cm；园墙压顶到瓦 5cm + 起拱空腔 39cm；月洞门脊下三角洞 42cm。

**不是**水面/台基标高漂了（WATER_Z→COURT_Z→MAIN_Z 台基链是闭合的）。

审计全文：`research/component_alignment_audit_2026-09-14.md`

---

## 2. 执行顺序（先生指定：规划 → 测 → 了解 → 再试 AI）

### G0 规划（本文件） — 现在
不改美学主线（燕云形制 / 黑神话氛围继续），但**把「封上墙和屋顶」提到 W4 之前**。没封上之前不扩 3000 件。

### G1 实测现有 YanYun.blend（不清空）
脚本 `measure_component_gaps.py`：按对象名前缀收集 `*_台基殿身` / `*_柱梁斗拱*` / `*_屋面封檐`，报世界 Z 的墙顶、梁顶、屋底、垂直 gap。
再拍一张正殿**东立面正交特写**（关体积雾干扰），主会话 Read 亲眼看缝。

门禁：正殿前檐 gap > 0.25m 或山面 gap > 0.40m → 判定「分离仍在」，必须改生成器。

### G2 了解：DLSS 5 真身探针（今日可失败）
1. 杀掉卡住的 `dlss5oneclick.exe --help`，改用超时捕获版本/字符串（是否含 nvngx、Tensor、SKIP_GPU）。
2. 确认 UE `Engine/Binaries/Win64` **无** dxgi.dll 注入（已确认无）。
3. **不**往 UE 里塞 dxgi.dll：MRQ 钩不到，编辑器视口注入会祸及下次开工程。
4. 写实超分 1 帧：`realesrgan-x4plus`，`-t 256` 防 2GB 爆显存。对比物 = 同一张 540p 帧的动漫 x2。

通过标准：写实模型必须比动漫模型**保留更多瓦楞/木纹/石皮高频**，不能把殿身抹成塑料。

### G3 外科对齐（改生成器，另存新档）
**禁清空** `TaiWei_Video.blend` / `TaiWei_YanYun.blend`。修复只进生成器，STUDY 重建到新目录 `TaiWei_Align/`。

最小改动，保持宋式出檐（`roof()` 曲线不动）：

1. `hall()` 补 **山花/垫板密封面**：沿墙顶矩形一周，垂直升到屋面底壳（inset 2cm 防 z-fight）。
2. `hall()` 补 **山面额枋**（`xx=±width*.45` 沿进深）。
3. `local_roof_z`：`top+.56` → `top+.37`（落到梁顶）；若斗拱帽顶更高，取 `max(梁顶, 斗拱帽)`。
4. 回廊 `2.53` → 梁顶 `2.415`；八角亭 `.17` → `.09`；园墙/月洞同样封腔。

验证：同一测量脚本 gap 前檐 ≤ 0.08m，山面 ≤ 0.12m；东立面特写不再透光。

### G4 对齐验收后再谈下一闸
封上之后才回到燕云 W4（侧脚/生起/卷杀）和组件扩编。AI 重构若 G2 写实模型成立，全片超分从 animevideov3 **换到 x4plus**（或 1080p 目标用 x4 后再压），并保留动漫对照以免回退。

---

## 3. 不在本轮范围

- 不把宫城重做进 UE5 当主线（先生已否 UE 首片；对齐是 Blender 生成器的病）。
- 不购买 RTX / 不装 Topaz（先用已落盘的 x4plus 实证「真 AI 重构」有没有 3A 增量）。
- 不往官方 `nvngx_dlss.dll` 上赌 SKIP_GPU_CHECK。
- 不对成片 blend 跑 `CLEAR_SCENE=1`。

---

## 4. 决策审计

| # | 决策 | 原则 | 理由 | 否决 |
|---|---|---|---|---|
| 1 | 对齐优先于扩件/燕云 W4 | 先生指定 | 墙顶分离是基本关系错误 | 先堆 3000 件 |
| 2 | 官方 DLSS5 判物理不可行，改测写实神经超分 | 完整+诚实 | TU117 无 Tensor；OptiScaler 钩不到离线 | 再往 UE 塞 dxgi |
| 3 | 封山花而不是把墙抬到正脊 | 显式 | 抬墙会穿出檐口；山花才是古建闭合 | 把殿身做成实心大方块 |
| 4 | 修复进生成器 + STUDY 新档 | 铁律 | Video/YanYun 禁清空 | 对着成片 blend 跑生成器 |

---

## 5. 完成定义

- [x] G1 测量表落盘，正殿 gap 数字与东立面图一致
- [x] G2 三图对照（原/动漫/写实）主会话看过；DLSS5 探针有失败证据
- [x] G3 STUDY 新档封闭殿身山花贴上屋面，东立面不再透亮缝（开敞亭榭仍无墙，属形制不是漏做墙）
- [x] 本计划状态：G0–G3 证据齐。下一闸 = 把封缝生成器打进 HIGH 新档并迁燕云氛围，而不是继续对着 YanYun 成片清空

## 6. 实测账（2026-09-14）

### G1 旧档 `TaiWei_YanYun.blend`
- 对象 577。bbox 墙顶→屋底：太微正殿 **+0.856m**，开敞仪门 **+3.396m**。
- 侧特写 `closeup/c_hall_side.png` 钉死：粉墙平顶、上方黑腔、屋顶另起一套。

### G2 DLSS 5 / 神经重构
- `dlss5oneclick.exe` 字符串自证：ReShade + DLSS5-Feeder + OptiScaler；**`no tensor cores`**；RTX 20/30 才走 FP16；`--help` 弹 GUI 挂死（PID 1592），不是 CLI。
- UE `Engine/Binaries/Win64` **无** dxgi/fakenvapi 注入。OptiScaler 钩的是 Present，离线 PNG 钩不到。
- 同帧 `frames_yy_540p/0060.png` 三路：bicubic x4 / `realesr-animevideov3` x2 / **`realesrgan-x4plus` x4 tile256**。写实模型在 MX450+Iris Vulkan 上跑通，瓦楞被重构成有釉面高光的密纹，不是动漫抹平。裁切在 `diag/ai_compare/crop_*.png`。

### G3 封缝 `TaiWei_Align/TaiWei_Align.blend`（STUDY，禁动成片）
- 生成器：`seal_wall_to_roof` + 山面额枋 + `local_roof_z` 落到梁顶/斗拱帽；回廊 2.53→2.415；八角亭 +.17→+.09；园墙/月洞补腔。
- 封闭殿：太微正殿 bbox gap **+0.856 → -0.744**（山花伸进屋面包围盒=贴合）。侧立面 `diag/align_east_side.png` 墙顶接到檐口，黑腔消失。
- 开敞厅（仪门/角亭/水榭）本来就没墙，bbox 仍 2m+；那是空亭形制，不是墙顶分离。下一刀补的是**额枋+垫板把柱头接到屋底**，不是砌实墙。
