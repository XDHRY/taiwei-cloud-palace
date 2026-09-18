import bpy
import os

OUT_DIR = r"E:\UserData\xdrhh\.openclaw\workspace\taiwei_video\TaiWei_WukongRebuild\shots_high"
os.makedirs(OUT_DIR, exist_ok=True)

scene = bpy.context.scene
scene.camera = bpy.data.objects.get("巡航相机")
if scene.camera is None:
    raise RuntimeError("Tour camera is missing")
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.eevee.taa_render_samples = 16
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.image_settings.color_depth = '8'
print(f"KEYFRAME SETTINGS: {scene.render.engine}, samples={scene.eevee.taa_render_samples}, 1920x1080", flush=True)

frames = [
    (1,   "tour_01s_南轴石牌坊破雾.png"),
    (140, "tour_06s_仪门石狮与双鼎.png"),
    (289, "tour_12s_高台铜鹤日晷.png"),
    (380, "tour_16s_九龙照壁与钟亭.png"),
    (720, "tour_30s_飞天俯瞰全景长卷.png"),
]

for f_num, fname in frames:
    scene.frame_set(f_num)
    fpath = os.path.join(OUT_DIR, fname)
    scene.render.filepath = fpath
    bpy.ops.render.render(write_still=True)
    print(f"RENDERED FRAME {f_num} -> {fname}")
