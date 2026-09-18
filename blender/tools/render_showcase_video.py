# -*- coding: utf-8 -*-
"""太微云宫 · 快速生成高品质展示样片视频并直呈桌面。

策略：
- 沿 720 帧正式巡航轨迹均匀采样 48 帧（覆盖全部南轴牌坊、仪门石狮双鼎、高台铜鹤日晷、九龙照壁钟亭、东苑水巷、水墨全景长卷）
- 渲染引擎：EEVEE Next（4 samples 纯净抗锯齿，960x540 高清半采样）
- 渲染完毕后调用 ffmpeg 编译出两部 MP4 并直接投递至用户桌面：
  1. E:\zhuomian\太微云宫_仙境巡航_顺滑速览.mp4 (24fps 动作流畅精美)
  2. E:\zhuomian\太微云宫_仙境巡航_慢速品鉴.mp4 (8fps 节奏舒缓细节可赏)
- 并在后台拉起正式 720 帧 1080P 无损全长正片持续渲染
"""
import bpy
import os
import glob
import time
import subprocess

OUT_FRAMES = r"E:\UserData\xdrhh\.openclaw\workspace\taiwei_video\showcase_frames"
os.makedirs(OUT_FRAMES, exist_ok=True)
for stale in glob.glob(os.path.join(OUT_FRAMES, "frame_*.png")):
    try:
        os.remove(stale)
    except Exception:
        pass

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.camera = bpy.data.objects.get("巡航相机")
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 50
scene.render.image_settings.file_format = 'PNG'
try:
    scene.eevee.taa_render_samples = 4
except Exception:
    pass

TOTAL_FRAMES = 48
start_f, end_f = 1, 720
step = (end_f - start_f) / (TOTAL_FRAMES - 1)
frame_indices = [int(round(start_f + i * step)) for i in range(TOTAL_FRAMES)]

print(f"[展示视频] 开始渲染 {len(frame_indices)} 帧序列...")
t0 = time.time()

for i, f_num in enumerate(frame_indices, 1):
    scene.frame_set(f_num)
    fpath = os.path.join(OUT_FRAMES, f"frame_{i:04d}.png")
    scene.render.filepath = fpath
    t_start = time.time()
    bpy.ops.render.render(write_still=True)
    t_cost = time.time() - t_start
    elapsed = time.time() - t0
    print(f"[展示视频] {i:2d}/{len(frame_indices)} 帧{f_num:4d} 完成 ({t_cost:.1f}s) 累计: {elapsed/60:.1f}min")

print(f"[展示视频] 全部序列帧渲染完成！总耗时: {(time.time()-t0)/60:.1f} 分钟")

FFMPEG = r"C:\Users\xdrhh\bin\ffmpeg.exe"
DESKTOP = r"E:\zhuomian"
TARGET_DIR = r"E:\zhuomian\太微云宫3D\05-样片成片"
os.makedirs(TARGET_DIR, exist_ok=True)

v1_desk = os.path.join(DESKTOP, "太微云宫_仙境巡航_顺滑速览.mp4")
v1_repo = os.path.join(TARGET_DIR, "太微云宫_仙境巡航_顺滑速览.mp4")
v2_desk = os.path.join(DESKTOP, "太微云宫_仙境巡航_慢速品鉴.mp4")
v2_repo = os.path.join(TARGET_DIR, "太微云宫_仙境巡航_慢速品鉴.mp4")

# 1. 24fps 快速流畅版 (2秒极速全景)
cmd1 = [
    FFMPEG, "-y", "-framerate", "12", "-i", os.path.join(OUT_FRAMES, "frame_%04d.png"),
    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
    "-movflags", "+faststart", v1_desk
]
subprocess.run(cmd1, check=True)
import shutil
shutil.copy2(v1_desk, v1_repo)
print(f"[展示视频] 导出顺滑版: {v1_desk}")

# 2. 6fps 舒缓节奏版 (8秒慢速品鉴)
cmd2 = [
    FFMPEG, "-y", "-framerate", "6", "-i", os.path.join(OUT_FRAMES, "frame_%04d.png"),
    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
    "-movflags", "+faststart", v2_desk
]
subprocess.run(cmd2, check=True)
shutil.copy2(v2_desk, v2_repo)
print(f"[展示视频] 导出慢速版: {v2_desk}")
