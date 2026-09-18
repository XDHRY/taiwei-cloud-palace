# 太微管线 v2 · Blender→UE5→DLSS5 电影级视频量产管线 · 宏大计划

> 版本：v2.0（2026-09-12 晚，先生定调后重构）
> 宗旨：**在我的电脑上建成一条「Blender 参数化建模 → 虚幻5 + DLSS5 渲染 → 精美展示视频」的稳定自动化管线，以后通过建模即可稳定量产产品展示/场景展示视频。**
> 方法铁律：**先大规模调研（GitHub/官方文档/社区实证），再动手；卡住两轮立即转调研，不闷头试错。**

---

## 1. 现状资产盘点（2026-09-12 实测核实）

| 资产 | 位置 | 状态 |
|---|---|---|
| Blender 4.5.12 LTS | `D:\blender-portable\` | ✅ 可用（便携版，命令行可驱动） |
| 太微云宫参数化生成器 | `workspace\taiwei_cloud_palace_generator.py` | ✅ 完整（独立场景生成：屋瓦/斗拱/栏杆/虹桥/松竹/仙鹤/飞瀑/云海，分 STUDY/HIGH/FINAL 档） |
| 太微洞天 blend 工程 | `workspace\taiwei_video\TaiWei_Video.blend`（103MB）等 3 个 | ✅ 含 30s@24fps 巡航运镜（Track-To+Bezier+景深） |
| FBX 切片 ×10 | `D:\UnrealProjects\Assets_FBX\`（山体/台基/木构/瓦作/雕饰/廊桥/池水/花木/庭石/陈设） | ✅ 已导出 |
| UE 5.4.4 工程 | `D:\UnrealProjects\TaiWei_Cinema\` | ✅ 资产已入库：10 网格+5 材质+场景+3 张 MRQ 预设+30s/720帧 六镜头电影序列 |
| MRQ 自动化机制 | `render_gui.bat` + `Content\Python\init_unreal.py`（武装旗标+PIE 执行器+哨兵） | ✅ **已打通**（渲染任务可全自动跑完并落盘 PNG 序列） |
| OptiScaler/DLSS5 桥 | `D:\UnrealProjects\OptiScaler_Bridge\`（OptiScaler v0.9.4 + dlss5oneclick v0.13.14 + fakenvapi/dxgi） | ⏸ 文件齐备，未注入（待调研定案后实施） |
| ffmpeg 8.1.1 | 系统 PATH | ✅ 可用 |
| **当前唯一卡点** | **场景级渲染全黑**（编辑器视口 unlit 亦黑；MRQ 帧 max=1/255） | 🔴 调研代理正在全网查已知解法 |

硬件约束：MX450 2GB VRAM + 24GB RAM（共享显存兜底）；工程与缓存放 D/E 盘，永不写 C 盘。

## 2. 管线五段架构（目标形态）

```
┌─ S1 建模段（Blender）──────────────────────────────┐
│  bpy 参数化生成器 → .blend 工程 → 分模块导出          │
│  标准：命名规范/模块粒度/UV2光照贴图/材质槽命名契约      │
└──────────────┬─────────────────────────────────────┘
               ▼ （导出桥：选型 ← 调研报告2）
┌─ S2 入库段（UE5 资产管线）───────────────────────────┐
│  自动导入 → 材质实例绑定 → 场景装配脚本               │
│  标准：每模块可独立替换，版本化重导不丢绑定             │
└──────────────┬─────────────────────────────────────┘
               ▼
┌─ S3 环境段（光照规范）───────────────────────────────┐
│  全动态电影光照 rig：Movable 太阳 + 天光实时捕获        │
│  + SkyAtmosphere + 云海高度雾 + 曝光规范              │
│  （本段为黑帧修复主战场 ← 调研报告1）                  │
└──────────────┬─────────────────────────────────────┘
               ▼
┌─ S4 渲染段（MRQ 自动化）─────────────────────────────┐
│  队列预设 + 电影运镜序列 + 升采样策略（TSR/DLSS5 定案   │
│  ← 调研报告3）+ 武装旗标全自动渲染（机制已通）          │
└──────────────┬─────────────────────────────────────┘
               ▼
┌─ S5 成片段 ─────────────────────────────────────────┐
│  PNG 序列 → ffmpeg H.265 成片 → （可选 AI 升采样/补帧） │
│  → 交付 E:\zhuomian\太微云宫电影级全片输出\            │
└─────────────────────────────────────────────────────┘
```

## 3. 目录布局（已建/待建）

| 用途 | 路径 | 状态 |
|---|---|---|
| 管线权威文档区 | `workspace\ue_pipeline\`（PLAN.md / DLSS5_NOTE.md） | ✅ |
| 调研报告归档 | `workspace\ue_pipeline\research\`（3 份报告落盘处） | ✅ 已建 |
| 管线编排脚本 | `workspace\ue_pipeline\scripts\` | ✅ 已建（待填） |
| 管线文档 | `workspace\ue_pipeline\docs\` | ✅ 已建（待填） |
| Blender 参数化源 | `workspace\taiwei_*.py` + `taiwei_video\*.blend` | ✅ 现存 |
| UE5 工程 | `D:\UnrealProjects\TaiWei_Cinema\` | ✅ 现存 |
| FBX 中转区 | `D:\UnrealProjects\Assets_FBX\` | ✅ 现存 |
| DLSS 注入桥 | `D:\UnrealProjects\OptiScaler_Bridge\` | ✅ 现存 |
| 成片交付区 | `E:\zhuomian\太微云宫电影级全片输出\` | ✅ 现存 |

## 4. 三路在途调研（2026-09-12 21:1x 派发，3.8 Flash）

| 调研 | 落盘 | 回答的问题 |
|---|---|---|
| ① MRQ 黑帧已知解法 | `research\mrq_black_frames_report.md` | 视口 unlit 全黑的根因与确切修法（Stationary 灯无烘焙/材质标记/游戏模式/曝光） |
| ② Blender→UE5 桥选型 | `research\blender_ue5_pipeline_report.md` | FBX/glTF/Datasmith/SendToUnreal 对比、模块粒度、材质映射、MRQ 自动化仓库参考 |
| ③ DLSS5 真相与低端卡策略 | `research\dlss5_report.md` | dlss5oneclick 真伪、OptiScaler 对离线 MRQ 有效性、2GB 显存最优配置、TSR vs 注入 vs 后处理升采样定案 |

## 5. 阶段清单

- [x] **P0 立项**：宗旨定调、资产盘点、目录骨架
- [x] **P0.5 调研**：三路全网调研（在途，落盘即读）
- [ ] **P1 黑帧歼灭**（靠①）：按调研结论修复场景渲染 → 冒烟帧亲眼验收非黑
- [ ] **P2 首片下线**：MRQ_TaiWei_Full180（180帧1080P）→ ffmpeg 成片 → 桌面交付
- [ ] **P3 导出桥定型**（靠②）：确立 Blender→UE5 标准导出/入库自动化，形成「改模型→一键重导→一键重渲」闭环
- [ ] **P4 升采样定案**（靠③）：DLSS5 注入 或 TSR 原生 或后处理 AI，出对比样张后定案
- [ ] **P5 全片 720 帧**：30 秒六镜头全片 + 交付验收
- [ ] **P6 量产化**：管线脚本化封装（建模变更→成片一键产出），写入操作手册

## 6. 今日实战沉淀的教训（永不再犯）

1. UE5 `-ExecutePythonScript` 会退出 GUI 编辑器 → 启动代码必须走项目 `Content\Python\init_unreal.py`
2. `-unattended` 会杀掉异步任务 → GUI 模式 + 武装旗标 + tick 延迟启动
3. Git Bash 会把 `/Game/...` 参数翻译成 `D:/Git/Game/...` → UE 启动一律走 .bat
4. 材质 `bUsedWithStaticLighting` 标记修复**必须持久化入库**，否则每次加载报警且编辑器外可能渲染异常
5. 子代理调研必须**边搜边落盘**（首条记录即骨架），终报丢失不等于工作丢失
6. 编辑器控制台 `py "..."` 可执行任意 Python（已实证），但输入可能丢失需日志确认
7. 看图判读只走主会话原生 Read，禁 vision MCP
8. **`unreal.Rotator` 位置参数序 = (roll, pitch, yaw)**（与 C++ 的 Pitch,Yaw,Roll 相反！）。任何脚本用 `Rotator(p, y, r)` 位置传参都会把相机拧成朝天（pitch=yaw≈95）。9/12 晚全部"SceneCapture 黑帧"都是这个 bug 拍的天空。**铁律：永远用关键字 `unreal.Rotator(pitch=.., yaw=.., roll=..)`，或把 `find_look_at_rotation` 返回的结构体直接传递，绝不按位置重建。**
9. **图像判读必须先拆 RGB/Alpha 通道**：alpha=255（PNG）或 alpha=1（EXR）会把 mean 抬到 63.75/0.25 伪装成"有内容"。同一晚两次中招（EXR 一次、MRQ PNG 一次）。统计只认 RGB 三通道。
10. **断言"已修复/已排除"前必须看副作用证据**：fix3 脚本 7 个材质全部因属性名 `value`（应为 `r`）报错中止、0 个网格被覆盖，却被当成"新材质也黑=材质已排除"的证据，白烧一晚。脚本日志的 errors 数组是判案的一部分。
11. SceneCapture 三分源判读法：`SCS_BASE_COLOR` 有内容=几何光栅化正常；`SCS_SCENE_COLOR_HDR`=0=光照/后处理链断；`SCS_FINAL_COLOR_LDR`=0 但 basecolor 正常 → 问题在 tonemap/曝光/光照段，与材质无关。
12. **关卡 PPV 的曝光钳位对 SceneCapture 与 MRQ 都无效**；曝光必须写到具体相机/捕获组件的 `post_process_settings`（`override_auto_exposure_bias=True` + `auto_exposure_bias=-8` + `post_process_blend_weight=1`）。65000 lux 直射阳光的太微场景实测 bias -8 收敛（mean≈0.37）。9/12 晚靠此让 MRQ 出片（`Scripts\_fix4_cam_exposure.py`）。
13. **bat 文件必须纯 ASCII**：UTF-8 中文 title/注释会被 cmd 按 GBK 乱码解析直接拒跑（render_gui.bat 因此静默失败一次）。

## 7. 待定案项（调研回来后 24h 内填）

- [x] **导出桥选型定案（据②报告）**：**模块化 FBX + JSON manifest 解耦管线**（评分 9.8/10 胜出）。Blender 端 `bpy` 导出唯一原型网格 `SM_*.fbx`（原点居中）+ `manifest.json` 记录全部实例变换；UE 端 Python `AssetTools` 导入（`build_nanite=True`）+ HISM 实例化装配（5000 构件≈15 draw calls、<400MB VRAM）。**材质 100% UE5 内部定义**（4 主材质 + ORM 打包贴图 + 材质槽命名契约 `MI_*` 自动绑定），Blender 程序化节点材质零依赖导入。Send-to-Unreal 需 GUI 会话、Datasmith 无官方 Blender 导出器、USD 对 2GB 显存过重——均落选。
- [x] **升采样路线定案（本地审计+架构分析）**：**TSR 原生为主路径**。理由：(1) MX450 是 Turing TU117 **无 Tensor Core**，任何真 DLSS（含 DLSS5 神经渲染）在本机物理上不可运行；(2) dlss5oneclick/OptiScaler 实证为升采样转换层（DLSS 输入→FSR2/XeSS 输出），只对实时游戏有意义；(3) **离线 MRQ 渲染不走 DLSS 插件路径**，且离线不在乎帧率——原生 1080P + TSR + Temporal Sample 8 即质量上限。DLL 注入轨降级为可选实验（非主路径）。渲染配置：TSR + temporal 8 + spatial 1 + 低显存 CVar（PoolSize=800、Lumen 软光追、关 VSM）。
- [ ] 黑帧确切根因与修法（子代理自主实测中 → `research\black_frames_diagnosis.md`）
- [ ] 材质库按定案重构为 4 主材质 + MI 实例（P3 随导出桥一起做）
