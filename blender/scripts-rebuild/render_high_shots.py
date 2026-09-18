
import bpy
from mathutils import Vector
cam = bpy.data.objects.get("08_正殿脊吻")
if cam is not None:
    cam.location = Vector((7.4, 13.8, 16.2))
    track = cam.constraints.get("Track To") or cam.constraints.new("TRACK_TO")
    # aim at upper ridge end
    empty = bpy.data.objects.get("_chiwen_aim")
    if empty is None:
        empty = bpy.data.objects.new("_chiwen_aim", None)
        bpy.context.scene.collection.objects.link(empty)
    empty.location = Vector((3.2, 13.8, 14.6))
    track.target = empty
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"
    print("retargeted 08 to", tuple(cam.location))


import bpy, os
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_percentage = 40
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.image_settings.color_depth = "8"
try:
    scene.eevee.taa_render_samples = 16
except Exception:
    pass
OUT = os.environ.get("TAIWEI_SHOT_DIR", bpy.path.abspath("//shots_high"))
os.makedirs(OUT, exist_ok=True)
names = ["01_云宫山水总览", "02_重檐正殿", "04_中轴礼序"]
for cam in bpy.data.objects:
    if cam.type == "CAMERA" and ("脊" in cam.name or cam.name.startswith("08")):
        names.append(cam.name)
seen=set()
for name in names:
    if name in seen:
        continue
    seen.add(name)
    cam = bpy.data.objects.get(name)
    if cam is None or cam.type != "CAMERA":
        print("missing", name)
        continue
    scene.camera = cam
    safe = name.replace("/", "_")
    scene.render.filepath = os.path.join(OUT, safe + ".png")
    bpy.ops.render.render(write_still=True)
    print("wrote", scene.render.filepath)
print("cameras", [o.name for o in bpy.data.objects if o.type=="CAMERA"])
