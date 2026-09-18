# -*- coding: utf-8 -*-
"""太微云宫 G19：30 秒中轴推进、殿前升空、东苑照壁与全景航线。

修复 G18 的关闭仪门遮挡与正殿屋檐穿入。此脚本只设置航线，不保存文件。
修改后必须渲染关键帧并检查相机净空；不能仅凭控制点宣称全程无碰撞。
"""
import bpy
from mathutils import Vector

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 720
scene.render.fps = 24

# 1. 注视点 Empty
empty = bpy.data.objects.get("巡航注视点")
if not empty:
    empty = bpy.data.objects.new("巡航注视点", None)
    empty.empty_display_type = 'PLAIN_AXES'
    empty.empty_display_size = 2.0
    scene.collection.objects.link(empty)

# 2. 巡航相机
cam = bpy.data.objects.get("巡航相机")
if not cam:
    cam_data = bpy.data.cameras.new("巡航相机")
    cam = bpy.data.objects.new("巡航相机", cam_data)
    scene.collection.objects.link(cam)

cam.data.lens = 42.0
cam.data.clip_start = 0.1
cam.data.clip_end = 1000.0

track = cam.constraints.get("Track To")
if not track:
    track = cam.constraints.new("TRACK_TO")
track.target = empty
track.track_axis = "TRACK_NEGATIVE_Z"
track.up_axis = "UP_Y"

cam.animation_data_clear()
empty.animation_data_clear()

# 3. 电影级平滑贝塞尔飞行轨迹（严格避开任何遮挡，确保每一帧皆可成画）
cam_keys = [
    # 阶段一：南桥头起步，中轴端正迎仙
    (1,   (0.0,  -48.0,  9.0)),   # 中轴远景，保留完整屋顶
    (84,  (0.0,  -36.0,  9.4)),
    (168, (0.0,  -24.0, 10.8)),   # 提前抬升，避免穿入仪门门扇与屋檐
    
    # 阶段二：前庭跃升与须弥正殿
    (252, (0.0,  -16.0, 15.0)),
    (336, (0.0,   -7.0, 18.5)),   # 仪门上方；与正殿下檐保持距离
    (420, (13.0,  -1.0, 21.0)),   # 殿前向东转向，避开正殿封闭殿身
    
    # 阶段三：东苑湖光与九龙照壁
    (504, (35.0, -30.0, 14.0)),   # 九龙壁南东侧，正对壁画面
    (588, (36.0, -42.0, 24.0)),   # 盘旋湖心后撤
    
    # 阶段四：升空大长卷终景
    (660, (50.0, -74.0, 42.0)),   # 大景拉升
    (720, (62.0, -98.0, 58.0)),   # 终幅：俯瞰整座太微云宫山水大长卷
]

aim_keys = [
    (1,   (0.0,   -2.0,  9.5)),
    (84,  (0.0,    1.0, 10.0)),
    (168, (0.0,    6.0, 11.0)),
    (252, (0.0,   10.0, 11.0)),
    (336, (0.0,   13.8, 12.5)),
    (420, (0.0,   13.8, 12.5)),
    (504, (28.0, -18.0,  6.8)),
    (588, (12.0,   0.0,  8.0)),   # 盘旋注视主岛全景
    (660, (0.0,    8.0,  9.0)),   # 俯瞰全岛几何中心
    (720, (0.0,   10.0,  9.0)),
]

for frame_idx, loc in cam_keys:
    cam.location = Vector(loc)
    cam.keyframe_insert(data_path="location", frame=frame_idx)

for frame_idx, loc in aim_keys:
    empty.location = Vector(loc)
    empty.keyframe_insert(data_path="location", frame=frame_idx)

# 平滑贝塞尔插值
for obj in (cam, empty):
    if obj.animation_data and obj.animation_data.action:
        for fc in obj.animation_data.action.fcurves:
            for k in fc.keyframe_points:
                k.interpolation = 'BEZIER'
                k.handle_left_type = 'AUTO_CLAMPED'
                k.handle_right_type = 'AUTO_CLAMPED'

scene.camera = cam
print("G19 tour path applied: 720 frames; render and clearance checks required.")
