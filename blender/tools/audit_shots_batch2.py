# audit_shots_batch2.py — 人视补拍 + 疑点对象指认(只读+临时相机,不保存blend)
import bpy, os, json
from mathutils import Vector

OUT = r'E:/UserData/xdrhh/.openclaw/workspace/taiwei_video/audit_2026-09-17'
os.makedirs(OUT, exist_ok=True)
s = bpy.context.scene
s.render.engine = 'BLENDER_EEVEE_NEXT'
s.render.resolution_x = 1920
s.render.resolution_y = 1080
s.render.image_settings.file_format = 'PNG'
s.frame_set(140)

# ---------- 1) 疑点对象指认 ----------
from mathutils import Vector as V
def in_box(o, lo, hi):
    p = o.matrix_world.translation
    return all(lo[i] <= p[i] <= hi[i] for i in range(3))

# 台阶两侧"绿桶上杆"疑物 (殿前月台前沿, z 6..11)
sus1 = [o.name for o in bpy.data.objects if o.type in ('MESH','EMPTY') and in_box(o, (-8, 2, 6), (8, 8, 11))]
# 瀑布对象
falls = [o.name for o in bpy.data.objects if ('瀑' in o.name or '泉' in o.name or '帘' in o.name)]
# 金葫芦宝顶: 正殿脊顶附近 (x±2, y 12..16, z 15..19)
finial = [o.name for o in bpy.data.objects if o.type=='MESH' and in_box(o, (-2, 12, 15), (2, 16, 19))]

# ---------- 2) 临时人视相机 ----------
cam_data = bpy.data.cameras.new('AUD_CAM')
cam_data.lens = 32
cam = bpy.data.objects.new('AUD_CAM', cam_data)
s.collection.objects.link(cam)

def shoot(pos, look, fn, lens=32):
    cam.location = pos
    cam_data.lens = lens
    d = (Vector(look) - Vector(pos)).normalized()
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    s.camera = cam
    s.render.filepath = os.path.join(OUT, fn)
    bpy.ops.render.render(write_still=True)
    return fn

done = []
done.append(shoot((0, -1.5, 7.6), (0, 14, 11), 'B1_人视殿前仰瞻.png', 35))      # 访客中轴仰望正殿
done.append(shoot((0, -34, 6.2), (0, -10, 9), 'B2_人视仪门牌坊.png', 32))        # 进谒动线: 牌坊后望仪门
done.append(shoot((22.5, -24.5, 6.5), (28, -18, 7), 'B3_九龙壁正面.png', 40))    # 九龙壁正视
done.append(shoot((14.5, 1.5, 11.5), (0, 14, 12.5), 'B4_正殿檐下斗拱带.png', 50)) # 东南角看檐下斗拱层
done.append(shoot((0, -55, 3.2), (0, -24, 8), 'B5_人视南桥进村.png', 28))        # 桥南人视(巡航起点应有画面)
done.append(shoot((52, 2, 8), (47.5, 6, 10), 'B6_东塔岛琉璃塔.png', 45))         # 琉璃塔审视

# 清理临时相机(不保存 blend, 双保险)
bpy.data.objects.remove(cam)
bpy.data.cameras.remove(cam_data)
s.camera = bpy.data.objects.get('巡航相机') or s.camera
s.frame_set(1)

print('AUDIT_BATCH2', json.dumps(done, ensure_ascii=False))
print('SUS_STAIR_OBJS', json.dumps(sus1, ensure_ascii=False))
print('WATERFALL_OBJS', json.dumps(falls, ensure_ascii=False))
print('FINIAL_ZONE', json.dumps(finial, ensure_ascii=False))
