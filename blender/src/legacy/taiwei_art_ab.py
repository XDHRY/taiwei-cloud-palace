# -*- coding: utf-8 -*-
"""画风 A/B：同机位同帧，先渲现状(before)，再套光影/色彩方案(after)。

改动四件事：
1. 主光变硬变强（太阳 1.6x、角度 7°->4°），补光砍到 34%，天光降到 52%
   —— 现状是"均匀打亮"，没有主次，所以没有体积感和光影情绪。
2. 琉璃瓦去金属、加粗糙、压暗底色 —— 现状像薄荷色塑料，因为它靠反照率发亮。
3. 苔土压暗 —— 现在那块草绿太亮太黄，抢戏。
4. 合成辉光从"几乎关掉"(mix -0.95) 提到 -0.58 —— 灯与月亮有一点晕，才有游戏感。
"""
import bpy
import math
import os
import time
from mathutils import Vector

scene = bpy.context.scene
scene.render.resolution_percentage = 55
scene.render.use_overwrite = True
scene.render.use_placeholder = False
scene.render.image_settings.file_format = "PNG"
try:
    scene.eevee.taa_render_samples = 32
except Exception:
    pass

OUT = os.path.join(os.path.dirname(bpy.data.filepath), "art")
os.makedirs(OUT, exist_ok=True)

cd = bpy.data.cameras.new("对照相机")
cd.sensor_width = 36
cd.clip_start = .05
cd.clip_end = 900
cam = bpy.data.objects.new("对照相机", cd)
scene.collection.objects.link(cam)
scene.camera = cam

SHOTS = [
    ("front", 547, (12.0, -44.0, 28.0), (0.0, 14.0, 12.5), 45),
    ("gate",  1,   (6.0, -46.0, 6.2),   (0.0, -16.0, 7.4), 45),
]


def shoot(tag, frame, loc, tgt, lens):
    cd.lens = lens
    scene.frame_set(frame)
    cam.location = Vector(loc)
    cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = os.path.join(OUT, tag + ".png")
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"[对照] {tag}  {time.time()-t0:.1f}s")


def scale_keys(id_block, factor, path_has):
    ad = getattr(id_block, "animation_data", None)
    if not ad or not ad.action:
        return 0
    n = 0
    for fc in ad.action.fcurves:
        if path_has not in fc.data_path:
            continue
        for kp in fc.keyframe_points:
            kp.co.y = kp.co.y * factor
            kp.handle_left.y = kp.handle_left.y * factor
            kp.handle_right.y = kp.handle_right.y * factor
        n += 1
    return n


for tag, f, loc, tgt, lens in SHOTS:
    if not os.path.exists(os.path.join(OUT, "before_" + tag + ".png")):
        shoot("before_" + tag, f, loc, tgt, lens)

# ============ 套用画风方案 ============

# 1) 主光：更硬更亮
sun = bpy.data.objects.get("晨阳主光")
if sun:
    sun.data.angle = math.radians(2.6)
    print("  日光 energy 键缩放:", scale_keys(sun.data, 2.40, "energy"))

# 2) 补光砍到 16%：补光一旦能压过主光，画面就没有主次、没有影子、没有体积
for name, factor in [("前庭柔光", .16), ("西侧青天光", .16),
                     ("后山轮廓光", .16), ("悬山弱补光", .16)]:
    ob = bpy.data.objects.get(name)
    if ob and ob.type == "LIGHT":
        ob.data.energy *= factor

# 3) 天光降到 38%
bg = next((n for n in scene.world.node_tree.nodes if n.type == "BACKGROUND"), None)
if bg:
    print("  天光 Strength 键缩放:", scale_keys(scene.world.node_tree, .38, bg.name))

# 4) 琉璃瓦：去金属、加粗糙、压暗
TILE = {
    "青碧琉璃瓦": (.52, .06, .46),
    "浅青旧釉":   (.52, .05, .50),
    "深青旧釉":   (.62, .04, .54),
    "黛青瓦底":   (.70, .04, .52),
}
for name, (mul, metal, rough) in TILE.items():
    m = bpy.data.materials.get(name)
    if not m:
        continue
    p = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if not p:
        continue
    p.inputs["Metallic"].default_value = metal
    p.inputs["Roughness"].default_value = rough
    for n in m.node_tree.nodes:
        if n.type == "VALTORGB":
            for el in n.color_ramp.elements:
                el.color = (el.color[0] * mul, el.color[1] * mul,
                            el.color[2] * mul, 1)

# 5) 苔土压暗
earth = bpy.data.materials.get("苔土")
if earth:
    for n in earth.node_tree.nodes:
        if n.type == "VALTORGB":
            for el in n.color_ramp.elements:
                el.color = (el.color[0] * .68, el.color[1] * .70,
                            el.color[2] * .62, 1)

# 6) 合成辉光：从"几乎关掉"提上来
for n in scene.node_tree.nodes:
    if n.type == "GLARE":
        n.mix = -.55
        n.threshold = 1.05
        n.size = 8

# 7) 曝光提回被压掉的整体亮度
scene.view_settings.exposure = .48

for tag, f, loc, tgt, lens in SHOTS:
    shoot("after2_" + tag, f, loc, tgt, lens)

print("[对照] 完成")
