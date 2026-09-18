# -*- coding: utf-8 -*-
"""
太微 · 云宫山水长卷 —— 视频版 prep
1. 以 HIGH 档重建场景（含远山/云海/水/天精修）
2. 建立 30s @24fps 一镜到底巡航运镜（Track-To 约束 + Bezier 缓动 + 景深）
3. 切换 EEVEE 高画质渲染设置
4. 保存 TaiWei_Video.blend 供分块量产
"""
import bpy
import os
import time

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
GENERATOR = os.path.join(WORKSPACE, "taiwei_cloud_palace_generator.py")
OUT_DIR = os.path.join(WORKSPACE, "taiwei_video")
FRAMES_DIR = os.path.join(OUT_DIR, "frames")
os.makedirs(FRAMES_DIR, exist_ok=True)

os.environ["TAIWEI_QUALITY"] = "HIGH"

GEN = {"__name__": "__main__"}
t0 = time.time()
with open(GENERATOR, "r", encoding="utf-8") as f:
    source = f.read()
exec(compile(source, GENERATOR, "exec"), GEN)
print(f"[视频prep] HIGH 场景重建 {time.time()-t0:.1f}s, 对象 {len(bpy.context.scene.objects)}")

scene = bpy.context.scene

# ---------------- 运镜: 30s @ 24fps = 720 帧 ----------------
FPS = 24
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = FPS * 30  # 720

# (归一化时刻, 相机位置, 注视点)
# 依场景叙事顺序推进：迎仙石阶 → 山门前庭 → 石桥池院 → 重檐正殿 → 后苑 → 云外远山
TOUR = [
    (0.000, (  6.0, -46.0,  6.2), ( 0.0, -16.0,  7.4)),  # 迎仙石阶：低机位仰望长阶与山门
    (0.130, (  2.0, -34.0,  8.2), ( 0.0,  -8.0,  9.0)),  # 推近长阶，缓缓入前庭
    (0.260, (  5.0, -24.0, 14.0), ( 0.0,   8.0, 11.0)),  # 越过山门，前庭在望
    (0.400, ( 24.0, -12.0, 12.0), (20.0,   6.0,  7.6)),  # 东移低掠，荷塘与虹桥在前
    (0.530, ( 36.0,   6.0, 13.5), (14.0,  14.0,  9.5)),  # 临波水榭与东翼廊庑侧掠
    (0.640, ( 22.0, -20.0, 16.0), ( 0.0,  13.0, 13.5)),  # 回中轴，重檐正殿推近
    (0.760, ( 12.0, -44.0, 28.0), ( 0.0,  14.0, 12.5)),  # 后撤抬升，重檐正殿全景
    (0.880, ( 34.0, -76.0, 44.0), ( 0.0,  12.0, 10.5)),  # 继续拉升，云海入画
    (1.000, ( 66.0,-101.0, 62.0), ( 0.0,   8.0,  9.3)),  # 云外远山，全景收尾
]

rig_group = bpy.data.collections.get("12_灯光相机") or scene.collection

target = bpy.data.objects.new("巡航注视点", None)
rig_group.objects.link(target)

cam_data = bpy.data.cameras.new("巡航相机")
cam_data.lens = 45
cam_data.sensor_width = 36
cam_data.clip_start = .1
cam_data.clip_end = 750
cam = bpy.data.objects.new("巡航相机", cam_data)
rig_group.objects.link(cam)

con = cam.constraints.new("TRACK_TO")
con.target = target
con.track_axis = "TRACK_NEGATIVE_Z"
con.up_axis = "UP_Y"

LAST = scene.frame_end - scene.frame_start

for t, loc, tgt in TOUR:
    frame = scene.frame_start + round(t * LAST)
    cam.location = loc
    cam.keyframe_insert("location", frame=frame)
    target.location = tgt
    target.keyframe_insert("location", frame=frame)

for ob in (cam, target):
    ad = ob.animation_data
    if ad and ad.action:
        for fc in ad.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER"
                kp.handle_left_type = "AUTO_CLAMPED"
                kp.handle_right_type = "AUTO_CLAMPED"

# 景深: 焦点锁注视点, f/8 轻微虚化保住体积云层次
cam_data.dof.use_dof = True
cam_data.dof.focus_object = target
cam_data.dof.aperture_fstop = 8.0

scene.camera = cam

# ---------------- 生命系统: 30秒时间弧 ----------------
import math as _m

F0, F1 = 1, 720


def _linear(id_block):
    ad = getattr(id_block, "animation_data", None)
    if ad and ad.action:
        for fc in ad.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"


def _principled(node_tree):
    """按类型取节点：中文界面下新建材质节点名是"原理化 BSDF"，按名字取会拿到 None。"""
    for node in node_tree.nodes:
        if node.type == "BSDF_PRINCIPLED":
            return node
    raise RuntimeError("材质缺少 Principled BSDF 节点")


# —— 日光弧: 破晓低斜 -> 晨光渐暖渐强 ——
sun_obj = bpy.data.objects.get("晨阳主光")
if sun_obj:
    sd = sun_obj.data
    sd.energy = 1.55
    sd.keyframe_insert("energy", frame=F0)
    sd.energy = 2.35
    sd.keyframe_insert("energy", frame=F1)
    sd.color = (1.0, .88, .68)
    sd.keyframe_insert("color", frame=F0)
    sd.color = (1.0, .78, .52)
    sd.keyframe_insert("color", frame=F1)
    sun_obj.rotation_euler = (_m.radians(22), _m.radians(-30), _m.radians(-31))
    sun_obj.keyframe_insert("rotation_euler", frame=F0)
    sun_obj.rotation_euler = (_m.radians(27), _m.radians(-30), _m.radians(-36.5))
    sun_obj.keyframe_insert("rotation_euler", frame=F1)
    _linear(sd)
    _linear(sun_obj)
    print("[生命] 日光弧 OK")

# —— 天空渐亮 ——
wn = scene.world.node_tree
bg = next(n for n in wn.nodes if n.type == "BACKGROUND")
bg.inputs["Strength"].default_value = .32
bg.inputs["Strength"].keyframe_insert("default_value", frame=F0)
bg.inputs["Strength"].default_value = .52
bg.inputs["Strength"].keyframe_insert("default_value", frame=F1)
_linear(wn)

# —— 星空: 破晓前满天, 240 帧内渐隐 ——
ramp_node = next(n for n in wn.nodes if n.type == "VALTORGB")
tex = next(n for n in wn.nodes if n.type == "TEX_COORD")
vor = wn.nodes.new("ShaderNodeTexVoronoi")
vor.feature = "F1"
vor.inputs["Scale"].default_value = 55.0
star_ramp = wn.nodes.new("ShaderNodeValToRGB")
star_ramp.color_ramp.elements[0].position = .0
star_ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
star_ramp.color_ramp.elements[1].position = .045
star_ramp.color_ramp.elements[1].color = (0, 0, 0, 1)
star_mul = wn.nodes.new("ShaderNodeMath")
star_mul.operation = "MULTIPLY"
star_mul.inputs[1].default_value = 2.6
star_mul.inputs[1].keyframe_insert("default_value", frame=F0)
star_mul.inputs[1].default_value = 0.0
star_mul.inputs[1].keyframe_insert("default_value", frame=240)
add = wn.nodes.new("ShaderNodeMixRGB")
add.blend_type = "ADD"
add.inputs[0].default_value = 1.0
wn.links.new(tex.outputs["Normal"], vor.inputs["Vector"])
wn.links.new(vor.outputs["Distance"], star_ramp.inputs["Fac"])
wn.links.new(star_ramp.outputs["Color"], star_mul.inputs[0])
wn.links.new(ramp_node.outputs["Color"], add.inputs[1])
wn.links.new(star_mul.outputs[0], add.inputs[2])
wn.links.new(add.outputs["Color"], bg.inputs["Color"])
_linear(wn)
print("[生命] 星空 OK")

# —— 残月: 开场可见, 200 帧落幕 ——
moon_mat = bpy.data.materials.new("残月清辉")
moon_mat.use_nodes = True
mp = _principled(moon_mat.node_tree)
mp.inputs["Base Color"].default_value = (.8, .8, .75, 1)
mp.inputs["Emission Color"].default_value = (1.0, .96, .86, 1)
mp.inputs["Emission Strength"].default_value = 6.0
bpy.ops.mesh.primitive_uv_sphere_add(
    segments=32, ring_count=16, radius=3.0, location=(-56, 93, 24)
)
moon = bpy.context.object
moon.name = "残月"
moon.data.materials.append(moon_mat)
for poly in moon.data.polygons:
    poly.use_smooth = True
coll11 = bpy.data.collections.get("11_远山云气")
if coll11:
    for c in list(moon.users_collection):
        c.objects.unlink(moon)
    coll11.objects.link(moon)
moon.hide_render = False
moon.keyframe_insert("hide_render", frame=190)
moon.hide_render = True
moon.keyframe_insert("hide_render", frame=200)
print("[生命] 残月 OK")

# —— 流云漂移 + 瀑脚水雾脉动 ——
if coll11:
    drift = {"山腰流云": 14.0, "远山横岚": 10.0, "云海托底": 6.0}
    n_drift = n_mist = 0
    for i, ob in enumerate(coll11.objects):
        if ob.name.startswith("瀑脚水雾"):
            for axis in range(3):
                base = ob.scale[axis]
                fc = ob.driver_add("scale", axis)
                fc.driver.expression = (
                    f"{base:.4f}*(1+0.08*sin(frame*0.055+{i * 0.7:.2f}))"
                )
            n_mist += 1
            continue
        for prefix, dist in drift.items():
            if ob.name.startswith(prefix):
                ob.keyframe_insert("location", frame=F0)
                ob.location.x += dist
                ob.location.y += dist * .3
                ob.keyframe_insert("location", frame=F1)
                _linear(ob)
                n_drift += 1
                break
    print(f"[生命] 流云漂移 {n_drift} 团, 水雾脉动 {n_mist} 处")

# —— 树木随风轻摇 ——
coll08 = bpy.data.collections.get("08_松竹花木")
n_tree = 0
if coll08:
    for i, ob in enumerate(coll08.objects):
        if ob.type != "MESH":
            continue
        phase = (i * 0.37) % 6.283
        fc = ob.driver_add("rotation_euler", 0)
        fc.driver.expression = f"0.022*sin(frame*0.04+{phase:.3f})"
        fc2 = ob.driver_add("rotation_euler", 1)
        fc2.driver.expression = f"0.016*sin(frame*0.031+{phase * 1.7:.3f})"
        n_tree += 1
print(f"[生命] 树木摇曳 {n_tree} 株")

# —— 宫灯三相位风烛明灭, 随天明渐弱 ——
lamp_mat = bpy.data.materials.get("暖绢宫灯")
if lamp_mat:
    variants = [lamp_mat]
    for k, tag in enumerate(("A", "B"), 1):
        mv = lamp_mat.copy()
        mv.name = f"暖绢宫灯_风{tag}"
        variants.append(mv)
    for mv, ph in zip(variants, (0.0, 2.1, 4.2)):
        p = _principled(mv.node_tree)
        fc = p.inputs["Emission Strength"].driver_add("default_value")
        fc.driver.expression = (
            f"(1.35-0.00042*frame)*(1+0.22*sin(frame*0.11+{ph}))"
        )
    idx = 0
    for ob in scene.objects:
        hit = False
        for slot in ob.material_slots:
            if slot.material and slot.material.name.startswith("暖绢宫灯"):
                slot.material = variants[idx % 3]
                hit = True
        if hit:
            idx += 1
    print(f"[生命] 宫灯三相位明灭, 共 {idx} 组")

# —— 窗内烛光呼吸 ——
win = bpy.data.materials.get("窗内暖光")
if win:
    p = _principled(win.node_tree)
    fc = p.inputs["Emission Strength"].driver_add("default_value")
    fc.driver.expression = "(0.42-0.00010*frame)*(1+0.08*sin(frame*0.07+1.3))"

# —— 池面涟漪爬行(4D 噪声时间维) ——
water = bpy.data.materials.get("碧池水")
if water:
    for n in water.node_tree.nodes:
        if n.type == "TEX_NOISE":
            n.noise_dimensions = "4D"
            fc = n.inputs["W"].driver_add("default_value")
            fc.driver.expression = "frame*0.008"
            print("[生命] 池面涟漪 OK")

# ---------------- EEVEE 高画质 ----------------
try:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
except Exception:
    scene.render.engine = "BLENDER_EEVEE"
print("[视频prep] 渲染引擎:", scene.render.engine)

eevee = scene.eevee
for attr, value in [
    ("taa_render_samples", 48),
    ("volumetric_tile_size", "4"),
    ("volumetric_samples", 48),
    ("volumetric_shadow_samples", 16),
    ("volumetric_start", .1),
    ("volumetric_end", 400.0),
    ("shadow_ray_count", 2),
    ("shadow_step_count", 8),
    ("use_shadow_jitter", True),
    ("use_raytracing", False),
    ("use_motion_blur", True),
    ("motion_blur_shutter", .35),
]:
    try:
        setattr(eevee, attr, value)
        print(f"  eevee.{attr} = {value}")
    except Exception as e:
        print(f"  eevee.{attr} 跳过 ({type(e).__name__})")

scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.image_settings.color_depth = "8"
scene.render.filepath = os.path.join(FRAMES_DIR, "f_")
scene.render.use_file_extension = True
scene.render.use_overwrite = False   # placeholder 模式: 已存在帧自动跳过, 支持断点续渲
scene.render.use_placeholder = True

for look in ("AgX - Medium High Contrast", "Medium High Contrast", "None"):
    try:
        scene.view_settings.look = look
        print("  色彩look =", look)
        break
    except Exception:
        continue

blend_path = os.path.join(OUT_DIR, "TaiWei_Video.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print(f"[视频prep] 已保存 {blend_path}")
print("[视频prep] 完成")
