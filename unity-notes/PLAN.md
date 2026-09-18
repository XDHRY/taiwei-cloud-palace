# 太微仙宫 Unity 组件级渲染与 DLSS 5 (Neural Rendering) 管线规划

## 1. 核心定位
先生令：
- 若 UE 存在不适配、黑场或材质脱节，自主在 **Unity** 里组织组件、挂载着色器与后处理；
- 接入 **DLSS 5 (Neural Rendering / OptiScaler)** 执行慢速高质量画面重构；
- 目标产物：**30 秒 180 帧 (或 720 帧全量) 电影 CG 级视频**。

## 2. 软硬件与环境基线
- 独显：NVIDIA GeForce MX450 (2GB VRAM)，系统物理内存 24GB 共享显存护航。
- 磁盘余量：D 盘 45.4GB，E 盘 84.8GB。
- 资产基础：已在 `D:\UnrealProjects\Assets_FBX\` 导出 10 大完整建筑群与自然景观切片（山体、台基、殿阁木构、琉璃瓦作、门窗雕饰、廊桥园墙、池水飞瀑、松竹花木、草花庭石、庭院陈设）。

## 3. 推进阶段
- [ ] **Phase 1 (Unity 环境与轻量工程部署)**：部署 Unity 运行环境至 D/E 盘，创建 `TaiWei_UnityCinema` URP/HDRP 高清影视工程。
- [ ] **Phase 2 (资产与组件装配)**：将 10 大 FBX 切片导入 Unity，挂载仙侠古建专用 PBR 材质组件（琉璃金顶、朱漆木柱、汉白玉、池水水纹）。
- [ ] **Phase 3 (DLSS 5 / OptiScaler 神经渲染注入)**：将 DLSS 5 桥接 DLL 注入 Unity 独立运行管道，开启时间超分辨率与神经画面重构。
- [ ] **Phase 4 (30 秒影视级巡航运镜与切片离线输出)**：使用 Unity Cinemachine 或 Recorder 逐帧离线捕获 180 帧/720 帧 1080P/4K 视频，压制合成为最终成片。
- [ ] **Phase 5 (桌面交付验收与任务终结)**：成品交付至 `E:\zhuomian\太微云宫电影级全片输出\`。
