
import bpy, os
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_percentage = 50
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.image_settings.color_depth = "8"
try:
    scene.eevee.taa_render_samples = 24
except Exception:
    pass
OUT = os.environ.get("TAIWEI_SHOT_DIR", bpy.path.abspath("//shots"))
os.makedirs(OUT, exist_ok=True)
names = ["01_云宫山水总览", "02_重檐正殿", "04_中轴礼序"]
for name in names:
    cam = bpy.data.objects.get(name)
    if cam is None or cam.type != "CAMERA":
        print("missing", name)
        continue
    scene.camera = cam
    scene.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("wrote", scene.render.filepath)
