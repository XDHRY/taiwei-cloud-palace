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

# V11 南轴：牌坊+幡竿+经幢
shoot("V11_南轴牌坊", (0.0, -34.0, 7.5), (0.0, -18.0, 5.5), 55)
# V12 殿庭：石狮+铜鼎+伞盖+铜鹤+日晷（自南向北看）
shoot("V12_殿庭仪仗", (0.0, -4.0, 7.0), (0.0, 9.0, 7.2), 55)
# V13 九龙壁（自西向东看壁面）
shoot("V13_九龙照壁", (8.0, -2.0, 7.5), (22.5, -2.0, 6.5), 50)
# V14 东钟亭
shoot("V14_东苑钟亭", (31.0, 1.5, 7.0), (25.0, 10.0, 6.0), 50)
# V15 西苑棋桌+鼓亭
shoot("V15_西苑棋鼓", (-13.0, 11.0, 7.0), (-23.0, 14.0, 5.5), 55)
# V16 后苑井亭+龟趺碑
shoot("V16_后苑井碑", (-1.0, 16.0, 7.5), (1.0, 25.0, 6.8), 55)
