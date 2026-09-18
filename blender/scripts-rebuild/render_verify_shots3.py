import bpy, os, math
from mathutils import Vector

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_percentage = 50
scene.render.image_settings.file_format = "PNG"
try:
    scene.eevee.taa_render_samples = 16
except Exception:
    pass

OUT = os.environ.get("TAIWEI_SHOT_DIR", bpy.path.abspath("//shots_high"))
os.makedirs(OUT, exist_ok=True)

def shoot(name, loc, aim, fov=50):
    cam_data = bpy.data.cameras.new(name)
    cam = bpy.data.objects.new(name, cam_data)
    scene.collection.objects.link(cam)
    cam.location = Vector(loc)
    cam_data.angle = math.radians(fov)
    empty = bpy.data.objects.new(name + "_aim", None)
    scene.collection.objects.link(empty)
    empty.location = Vector(aim)
    con = cam.constraints.new("TRACK_TO")
    con.target = empty
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    scene.camera = cam
    scene.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("wrote", scene.render.filepath)
    bpy.data.objects.remove(cam)
    bpy.data.objects.remove(empty)

# V9 远山水面低视角：东南开阔水面看西北山脊+云带
shoot("V9_远山水面", (34.0, -46.0, 6.5), (-10.0, 70.0, 20.0), 55)
# V10 北崖门+北石阶：西北水面看北崖
shoot("V10_北崖门阶", (-20.0, 52.0, 8.0), (2.0, 42.0, 5.0), 55)
