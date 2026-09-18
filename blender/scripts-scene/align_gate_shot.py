# -*- coding: utf-8 -*-
"""Mid-distance 3/4 view of 前庭仪门: columns, fascia, eaves in one frame."""
import bpy
from mathutils import Vector

wood = bpy.data.objects.get("前庭仪门_柱梁斗拱雀替")
roof = bpy.data.objects.get("前庭仪门_屋面封檐")
stone = bpy.data.objects.get("前庭仪门_台基殿身")
assert wood and roof, "missing gate"

def zrange(o):
    zs = [(o.matrix_world @ Vector(c)).z for c in o.bound_box]
    return min(zs), max(zs)

wz0, wz1 = zrange(wood)
rz0, rz1 = zrange(roof)
print("GATE_WOOD", round(wz0,3), round(wz1,3))
print("GATE_ROOF", round(rz0,3), round(rz1,3))
print("GATE_GAP", round(rz0-wz1,3))

# 仪门 world XY from stone if present
origin = stone.matrix_world.translation if stone else Vector((0.0, -11.4, 5.5))
look = Vector((origin.x, origin.y, (wz1+rz0)*0.5))

cam_data = bpy.data.cameras.new("ALIGN_GATE")
cam_data.lens = 35
cam_data.clip_end = 400
cam_obj = bpy.data.objects.new("ALIGN_GATE", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
cam_obj.location = (look.x + 11.0, look.y - 9.5, look.z + 1.6)
cam_obj.rotation_euler = (look - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.eevee.taa_render_samples = 24
scene.camera = cam_obj
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.filepath = bpy.path.abspath("//diag/align_gate_side.png")
scene.render.image_settings.file_format = "PNG"
bpy.ops.render.render(write_still=True)
print("SHOT", scene.render.filepath)
print("GATE_SHOT_DONE")
