"""W1b 材质二次校准（黑神话报告配方）：
- 木构：Sheen 绒光 0.55（木质微毛切线散射）
- 琉璃瓦：Coat 清漆层 0.4（雨后高光）+ 底层糙度提升
- 粉墙：雨淋泪痕竖条（Z 拉伸 noise）
- 旧铜：缝隙概念已由 AO 覆盖，此处提 Metallic 本色
幂等。blender -b TaiWei_YanYun.blend -P material_calib.py
"""
import bpy
import os

BLEND_OUT = os.environ.get(
    "TAIWEI_BLEND_OUT",
    "E:/UserData/xdrhh/.openclaw/workspace/taiwei_video/TaiWei_YanYun.blend",
)
DIAG = "E:/UserData/xdrhh/.openclaw/workspace/taiwei_video/diag/"
SKIP_SHOTS = os.environ.get("TAIWEI_SKIP_SHOTS", "0") in ("1", "true", "True")


def principled(nt):
    for n in nt.nodes:
        if n.type == "BSDF_PRINCIPLED":
            return n
    return None


# ---------- 1. 木构 Sheen 绒光 ----------
for name in ("沉朱漆木", "梁枋暗朱", "古木与树皮", "乌木格扇"):
    m = bpy.data.materials.get(name)
    if m:
        p = principled(m.node_tree)
        p.inputs["Sheen Weight"].default_value = 0.55
        p.inputs["Sheen Roughness"].default_value = 0.6
        print("SHEEN", name)

# ---------- 2. 瓦 Coat 清漆层 + 底层糙 ----------
for name in ("青碧琉璃瓦", "浅青旧釉", "深青旧釉", "黛青瓦底"):
    m = bpy.data.materials.get(name)
    if m:
        p = principled(m.node_tree)
        p.inputs["Coat Weight"].default_value = 0.4
        p.inputs["Coat Roughness"].default_value = 0.22
        print("COAT", name)

# ---------- 3. 粉墙雨痕竖条 ----------
m = bpy.data.materials.get("粉墙")
if m:
    nt = m.node_tree
    p = principled(nt)
    if p and not any(n.name == "雨痕条纹" for n in nt.nodes):
        nodes, links = nt.nodes, nt.links
        src_link = p.inputs["Base Color"].links[0]
        src_socket = src_link.from_socket
        links.remove(src_link)

        coord = nodes.new("ShaderNodeTexCoord")
        vmul = nodes.new("ShaderNodeVectorMath")
        vmul.operation = "MULTIPLY"
        vmul.inputs[1].default_value = (2.2, 2.2, 16.0)   # Z 轴拉伸成竖条
        links.new(coord.outputs["Generated"], vmul.inputs[0])

        rain = nodes.new("ShaderNodeTexNoise")
        rain.name = "雨痕条纹"
        rain.inputs["Scale"].default_value = 1.6
        rain.inputs["Detail"].default_value = 5.0
        rain.inputs["Roughness"].default_value = 0.8
        links.new(vmul.outputs["Vector"], rain.inputs["Vector"])

        ramp = nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.42
        ramp.color_ramp.elements[0].color = (0.42, 0.43, 0.40, 1)
        ramp.color_ramp.elements[1].position = 0.58
        ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
        links.new(rain.outputs["Fac"], ramp.inputs["Fac"])

        mix = nodes.new("ShaderNodeMixRGB")
        mix.blend_type = "MULTIPLY"
        mix.inputs[0].default_value = 0.38
        links.new(src_socket, mix.inputs[1])
        links.new(ramp.outputs["Color"], mix.inputs[2])
        links.new(mix.outputs["Color"], p.inputs["Base Color"])
        print("RAIN_STREAKS 粉墙")

# ---------- 4. 暖白石压暗：庭院太新太白 ----------
for name, extra_rough, extra_grime in (
    ("暖白石", 0.18, 0.22),
    ("青石", 0.08, 0.12),
):
    m = bpy.data.materials.get(name)
    if not m:
        continue
    p = principled(m.node_tree)
    if p is None:
        continue
    p.inputs["Roughness"].default_value = min(
        1.0, p.inputs["Roughness"].default_value + extra_rough
    )
    if not any(n.name == "庭院压暗" for n in m.node_tree.nodes):
        nodes, links = m.node_tree.nodes, m.node_tree.links
        src = p.inputs["Base Color"].links[0]
        src_socket = src.from_socket
        links.remove(src)
        mix = nodes.new("ShaderNodeMixRGB")
        mix.name = "庭院压暗"
        mix.blend_type = "MULTIPLY"
        mix.inputs[0].default_value = extra_grime + 0.42
        mix.inputs[2].default_value = (0.48, 0.50, 0.44, 1)
        links.new(src_socket, mix.inputs[1])
        links.new(mix.outputs["Color"], p.inputs["Base Color"])
        print("STONE_MUTE", name)

bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUT)
print("SAVED", BLEND_OUT)

if SKIP_SHOTS:
    print("SKIP_SHOTS")
    print("ALL_DONE")
else:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    cam = bpy.data.objects.get("巡航相机")
    scene.camera = cam
    for f in (60, 360):
        scene.frame_set(f)
        scene.render.filepath = DIAG + "calib_f%04d.png" % f
        bpy.ops.render.render(write_still=True)
        print("SHOT", f)
    print("ALL_DONE")
