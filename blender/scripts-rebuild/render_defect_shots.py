import bpy, os
from mathutils import Vector
scene = bpy.context.scene

# 08 近景对准正殿右侧鸱吻 v3
cam8 = bpy.data.objects.get("08_正殿脊吻")
if cam8 is not None:
    cam8.location = Vector((10.5, 5.0, 17.4))
    track = cam8.constraints.get("Track To") or cam8.constraints.new("TRACK_TO")
    empty = bpy.data.objects.get("_chiwen_aim")
    if empty is None:
        empty = bpy.data.objects.new("_chiwen_aim", None)
        bpy.context.scene.collection.objects.link(empty)
    empty.location = Vector((3.7, 13.8, 16.9))
    track.target = empty
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"

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
names = ["01_云宫山水总览", "02_重檐正殿", "04_中轴礼序", "06_正殿平视", "07_东侧立面", "08_正殿脊吻"]
for name in names:
    cam = bpy.data.objects.get(name)
    if cam is None or cam.type != "CAMERA":
        print("missing", name)
        continue
    scene.camera = cam
    scene.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("wrote", scene.render.filepath)
