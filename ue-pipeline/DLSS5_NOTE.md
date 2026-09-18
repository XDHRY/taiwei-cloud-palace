# DLSS 5 偷跑落地纪录

- **版本来源**：社区前沿泄露版 DLSS 5 神经渲染套件（`faisalkindi/DLSS5oneclick` v0.13.14，基于 `renodx-dlss5` 与 `nvngx_dlssnr.dll` 神经网络重构核心）。
- **部署位置**：`D:\UnrealProjects\OptiScaler_Bridge\`。
- **运行机制**：
  1. 通过 `dlss5oneclick.exe` 注入底层渲染管道；
  2. 使用 `DLSS5ONECLICK_SKIP_GPU_CHECK=1` 绕过传统显卡硬件检测；
  3. 接管虚幻 5 的帧后处理，通过慢速神经网络渲染（Neural Rendering）在离线渲染队列中执行逐帧画面重构。
