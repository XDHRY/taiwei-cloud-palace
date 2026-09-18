# audit_shots_batch1.py — 6 个固定机位 + 巡航首帧, EEVEE 1080p, 输出到 audit 目录
import bpy, os, json

OUT = r'E:/UserData/xdrhh/.openclaw/workspace/taiwei_video/audit_2026-09-17'
os.makedirs(OUT, exist_ok=True)
s = bpy.context.scene
s.render.engine = 'BLENDER_EEVEE_NEXT'
s.render.resolution_x = 1920
s.render.resolution_y = 1080
s.render.image_settings.file_format = 'PNG'

jobs = [
    ('05_俯视总平', None, 140, 'A1_俯视总平.png'),
    ('04_中轴礼序', None, 140, 'A2_中轴礼序.png'),
    ('06_正殿平视', None, 140, 'A3_正殿平视.png'),
    ('08_正殿脊吻', None, 140, 'A4_脊吻特写.png'),
    ('03_荷塘虹桥', None, 140, 'A5_荷塘虹桥.png'),
    ('09_北崖飞瀑', None, 140, 'A6_北崖飞瀑.png'),
    ('02_重檐正殿', None, 140, 'A7_正殿侧翼.png'),
    ('巡航相机',   None,   1, 'A8_巡航首帧.png'),
]
done = []
for name, _, fr, fn in jobs:
    cam = bpy.data.objects.get(name)
    if cam is None:
        done.append((name, 'MISSING'))
        continue
    s.camera = cam
    s.frame_set(fr)
    s.render.filepath = os.path.join(OUT, fn)
    bpy.ops.render.render(write_still=True)
    done.append((name, 'OK'))
s.frame_set(1)
print('AUDIT_BATCH1', json.dumps(done, ensure_ascii=False))
