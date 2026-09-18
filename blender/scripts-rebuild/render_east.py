
import bpy, os
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_percentage = 45
try:
    scene.eevee.taa_render_samples = 16
except Exception:
    pass
OUT = os.environ.get("TAIWEI_SHOT_DIR", bpy.path.abspath("//shots_high"))
os.makedirs(OUT, exist_ok=True)
for name in ["06_正殿平视", "07_东侧立面"]:
    cam = bpy.data.objects.get(name)
    if cam is None:
        print("missing", name); continue
    scene.camera = cam
    scene.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("wrote", scene.render.filepath)
