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

# V1 东门+东桥近景：门(44.9,5.9) 桥(37.9,5.8)，从东南水面看向西北
shoot("V1_东门东桥", (52.0, -6.0, 9.0), (41.0, 6.0, 5.5), 55)
# V2 西门+西桥近景：门(-44.1,7.8) 桥(-37.5,7.3)，从西南水面看向东北
shoot("V2_西门西桥", (-52.0, -4.0, 9.0), (-40.0, 8.0, 5.5), 55)
# V3 南矶门+南石阶+双桥（瀛洲/方丈），从正南低角看北
shoot("V3_南矶门阶", (2.0, -58.0, 8.0), (0.0, -36.0, 5.0), 60)
# V4 桥落岛特写：东南桥(29.9,-20.2)，从东侧水面贴水看
shoot("V4_东南桥落岛", (44.0, -30.0, 6.0), (30.0, -20.0, 5.0), 55)
# V5 远山+云带低视角：从主岛南侧水面近水平看北山
shoot("V5_远山云带", (0.0, -20.0, 6.5), (0.0, 60.0, 14.0), 60)
