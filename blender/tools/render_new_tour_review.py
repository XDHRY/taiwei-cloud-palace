import bpy, os

OUT = r"E:\UserData\xdrhh\.openclaw\workspace\taiwei_video\audit_inspection\new_tour_review"
os.makedirs(OUT, exist_ok=True)

scene = bpy.context.scene
scene.camera = bpy.data.objects['巡航相机']
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
try:
    scene.eevee.taa_render_samples = 8
except:
    pass

frames = [
    (1,   "01_开场水面南轴破雾.png"),
    (168, "02_穿牌坊见仪门.png"),
    (312, "03_御道踏跺仰正殿.png"),
    (468, "04_东苑水巷九龙壁.png"),
    (720, "05_飞升俯瞰水墨长卷.png"),
]

for f_num, fname in frames:
    scene.frame_set(f_num)
    fpath = os.path.join(OUT, fname)
    scene.render.filepath = fpath
    bpy.ops.render.render(write_still=True)
    print(f"RENDERED {f_num} -> {fname}")

print("ALL 5 NEW TOUR FRAMES RENDERED!")
