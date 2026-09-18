# 太微云宫 · Blender 渲染 + AI 超分成片管线

2026-09-13 先生定调：UE5 首片效果不够好，渲染主线切回 Blender，叠加「DLSS5」画质增强。
物理真相：MX450 (Turing TU117) 无 Tensor Core，官方 DLSS 5 不可跑。
**2026-09-14 先生纠偏：animevideov3 是动漫去网点，不算 DLSS，不进正片。**
现行超分 = `realesrgan-x4plus`（写实 RRDB）。批量必须 `-g 1 -j 1:1:1 -t 192`（指定 MX450、单线程）；默认并行会打爆 2GB 写出 24KB 坏帧。
活计划：`PLAN_LIVE.md`。

## 管线（已全链路验证）

```
工作档（封缝后）TaiWei_Align_HIGH.blend 或迁入燕云氛围的新档
  → EEVEE 渲 960x540
  → ESRGAN realesrgan-x4plus -s 4 -t 256
  → ffmpeg scale=1920:1080 + H.265
```

对比旧线：1080p 直渲 25.7s/帧 ≈ 5-6 小时 → 新线总计约 1 小时 50 分，**快 3 倍**，且超分后瓦楞/枝叶比原生 1080p 更锐（AI 补细节）。

## 工具

- 超分: `D:\dev-tools\esrgan\realesrgan-ncnn-vulkan.exe`
  - **正片模型 `realesrgan-x4plus`**（写实）。动漫 `realesr-animevideov3` 仅作对照，禁止当正片。
  - 批处理: `realesrgan-ncnn-vulkan.exe -i <in_dir> -o <out_dir> -n realesrgan-x4plus -s 4 -t 256 -f png`
  - 旋钮：假细节太多改 `realesrnet-x4plus`；2GB 爆显存把 `-t` 降到 192。
- Blender: `D:\blender-portable\blender.exe` (4.5.12 LTS)
- ffmpeg: `C:\Users\xdrhh\bin\ffmpeg.exe`

## 本次执行记录

1. 样片（已交付验证）：preview 现成 180 帧 540p → 超分 1m36s → H.265
   `E:\zhuomian\太微云宫电影级全片输出\太微云宫_Blender超分样片_7.5秒_1080P.mp4` (hevc/1080p/7.5s/16.2Mbps)
2. 全片（渲染中）：`render_540p.py` 锁 960x540 输出到 `frames_540p/%04d.png`
   `blender -b TaiWei_Video.blend -P render_540p.py -s 1 -e 720 -a`
   实测 8.2s/帧、内存 630MB、48 samples

## 合成配方（沿用首片验证过的）

```
ffmpeg -y -framerate 24 -i frames_upscaled/%04d.png \
  -vf "fade=t=in:st=0:d=1.0,fade=t=out:st=28.6:d=1.4" \
  -c:v libx265 -preset medium -crf 17 -pix_fmt yuv420p -tag:v hvc1 输出.mp4
```

## 注意

- 逐帧超分无时序一致性约束，animevideov3 是逐帧方案里闪烁最少的；若发现闪烁再考虑 RIFE/时序滤波。
- frames_540p 命名是 `0001.png` 无前缀（render filepath 未加前缀），合成时注意通配符。
- 勿动 TaiWei_Video.blend 内容（禁清空铁律）；分辨率只走 render_540p.py 运行时覆盖，不写回 blend。
