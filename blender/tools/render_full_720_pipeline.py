# -*- coding: utf-8 -*-
r"""太微云宫 · 720 帧 1080P 电影级巡航正片渲染与自动化合成管线。

- 目标：完整 30 秒 @ 24fps（帧 1 至 720）
- 分辨率：1920x1080（1080P 逐帧全量计算，绝不跳帧）
- 引擎：EEVEE Next（8 samples 细腻抗锯齿，全量动态光影、万木生风、日光弧全开）
- 特性：
  1. 帧断点续渲：如果某帧已存在且有效，自动跳过，支持随时中断/重启
  2. 实时进度落盘日志：E:\UserData\xdrhh\.openclaw\workspace\taiwei_video\render_720.log
  3. 全部 720 帧计算完毕后，自动调用 ffmpeg 压制出两部正片并直接送至桌面：
     - E:\zhuomian\太微云宫_30秒电影级正片_H264.mp4
     - E:\zhuomian\太微云宫_30秒电影级正片_H265.mp4
     同时归档入 E:\zhuomian\太微云宫3D\05-样片成片\
"""
import bpy
import os
import sys
import time
import subprocess

OUT_DIR = r"E:\UserData\xdrhh\.openclaw\workspace\taiwei_video\frames_720_g19"
os.makedirs(OUT_DIR, exist_ok=True)

LOG_FILE = r"E:\UserData\xdrhh\.openclaw\workspace\taiwei_video\render_720.log"

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.camera = bpy.data.objects.get("巡航相机")
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.image_settings.color_depth = '8'

try:
    scene.eevee.taa_render_samples = 16
except Exception:
    pass

F_START = 1
F_END = 720

log(f"============================================================")
log(f"启动太微云宫 720 帧 1080P 挂机渲染管线")
log(f"总帧数: {F_START} .. {F_END} (30 秒 @ 24fps)")
log(f"相机: {scene.camera.name}, 引擎: {scene.render.engine}")
log(f"帧存储目录: {OUT_DIR}")
log(f"============================================================")

t_all_start = time.time()
rendered_count = 0
skipped_count = 0

for f_num in range(F_START, F_END + 1):
    fpath = os.path.join(OUT_DIR, f"f_{f_num:04d}.png")
    # 断点检测：若文件存在且大于 100KB，跳过
    if os.path.exists(fpath) and os.path.getsize(fpath) > 100000:
        skipped_count += 1
        continue
    
    scene.frame_set(f_num)
    scene.render.filepath = fpath
    t_frame = time.time()
    bpy.ops.render.render(write_still=True)
    cost = time.time() - t_frame
    rendered_count += 1
    
    remaining_frames = (F_END - f_num)
    est_remain_min = (remaining_frames * cost) / 60.0
    elapsed_min = (time.time() - t_all_start) / 60.0
    
    log(f"渲染进度: {f_num:3d}/720 (本帧耗时: {cost:4.1f}s) | 累计已渲染: {rendered_count} 帧, 跳过: {skipped_count} 帧 | 剩余预计: {est_remain_min:5.1f} 分钟")

log(f"============================================================")
log(f"720 帧序列已全部完成！总耗时: {(time.time() - t_all_start)/60.0:.1f} 分钟")
log(f"开始执行 ffmpeg 影视级后期合成...")
log(f"============================================================")

FFMPEG = r"C:\Users\xdrhh\bin\ffmpeg.exe"
DESKTOP = r"E:\zhuomian"
TARGET_DIR = r"E:\zhuomian\太微云宫3D\05-样片成片"
os.makedirs(TARGET_DIR, exist_ok=True)

v_h264_desk = os.path.join(DESKTOP, "太微云宫_30秒电影级正片_H264.mp4")
v_h264_repo = os.path.join(TARGET_DIR, "太微云宫_30秒电影级正片_H264.mp4")
v_h265_desk = os.path.join(DESKTOP, "太微云宫_30秒电影级正片_H265.mp4")
v_h265_repo = os.path.join(TARGET_DIR, "太微云宫_30秒电影级正片_H265.mp4")

# 1. 合成 H.264 兼容版 (带电影级淡入淡出转场)
cmd1 = [
    FFMPEG, "-y", "-framerate", "24", "-i", os.path.join(OUT_DIR, "f_%04d.png"),
    "-vf", "fade=t=in:st=0:d=1.0,fade=t=out:st=28.5:d=1.5",
    "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
    "-movflags", "+faststart", v_h264_desk
]
log(f"正在编译 H.264: {' '.join(cmd1)}")
subprocess.run(cmd1, check=True)
import shutil
shutil.copy2(v_h264_desk, v_h264_repo)
log(f"H.264 编译完成: {v_h264_desk}")

# 2. 合成 H.265 极清版 (极高画质比率)
cmd2 = [
    FFMPEG, "-y", "-framerate", "24", "-i", os.path.join(OUT_DIR, "f_%04d.png"),
    "-vf", "fade=t=in:st=0:d=1.0,fade=t=out:st=28.5:d=1.5",
    "-c:v", "libx265", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
    "-tag:v", "hvc1", v_h265_desk
]
log(f"正在编译 H.265: {' '.join(cmd2)}")
subprocess.run(cmd2, check=True)
shutil.copy2(v_h265_desk, v_h265_repo)
log(f"H.265 编译完成: {v_h265_desk}")

log(f"============================================================")
log(f"太微云宫 30 秒 1080P 全量正片已成功投递桌面！")
log(f"============================================================")
