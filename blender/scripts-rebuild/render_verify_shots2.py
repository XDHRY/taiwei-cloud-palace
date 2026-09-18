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

# V6 东南桥全跨：垂直于桥向的水面视角
shoot("V6_东南桥全跨", (42.9, -7.8, 8.5), (29.9, -20.2, 4.7), 55)
# V7 远山水面低视角：正南开阔水面看北山剪影+云带
shoot("V7_远山水面", (0.0, -48.0, 6.0), (0.0, 55.0, 15.0), 55)
# V8 北崖门+北石阶：从北侧水面看北崖
shoot("V8_北崖门阶", (8.0, 56.0, 9.0), (2.0, 40.0, 5.5), 55)
