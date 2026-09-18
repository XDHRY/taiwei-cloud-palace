"""岁月感材质升级：对 TaiWei_Video.blend 全库材质做 aged v2 重建。
读 base color → 清节点 → 多层Noise+AO积垢+Z向污垢+粗糙度变化+Bump → 保留发光。
blender -b TaiWei_Video.blend -P upgrade_materials.py
产出：TaiWei_YanYun.blend + diag/upgrade_f0360.png + upgrade_f0700.png 对比帧。
"""
import bpy
import math
import os

SRC = "E:/UserData/xdrhh/.openclaw/workspace/taiwei_video/TaiWei_Video.blend"
DST = os.environ.get(
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


def agedify(mat, scale_big=2.2, scale_mid=7.0, scale_fine=20.0,
            dark_f=0.62, light_f=1.22, rough_var=0.2,
            bump=0.3, bump_dist=0.06,
            grime=0.5, grime_z=0.28, grime_hue=(0.7, 1.1, 0.7),
            ao_dirt=0.45):
    """在既有材质上重建节点树为 aged v2。base 色从原 Principled 读取。"""
    nt = mat.node_tree
    old_p = principled(nt)
    base = tuple(old_p.inputs["Base Color"].default_value[:3])
    old_rough = old_p.inputs["Roughness"].default_value
    old_metal = old_p.inputs["Metallic"].default_value
    emission = tuple(old_p.inputs["Emission Color"].default_value[:3])
    em_str = old_p.inputs["Emission Strength"].default_value
    subsurface = old_p.inputs["Subsurface Weight"].default_value

    dark = tuple(c * dark_f for c in base)
    light = tuple(min(1.0, c * light_f) for c in base)
    grime_color = tuple(min(1.0, c * g * 0.35) for c, g in zip(base, grime_hue))

    nt.nodes.clear()
    nodes, links = nt.nodes, nt.links
    out = nodes.new("ShaderNodeOutputMaterial")
    p = nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Roughness"].default_value = old_rough
    p.inputs["Metallic"].default_value = old_metal
    p.inputs["Subsurface Weight"].default_value = subsurface
    if em_str > 0:
        p.inputs["Emission Color"].default_value = (*emission, 1)
        p.inputs["Emission Strength"].default_value = em_str
    links.new(p.outputs["BSDF"], out.inputs["Surface"])

    coord = nodes.new("ShaderNodeTexCoord")

    # 大尺度斑块
    nz_big = nodes.new("ShaderNodeTexNoise")
    nz_big.inputs["Scale"].default_value = scale_big
    nz_big.inputs["Detail"].default_value = 3.5
    nz_big.inputs["Roughness"].default_value = 0.75
    links.new(coord.outputs["Generated"], nz_big.inputs["Vector"])
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.26
    ramp.color_ramp.elements[0].color = (*dark, 1)
    ramp.color_ramp.elements[1].position = 0.74
    ramp.color_ramp.elements[1].color = (*light, 1)
    links.new(nz_big.outputs["Fac"], ramp.inputs["Fac"])

    base_mix = nodes.new("ShaderNodeMixRGB")
    base_mix.blend_type = "MULTIPLY"
    base_mix.inputs[0].default_value = 0.92
    base_mix.inputs[1].default_value = (*base, 1)
    links.new(ramp.outputs["Color"], base_mix.inputs[2])

    # 中尺度碎纹调制（浅灰乘色，只破匀不压暗）
    nz_mid = nodes.new("ShaderNodeTexNoise")
    nz_mid.inputs["Scale"].default_value = scale_mid
    nz_mid.inputs["Detail"].default_value = 4
    links.new(coord.outputs["Generated"], nz_mid.inputs["Vector"])
    mid_mix = nodes.new("ShaderNodeMixRGB")
    mid_mix.blend_type = "MULTIPLY"
    mid_mix.inputs[2].default_value = (0.86, 0.86, 0.86, 1)
    links.new(base_mix.outputs["Color"], mid_mix.inputs[1])
    links.new(nz_mid.outputs["Fac"], mid_mix.inputs[0])

    # AO 积垢：遮蔽处 AO 值低→乘色变暗；开阔处≈1→不变。
    # 正确接法：Fac=常数强度，Color2=AO 值。
    ao = nodes.new("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = 0.6
    ao_dark = nodes.new("ShaderNodeMixRGB")
    ao_dark.blend_type = "MULTIPLY"
    ao_dark.inputs[0].default_value = ao_dirt
    links.new(mid_mix.outputs["Color"], ao_dark.inputs[1])
    links.new(ao.outputs["Color"], ao_dark.inputs[2])

    # Z 向墙根污垢：用 Generated Z（对象局部 0-1），底部 grime_z 范围内渐深
    coord2 = nodes.new("ShaderNodeTexCoord")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(coord2.outputs["Generated"], sep.inputs["Vector"])
    rampz = nodes.new("ShaderNodeValToRGB")
    rampz.color_ramp.elements[0].position = 0.0
    rampz.color_ramp.elements[0].color = (*grime_color, 1)
    rampz.color_ramp.elements[1].position = grime_z
    rampz.color_ramp.elements[1].color = (1, 1, 1, 1)
    links.new(sep.outputs["Z"], rampz.inputs["Fac"])
    grime_mix = nodes.new("ShaderNodeMixRGB")
    grime_mix.blend_type = "MULTIPLY"
    grime_mix.inputs[0].default_value = grime
    links.new(ao_dark.outputs["Color"], grime_mix.inputs[1])
    links.new(rampz.outputs["Color"], grime_mix.inputs[2])
    links.new(grime_mix.outputs["Color"], p.inputs["Base Color"])

    # 粗糙度变化
    rr = nodes.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = max(0.05, old_rough - rough_var)
    rr.inputs["To Max"].default_value = min(1.0, old_rough + rough_var)
    links.new(nz_big.outputs["Fac"], rr.inputs["Value"])
    links.new(rr.outputs["Result"], p.inputs["Roughness"])

    # Bump 中+细
    nz_fine = nodes.new("ShaderNodeTexNoise")
    nz_fine.inputs["Scale"].default_value = scale_fine
    nz_fine.inputs["Detail"].default_value = 2.5
    links.new(coord.outputs["Generated"], nz_fine.inputs["Vector"])
    mix_h = nodes.new("ShaderNodeMixRGB")
    mix_h.blend_type = "MULTIPLY"
    mix_h.inputs[0].default_value = 0.6
    links.new(nz_mid.outputs["Fac"], mix_h.inputs[1])
    links.new(nz_fine.outputs["Fac"], mix_h.inputs[2])
    bn = nodes.new("ShaderNodeBump")
    bn.inputs["Strength"].default_value = bump
    bn.inputs["Distance"].default_value = bump_dist
    links.new(mix_h.outputs["Color"], bn.inputs["Height"])
    links.new(bn.outputs["Normal"], p.inputs["Normal"])
    return mat


# ---- 分组参数表（按材质中文名）----
SKIP = {"碧池水", "清泉水丝", "水沫", "暖绢宫灯", "窗内暖光",
        "鹤羽", "鹤翎", "鹤顶丹红"}

GROUPS = {
    "瓦作": ({"scale_big": 2.0, "scale_mid": 6.5, "scale_fine": 22.0,
             "rough_var": 0.22, "bump": 0.5, "bump_dist": 0.06,
             "grime": 0.5, "grime_z": 0.35, "ao_dirt": 0.5},
            {"黛青瓦底", "青碧琉璃瓦", "浅青旧釉", "深青旧釉"}),
    "木构": ({"scale_big": 1.8, "scale_mid": 6.0, "scale_fine": 18.0,
             "rough_var": 0.3, "bump": 0.35, "bump_dist": 0.05,
             "grime": 0.45, "grime_z": 0.7, "ao_dirt": 0.45},
            {"沉朱漆木", "梁枋暗朱", "古木与树皮", "乌木格扇"}),
    "石作": ({"scale_big": 2.4, "scale_mid": 7.0, "scale_fine": 24.0,
             "rough_var": 0.24, "bump": 0.5, "bump_dist": 0.09,
             "grime": 0.6, "grime_z": 0.5, "ao_dirt": 0.6},
            {"暖白石", "青石", "铺地灰缝", "青灰层岩", "庭园洞石"}),
    "粉墙": ({"scale_big": 2.2, "scale_mid": 7.0, "scale_fine": 20.0,
             "rough_var": 0.13, "bump": 0.22, "bump_dist": 0.035,
             "grime": 0.75, "grime_z": 0.85, "ao_dirt": 0.55},
            {"粉墙"}),
    "金属": ({"scale_big": 2.0, "scale_mid": 8.0, "scale_fine": 26.0,
             "rough_var": 0.28, "bump": 0.3, "bump_dist": 0.02,
             "grime": 0.4, "grime_z": 0.5, "ao_dirt": 0.5},
            {"哑光鎏金", "旧铜", "铜绿"}),
    "植被": ({"scale_big": 2.6, "scale_mid": 9.0, "scale_fine": 28.0,
             "dark_f": 0.6, "light_f": 1.4, "rough_var": 0.15,
             "bump": 0.2, "bump_dist": 0.03,
             "grime": 0.0, "ao_dirt": 0.25},
            {"松针墨绿", "深翠叶", "春叶", "竹秆", "深绿草叶", "嫩绿草叶",
             "桃花胭脂", "桃花浅粉", "玉白花瓣", "荷叶", "芦苇花穗"}),
    "水土": ({"scale_big": 2.0, "scale_mid": 6.0, "scale_fine": 18.0,
             "rough_var": 0.18, "bump": 0.4, "bump_dist": 0.08,
             "grime": 0.3, "grime_z": 1.2, "ao_dirt": 0.4},
            {"苔土", "苔青"}),
    "远山": ({"scale_big": 1.2, "scale_mid": 4.0, "scale_fine": 12.0,
             "rough_var": 0.1, "bump": 0.45, "bump_dist": 0.25,
             "grime": 0.0, "ao_dirt": 0.3},
            {"近远山青", "中远山青", "极远山青"}),
}

upgraded, skipped, missing = [], [], []
for params, names in GROUPS.values():
    for name in names:
        mat = bpy.data.materials.get(name)
        if mat is None:
            missing.append(name)
            continue
        if name in SKIP:
            skipped.append(name)
            continue
        agedify(mat, **dict(params))
        upgraded.append(name)

print("UPGRADED", len(upgraded), "MISSING", missing, "SKIPPED", skipped)

# ---- 另存新 blend ----
bpy.ops.wm.save_as_mainfile(filepath=DST)
print("SAVED", DST)

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
    if cam:
        scene.camera = cam
    for f in (360, 700):
        scene.frame_set(f)
        scene.render.filepath = DIAG + "upgrade_f%04d.png" % f
        bpy.ops.render.render(write_still=True)
        print("SHOT", scene.render.filepath)
    print("ALL_DONE")
