# -*- coding: utf-8 -*-
"""G9 stills with proven mid-distance cameras. Never clears the scene."""
import bpy
import os
from mathutils import Vector

DIAG = "E:/UserData/xdrhh/.openclaw/workspace/taiwei_video/diag/"
PREFIX = os.environ.get("TAIWEI_SHOT_PREFIX", "")
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.eevee.taa_render_samples = 24
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"


def look(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def zrange(o):
    zs = [(o.matrix_world @ Vector(c)).z for c in o.bound_box]
    return min(zs), max(zs)


cam = bpy.data.objects.get("G9_STILL")
if cam is None:
    data = bpy.data.cameras.new("G9_STILL")
    cam = bpy.data.objects.new("G9_STILL", data)
    scene.collection.objects.link(cam)
cam.data.clip_end = 400
scene.camera = cam

hall = bpy.data.objects.get("太微正殿_台基殿身")
roof = bpy.data.objects.get("太微正殿_屋面封檐")
assert hall and roof
wz0, wz1 = zrange(hall)
rz0, rz1 = zrange(roof)
target = hall.matrix_world.translation.copy()
mid_z = (wz1 + rz0) / 2

shots = []
# 正殿东立面：墙顶贴檐
shots.append(("g9_east_hall.png", (target.x + 16.5, target.y + 1.2, mid_z + 0.4),
              (target.x, target.y, mid_z), 50))
# 仪门 3/4：柱头接到屋檐
gate = bpy.data.objects.get("前庭仪门_台基殿身")
gwood = bpy.data.objects.get("前庭仪门_柱梁斗拱雀替")
groof = bpy.data.objects.get("前庭仪门_屋面封檐")
if gate and gwood and groof:
    origin = gate.matrix_world.translation
    gw1 = zrange(gwood)[1]
    gr0 = zrange(groof)[0]
    look_pt = Vector((origin.x, origin.y, (gw1 + gr0) * 0.5))
    shots.append(("g9_gate.png", (look_pt.x + 11.0, look_pt.y - 9.5, look_pt.z + 1.6),
                  tuple(look_pt), 35))
# 中轴庭院：烟火气 + 正殿关系
shots.append(("g9_courtyard.png", (0.0, -42.0, 22.5), (0.0, 12.0, 10.2), 35))
# 东池柳船
shots.append(("g9_willow_boat.png", (30.0, -14.0, 8.5), (16.0, 5.0, 4.5), 40))
# 回廊接缝：从月台西南看翼廊柱头接到屋檐
shots.append(("g9_corridor.png", (-6.2, -1.8, 8.6), (-12.2, 2.55, 7.5), 38))
# 正殿檐下：柱头铺作 + 柱间补间
shots.append(("g9_eaves.png", (8.6, 4.2, 11.4), (0.0, 11.2, 10.6), 42))
# 仙宫群宽景：东西苑 + 外岛
shots.append(("g9_cluster.png", (0.0, -62.0, 38.0), (0.0, 8.0, 8.0), 32))
# 南岛廊桥：瀛洲/方丈是否接到主岛
shots.append(("g9_south_islands.png", (2.0, -72.0, 28.0), (4.0, -34.0, 6.5), 34))
# 东西外岛廊桥
shots.append(("g9_east_west_islands.png", (58.0, -8.0, 26.0), (20.0, 12.0, 8.0), 32))

for name, loc, tgt, lens in shots:
    cam.location = loc
    look(cam, tgt)
    cam.data.lens = lens
    scene.render.filepath = DIAG + PREFIX + name
    bpy.ops.render.render(write_still=True)
    print("SHOT", scene.render.filepath)
print("G9_STILLS_DONE")
