# -*- coding: utf-8 -*-
"""East elevation still aimed at 太微正殿 after STUDY rebuild. Read-only besides adding a camera."""
import bpy
from mathutils import Vector

hall = bpy.data.objects.get("太微正殿_台基殿身")
roof = bpy.data.objects.get("太微正殿_屋面封檐")
assert hall and roof, "missing hall/roof"

def zrange(o):
    zs = [(o.matrix_world @ Vector(c)).z for c in o.bound_box]
    return min(zs), max(zs)

wz0, wz1 = zrange(hall)
rz0, rz1 = zrange(roof)
print("ALIGN_WALL", round(wz0,3), round(wz1,3))
print("ALIGN_ROOF", round(rz0,3), round(rz1,3))
print("ALIGN_GAP", round(rz0-wz1,3))

target = hall.matrix_world.translation.copy()
mid_z = (wz1+rz0)/2
cam_data = bpy.data.cameras.new("ALIGN_EAST")
cam_data.lens = 50
cam_data.clip_end = 400
cam_obj = bpy.data.objects.new("ALIGN_EAST", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
cam_obj.location = (target.x+16.5, target.y+1.2, mid_z+0.4)
direction = Vector((target.x, target.y, mid_z)) - cam_obj.location
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.eevee.taa_render_samples = 24
scene.camera = cam_obj
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = bpy.path.abspath("//diag/align_east_side.png")
bpy.ops.render.render(write_still=True)
print("SHOT", scene.render.filepath)
print("ALIGN_SHOT_DONE")
