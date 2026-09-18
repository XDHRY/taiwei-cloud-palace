"""W6 氛围黑神话化：大光比暗调 + 低角度太阳 + 体积雾前向散射 + 地面薄雾带 + 色彩分级。
幂等改数值，可重跑。blender -b TaiWei_YanYun.blend -P atmosphere_blackmyth.py
依据 research/blackmyth_atmosphere.md：
- 阳光:天光 = 8:1~10:1；太阳 15-30° 掠射、角直径 2-3.5°
- 体积雾极稀薄 + Anisotropy 0.65-0.80（逆光丁达尔）
- AgX + High Contrast；60% 像素落低灰度区
"""
import bpy
import math
import os
from mathutils import Vector

BLEND_OUT = os.environ.get(
    "TAIWEI_BLEND_OUT",
    "E:/UserData/xdrhh/.openclaw/workspace/taiwei_video/TaiWei_YanYun.blend",
)
DIAG = "E:/UserData/xdrhh/.openclaw/workspace/taiwei_video/diag/"
SKIP_SHOTS = os.environ.get("TAIWEI_SKIP_SHOTS", "0") in ("1", "true", "True")

scene = bpy.context.scene
SEASON = os.environ.get("TAIWEI_SEASON", "autumn").lower()

# ---------- 1. 世界天光：秋冬压暗，春夏留一口气 ----------
world_strength = {"spring": 0.32, "summer": 0.36, "winter": 0.16}.get(SEASON, 0.22)
world = scene.world
if world and world.use_nodes:
    for n in world.node_tree.nodes:
        if n.type == "BACKGROUND":
            n.inputs["Strength"].default_value = world_strength
            print("WORLD_STRENGTH ->", world_strength, SEASON)

# ---------- 2. 太阳：秋冬低掠射，春夏抬高 ----------
sun_elev = {"spring": 28, "summer": 42, "winter": 10}.get(SEASON, 14)
sun_energy = {"spring": 2.35, "summer": 2.85, "winter": 1.85}.get(SEASON, 2.65)
sun_color = {
    "spring": (1.0, 0.86, 0.72),
    "summer": (1.0, 0.90, 0.78),
    "winter": (0.82, 0.88, 0.95),
}.get(SEASON, (1.0, 0.76, 0.52))
sun = bpy.data.objects.get("晨阳主光")
if sun and sun.data.type == "SUN":
    sun.rotation_euler = (
        math.radians(sun_elev),
        math.radians(-30),
        math.radians(-38),
    )
    sun.data.energy = sun_energy
    sun.data.angle = math.radians(2.4 if SEASON == "winter" else 2.8)
    sun.data.color = sun_color
    print("SUN -> energy", sun_energy, "elev", sun_elev, SEASON)

# ---------- 3. 补光大收敛（×0.35） ----------
for name, f in (("前庭柔光", 0.35), ("西侧青天光", 0.30),
                ("后山轮廓光", 0.55), ("悬山弱补光", 0.40)):
    o = bpy.data.objects.get(name)
    if o and o.data.type == "AREA":
        o.data.energy *= f
        print("AREA", name, "->", round(o.data.energy, 0))

# ---------- 4. 大气体积：前向散射 g 提升（逆光丁达尔） ----------
atm = bpy.data.materials.get("高度衰减空气")
if atm and atm.use_nodes:
    for n in atm.node_tree.nodes:
        if n.type == "VOLUME_PRINCIPLED":
            n.inputs["Anisotropy"].default_value = 0.68
            # 密度略降（黑神话是稀薄雾）
            print("ATMO anisotropy -> 0.68")

# ---------- 5. 地面带状薄雾（掩桥船下半截，黑神话掩映感） ----------
old = bpy.data.objects.get("地面薄雾带")
if old:
    bpy.data.objects.remove(old, do_unlink=True)

m = bpy.data.materials.get("地面薄雾")
if m is None:
    m = bpy.data.materials.new("地面薄雾")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    nodes, links = nt.nodes, nt.links
    out = nodes.new("ShaderNodeOutputMaterial")
    vol = nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (0.75, 0.80, 0.78, 1)
    vol.inputs["Anisotropy"].default_value = 0.55
    coord = nodes.new("ShaderNodeTexCoord")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(coord.outputs["Generated"], sep.inputs["Vector"])
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[1].color = (0, 0, 0, 1)
    ramp.color_ramp.elements[1].position = 0.72
    links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    mult = nodes.new("ShaderNodeMath")
    mult.operation = "MULTIPLY"
    mult.inputs[1].default_value = 0.045
    links.new(ramp.outputs["Color"], mult.inputs[0])
    links.new(mult.outputs[0], vol.inputs["Density"])
    links.new(vol.outputs["Volume"], out.inputs["Volume"])

bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 5, 4.6))
fog = bpy.context.object
fog.name = "地面薄雾带"
fog.scale = (46, 42, 1.5)
bpy.ops.object.transform_apply(scale=True)
grp = bpy.data.collections.get("11_远山云气")
if grp:
    for c in list(fog.users_collection):
        c.objects.unlink(fog)
    grp.objects.link(fog)
fog.data.materials.append(m)
fog.display_type = "WIRE"
print("GROUND_FOG added")

# ---------- 6. 色彩管理：AgX High Contrast ----------
scene.view_settings.view_transform = "AgX"
try:
    scene.view_settings.look = "AgX - Medium High Contrast"
except TypeError:
    scene.view_settings.look = "AgX - Very High Contrast"
scene.view_settings.exposure = 0.05
print("LOOK ->", scene.view_settings.look)

# ---------- 7. 合成器色彩分级：暗部偏青、亮部偏暖 ----------
scene.use_nodes = True
nodes = scene.node_tree.nodes
links = scene.node_tree.links
rl = next((n for n in nodes if n.type == "R_LAYERS"), None)
comp = next((n for n in nodes if n.type == "COMPOSITE"), None)
if rl and comp and not any(n.type == "COLORBALANCE" for n in nodes):
    glare = next((n for n in nodes if n.type == "GLARE"), None)
    cb = nodes.new("CompositorNodeColorBalance")
    cb.correction_method = "LIFT_GAMMA_GAIN"
    # lift 偏青绿（暗部）、gain 偏暖金（亮部）、gamma 略提中部防死黑
    cb.lift = (0.965, 1.0, 1.045)
    cb.gamma = (1.0, 1.0, 1.0)
    cb.gain = (1.045, 1.0, 0.955)
    # 插入：RLayers -> [glare] -> ColorBalance -> Composite
    prev_out = rl.outputs["Image"]
    if glare:
        for l in list(links):
            if l.to_node == comp and l.from_node == glare:
                links.remove(l)
        for l in list(links):
            if l.to_node == glare and l.from_node == rl:
                links.remove(l)
        links.new(rl.outputs["Image"], glare.inputs["Image"])
        links.new(glare.outputs["Image"], cb.inputs["Image"])
    else:
        for l in list(links):
            if l.to_node == comp:
                links.remove(l)
        links.new(prev_out, cb.inputs["Image"])
    links.new(cb.outputs["Image"], comp.inputs["Image"])
    print("COLORBALANCE inserted")

bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUT)
print("SAVED", BLEND_OUT)

if SKIP_SHOTS:
    print("SKIP_SHOTS")
    print("ALL_DONE")
else:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    cam = bpy.data.objects.get("巡航相机")
    scene.camera = cam
    for f in (60, 360, 700):
        scene.frame_set(f)
        scene.render.filepath = DIAG + "atmo_f%04d.png" % f
        bpy.ops.render.render(write_still=True)
        print("SHOT", f)
    print("ALL_DONE")
