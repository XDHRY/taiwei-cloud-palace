# -*- coding: utf-8 -*-
"""
===============================================================================
                         太 微 · 云 宫 山 水 长 卷
===============================================================================

Blender 4.2 LTS / Cycles
独立完整场景生成器，无外部模型、无贴图、无第三方插件。

视觉结构：
    迎仙石阶
      → 山门与前庭
      → 石桥、池院与两翼廊庑
      → 高台重檐正殿
      → 后苑藏书楼
      → 云外远山

构件系统：
    分坡屋面、分行筒瓦、瓦当、正脊、吻兽、飞檐、风铃
    柱础、柱箍、斗拱、雀替、梁枋、菱花格扇、门环
    白玉栏杆、莲瓣柱头、垂花门、月洞门、八角亭
    自然驳岸、虹桥、曲径、荷叶、莲花、芦苇
    松针、竹叶、花树、盆景、落瓣、苔石、穿孔庭石
    仙鹤、宫灯、铜鼎、石桌、鼓凳
    飞瀑、层云、空气透视、远山、摄影灯光

注意：
    清空当前场景。
    HIGH 和 FINAL 档会生成较多几何。
    先使用 STUDY 检查布局，再提高档位。
    这是艺术化视觉场景，不是古建测绘或施工模型。
===============================================================================
"""

import bpy
import bmesh
import math
import random
import time
import os

from mathutils import Vector
from collections import defaultdict


# =============================================================================
# 00. 用户配置
# =============================================================================

QUALITY = os.environ.get("TAIWEI_QUALITY", "HIGH").upper()  # STUDY / HIGH / FINAL
SEED = 10836

ENABLE_TILE_GEOMETRY = True
ENABLE_CLOUDS = True
ENABLE_AERIAL_PERSPECTIVE = True
ENABLE_WATERFALLS = True
ENABLE_SCHOLAR_ROCKS = True
ENABLE_BIRDS = True
ENABLE_M1_SATURATION = os.environ.get("TAIWEI_M1", "1") not in ("0", "false", "False")
SEASON = os.environ.get("TAIWEI_SEASON", "autumn").lower()  # spring summer autumn winter

USE_GPU = False                   # 需先在 Blender 首选项配置 GPU
AUTO_SAVE = os.environ.get("TAIWEI_SAVE", "0") in ("1", "true", "True")
AUTO_RENDER = False
RENDER_ALL_CAMERAS = False
CLEAR_SCENE = os.environ.get("TAIWEI_CLEAR", "1") not in ("0", "false", "False")

OUTPUT_DIRECTORY = os.environ.get("TAIWEI_OUTPUT_DIRECTORY", "//TaiWei_Output")
PROJECT_FILENAME = os.environ.get("TAIWEI_PROJECT_FILENAME", "TaiWei_Cloud_Palace.blend")
TEXTURE_DIR = os.environ.get(
    "TAIWEI_TEXTURE_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "taiwei_video", "textures_wukong"),
)

def _kit_flag(name, default=True):
    raw = os.environ.get("TAIWEI_KIT_" + name.upper())
    if raw is None:
        return default
    return raw not in ("0", "false", "False")

KIT = {
    "odd_bays": _kit_flag("odd_bays"),
    "corner_bracket": _kit_flag("corner_bracket"),
    "through_ang": _kit_flag("through_ang"),
    "geshan": _kit_flag("geshan"),
    "xumizuo": _kit_flag("xumizuo"),
    "chiwen_v2": _kit_flag("chiwen_v2"),
    "chiwen_v3": _kit_flag("chiwen_v3"),
    "textures": _kit_flag("textures"),
}

# 风格调整：推荐先只修改这些参数
SUN_STRENGTH = 3.00
WORLD_STRENGTH = 0.22
ATMOSPHERE_MULTIPLIER = 0.085
TREE_DENSITY_MULTIPLIER = 1.0
CAMERA_LENS = 45.0

PRESETS = {
    "STUDY": {
        "resolution": (1400, 1050),
        "samples": 40,
        "noise": 0.045,
        "terrain_n": 112,
        "terrain_rings": 34,
        "tile_spacing": 0.40,
        "tile_rows": 7,
        "tile_cross": 3,
        "trees": 65,
        "leaf_density": 0.34,
        "grass": 2200,
        "flowers": 180,
        "clouds": 8,
        "rock_subdivisions": 2,
    },
    "HIGH": {
        "resolution": (2400, 1800),
        "samples": 160,
        "noise": 0.015,
        "terrain_n": 168,
        "terrain_rings": 58,
        "tile_spacing": 0.28,
        "tile_rows": 12,
        "tile_cross": 4,
        "trees": 145,
        "leaf_density": 0.78,
        "grass": 8500,
        "flowers": 620,
        "clouds": 16,
        "rock_subdivisions": 3,
    },
    "FINAL": {
        "resolution": (4000, 3000),
        "samples": 640,
        "noise": 0.007,
        "terrain_n": 224,
        "terrain_rings": 82,
        "tile_spacing": 0.21,
        "tile_rows": 18,
        "tile_cross": 5,
        "trees": 230,
        "leaf_density": 1.25,
        "grass": 18500,
        "flowers": 1450,
        "clouds": 24,
        "rock_subdivisions": 4,
    },
}

P = PRESETS[QUALITY]
TAU = math.tau
START = time.time()

R_ARCH = random.Random(SEED + 101)
R_LAND = random.Random(SEED + 202)
R_TREE = random.Random(SEED + 303)
R_GRASS = random.Random(SEED + 404)
R_CLOUD = random.Random(SEED + 505)

COURT_Z = 5.50
MAIN_Z = 7.20
BACK_Z = 6.45
WATER_Z = 3.58

RX = 34.5
RY = 31.5
CY = 5.0


def report(message):
    print(f"[太微 {time.time() - START:7.1f}s] {message}")


# =============================================================================
# 01. 初始化与集合
# =============================================================================

if bpy.context.object and bpy.context.object.mode != "OBJECT":
    bpy.ops.object.mode_set(mode="OBJECT")

if CLEAR_SCENE:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
else:
    raise RuntimeError(
        "TAIWEI_CLEAR=0 时生成器仍会重建整座宫，禁止对成片 blend 追加。"
        "扩建请写入独立的 TaiWei_Expand.blend。"
    )

scene = bpy.context.scene
scene.render.engine = "CYCLES"

scene.cycles.samples = P["samples"]
scene.cycles.use_denoising = True
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = P["noise"]
scene.cycles.max_bounces = 10
scene.cycles.diffuse_bounces = 3
scene.cycles.glossy_bounces = 4
scene.cycles.transmission_bounces = 6
scene.cycles.volume_bounces = 1

if USE_GPU:
    scene.cycles.device = "GPU"

scene.render.resolution_x, scene.render.resolution_y = P["resolution"]
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.image_settings.color_depth = "16"
scene.render.film_transparent = False

scene.view_settings.view_transform = "AgX"
scene.view_settings.exposure = 0.20

GROUP_NAMES = [
    "01_山体地形",
    "02_台基庭院",
    "03_殿阁木构",
    "04_琉璃瓦作",
    "05_门窗雕饰",
    "06_廊桥园墙",
    "07_池水飞瀑",
    "08_松竹花木",
    "09_草花庭石",
    "10_庭院陈设",
    "11_远山云气",
    "12_灯光相机",
]

GROUPS = {}
for name in GROUP_NAMES:
    collection = bpy.data.collections.new(name)
    scene.collection.children.link(collection)
    GROUPS[name] = collection


def link_object(name, data, group):
    obj = bpy.data.objects.new(name, data)
    GROUPS[group].objects.link(obj)
    return obj


def relocate(obj, group):
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    GROUPS[group].objects.link(obj)


# =============================================================================
# 02. 材质
# =============================================================================

MAT = {}


def principled(node_tree):
    """按类型取节点：界面语言为中文时新建节点名是"原理化 BSDF"，按名字取会拿到 None。"""
    for node in node_tree.nodes:
        if node.type == "BSDF_PRINCIPLED":
            return node
    raise RuntimeError("材质缺少 Principled BSDF 节点")


def material(key, name, color, roughness=.5, metallic=0,
             emission=None, strength=0, subsurface=0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = principled(m.node_tree)

    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Roughness"].default_value = roughness
    p.inputs["Metallic"].default_value = metallic
    p.inputs["Subsurface Weight"].default_value = subsurface

    if emission is not None:
        p.inputs["Emission Color"].default_value = (*emission, 1)
        p.inputs["Emission Strength"].default_value = strength

    m.diffuse_color = (*color, 1)
    MAT[key] = m
    return m


def procedural_material(key, dark, light, scale=4,
                        detail=4, bump=.15, distance=.04,
                        stretch=(1, 1, 1)):
    m = MAT[key]
    nodes, links = m.node_tree.nodes, m.node_tree.links
    p = principled(m.node_tree)

    coord = nodes.new("ShaderNodeTexCoord")
    multiply = nodes.new("ShaderNodeVectorMath")
    multiply.operation = "MULTIPLY"
    multiply.inputs[1].default_value = stretch

    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = detail
    noise.inputs["Roughness"].default_value = .72

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = .22
    ramp.color_ramp.elements[0].color = (*dark, 1)
    ramp.color_ramp.elements[1].position = .78
    ramp.color_ramp.elements[1].color = (*light, 1)

    bump_node = nodes.new("ShaderNodeBump")
    bump_node.inputs["Strength"].default_value = bump
    bump_node.inputs["Distance"].default_value = distance

    links.new(coord.outputs["Object"], multiply.inputs[0])
    links.new(multiply.outputs["Vector"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], p.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump_node.inputs["Height"])
    links.new(bump_node.outputs["Normal"], p.inputs["Normal"])


def bind_texture(key, filename, scale=4.0, bump=0.18):
    path = os.path.join(TEXTURE_DIR, filename)
    if not os.path.isfile(path) or key not in MAT:
        return False
    m = MAT[key]
    nodes, links = m.node_tree.nodes, m.node_tree.links
    p = principled(m.node_tree)
    img = bpy.data.images.load(path, check_existing=True)
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.projection = "BOX"
    try:
        tex.projection_blend = 0.22
    except Exception:
        pass
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (scale, scale, scale)
    coord = nodes.new("ShaderNodeTexCoord")
    bump_node = nodes.new("ShaderNodeBump")
    bump_node.inputs["Strength"].default_value = bump
    links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
    links.new(tex.outputs["Color"], p.inputs["Base Color"])
    links.new(tex.outputs["Color"], bump_node.inputs["Height"])
    links.new(bump_node.outputs["Normal"], p.inputs["Normal"])
    return True


def bind_mountain_rock(key, dark, light, scale_xy=1.15, scale_z=0.32, bump_str=0.26, mid=None):
    """远山崖岩贴图：非等比映射（Z 压低抗竖向拉伸）+ RGBToBW/ColorRamp 三段着色。
    暗部沟壑、中段岩体、亮部棱线，杜绝平涂馒头。"""
    path = os.path.join(TEXTURE_DIR, "tex-cliff-rock.png")
    if not os.path.isfile(path) or key not in MAT:
        return False
    m = MAT[key]
    nodes, links = m.node_tree.nodes, m.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    p = nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Roughness"].default_value = 0.92
    p.inputs["Specular IOR Level"].default_value = 0.25
    coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (scale_xy, scale_xy, scale_z)
    img = bpy.data.images.load(path, check_existing=True)
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.projection = "BOX"
    try:
        tex.projection_blend = 0.35
    except Exception:
        pass
    bw = nodes.new("ShaderNodeRGBToBW")
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.12
    ramp.color_ramp.elements[0].color = (*dark, 1)
    ramp.color_ramp.elements[1].position = 0.88
    ramp.color_ramp.elements[1].color = (*light, 1)
    if mid is not None:
        mid_el = ramp.color_ramp.elements.new(0.52)
        mid_el.color = (*mid, 1)
    bump_node = nodes.new("ShaderNodeBump")
    bump_node.inputs["Strength"].default_value = bump_str
    bump_node.inputs["Distance"].default_value = 0.9
    links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
    links.new(tex.outputs["Color"], bw.inputs["Color"])
    links.new(bw.outputs["Val"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], p.inputs["Base Color"])
    links.new(tex.outputs["Color"], bump_node.inputs["Height"])
    links.new(bump_node.outputs["Normal"], p.inputs["Normal"])
    links.new(p.outputs["BSDF"], output.inputs["Surface"])
    return True


material("roof", "黛青瓦底", (.010, .045, .052), .48, .10)
material("tile", "青碧琉璃瓦", (.016, .085, .082), .34, .19)
material("tile_light", "浅青旧釉", (.032, .135, .118), .38, .14)
material("tile_dark", "深青旧釉", (.007, .032, .038), .42, .12)

material("gold", "哑光鎏金", (.65, .405, .12), .35, .75)
material("bronze", "旧铜", (.19, .13, .055), .46, .68)
material("patina", "铜绿", (.065, .17, .13), .57, .40)

material("red", "沉朱漆木", (.24, .030, .022), .40, .04)
material("beam", "梁枋暗朱", (.11, .022, .017), .52)
material("wood", "古木与树皮", (.11, .057, .023), .89)
material("darkwood", "乌木格扇", (.023, .037, .029), .57)

material("ivory", "暖白石", (.74, .79, .69), .48)
material("stone", "青石", (.23, .30, .265), .81)
material("wall", "粉墙", (.73, .77, .66), .91)
material("joint", "铺地灰缝", (.10, .145, .12), .98)

material("rock", "青灰层岩", (.135, .19, .18), .92)
material("scholar", "庭园洞石", (.28, .33, .28), .89)
material("earth", "苔土", (.14, .195, .07), .98)
material("moss", "苔青", (.12, .235, .055), .99)

material("pine", "松针墨绿", (.021, .085, .043), .89)
material("leaf", "深翠叶", (.052, .17, .047), .81, subsurface=.025)
material("leaf_light", "春叶", (.17, .31, .065), .77, subsurface=.035)
material("bamboo", "竹秆", (.18, .27, .065), .74)
material("grass", "深绿草叶", (.068, .17, .029), .91)
material("grass_light", "嫩绿草叶", (.21, .33, .055), .87)

material("pink", "桃花胭脂", (.72, .22, .275), .65, subsurface=.04)
material("pink_light", "桃花浅粉", (.92, .58, .56), .63, subsurface=.045)
material("flower_white", "玉白花瓣", (.88, .85, .68), .66)
material("pollen", "花蕊", (.80, .50, .09), .67)

material("lotus", "荷叶", (.028, .21, .115), .49)
material("reed", "芦苇花穗", (.47, .43, .25), .91)

material("water", "碧池水", (.010, .060, .078), .20, .01)
material("fall", "清泉水丝", (.36, .64, .65), .21)
material("foam", "水沫", (.75, .85, .78), .42)

material("lamp", "暖绢宫灯", (.92, .59, .23), .70,
         emission=(1.0, .44, .13), strength=1.45)
material("window", "窗内暖光", (.55, .35, .14), .70,
         emission=(1.0, .45, .15), strength=.22)

material("feather", "鹤羽", (.83, .87, .79), .63)
material("feather_dark", "鹤翎", (.015, .022, .018), .56)
material("crane_red", "鹤顶丹红", (.45, .030, .019), .59)

material("far_near", "近远山青", (.055, .115, .105), .99)
material("far_mid", "中远山青", (.095, .165, .175), .99)
material("far_far", "极远山青", (.16, .225, .225), .99)

procedural_material(
    "far_near", (.010, .032, .030), (.055, .165, .135),
    .18, 4, .46, .40, (.4, .4, 2.2)
)
procedural_material(
    "far_mid", (.025, .060, .078), (.105, .225, .225),
    .16, 4, .38, .33, (.4, .4, 2.0)
)
procedural_material(
    "far_far", (.070, .105, .125), (.225, .305, .310),
    .13, 4, .28, .25, (.4, .4, 1.8)
)

procedural_material(
    "rock", (.045, .078, .074), (.25, .29, .255),
    2.4, 5, .43, .20, (1.7, 1.7, .32)
)
procedural_material(
    "scholar", (.14, .19, .15), (.40, .43, .33),
    4.7, 5, .31, .10
)
procedural_material(
    "earth", (.045, .078, .015), (.24, .28, .085),
    4.8, 4, .31, .08
)
procedural_material(
    "ivory", (.63, .68, .58), (.85, .86, .74),
    2.4, 3, .060, .016
)
procedural_material(
    "stone", (.13, .19, .16), (.34, .385, .31),
    5.3, 4, .18, .05
)
procedural_material(
    "wood", (.028, .012, .004), (.20, .105, .027),
    3.5, 4, .28, .05, (5, 5, .35)
)
procedural_material(
    "wall", (.65, .69, .59), (.80, .83, .71),
    8, 3, .09, .016
)
procedural_material(
    "bronze", (.09, .058, .020), (.28, .21, .075),
    7, 3, .09, .016
)

water_p = principled(MAT["water"].node_tree)
water_p.inputs["Transmission Weight"].default_value = .30
water_p.inputs["IOR"].default_value = 1.333

nodes, links = MAT["water"].node_tree.nodes, MAT["water"].node_tree.links
noise = nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 12
noise.inputs["Detail"].default_value = 3
bump = nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = .12
bump.inputs["Distance"].default_value = .04
links.new(noise.outputs["Fac"], bump.inputs["Height"])
links.new(bump.outputs["Normal"], water_p.inputs["Normal"])

# 水波贴图叠加：tex-water-ripples 作为第二重法线源，碎开程序噪声的均匀感
_ripple_path = os.path.join(TEXTURE_DIR, "tex-water-ripples.png")
if KIT["textures"] and os.path.isfile(_ripple_path):
    _rw_img = bpy.data.images.load(_ripple_path, check_existing=True)
    _rw_tex = nodes.new("ShaderNodeTexImage")
    _rw_tex.image = _rw_img
    _rw_tex.projection = "BOX"
    _rw_map = nodes.new("ShaderNodeMapping")
    _rw_map.inputs["Scale"].default_value = (1.4, 1.4, 1.4)
    _rw_coord = nodes.new("ShaderNodeTexCoord")
    _rw_bump = nodes.new("ShaderNodeBump")
    _rw_bump.inputs["Strength"].default_value = .30
    _rw_bump.inputs["Distance"].default_value = .10
    links.new(_rw_coord.outputs["Object"], _rw_map.inputs["Vector"])
    links.new(_rw_map.outputs["Vector"], _rw_tex.inputs["Vector"])
    links.new(_rw_tex.outputs["Color"], _rw_bump.inputs["Height"])
    links.new(bump.outputs["Normal"], _rw_bump.inputs["Normal"])
    links.new(_rw_bump.outputs["Normal"], water_p.inputs["Normal"])

# 组件级专属材质：每个重点组件一张专属贴图
material("bridge_deck", "桥面白石", (.72, .75, .68), .42)
material("stair_tread", "踏跺条石", (.36, .40, .36), .78)
material("balustrade", "栏板雕石", (.62, .66, .60), .55)
material("carved_wood", "垂花雕木", (.20, .045, .030), .48)
material("pillar_red", "金柱朱漆", (.30, .035, .024), .38)
material("door_gold", "铺首鎏金", (.58, .36, .10), .40, .60)
material("plaque", "匾额青金石底", (.016, .048, .105), .32, .18)
material("bell_bronze", "风铃铁马", (.16, .11, .06), .52, .55)
material("lantern_stone", "灯柱青石", (.42, .46, .42), .80)
material("censer_bronze", "香炉饕餮铜", (.14, .10, .05), .50, .62)
material("baogu_stone", "抱鼓青石", (.50, .54, .48), .66)
material("koi", "锦鲤金鳞", (.62, .25, .06), .35)
material("paifang_stone", "牌坊青石", (.42, .46, .44), .72)
material("dharani", "经幢刻石", (.46, .47, .42), .68)
material("ding_bronze", "铜鼎夔纹", (.13, .10, .05), .50, .60)
material("bell_cast", "铸钟铭文铜", (.12, .09, .05), .52, .58)
material("drum_leather", "鼓面皮革", (.52, .38, .20), .75)
material("well_stone", "井栏湿石", (.34, .37, .33), .80)
material("chess_jade", "棋枰玉", (.60, .68, .58), .32)
material("banner_silk", "幡旗织金", (.45, .10, .08), .62)
material("canopy_silk", "伞盖团花绢", (.50, .12, .10), .58)
material("lakebed", "湖底卵石", (.30, .32, .26), .85)
material("coral", "水底珊瑚石", (.48, .16, .10), .70)
material("lion_stone", "石狮白玉", (.68, .70, .64), .58)
material("stele_stone", "龟趺碑石", (.30, .31, .28), .74)
material("sundial_marble", "日晷白玉", (.72, .74, .68), .36)
material("dragon_wall", "九龙壁琉璃", (.10, .22, .42), .30)
material("crane_cast", "铜鹤铸羽", (.14, .11, .06), .52, .58)

_tex_bound = 0
if KIT["textures"]:
    for _key, _file, _scale in (
        ("bridge_deck", "tex-bridge-white-stone.png", 1.3),
        ("stair_tread", "tex-stair-tread-stone.png", 1.1),
        ("balustrade", "tex-balustrade-post-relief.png", 1.0),
        ("carved_wood", "tex-chuihua-carved-wood.png", 1.2),
        ("pillar_red", "tex-pillar-vermilion-close.png", 1.0),
        ("door_gold", "tex-doorknocker-taotie-gold.png", 0.9),
        ("bell_bronze", "tex-windchime-bronze-plate.png", 0.8),
        ("lantern_stone", "tex-stone-lantern-carving.png", 0.9),
        ("censer_bronze", "tex-censer-beast-face.png", 1.0),
        ("baogu_stone", "tex-drum-stone-baogu.png", 0.8),
        ("koi", "tex-koi-fish-scales.png", 0.6),
        ("scholar", "tex-moss-rock-close.png", 1.5),
        ("feather", "tex-crane-feather-down.png", 0.7),
        ("fall", "tex-waterfall-sheet.png", 1.2),
        ("paifang_stone", "tex-paifang-bluestone.png", 1.0),
        ("dharani", "tex-dharani-pillar-script.png", 1.0),
        ("ding_bronze", "tex-cauldron-bronze-motif.png", 0.9),
        ("bell_cast", "tex-temple-bell-inscriptions.png", 0.8),
        ("drum_leather", "tex-drum-head-leather.png", 0.8),
        ("well_stone", "tex-well-curb-stone.png", 0.9),
        ("chess_jade", "tex-chessboard-stone-table.png", 0.7),
        ("banner_silk", "tex-ceremonial-banner-fabric.png", 0.8),
        ("canopy_silk", "tex-canopy-brocade-silk.png", 0.8),
        ("lakebed", "tex-lakebed-pebbles.png", 1.6),
        ("lion_stone", "tex-stone-lion-guardian.png", 0.8),
        ("stele_stone", "tex-bixi-turtle-stele.png", 0.9),
        ("sundial_marble", "tex-sundial-marble.png", 0.6),
        ("crane_cast", "tex-crane-bronze-cast.png", 0.8),
        ("wood", "tex-walnut.png", 1.15),
        ("red", "tex-cinnabar.png", 1.05),
        ("beam", "tex-caisson-paint.png", 2.0),
        ("tile", "tex-liuli-blue.png", 2.4),
        ("tile_light", "tex-liuli-blue.png", 2.2),
        ("tile_dark", "tex-liuli-blue.png", 2.9),
        ("roof", "tex-tile-back.png", 1.6),
        ("stone", "tex-bluestone.png", 0.85),
        ("ivory", "tex-white-marble.png", 0.70),
        ("gold", "tex-gilt-bronze.png", 1.8),
        ("bronze", "tex-cloud-bronze.png", 1.6),
        ("patina", "tex-patina-bronze.png", 1.4),
        ("wall", "tex-plaster.png", 0.55),
        ("window", "tex-lattice-paper.png", 1.4),
        ("darkwood", "tex-lattice-wood.png", 1.5),
        ("moss", "tex-moss-stone.png", 1.2),
        ("rock", "tex-cliff-rock.png", 1.8),
    ):
        if bind_texture(_key, _file, _scale):
            _tex_bound += 1
    # 地面三件套：新专用贴图优先（苔藓地面/无花哑草），缺失时回退旧贴图
    if not bind_texture("earth", "tex-mossy-ground.png", 1.4):
        bind_texture("earth", "tex-velvet-moss-ground.png", 1.4)
    if not bind_texture("grass", "tex-grass-muted.png", 1.6):
        bind_texture("grass", "tex-lush-grassland.png", 1.6)
    if not bind_texture("grass_light", "tex-grass-muted.png", 2.1):
        bind_texture("grass_light", "tex-lush-grassland.png", 2.1)
    if not bind_texture("roof", "tex-tile-back.png", 4.0):
        bind_texture("roof", "tex-banwa.png", 4.0)
    # ivory 统一白大理石（loop 已绑）；莲瓣浮雕贴图只属栏板望柱，不得覆盖铺地与台基
    if not bind_texture("bronze", "tex-cloud-bronze.png", 5.0):
        bind_texture("bronze", "tex-bronze.png", 5.0)
    if bind_mountain_rock("far_near", (.012, .048, .042), (.075, .300, .225), .10, .05, .38, mid=(.040, .165, .125)):
        _tex_bound += 1
    if bind_mountain_rock("far_mid", (.032, .095, .125), (.150, .360, .360), .08, .04, .30, mid=(.085, .225, .235)):
        _tex_bound += 1
    # 极远山也要岩理，但色阶更灰更浅（空气透视感），bump 更弱防噪点
    # 注意：Object 坐标按米计，scale 必须 <<1 才有山体尺度的岩理特征
    if bind_mountain_rock("far_far", (.085, .165, .155), (.295, .405, .375), .06, .03, .22, mid=(.185, .290, .265)):
        _tex_bound += 1
report(f"材质建立完成 贴图绑定 {_tex_bound} KIT={ {k:v for k,v in KIT.items()} }")


# =============================================================================
# 03. 几何工具
# =============================================================================

bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1)
unit_mesh = bpy.data.meshes.new("_unit_ico")
bm.to_mesh(unit_mesh)
bm.free()

ICO_V = [v.co.copy() for v in unit_mesh.vertices]
ICO_F = [tuple(p.vertices) for p in unit_mesh.polygons]
bpy.data.meshes.remove(unit_mesh)


class Frame:
    def __init__(self, x=0, y=0, z=0, angle=0):
        self.origin = Vector((x, y, z))
        self.angle = angle
        self.c = math.cos(angle)
        self.s = math.sin(angle)

    def p(self, x, y, z):
        return self.origin + Vector((
            x*self.c-y*self.s,
            x*self.s+y*self.c,
            z
        ))

    def d(self, x, y, z):
        return Vector((
            x*self.c-y*self.s,
            x*self.s+y*self.c,
            z
        ))

    def inverse_xy(self, x, y):
        dx = x-self.origin.x
        dy = y-self.origin.y
        return dx*self.c+dy*self.s, -dx*self.s+dy*self.c


class Geo:
    def __init__(self):
        self.v = []
        self.f = []
        self.ids = []
        self.smooth = []
        self.keys = []
        self.keymap = {}

    def mid(self, key):
        if key not in self.keymap:
            self.keymap[key] = len(self.keys)
            self.keys.append(key)
        return self.keymap[key]

    def face(self, points, key, smooth=False):
        start = len(self.v)
        self.v.extend(tuple(p) for p in points)
        self.f.append(tuple(range(start, start+len(points))))
        self.ids.append(self.mid(key))
        self.smooth.append(smooth)

    def indexed(self, vertices, faces, key, smooth=False):
        start = len(self.v)
        self.v.extend(tuple(p) for p in vertices)
        material_id = self.mid(key)
        for face in faces:
            self.f.append(tuple(start+i for i in face))
            self.ids.append(material_id)
            self.smooth.append(smooth)

    def box(self, center, size, key, frame=None):
        c = Vector(center)
        x, y, z = [s/2 for s in size]
        vertices = [
            c+Vector((-x,-y,-z)), c+Vector((x,-y,-z)),
            c+Vector((x,y,-z)), c+Vector((-x,y,-z)),
            c+Vector((-x,-y,z)), c+Vector((x,-y,z)),
            c+Vector((x,y,z)), c+Vector((-x,y,z)),
        ]
        if frame is not None:
            vertices = [frame.p(*v) for v in vertices]
        faces = [
            (0,3,2,1), (4,5,6,7),
            (0,1,5,4), (1,2,6,5),
            (2,3,7,6), (3,0,4,7),
        ]
        self.indexed(vertices, faces, key)

    def ellipsoid(self, center, scale, key, rotation=None):
        center = Vector(center)
        vertices = []
        for p in ICO_V:
            q = Vector((p.x*scale[0], p.y*scale[1], p.z*scale[2]))
            if rotation is not None:
                q = rotation @ q
            vertices.append(center+q)
        self.indexed(vertices, ICO_F, key, True)

    def rod(self, a, b, radius, key, end_radius=None, sides=8):
        a, b = Vector(a), Vector(b)
        axis = b-a
        if axis.length < 1e-7:
            return
        axis.normalize()

        u = axis.cross(Vector((0,0,1)))
        if u.length < .01:
            u = axis.cross(Vector((0,1,0)))
        u.normalize()
        v = axis.cross(u).normalized()

        r2 = radius if end_radius is None else end_radius
        vertices = []

        for center, r in ((a, radius), (b, r2)):
            for i in range(sides):
                t = TAU*i/sides
                vertices.append(center+r*(u*math.cos(t)+v*math.sin(t)))

        faces = [
            (i, (i+1)%sides, (i+1)%sides+sides, i+sides)
            for i in range(sides)
        ]
        faces.extend([
            tuple(range(sides-1, -1, -1)),
            tuple(range(sides, sides*2))
        ])
        self.indexed(vertices, faces, key, True)

    def lathe(self, center, profile, key, segments=32):
        center = Vector(center)
        vertices = []
        for radius, z in profile:
            for i in range(segments):
                a = TAU*i/segments
                vertices.append(center+Vector((
                    radius*math.cos(a), radius*math.sin(a), z
                )))

        faces = []
        for j in range(len(profile)-1):
            for i in range(segments):
                ni = (i+1)%segments
                faces.append((
                    j*segments+i, j*segments+ni,
                    (j+1)*segments+ni, (j+1)*segments+i
                ))

        faces.append(tuple(range(segments-1, -1, -1)))
        start = (len(profile)-1)*segments
        faces.append(tuple(start+i for i in range(segments)))
        self.indexed(vertices, faces, key, True)

    def leaf(self, origin, direction, length, width, key, curl=.12):
        origin = Vector(origin)
        direction = Vector(direction)
        if direction.length < .001:
            direction = Vector((1,0,.1))
        direction.normalize()

        side = direction.cross(Vector((0,0,1)))
        if side.length < .01:
            side = Vector((1,0,0))
        side.normalize()

        middle = origin+direction*length*.54+Vector((0,0,curl*length))
        tip = origin+direction*length
        ridge = middle+Vector((0,0,width*.24))

        self.face([origin, middle-side*width, ridge], key)
        self.face([middle-side*width, tip, ridge], key)
        self.face([tip, middle+side*width, ridge], key)
        self.face([middle+side*width, origin, ridge], key)

    def mesh(self, name):
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(self.v, [], self.f)
        mesh.update()

        for key in self.keys:
            mesh.materials.append(MAT[key])

        for poly, mid, smooth in zip(mesh.polygons, self.ids, self.smooth):
            poly.material_index = mid
            poly.use_smooth = smooth

        return mesh

    def object(self, name, group, bevel=0):
        if not self.v:
            return None
        obj = link_object(name, self.mesh(name), group)
        if bevel:
            mod = obj.modifiers.new("边缘微倒角", "BEVEL")
            mod.width = bevel
            mod.segments = 2
            mod.limit_method = "ANGLE"
        return obj


CURVES = defaultdict(list)


def line(points, key="bronze", radius=.02,
         group="05_门窗雕饰", closed=False):
    if len(points) < 2:
        return
    bucket = (group, key, round(radius, 4))
    CURVES[bucket].append(([tuple(p) for p in points], closed))


def local_line(frame, points, key="bronze", radius=.02,
               group="05_门窗雕饰", closed=False):
    line([frame.p(*p) for p in points], key, radius, group, closed)


def circle(center, radius, normal=(0,0,1), key="bronze",
           tube=.02, group="05_门窗雕饰", segments=48):
    center = Vector(center)
    q = Vector((0,0,1)).rotation_difference(Vector(normal).normalized())
    line([
        center+q@Vector((
            radius*math.cos(TAU*i/segments),
            radius*math.sin(TAU*i/segments), 0
        ))
        for i in range(segments)
    ], key, tube, group, True)


def catmull(points, resolution=8):
    p = [Vector(points[0])] + [Vector(v) for v in points] + [Vector(points[-1])]
    out = []
    for i in range(1, len(p)-2):
        a,b,c,d = p[i-1:i+3]
        for j in range(resolution):
            t = j/resolution
            out.append(.5*(
                2*b+(-a+c)*t+
                (2*a-5*b+4*c-d)*t*t+
                (-a+3*b-3*c+d)*t*t*t
            ))
    out.append(Vector(points[-1]))
    return out


def flush_curves():
    for (group, key, radius), paths in CURVES.items():
        data = bpy.data.curves.new("合批曲线_"+key, "CURVE")
        data.dimensions = "3D"
        data.resolution_u = 1
        data.bevel_depth = radius
        data.bevel_resolution = 1 if QUALITY == "STUDY" else 2
        data.use_fill_caps = True

        for points, closed in paths:
            spline = data.splines.new("POLY")
            spline.points.add(len(points)-1)
            for p, co in zip(spline.points, points):
                p.co = (*co, 1)
            spline.use_cyclic_u = closed

        data.materials.append(MAT[key])
        link_object("线饰_"+key, data, group)

    CURVES.clear()


# =============================================================================
# 04. 场地规则
# =============================================================================

PONDS = [
    (-23.8, -.8, 4.9, 8.5),
    (23.8, 3.0, 5.2, 8.8),
]

EXCLUSIONS = []
PATH_SEGMENTS = []


def pond_distance(x, y, pond):
    px, py, rx, ry = pond
    return math.sqrt(((x-px)/rx)**2+((y-py)/ry)**2)


def ground_z(x, y):
    z = 4.02
    z += .13*math.sin(x*.31)*math.cos(y*.25)
    z += .075*math.sin(x*.87+y*.51)
    z += 2.7*math.exp(-((x+26)**2/28+(y-19)**2/48))
    z += 3.3*math.exp(-((x-26)**2/29+(y-22)**2/46))
    z += 1.8*math.exp(-((x+8)**2/95+(y-32)**2/17))

    if abs(x) < 17.5 and -16.5 < y < 26:
        z = 4.02

    for pond in PONDS:
        d = pond_distance(x,y,pond)
        if d < 1:
            z -= 2.0*(1-d*d)**.60
    return z


def reserve(frame, width, depth, padding=.5):
    EXCLUSIONS.append((frame, width/2+padding, depth/2+padding))


def in_building(x, y, margin=0):
    for frame, hw, hd in EXCLUSIONS:
        xx, yy = frame.inverse_xy(x,y)
        if abs(xx) < hw+margin and abs(yy) < hd+margin:
            return True
    return False


def segment_distance(x, y, a, b):
    p = Vector((x,y,0))
    a = Vector((a[0],a[1],0))
    b = Vector((b[0],b[1],0))
    d = b-a
    if d.length_squared < 1e-8:
        return (p-a).length
    t = max(0, min(1, (p-a).dot(d)/d.length_squared))
    return (p-(a+d*t)).length


def near_path(x, y, padding=.2):
    return any(
        segment_distance(x,y,a,b) < width+padding
        for a,b,width in PATH_SEGMENTS
    )


def valid_garden(x, y, tree=False, margin=0):
    if (x/RX)**2+((y-CY)/RY)**2 > .91**2:
        return False
    if abs(x) < 17.5 and -16.5 < y < 26:
        return False
    if abs(x) < 3.8 and y < -14:
        return False
    if in_building(x,y,margin):
        return False
    if any(pond_distance(x,y,p) < (1.16 if tree else 1.07) for p in PONDS):
        return False
    if near_path(x,y,.65 if tree else .18):
        return False
    return True


# =============================================================================
# 05. 主山与崖壁
# =============================================================================

def main_island():
    n = P["terrain_n"]
    rings = P["terrain_rings"]
    vertices = [(0,CY,ground_z(0,CY))]
    faces = []
    mids = []

    def outline(i):
        return 1+.022*math.sin(i*.69)+.014*math.sin(i*1.91)

    for j in range(1,rings+1):
        t = j/rings
        for i in range(n):
            a = TAU*i/n
            k = 1+(outline(i)-1)*t*t
            x = RX*t*k*math.cos(a)
            y = CY+RY*t*k*math.sin(a)
            vertices.append((x,y,ground_z(x,y)))

    for i in range(n):
        faces.append((0,1+i,1+(i+1)%n))
        mids.append(0)

    for j in range(rings-1):
        a = 1+j*n
        b = a+n
        for i in range(n):
            ni = (i+1)%n
            faces.extend([(a+i,b+i,b+ni),(a+i,b+ni,a+ni)])
            mids.extend((0,0))

    previous = 1+(rings-1)*n
    strata = [
        (3.0,1.02), (.6,1.0), (-2.8,.92),
        (-6.4,.80), (-10.7,.64), (-14.6,.44),
        (-18.1,.24), (-20.7,.055),
    ]

    for layer,(z,radius) in enumerate(strata):
        start = len(vertices)
        for i in range(n):
            a = TAU*i/n
            k = outline(i)*(1+.037*math.sin(i*1.33+layer*.7))
            vertices.append((
                RX*radius*k*math.cos(a)+layer*.26,
                CY+RY*radius*k*math.sin(a),
                z+.43*math.sin(i*.77+layer)+.19*math.sin(i*2.7)
            ))

        for i in range(n):
            ni = (i+1)%n
            faces.extend([
                (previous+i,start+i,start+ni),
                (previous+i,start+ni,previous+ni),
            ])
            mids.extend((1,1))
        previous = start

    tip = len(vertices)
    vertices.append((2,CY,-22))
    for i in range(n):
        faces.append((previous+i,tip,previous+(i+1)%n))
        mids.append(1)

    mesh = bpy.data.meshes.new("主山地形")
    mesh.from_pydata(vertices,[],faces)
    mesh.materials.append(MAT["earth"])
    mesh.materials.append(MAT["rock"])
    mesh.update()

    for poly,mid in zip(mesh.polygons,mids):
        poly.material_index = mid
        poly.use_smooth = mid == 0

    link_object("太微主悬山",mesh,"01_山体地形")


main_island()

cliff = Geo()
for i in range(110 if QUALITY != "STUDY" else 42):
    a = R_LAND.uniform(0,TAU)
    radius = R_LAND.uniform(.93,1.01)
    x = RX*radius*math.cos(a)
    y = CY+RY*radius*math.sin(a)
    z = R_LAND.uniform(-5,1.6)

    cliff.ellipsoid(
        (x,y,z),
        (R_LAND.uniform(.45,1.05),
         R_LAND.uniform(.45,.95),
         R_LAND.uniform(1.2,2.9)),
        "rock"
    )
    if i % 4 == 0:
        cliff.ellipsoid((x,y,z+1.1),(.52,.43,.10),"moss")

cliff.object("崖壁石柱苔皮","01_山体地形")
report("主山完成")


# =============================================================================
# 06. 台基、铺装、御道
# =============================================================================

def terrace(name, x, y, z, width, depth, height, ornate=False):
    g = Geo()
    bottom = z-height
    # 圭角/下枋/下枭/束腰/上枭/上枋 ≈ 10:8:6:8:6:9
    bands = [
        (.07,.14,.86,"stone"),
        (.18,.12,.58,"ivory"),
        (.30,.10,.38,"ivory"),
        (.48,.24,.00,"stone"),
        (.66,.10,.28,"ivory"),
        (.80,.16,.52,"ivory"),
    ]
    for center,thickness,extra,key in bands:
        g.box(
            (x,y,bottom+height*center),
            (width+extra,depth+extra,height*thickness),
            key
        )
    g.box((x,y,z-.03),(width+.33,depth+.33,.06),"ivory")
    if ornate:
        waist_z = bottom + height * 0.48
        for i in range(6):
            t = (i + 0.5) / 6
            xx = x - width * 0.38 + width * 0.76 * t
            g.box((xx, y + depth * 0.02, waist_z), (width * 0.09, 0.12, height * 0.16), "ivory")
        hw, hd = width * 0.52, depth * 0.52
        for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            mouth = (x + sx * hw, y + sy * hd, bottom + height * 0.42)
            g.ellipsoid(mouth, (0.38, 0.28, 0.22), "stone")
            g.ellipsoid(
                (mouth[0] + sx * 0.28, mouth[1] + sy * 0.22, mouth[2] - 0.04),
                (0.22, 0.16, 0.12),
                "ivory",
            )
            g.rod(
                mouth,
                (mouth[0] + sx * 0.55, mouth[1] + sy * 0.42, mouth[2] - 0.22),
                0.07, "ivory", 0.04, 8
            )
    g.object(name,"02_台基庭院",.024)


terrace("宫城五叠总台",0,5.0,COURT_Z,32.4,40.2,1.46)
terrace("正殿须弥高台",0,13.8,MAIN_Z,18.0,13.8,MAIN_Z-COURT_Z, ornate=KIT["xumizuo"])
terrace("后苑台",0,25.0,BACK_Z,29.5,5.5,BACK_Z-COURT_Z)

paving = Geo()
rng_pave = random.Random(SEED+77)
STEP_X, STEP_Y = 1.48, 0.92
for iy in range(-22, 23):
    y = 5.0 + iy * STEP_Y
    if y < -14.6 or y > 24.6:
        continue
    row_offset = (iy % 2) * (STEP_X * 0.5)
    for ix in range(-14, 14):
        x = (ix + 0.5) * STEP_X + row_offset
        if abs(x) > 15.9:
            continue
        if abs(x) < 9.2 and 6.7 < y < 20.9:
            continue
        if abs(x) < 1.78:
            continue
        near_wall = min(15.9 - abs(x), y + 14.6, 24.6 - y) < 1.8
        zoff = rng_pave.gauss(0, 0.0035)
        if rng_pave.random() < 0.025:
            zoff -= rng_pave.uniform(0.012, 0.025)
        gap = rng_pave.uniform(0.014, 0.038 if near_wall else 0.022)
        sx, sy = STEP_X - gap, STEP_Y - gap
        # 全场统一青石大板，仅靠墙根偶见苔痕，杜绝补丁感
        if near_wall:
            key = "moss" if rng_pave.random() < 0.15 else "stone"
        else:
            key = "stone"
        paving.box((x, y, COURT_Z + 0.015 + zoff), (sx, sy, 0.035), key)
        if rng_pave.random() < 0.04:
            paving.box(
                (x + sx * 0.22, y, COURT_Z + 0.012 + zoff),
                (sx * 0.42, sy * 0.48, 0.03),
                "stone",
            )
paving.object("庭院分缝石板","02_台基庭院")

axis = Geo()
axis.box((0,-.7,COURT_Z+.065),(3.1,25.4,.08),"stone")
for side in (-1,1):
    axis.box((side*1.61,-.7,COURT_Z+.08),(.095,25.4,.065),"ivory")
axis.object("中轴御道","02_台基庭院",.008)


# =============================================================================
# 07. 装饰语汇与栏杆
# =============================================================================

def cloud_scroll(frame,x,y,z,scale=.5,key="bronze"):
    spiral = []
    for i in range(45):
        t = i/44
        a = -.25+TAU*1.15*t
        radius = .43*scale*(1-.82*t)
        spiral.append((x+radius*math.cos(a),y,z+radius*math.sin(a)))
    local_line(frame,spiral,key,.018*scale)

    for sign in (-1,1):
        controls = [
            frame.p(x+sign*.14*scale,y,z-.10*scale),
            frame.p(x+sign*.49*scale,y,z-.23*scale),
            frame.p(x+sign*.79*scale,y,z-.02*scale),
            frame.p(x+sign*1.02*scale,y,z-.08*scale),
        ]
        line(catmull(controls,6),key,.018*scale)


def fret_band(frame,x0,x1,y,z,cell=.48,height=.14,key="bronze"):
    count = max(1,int((x1-x0)/cell))
    step = (x1-x0)/count
    for i in range(count):
        x = x0+i*step
        local_line(frame,[
            (x,y,z),
            (x+step*.82,y,z),
            (x+step*.82,y,z+height),
            (x+step*.22,y,z+height),
            (x+step*.22,y,z+height*.42),
            (x+step*.58,y,z+height*.42),
        ],key,.011)


def railing(a,b,height=.87,spacing=1.3,ornate=True):
    a,b = Vector(a),Vector(b)
    delta = b-a
    length = delta.length
    if length < .01:
        return
    direction = delta.normalized()
    count = max(1,int(length/spacing))
    g = Geo()

    for i in range(count+1):
        p = a.lerp(b,i/count)
        g.box(p+Vector((0,0,.075)),(.23,.23,.15),"balustrade")
        g.box(p+Vector((0,0,height*.46)),(.13,.13,height*.9),"balustrade")
        g.lathe(p,[
            (.10,height*.90),
            (.13,height*.97),
            (.083,height*1.07),
            (.023,height*1.13),
        ],"balustrade",16)

    for z,r,key in [(.24,.036,"balustrade"),(.65,.042,"balustrade"),(height*.89,.049,"balustrade")]:
        line([a+Vector((0,0,z)),b+Vector((0,0,z))],key,r)

    if ornate:
        for i in range(count):
            center = a.lerp(b,(i+.5)/count)+Vector((0,0,.445))
            half = length/count*.28
            line([
                center-direction*half,
                center+Vector((0,0,.15)),
                center+direction*half,
                center-Vector((0,0,.15)),
            ],"balustrade",.020,closed=True)

    g.object("莲头青石栏杆","05_门窗雕饰",.004)


for x in (-15.8,15.8):
    railing((x,-14.7,COURT_Z),(x,24.0,COURT_Z))
railing((-15.8,-14.7,COURT_Z),(-3,-14.7,COURT_Z))
railing((3,-14.7,COURT_Z),(15.8,-14.7,COURT_Z))
railing((-15.1,27.1,BACK_Z),(15.1,27.1,BACK_Z))

for side in (-1,1):
    railing((side*8.74,7.05,MAIN_Z),(side*8.74,20.35,MAIN_Z))
    railing((side*3.25,7.05,MAIN_Z),(side*8.74,7.05,MAIN_Z))

front_frame = Frame(0,-15.35,4.75)
for x in range(-13,14,2):
    cloud_scroll(front_frame,x,-.02,.1,.54)

for radius in (1.15,1.0,.36):
    circle((0,-4.8,COURT_Z+.11),radius,key="bronze",
           tube=.015,group="02_台基庭院")
for i in range(8):
    a = TAU*i/8
    line([
        (r*math.cos(a),-4.8+r*math.sin(a),COURT_Z+.11)
        for r in (.46,.82)
    ],"bronze",.020,"02_台基庭院")


# =============================================================================
# 08. 四坡屋顶与分行筒瓦
# =============================================================================

def roof_border(side,u):
    if side == 0:
        return -1+2*u,-1
    if side == 1:
        return 1,-1+2*u
    if side == 2:
        return 1-2*u,1
    return -1,1-2*u


def roof_xyz(width,depth,z,rise,side,u,t,lift=0,ridge_ratio=0.47):
    """Local (x, y, z) on the hip-roof surface. t=0 ridge, t=1 eave."""
    half_w,half_d = width/2,depth/2
    ridge_half = half_w*ridge_ratio
    px,py = roof_border(side,u)
    corner = abs(px*py)**3.4
    x = px*(ridge_half+(half_w-ridge_half)*t)
    y = py*half_d*t
    zz = (
        z+rise*(1-t)**1.28
        +rise*.10*t**4
        +rise*.16*corner*t**5
        +lift
    )
    return x,y,zz


def roof_z_at_local(width,depth,z,rise,lx,ly,lift=-.02,ridge_ratio=0.47):
    """Roof surface Z at a local plan point, using the same hip parameterization."""
    half_w,half_d = max(width/2,1e-6),max(depth/2,1e-6)
    t = min(1.0,max(abs(lx)/half_w,abs(ly)/half_d))
    if abs(ly)*half_w >= abs(lx)*half_d:
        side = 0 if ly < 0 else 2
        span = half_w*ridge_ratio+(half_w-half_w*ridge_ratio)*t
        px = lx/max(span,1e-6)
        u = (px+1)*.5 if side == 0 else (1-px)*.5
    else:
        side = 1 if lx > 0 else 3
        u = (ly/half_d+1)*.5 if side == 1 else (1-ly/half_d)*.5
    u = min(1.0,max(0.0,u))
    _x,_y,zz = roof_xyz(width,depth,z,rise,side,u,t,lift,ridge_ratio)
    return zz


def seal_wall_to_roof(geo,frame,wall_w,wall_d,wall_top,roof_w,roof_d,roof_z,rise,key="wall",ridge_ratio=0.47):
    """Vertical 山花/额枋垫板 from the flat wall top up to the roof shell."""
    hw,hd = wall_w/2,wall_d/2
    edges = [
        [(-hw,-hd),(hw,-hd)],
        [(hw,-hd),(hw,hd)],
        [(hw,hd),(-hw,hd)],
        [(-hw,hd),(-hw,-hd)],
    ]
    samples = max(10,int(max(wall_w,wall_d)/.45))
    for (a,b) in edges:
        prev_bottom = prev_top = None
        for i in range(samples+1):
            t = i/samples
            lx = a[0]+(b[0]-a[0])*t
            ly = a[1]+(b[1]-a[1])*t
            rz = max(wall_top+.04,roof_z_at_local(roof_w,roof_d,roof_z,rise,lx,ly,-.03,ridge_ratio))
            bottom = frame.p(lx,ly,wall_top-.02)
            top = frame.p(lx,ly,rz)
            if prev_bottom is not None:
                geo.face([prev_bottom,bottom,top,prev_top],key)
            prev_bottom,prev_top = bottom,top


def soffit(geo,frame,width,depth,z,key="beam"):
    """望板：封住柱头到出檐的黑腔。"""
    geo.box((0,0,z),(width,depth,.055),key,frame)


CEJIAO_FRONT = 0.008
CEJIAO_SIDE = 0.010
SHENGQI_EXP = 1.6
ENTASIS_SPLIT = 0.67
ENTASIS_TOP = 0.88
OVERHANG_RATIO = 0.55


def shengqi_scale(i, n, smax=0.022):
    if n <= 1:
        return 1.0
    u = (2.0 * i - (n - 1)) / (n - 1)
    return 1.0 + smax * abs(u) ** SHENGQI_EXP


def cejiao_delta(xx, yy, height, end_x):
    dx = -math.copysign(height * CEJIAO_FRONT, xx) if end_x else 0.0
    dy = -math.copysign(height * CEJIAO_SIDE, yy)
    return dx, dy


def _perp_xy(direction):
    d = Vector(direction)
    d.z = 0
    if d.length < 1e-6:
        d = Vector((1, 0, 0))
    d.normalize()
    return Vector((-d.y, d.x, 0))


def add_ridge_beast(geo, origin, along, scale=0.11, lead=False, form=(1.0, 1.3)):
    """A seated ceramic beast, not a stacked pebble. form=(体宽比, 体高比) 分形态。"""
    along = Vector(along)
    along.z = 0
    if along.length < 1e-6:
        along = Vector((0, 1, 0))
    along.normalize()
    side = _perp_xy(along)
    origin = Vector(origin)
    fx, fz = form
    body = origin + Vector((0, 0, scale * 0.55 * fz))
    geo.ellipsoid(body, (scale * 0.42 * fx, scale * 0.55 * fx, scale * 0.48 * fz), "tile_light")
    geo.ellipsoid(body + along * scale * 0.38 + Vector((0, 0, scale * 0.28 * fz)),
                  (scale * 0.28 * fx, scale * 0.32 * fx, scale * 0.30 * fz), "gold" if lead else "patina")
    geo.ellipsoid(body - along * scale * 0.42 + Vector((0, 0, scale * 0.18)),
                  (scale * 0.18 * fx, scale * 0.22 * fx, scale * 0.16), "patina")
    geo.rod(body + side * scale * 0.22, body + side * scale * 0.22 + Vector((0, 0, -scale * 0.55 * fz)),
            scale * 0.07, "tile_light", scale * 0.05, 6)
    geo.rod(body - side * scale * 0.22, body - side * scale * 0.22 + Vector((0, 0, -scale * 0.55 * fz)),
            scale * 0.07, "tile_light", scale * 0.05, 6)


def add_chiwen(geo, frame, side, ridge_half, z, rise):
    """Fish-dragon lying on the ridge: mouth clamps the beam, body coils inward and up."""
    sx = side
    origin = frame.p(sx * ridge_half, 0, z + rise + 0.06)
    mouth = origin + frame.d(sx * 0.28, 0, 0.02)
    jaw_l = mouth + frame.d(sx * 0.18, 0.10, -0.08)
    jaw_r = mouth + frame.d(sx * 0.18, -0.10, -0.08)
    choke = origin + frame.d(sx * 0.02, 0, 0.10)
    belly = origin + frame.d(-sx * 0.22, 0, 0.28)
    coil = origin + frame.d(-sx * 0.38, 0, 0.62)
    tail = origin + frame.d(-sx * 0.10, 0, 0.92)
    fin_tip = origin + frame.d(sx * 0.08, 0, 1.08)
    geo.ellipsoid(mouth, (0.24, 0.18, 0.16), "gold")
    geo.rod(mouth, jaw_l, 0.055, "tile_light", 0.02, 8)
    geo.rod(mouth, jaw_r, 0.055, "tile_light", 0.02, 8)
    geo.rod(mouth, origin + frame.d(-sx * 0.16, 0, -0.10), 0.05, "tile_light", 0.04, 8)
    spine = [mouth, choke, belly, coil, tail, fin_tip]
    radii = (0.15, 0.18, 0.16, 0.12, 0.08, 0.04)
    for a, b, ra, rb in zip(spine, spine[1:], radii, radii[1:]):
        geo.rod(a, b, ra, "tile_light", rb, 10)
    geo.ellipsoid(belly + Vector((0, 0, 0.18)), (0.07, 0.04, 0.16), "patina")
    geo.ellipsoid(coil + Vector((0, 0, 0.16)), (0.06, 0.03, 0.14), "gold")
    geo.ellipsoid(tail, (0.08, 0.06, 0.12), "patina")
    geo.ellipsoid(fin_tip, (0.05, 0.04, 0.10), "gold")


def add_chiwen_v3(geo, frame, side, ridge_half, z, rise):
    """扫描级鱼龙大吻：张口吞脊、鳞身内卷、扇尾外扬（蓝本 guide-chiwen-scan）。"""
    sx = side
    base = frame.p(sx * ridge_half, 0, z + rise + 0.04)
    D = frame.d

    # 头：张口吞脊
    snout = base + D(sx * 0.30, 0, 0.16)
    geo.ellipsoid(snout, (0.20, 0.17, 0.15), "tile_light")
    skull = base + D(sx * 0.12, 0, 0.24)
    geo.ellipsoid(skull, (0.24, 0.20, 0.20), "tile_light")
    upper = base + D(sx * 0.26, 0, 0.06)
    geo.ellipsoid(upper, (0.16, 0.15, 0.07), "gold")
    lower = base + D(sx * 0.20, 0, -0.04)
    geo.ellipsoid(lower, (0.14, 0.13, 0.05), "gold")
    for sy in (-1, 1):
        geo.ellipsoid(skull + D(sx * 0.10, sy * 0.15, 0.06),
                      (0.045, 0.04, 0.045), "gold")
        geo.ellipsoid(skull + D(sx * 0.10, sy * 0.17, 0.06),
                      (0.022, 0.02, 0.022), "feather_dark")
        geo.rod(upper + D(sx * 0.06, sy * 0.10, -0.02),
                upper + D(sx * 0.10, sy * 0.10, -0.12),
                0.025, "ivory", 0.006, 6)
    # 双角后掠
    for sy in (-1, 1):
        h0 = skull + D(-sx * 0.02, sy * 0.08, 0.14)
        h1 = skull + D(-sx * 0.20, sy * 0.13, 0.38)
        h2 = skull + D(-sx * 0.30, sy * 0.15, 0.58)
        geo.rod(h0, h1, 0.045, "gold", 0.028, 8)
        geo.rod(h1, h2, 0.028, "gold", 0.008, 8)

    # 躯干：沿脊内卷
    spine = [
        base + D(sx * 0.05, 0, 0.10),
        base + D(-sx * 0.12, 0, 0.34),
        base + D(-sx * 0.30, 0, 0.62),
        base + D(-sx * 0.46, 0, 0.92),
        base + D(-sx * 0.36, 0, 1.22),
        base + D(-sx * 0.12, 0, 1.44),
    ]
    radii = (0.17, 0.19, 0.16, 0.13, 0.10, 0.06)
    for a, b, ra, rb in zip(spine, spine[1:], radii, radii[1:]):
        geo.rod(a, b, ra, "tile_light", rb, 10)
    # 鳞甲覆片
    for k, p in enumerate(spine[1:-1]):
        r = radii[k + 1]
        for sy in (-1, 0):
            off = D(0, sy * r * 0.7, r * (0.75 if sy == 0 else 0.35))
            geo.ellipsoid(p + off, (0.055, 0.035, 0.028),
                          "patina" if k % 2 else "tile_dark")
    # 背鳍立板
    for k, p in enumerate(spine[1:]):
        fin_h = 0.16 - 0.02 * k
        geo.ellipsoid(p + D(0, 0, radii[k + 1] + fin_h * 0.6),
                      (0.030, 0.075, fin_h), "gold")
    # 扇尾外扬
    tail_root = spine[-1]
    for k in range(5):
        spread = (k - 2) * 0.24
        lift = 0.26 + 0.05 * abs(k - 2)
        tip = tail_root + D(sx * (0.16 + 0.05 * k), spread, lift + 0.16)
        geo.rod(tail_root + D(0, 0, 0.04), tip, 0.030, "gold", 0.010, 6)
        geo.ellipsoid(tip, (0.045, 0.055, 0.10),
                      "tile_light" if k % 2 else "gold")
    geo.ellipsoid(tail_root + D(sx * 0.10, 0, 0.30),
                  (0.06, 0.10, 0.22), "tile_light")
    # 吞脊底座
    geo.ellipsoid(base + D(sx * 0.02, 0, 0.02), (0.22, 0.19, 0.10), "tile_light")


def roof(frame,z,width,depth,rise,name,imperial=False,ridge_ratio=0.47,ornaments=True):
    ridge_half = (width/2)*ridge_ratio
    border = roof_border

    def point(side,u,t,lift=0):
        x,y,zz = roof_xyz(width,depth,z,rise,side,u,t,lift,ridge_ratio)
        return frame.p(x,y,zz)

    shell,tiles,detail = Geo(),Geo(),Geo()
    edge_steps = max(12,int(max(width,depth)/.43))
    slope_steps = 19

    for side in range(4):
        for i in range(edge_steps):
            u0,u1 = i/edge_steps,(i+1)/edge_steps
            for j in range(slope_steps):
                t0 = .006+.994*j/slope_steps
                t1 = .006+.994*(j+1)/slope_steps
                shell.face([
                    point(side,u0,t0),
                    point(side,u0,t1),
                    point(side,u1,t1),
                    point(side,u1,t0),
                ],"roof",True)

            shell.face([
                point(side,u0,1),
                point(side,u0,1,-.14),
                point(side,u1,1,-.14),
                point(side,u1,1),
            ],"beam")

        line([
            point(side,i/edge_steps,1,.017)
            for i in range(edge_steps+1)
        ],"tile_light",.044,"04_琉璃瓦作")

        if imperial:
            line([
                point(side,i/edge_steps,1,-.050)
                for i in range(edge_steps+1)
            ],"bronze",.013,"04_琉璃瓦作")

    # 顶部狭缝由正脊覆盖；额外封面避免漏光
    cap = []
    for side in range(4):
        cap.extend(point(side,i/edge_steps,.006) for i in range(edge_steps))
    shell.face(cap,"roof")
    shell.object(name+"_屋面封檐","04_琉璃瓦作")

    if ENABLE_TILE_GEOMETRY:
        for side in range(4):
            edge_length = width if side%2 == 0 else depth
            columns = max(6,int(edge_length/P["tile_spacing"]))
            rows = max(6,int(P["tile_rows"]*min(1.4,depth/6.5)))

            for column in range(columns):
                ua = (column+.10)/columns
                ub = (column+.90)/columns
                key = R_ARCH.choices(
                    ["tile","tile_light","tile_dark"],[.78,.14,.08]
                )[0]

                for row in range(rows):
                    t0 = .044+.956*row/rows
                    t1 = min(1,.044+.956*(row+1)/rows+.004)

                    for cross in range(P["tile_cross"]):
                        s0 = cross/P["tile_cross"]
                        s1 = (cross+1)/P["tile_cross"]
                        u0 = ua+(ub-ua)*s0
                        u1 = ua+(ub-ua)*s1
                        h0 = .019+.039*math.sin(math.pi*s0)
                        h1 = .019+.039*math.sin(math.pi*s1)

                        tiles.face([
                            point(side,u0,t0,h0+.008),
                            point(side,u0,t1,h0),
                            point(side,u1,t1,h1),
                            point(side,u1,t0,h1+.008),
                        ],key,True)

                    if row == rows-1:
                        p = point(side,(ua+ub)/2,1,-.016)
                        disc = .072 if imperial else .048
                        drop = .086 if imperial else .058
                        detail.ellipsoid(p,(disc,disc,drop),"tile_light")
                        if imperial:
                            detail.ellipsoid(
                                p+frame.d(0,0,-drop*.55),
                                (disc*.42,disc*.42,drop*.38),
                                "gold"
                            )

        tiles.object(name+"_分行筒瓦","04_琉璃瓦作")

    local_line(frame,[
        (-ridge_half-.28,0,z+rise+.27),
        (-ridge_half,0,z+rise+.10),
        (ridge_half,0,z+rise+.10),
        (ridge_half+.28,0,z+rise+.27),
    ],"tile_light",.095,"04_琉璃瓦作")

    if imperial:
        local_line(frame,[
            (-ridge_half,0,z+rise+.19),
            (ridge_half,0,z+rise+.19),
        ],"gold",.016,"04_琉璃瓦作")

    for side in range(4):
        line([
            point(side,0,.044+.956*i/28,.034)
            for i in range(29)
        ],"tile_light",.071,"04_琉璃瓦作")

        px,py = border(side,0)
        corner = point(side,0,1)
        tip = corner+frame.d(px*.21,py*.21,.33)
        line([
            point(side,0,.84),corner,tip
        ],"tile_light",.067,"04_琉璃瓦作")

        gable_side = ridge_ratio > 0.55 and side % 2 == 1
        if ornaments and not gable_side:
            along = frame.d(px, py, 0)
            if along.length > 1e-6:
                along.normalize()
            else:
                along = Vector((0, 1, 0))
            if imperial:
                detail.ellipsoid(tip,(.09,.09,.11),"gold")
                beast_count = (7 if width > 10 else 5) if KIT["chiwen_v2"] else (5 if width > 10 else 3)
                forms = ((1.00,1.55),(0.82,1.25),(1.12,1.05),(0.72,1.40),(0.92,1.15),(0.78,1.28),(0.66,1.10))
                for i in range(beast_count):
                    t = .58 + .32*i/max(1,beast_count-1)
                    p = point(side,0,t,.14)
                    add_ridge_beast(detail, p, along, .11 - .008*i,
                                    lead=(i == 0), form=forms[i % len(forms)])
            else:
                for t in (.79,.90):
                    p = point(side,0,t,.11)
                    add_ridge_beast(detail, p, along, .09, lead=False)

            bell = corner+Vector((0,0,-.43))
            line([corner,bell],"bell_bronze",.0075)
            detail.rod(
                bell+Vector((0,0,-.115)),
                bell+Vector((0,0,.035)),
                .074,"bell_bronze",.039,10
            )
            detail.ellipsoid(
                bell+Vector((0,0,-.145)),
                (.020,.020,.030),"bell_bronze"
            )

    if not ornaments:
        detail.object(name+"_瓦当吻兽风铃","05_门窗雕饰")
        return z+rise

    for side in (-1,1):
        if imperial and KIT["chiwen_v3"]:
            add_chiwen_v3(detail, frame, side, ridge_half, z, rise)
        elif imperial and KIT["chiwen_v2"]:
            add_chiwen(detail, frame, side, ridge_half, z, rise)
        elif imperial:
            controls = [
                frame.p(side*(ridge_half-.06),0,z+rise+.12),
                frame.p(side*(ridge_half+.28),0,z+rise+.48),
                frame.p(side*(ridge_half+.22),0,z+rise+.92),
                frame.p(side*(ridge_half+.02),0,z+rise+1.18),
                frame.p(side*(ridge_half-.18),0,z+rise+1.08),
            ]
            line(catmull(controls,10),"tile_light",.13,"04_琉璃瓦作")
            mouth = controls[-1]
            detail.ellipsoid(mouth,(.22,.18,.16),"tile_light")
            detail.ellipsoid(mouth+Vector((0,0,.14)),(.12,.10,.11),"gold")
        else:
            controls = [
                frame.p(side*(ridge_half-.04),0,z+rise+.10),
                frame.p(side*(ridge_half+.17),0,z+rise+.36),
                frame.p(side*(ridge_half+.09),0,z+rise+.65),
                frame.p(side*(ridge_half-.12),0,z+rise+.72),
            ]
            line(catmull(controls,7),"tile_light",.095,"04_琉璃瓦作")
            detail.ellipsoid(controls[-1],(.115,.105,.09),"tile_light")

    detail.object(name+"_瓦当吻兽风铃","05_门窗雕饰")
    return z+rise


# =============================================================================
# 09. 斗拱、雀替、格扇、门环
# =============================================================================

def _prism(g,frame,x,y,z,profile,half_w,key):
    """Extrude a YZ profile along X. profile is [(y,z), ...] in local offsets."""
    left = [frame.p(x-half_w,y+py,z+pz) for py,pz in profile]
    right = [frame.p(x+half_w,y+py,z+pz) for py,pz in profile]
    g.face(left,key)
    g.face(list(reversed(right)),key)
    n = len(profile)
    for i in range(n):
        j = (i+1)%n
        g.face([left[i],left[j],right[j],right[i]],key)


def _prism_y(g,frame,x,y,z,profile,half_d,key):
    """Extrude an XZ profile along Y. profile is [(x,z), ...] in local offsets."""
    front = [frame.p(x+px,y-half_d,z+pz) for px,pz in profile]
    back = [frame.p(x+px,y+half_d,z+pz) for px,pz in profile]
    g.face(front,key)
    g.face(list(reversed(back)),key)
    n = len(profile)
    for i in range(n):
        j = (i+1)%n
        g.face([front[i],front[j],back[j],back[i]],key)


def _gong_profile(length, s):
    return [
        (0.00 * length, 0.00 * s),
        (0.18 * length, 0.018 * s),
        (0.48 * length, 0.026 * s),
        (0.78 * length, 0.010 * s),
        (1.00 * length, -0.022 * s),
        (0.90 * length, -0.062 * s),
        (0.58 * length, -0.086 * s),
        (0.26 * length, -0.074 * s),
        (0.00 * length, -0.050 * s),
    ]


def _ludou(g, frame, x, y, z, s):
    """栌斗：耳 / 平 / 欹 约 8:4:8。"""
    g.box((x, y, z + 0.016 * s), (0.23 * s, 0.23 * s, 0.032 * s), "red", frame)
    g.box((x, y, z + 0.040 * s), (0.30 * s, 0.30 * s, 0.018 * s), "beam", frame)
    g.box((x, y, z + 0.066 * s), (0.34 * s, 0.34 * s, 0.028 * s), "red", frame)


def bracket(g, frame, x, y, z, scale=1, corner=False):
    """柱头铺作：两跳华栱 + 横栱 + 通长下昂。corner=True 时加 45° 角华栱。"""
    s = scale
    _ludou(g, frame, x, y, z, s)
    lengths = (0.40 * s, 0.62 * s)
    for jump, length in enumerate(lengths):
        zz = z + (0.12 + jump * 0.135) * s
        profile = _gong_profile(length, s)
        _prism(g, frame, x, y, zz, profile, 0.072 * s, "red")
        _prism(g, frame, x, y, zz, [(-py, pz) for py, pz in profile], 0.072 * s, "red")
        hx = (0.38 + jump * 0.14) * s
        heng = _gong_profile(hx, s)
        _prism_y(g, frame, x, y, zz, heng, 0.052 * s, "beam")
        _prism_y(g, frame, x, y, zz, [(-px, pz) for px, pz in heng], 0.052 * s, "beam")
        g.box((x + hx * 0.94, y, zz + 0.010 * s), (0.08 * s, 0.10 * s, 0.055 * s), "red", frame)
        g.box((x - hx * 0.94, y, zz + 0.010 * s), (0.08 * s, 0.10 * s, 0.055 * s), "red", frame)
    last_len = lengths[-1]
    last_z = z + 0.255 * s
    if KIT["through_ang"]:
        for sy in (-1, 1):
            g.rod(
                frame.p(x, y - sy * last_len * 0.15, last_z + 0.10 * s),
                frame.p(x, y + sy * last_len * 1.18, last_z - 0.16 * s),
                0.030 * s, "beam", 0.016 * s, 8
            )
    else:
        for sy in (-1, 1):
            g.rod(
                frame.p(x, y + sy * last_len * 0.62, last_z - 0.01 * s),
                frame.p(x, y + sy * last_len * 1.08, last_z - 0.085 * s),
                0.026 * s, "beam", 0.014 * s, 6
            )
    if corner and KIT["corner_bracket"]:
        g.ellipsoid(frame.p(x, y, z + 0.20 * s), (0.09 * s, 0.09 * s, 0.11 * s), "ivory")
        for jump in range(2):
            zz = z + (0.12 + jump * 0.135) * s
            reach = (0.42 + jump * 0.17) * s
            for sx, sy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                # 45° 角华栱（每跳一层）
                g.rod(
                    frame.p(x, y, zz + 0.02 * s),
                    frame.p(x + sx * reach, y + sy * reach, zz - 0.06 * s),
                    0.030 * s, "red", 0.016 * s, 6
                )
                # 角下昂
                g.rod(
                    frame.p(x + sx * 0.08 * s, y + sy * 0.08 * s, zz + 0.09 * s),
                    frame.p(x + sx * (reach + 0.14 * s), y + sy * (reach + 0.14 * s), zz - 0.10 * s),
                    0.022 * s, "beam", 0.011 * s, 6
                )
                # 交互斗
                g.box(
                    (x + sx * reach * 0.92, y + sy * reach * 0.92, zz - 0.03 * s),
                    (0.075 * s, 0.075 * s, 0.05 * s), "red", frame
                )
    g.box((x, y, z + 0.42 * s), (0.16 * s, 0.16 * s, 0.05 * s), "red", frame)
    g.box((x, y, z + 0.49 * s), (0.96 * s, 0.56 * s, 0.09 * s), "beam", frame)


def brace(g,frame,x,y,z,direction=1,scale=1):
    s = scale
    front = [
        frame.p(x,y-.045,z),
        frame.p(x+direction*.18*s,y-.045,z+.01*s),
        frame.p(x+direction*.40*s,y-.045,z-.04*s),
        frame.p(x+direction*.55*s,y-.045,z-.16*s),
        frame.p(x+direction*.42*s,y-.045,z-.28*s),
        frame.p(x+direction*.22*s,y-.045,z-.38*s),
        frame.p(x,y-.045,z-.42*s),
    ]
    back = [p+frame.d(0,.09,0) for p in front]

    g.face(front,"red")
    g.face(list(reversed(back)),"red")
    for i in range(len(front)):
        j = (i+1)%len(front)
        g.face([front[i],front[j],back[j],back[i]],"red")

    line(catmull([
        frame.p(x+direction*.08*s,y-.095,z-.08*s),
        frame.p(x+direction*.23*s,y-.095,z-.13*s),
        frame.p(x+direction*.37*s,y-.095,z-.05*s),
    ],6),"bronze",.009)


def lattice_window(g,frame,x,y,z,width,height,side=-1,lit=False):
    front = y+side*.043
    g.box((x,y,z),(width,.033,height),
          "window" if lit else "darkwood",frame)

    for dx in (-width/2,width/2):
        g.box((x+dx,front,z),(.053,.068,height+.07),"red",frame)
    for dz in (-height/2,height/2,-height*.22):
        g.box((x,front,z+dz),(width+.06,.068,.053),"red",frame)

    g.box((x,front,z-height*.35),
          (width-.045,.032,height*.25),"beam",frame)

    xmin,xmax = x-width*.43,x+width*.43
    zmin,zmax = z-height*.16,z+height*.43
    yy = front+side*.025
    bars = max(5,int(width/0.14))
    for i in range(bars):
        xx = xmin+(xmax-xmin)*(i+0.5)/bars
        local_line(frame,[(xx,yy,zmin),(xx,yy,zmax)],"red",.010)
    waist = z-height*.02
    local_line(frame,[(xmin,yy,waist),(xmax,yy,waist)],"beam",.014)

    cloud_scroll(
        frame,x,front+side*.023,z-height*.35,
        min(.29,width*.33),"bronze"
    )


def door_pair(g, frame, width, depth, height, studded=False, tall=False, open_degrees=0):
    y = -depth * .36 - .10
    total_width = width * .18
    h = height * (0.92 if tall else 0.78)
    bottom = 0.43

    # 抱框：门扇嵌进门框，不再孤悬
    for fx in (-1, 1):
        g.box((fx * total_width * .53, y + .02, bottom + h / 2),
              (.13, .13, h), "red", frame)
    g.box((0, y + .02, bottom + h + .07),
          (total_width * 1.18, .15, .16), "beam", frame)
    g.box((0, y + .02, bottom + .02),
          (total_width * 1.12, .16, .10), "ivory", frame)

    fixed_frame = frame
    for side in (-1, 1):
        # Rotate the complete leaf, including studs and ring, about its hinge.
        theta = math.radians(-side * open_degrees)
        hx = side * total_width * .495
        c, s = math.cos(theta), math.sin(theta)
        origin = fixed_frame.p(hx-c*hx+s*y, y-s*hx-c*y, 0)
        frame = Frame(*origin, fixed_frame.angle + theta)
        x = side * total_width * .255
        g.box((x, y, bottom + h / 2), (total_width * .48, .10, h), "red", frame)
        if studded:
            for row in range(5):
                for col in range(2):
                    g.ellipsoid(
                        frame.p(
                            x + (col - .5) * total_width * .18,
                            y - .065, .63 + row * h * .16
                        ),
                        (.022, .017, .022), "door_gold"
                    )
            center = frame.p(x, y - .095, bottom + h * .53)
            g.ellipsoid(center, (.074, .024, .095), "door_gold")
            circle(center + Vector((0, 0, -.061)), .065,
                   frame.d(0, -1, 0), "door_gold", .010, segments=24)
        else:
            leaf_w = total_width * .42
            # 格心
            lattice_window(
                g, frame, x, y + .02, bottom + h * 0.62,
                leaf_w, h * 0.42, -1, lit=True
            )
            # 绦环板
            g.box((x, y - .02, bottom + h * 0.36), (leaf_w * .92, .06, h * 0.12), "beam", frame)
            # 裙板
            g.box((x, y - .02, bottom + h * 0.16), (leaf_w * .92, .07, h * 0.22), "darkwood", frame)


# =============================================================================
# 10. 殿堂构造
# =============================================================================

def hall(name,x,y,z,width,depth,height,angle=0,
         open_hall=False,imperial=False,register=True,studded_doors=False,
         double_eave=False,xieshan=False):
    frame = Frame(x,y,z,angle)
    if register:
        reserve(frame,width+1.5,depth+1.4)

    stone,wood,ornament = Geo(),Geo(),Geo()

    stone.box((0,0,.10),(width+.70,depth+.70,.20),"stone",frame)
    stone.box((0,0,.25),(width+.42,depth+.42,.10),"ivory",frame)
    stone.box((0,0,.36),(width+.56,depth+.56,.12),"ivory",frame)

    bottom = .43
    top = bottom+height

    if not open_hall:
        stone.box((0,0,bottom+height/2),
                  (width*.78,depth*.72,height),"wall",frame)

        panels = max(3,int(width/1.25))
        if panels%2 == 0:
            panels += 1

        for side in (-1,1):
            for i in range(panels):
                xx = (i-(panels-1)/2)*width*.70/panels
                skip_front_door = (
                    side == -1
                    and abs(xx) < width * .11
                    and (studded_doors or not KIT["geshan"])
                )
                if skip_front_door:
                    continue
                lattice_window(
                    ornament,frame,xx,side*(depth*.36+.025),
                    bottom+height*.52,
                    width*.57/panels,height*.70,
                    side,lit=(i%3 != 2)
                )

        if studded_doors or not KIT["geshan"]:
            door_pair(ornament,frame,width,depth,height,studded=studded_doors)

        for side in (-1,1):
            for i in range(5):
                yy = (i-2)*depth*.135
                wood.box(
                    (side*width*.397,yy,bottom+height/2),
                    (.10,.10,height),"red",frame
                )

            side_frame = Frame(
                *frame.p(side*width*.40,0,0),
                angle+side*math.pi/2
            )
            lattice_window(
                ornament,side_frame,0,-.025,bottom+height*.53,
                depth*.42,height*.61,-1,imperial
            )
    elif studded_doors:
        door_pair(ornament,frame,width,depth,height,studded=True,tall=True,
                  open_degrees=78 if name == "前庭仪门" else 0)

    if KIT["odd_bays"]:
        bays = max(3, int(round(width / 2.05)))
        if bays % 2 == 0:
            bays += 1
        columns = bays + 1
    else:
        columns = max(4, int(width / 1.7) + 1)
        bays = columns - 1
    column_radius = .13 if imperial else .10
    smax = 0.022 if height >= 3.5 else 0.015
    overhang = height * OVERHANG_RATIO
    bracket_scale = .93 if imperial else .73
    weights = []
    mid = bays // 2
    for i in range(bays):
        dist = abs(i - mid)
        weights.append(1.18 - 0.12 * dist)
    weight_sum = sum(weights)
    bay_widths = [width * 0.90 * w / weight_sum for w in weights]
    bay = sum(bay_widths) / len(bay_widths)
    inter_count = 0 if bay <= 1.35 else (1 if bay <= 2.30 else 2)

    heads = []
    col_x = [-width * 0.45]
    for bw in bay_widths:
        col_x.append(col_x[-1] + bw)
    for side in (-1,1):
        yy = side*depth*.445
        row_heads = []
        for i in range(columns):
            xx = col_x[i]
            hi = height * shengqi_scale(i, columns, smax)
            end_x = i in (0, columns - 1)
            dx, dy = cejiao_delta(xx, yy, hi, end_x)
            foot = (xx, yy, bottom)
            head = (xx + dx, yy + dy, bottom + hi)
            mid = (
                foot[0] + (head[0] - foot[0]) * ENTASIS_SPLIT,
                foot[1] + (head[1] - foot[1]) * ENTASIS_SPLIT,
                foot[2] + (head[2] - foot[2]) * ENTASIS_SPLIT,
            )
            wood.rod(
                frame.p(*foot), frame.p(*mid),
                column_radius, "pillar_red", column_radius, 16
            )
            wood.rod(
                frame.p(*mid), frame.p(*head),
                column_radius, "pillar_red", column_radius * ENTASIS_TOP, 16
            )
            stone.lathe(frame.p(xx,yy,0),[
                (.22,.39),(.225,.45),(.18,.51),(.153,.60)
            ],"ivory",24)
            wood.rod(
                frame.p(xx,yy,bottom+.07),
                frame.p(xx,yy,bottom+.145),
                column_radius*1.07,"bronze",sides=16
            )
            bracket(
                wood, frame, head[0], head[1], head[2], bracket_scale,
                corner=end_x and KIT["corner_bracket"],
            )
            if i < columns-1:
                brace(wood,frame,head[0],head[1],head[2]-.02,1,.93 if imperial else .70)
            if i > 0:
                brace(wood,frame,head[0],head[1],head[2]-.02,-1,.93 if imperial else .70)
            row_heads.append(head)
        heads.append(row_heads)
        mean_y = sum(h[1] for h in row_heads) / len(row_heads)
        mean_z = sum(h[2] for h in row_heads) / len(row_heads)
        wood.box((0,mean_y,mean_z+.24),(width+.12,.23,.22),"beam",frame)
        wood.box((0,mean_y+side*.13,mean_z+.28),
                 (width*.97,.04,.053),"tile_dark",frame)
        for i in range(columns-1):
            a_h, b_h = row_heads[i], row_heads[i + 1]
            for k in range(inter_count):
                t = 0.5 if inter_count == 1 else (k + 1) / (inter_count + 1)
                hx = a_h[0] + (b_h[0] - a_h[0]) * t
                hy = a_h[1] + (b_h[1] - a_h[1]) * t
                hz = a_h[2] + (b_h[2] - a_h[2]) * t
                bracket(wood, frame, hx, hy, hz, bracket_scale * 0.82)
                cloud_scroll(
                    frame, hx, hy + side * .12, hz + .12,
                    .22, "gold" if imperial else "bronze"
                )

    for side in (-1,1):
        xx = side*width*.45
        wood.box((xx,0,top+.26),(.23,depth+.12,.22),"beam",frame)
        wood.box((xx+side*.13,0,top+.30),
                 (.04,depth*.97,.053),"tile_dark",frame)

    if imperial and not open_hall:
        inner_xs = col_x[1:-1]
        for ix in inner_xs[1:-1] if len(inner_xs) > 2 else inner_xs:
            for iy in (-depth * 0.18, depth * 0.18):
                hi = height * 0.92
                wood.rod(
                    frame.p(ix, iy, bottom),
                    frame.p(ix, iy, bottom + hi),
                    column_radius * 0.92, "pillar_red", column_radius * 0.80, 14
                )
                stone.lathe(frame.p(ix, iy, 0), [
                    (.18, .39), (.20, .45), (.15, .51), (.13, .58)
                ], "ivory", 20)

    if not open_hall:
        ornament.box(
            (0,-depth*.465,top-.12),
            (width*.29,.10,.43),"bronze",frame
        )
        ornament.box(
            (0,-depth*.465-.06,top-.12),
            (width*.27,.034,.32),"plaque",frame
        )
        cloud_scroll(frame,0,-depth*.465-.085,top-.12,.42,"gold")

    corner_top = bottom + height * shengqi_scale(0, columns, smax)
    local_roof_z = corner_top + bracket_scale * 0.58 + 0.06
    rise = depth * (0.308 if imperial else 0.256)
    roof_w = width + 2 * overhang + 0.35
    roof_d = depth + 2 * overhang + 0.35

    rafter_count = max(14,int(width/.28))
    inner_y = depth * .28
    mid_y = depth * .50 + overhang * 0.55
    eave_y = depth * .50 + overhang * 1.00
    fly_y = depth * .50 + overhang * 1.12
    for side in (-1,1):
        for i in range(rafter_count):
            xx = -width*.49+width*.98*i/(rafter_count-1)
            wood.rod(
                frame.p(xx,side*inner_y,local_roof_z-.14),
                frame.p(xx,side*eave_y,local_roof_z-.05),
                .036,"wood",.030,sides=8
            )
            wood.rod(
                frame.p(xx,side*mid_y,local_roof_z-.07),
                frame.p(xx,side*fly_y,local_roof_z-.01),
                .018,"wood",.014,sides=4
            )
    soffit(wood,frame,roof_w-0.78,roof_d-0.78,local_roof_z-.06)
    wall_top = corner_top
    if not open_hall:
        seal_wall_to_roof(
            stone,frame,width*.78,depth*.72,wall_top,
            roof_w,roof_d,local_roof_z,rise
        )
    else:
        seal_wall_to_roof(
            wood,frame,width*.90,depth*.89,wall_top,
            roof_w,roof_d,local_roof_z,rise,"beam"
        )

    stone.object(name+"_台基殿身","03_殿阁木构",.011)
    wood.object(name+"_柱梁斗拱雀替","03_殿阁木构",.005)
    ornament.object(name+"_门窗格扇","05_门窗雕饰",.003)

    lower_ratio = 0.47
    roof(
        frame, local_roof_z, roof_w, roof_d, rise * (0.72 if double_eave else 1.0),
        name + ("_下檐" if double_eave else ""),
        imperial,
        ridge_ratio=lower_ratio,
        ornaments=not double_eave,
    )
    peak = z + local_roof_z + rise * (0.72 if double_eave else 1.0)
    if double_eave:
        upper_w = width * 0.68 + 2 * overhang * 0.45
        upper_d = depth * 0.52 + 2 * overhang * 0.45
        upper_z = local_roof_z + height * 0.38
        upper_rise = depth * 0.20
        gable = Geo()
        # 上层檐墙：填满下檐与上檐之间的黑洞带
        band_w, band_d = upper_w * 0.52, upper_d * 0.46
        band_z0 = local_roof_z - 0.06
        band_z1 = upper_z + 0.10
        band_h = band_z1 - band_z0
        gable.box((0, 0, (band_z0 + band_z1) / 2),
                  (band_w, band_d, band_h), "wall", frame)
        for sy in (-1, 1):
            lattice_window(
                gable, frame, 0, sy * (band_d * .5 + .005),
                (band_z0 + band_z1) / 2,
                band_w * .46, band_h * .66, sy, lit=True
            )
        gx = upper_w * 0.31
        gy = upper_d * 0.46
        peak_z = upper_z + upper_rise + 0.04
        for sx in (-1, 1):
            # recessed gable wall, inside the roof plane
            gable.face([
                frame.p(sx * gx, -gy * 0.92, upper_z + 0.02),
                frame.p(sx * gx, gy * 0.92, upper_z + 0.02),
                frame.p(sx * gx, 0, peak_z),
            ], "wall")
            # 博风板 along the two rakes
            for sy in (-1, 1):
                a = frame.p(sx * gx, sy * gy * 0.92, upper_z + 0.05)
                b = frame.p(sx * gx, 0, peak_z + 0.03)
                wood.rod(a, b, 0.055, "beam", 0.040, 8)
            # 悬鱼
            fish = frame.p(sx * (gx + 0.04), 0, upper_z + upper_rise * 0.42)
            gable.ellipsoid(fish, (0.05, 0.08, 0.16), "gold")
            gable.ellipsoid(fish + Vector((0, 0, -0.14)), (0.03, 0.05, 0.08), "gold")
        gable.object(name+"_歇山山花","03_殿阁木构",.008)
        roof(
            frame, upper_z, upper_w, upper_d, upper_rise,
            name+"_上檐", imperial, ridge_ratio=0.62 if xieshan else 0.42, ornaments=True,
        )
        peak = z + upper_z + upper_rise
    return peak


report("开始构建宫殿群")

main_top = hall(
    "太微正殿",0,13.8,MAIN_Z,
    14.4,9.5,4.2,imperial=True,
    double_eave=True, xieshan=True,
)

finial = Geo()
finial.lathe((0,13.8,main_top),[
    (.24,0),(.30,.09),(.22,.17),(.25,.25),
    (.13,.35),(.15,.46),(.065,.68),(.012,.98),
],"gold",40)
finial.object("重阁宝刹","05_门窗雕饰")

for side in (-1,1):
    hall("东西配殿",side*12.2,11.6,COURT_Z,4.7,8.2,2.8)
    hall("斋心前殿",side*12.2,-5.0,COURT_Z,4.7,5.6,2.45)

hall("后苑藏书楼",0,25.0,BACK_Z,7.2,3.8,2.5)

for side in (-1,1):
    hall(
        "后苑角楼",side*12.0,24.9,BACK_Z,
        3.1,3.1,1.9,open_hall=True
    )
    hall(
        "后苑角楼上层",side*12.0,24.9,BACK_Z+2.55,
        2.15,2.15,1.32,open_hall=True
    )

hall(
    "前庭仪门",0,-11.4,COURT_Z,
    7.4,3.5,2.85,open_hall=True,imperial=True,studded_doors=True
)

for side in (-1,1):
    hall(
        "前庭角亭",side*13.4,-12.2,COURT_Z,
        2.55,2.55,1.75,open_hall=True
    )

hall(
    "临波水榭",23.8,15.1,ground_z(23.8,15.1)+.07,
    4.0,3.3,2.05,open_hall=True
)

hall(
    "桃阴小亭",-20.2,-17.0,ground_z(-20.2,-17.0)+.07,
    3.0,2.7,1.8,open_hall=True
)


# =============================================================================
# 11. 八角亭：独立的攒尖屋顶
# =============================================================================

def octagonal_pavilion(x,y,z,radius=1.8,height=2.5):
    frame = Frame(x,y,z)
    reserve(frame,radius*2.7,radius*2.7,.2)
    g,roof_geo = Geo(),Geo()

    g.lathe((x,y,z),[
        (radius+.35,0),(radius+.35,.16),
        (radius+.18,.24),(radius+.18,.34),
    ],"ivory",8)

    n = 8
    for i in range(n):
        a = TAU*i/n+math.pi/8
        b = TAU*(i+1)/n+math.pi/8

        p = Vector((x+radius*math.cos(a),y+radius*math.sin(a),z+.34))
        q = Vector((x+radius*math.cos(b),y+radius*math.sin(b),z+.34))

        g.rod(p,p+Vector((0,0,height)),.085,"red",sides=12)
        g.rod(
            p+Vector((0,0,height)),
            q+Vector((0,0,height)),
            .09,"beam",sides=8
        )

        if i not in (5,6):
            railing(p,q,.64,1.2,False)

        g.face([
            p+Vector((0,0,height-.02)),
            q+Vector((0,0,height-.02)),
            q+Vector((0,0,height+.09)),
            p+Vector((0,0,height+.09)),
        ],"beam")

    soffit_r = radius+.62
    soffit_z = z+.34+height+.03
    g.face([
        Vector((
            x+soffit_r*math.cos(TAU*i/n+math.pi/8),
            y+soffit_r*math.sin(TAU*i/n+math.pi/8),
            soffit_z
        ))
        for i in range(n)
    ],"beam")

    roof_radius = radius+1.02
    roof_base = z+.34+height+.09
    roof_rise = 2.0

    def p_roof(side,u,t,lift=0):
        a = TAU*side/n+math.pi/8
        b = TAU*(side+1)/n+math.pi/8
        edge = Vector((
            (1-u)*math.cos(a)+u*math.cos(b),
            (1-u)*math.sin(a)+u*math.sin(b),
            0
        ))
        corner = abs(u-.5)*2
        return Vector((
            x+edge.x*roof_radius*t,
            y+edge.y*roof_radius*t,
            roof_base+roof_rise*(1-t)**.94
            +.28*t**7+.31*corner**4*t**8+lift
        ))

    for side in range(n):
        for i in range(12):
            u0,u1 = i/12,(i+1)/12
            for j in range(16):
                t0 = .015+.985*j/16
                t1 = .015+.985*(j+1)/16
                roof_geo.face([
                    p_roof(side,u0,t0),p_roof(side,u0,t1),
                    p_roof(side,u1,t1),p_roof(side,u1,t0),
                ],"tile",True)

        for i in range(9):
            u = i/8
            line([
                p_roof(side,u,.03+.97*j/24,.025)
                for j in range(25)
            ],"tile_light",.023,"04_琉璃瓦作")

        line([
            p_roof(side,i/16,1,.02) for i in range(17)
        ],"tile_light",.052,"04_琉璃瓦作")

        line([
            p_roof(side,0,.03+.97*j/24,.03)
            for j in range(25)
        ],"tile_light",.062,"04_琉璃瓦作")

    g.lathe((x,y,roof_base+roof_rise),[
        (.17,0),(.23,.08),(.13,.18),(.14,.28),(.025,.60),
    ],"gold",32)

    g.object("八角亭柱梁栏座","03_殿阁木构",.006)
    roof_geo.object("八角攒尖亭顶","04_琉璃瓦作")


octagonal_pavilion(-24.5,14.2,ground_z(-24.5,14.2)+.06)

if ENABLE_M1_SATURATION:
    octagonal_pavilion(24.8,-8.6,ground_z(24.8,-8.6)+.06,1.45,2.15)
    for side, name in ((-1, "太微钟楼"), (1, "太微鼓楼")):
        hall(
            name, side*16.2, -1.2, COURT_Z,
            2.55, 2.55, 1.85, open_hall=True
        )
    terrace_rail = [
        ((-8.6,7.05,MAIN_Z+.22),(8.6,7.05,MAIN_Z+.22)),
        ((-8.6,20.4,MAIN_Z+.22),(8.6,20.4,MAIN_Z+.22)),
        ((-8.6,7.05,MAIN_Z+.22),(-8.6,20.4,MAIN_Z+.22)),
        ((8.6,7.05,MAIN_Z+.22),(8.6,20.4,MAIN_Z+.22)),
    ]
    for a, b in terrace_rail:
        railing(Vector(a), Vector(b), 1.12, .92, True)
    cap = Geo()
    cap.box((0,13.72,MAIN_Z+.16),(17.4,.28,.12),"stone")
    cap.box((0,20.40,MAIN_Z+.16),(17.4,.28,.12),"stone")
    cap.box((-8.60,13.72,MAIN_Z+.16),(.28,13.7,.12),"stone")
    cap.box((8.60,13.72,MAIN_Z+.16),(.28,13.7,.12),"stone")
    cap.object("月台压顶石","02_台基庭院",.006)
report("宫殿与亭阁完成")


# =============================================================================
# 12. 回廊、垂花门与月洞门
# =============================================================================

def corridor(x,y,z,length,angle=0,roof_width=2.40,roof_rise=.78,roof_overhang=.55):
    frame = Frame(x,y,z,angle)
    reserve(frame,max(2.0,roof_width*.85),length,.1)
    g = Geo()

    g.box((0,0,.10),(1.92,length,.20),"stone",frame)
    count = max(3,int(length/1.55))
    half = min(.73,roof_width*.30)

    for i in range(count+1):
        yy = -length/2+length*i/count
        for xx in (-half,half):
            g.rod(frame.p(xx,yy,.20),frame.p(xx,yy,2.18),
                  .072,"red",.063,12)
            bracket(g,frame,xx,yy,2.18,.51)
        g.box((0,yy,2.33),(1.90,.15,.17),"beam",frame)
        if i < count:
            y_mid = yy + length / count / 2
            for xx in (-half, half):
                bracket(g, frame, xx, y_mid, 2.18, .42)

    roof_frame = Frame(x,y,z,angle+math.pi/2)
    roof_len = length + roof_overhang + 0.22
    roof_wid = roof_width + 0.28
    roof_z = 2.38
    soffit(g,frame,roof_wid-0.28,roof_len-0.18,2.33)
    seal_wall_to_roof(
        g,roof_frame,roof_len*.92,roof_wid*.72,2.33,
        roof_len,roof_wid,roof_z,roof_rise,"beam"
    )
    g.object("回廊柱梁","06_廊桥园墙",.004)
    roof(roof_frame,roof_z,roof_len,roof_wid,roof_rise,"回廊",False)

    for side in (-1,1):
        railing(frame.p(side*half,-length/2,.20),
                frame.p(side*half,length/2,.20),
                .56,1.55,False)


# 翼廊只铺在前殿北檐与配殿南檐之间的空当，不再伸进两殿屋面
for x in (-12.2,12.2):
    corridor(x,2.55,COURT_Z,5.0,roof_width=1.82,roof_rise=.52,roof_overhang=.18)
# 后苑横廊贴北墙内侧，躲开藏书楼东西出檐
for x in (-10.4,10.4):
    corridor(x,26.55,BACK_Z,4.4,math.pi/2,roof_width=1.70,roof_rise=.46,roof_overhang=.14)

if ENABLE_M1_SATURATION:
    # 正殿前夹廊放在月台南、中轴两侧的庭院空地，不钻配殿/正殿出檐缝
    for x in (-5.8,5.8):
        corridor(x,5.15,COURT_Z,2.6,roof_width=1.58,roof_rise=.42,roof_overhang=.12)
    # 配殿北到后苑：缩短收檐，躲开配殿北坡
    for x in (-12.2,12.2):
        corridor(x,19.55,COURT_Z,2.8,roof_width=1.70,roof_rise=.46,roof_overhang=.14)
    # 翼廊空当的窄连接廊：只填缝，不盖进配殿出檐
    for x in (-12.2,12.2):
        corridor(x,5.95,COURT_Z,1.40,roof_width=1.38,roof_rise=.32,roof_overhang=.06)
        corridor(x,17.35,COURT_Z,1.20,roof_width=1.38,roof_rise=.32,roof_overhang=.06)


def hanging_flower_gate(x,y,z,angle=0):
    frame = Frame(x,y,z,angle)
    reserve(frame,4.4,2.1,.2)
    g = Geo()

    for side in (-1,1):
        g.rod(frame.p(side*1.45,0,.10),frame.p(side*1.45,0,2.63),
              .113,"red",sides=16)
        g.lathe(frame.p(side*1.45,0,0),[
            (.24,.02),(.24,.15),(.17,.23),(.15,.30)
        ],"baogu_stone",24)

        g.rod(
            frame.p(side*.88,-.61,1.83),
            frame.p(side*.88,-.61,2.79),
            .082,"red",sides=12
        )
        center = frame.p(side*.88,-.61,1.80)
        g.lathe(center,[
            (.034,-.23),(.12,-.16),(.165,-.05),(.10,.06)
        ],"door_gold",24)

        for j in range(8):
            a = TAU*j/8
            g.leaf(
                center+Vector((.05*math.cos(a),.05*math.sin(a),-.11)),
                (math.cos(a),math.sin(a),.7),
                .185,.052,"carved_wood",.05
            )

    g.box((0,0,2.62),(3.30,.26,.26),"beam",frame)
    g.box((0,-.58,2.78),(2.30,.19,.21),"red",frame)

    for side in (-1,1):
        brace(g,frame,side*1.45,-.04,2.56,-side,1.08)

    fret_band(frame,-1.35,1.35,-.15,2.57,.45,.12,key="carved_wood")
    soffit(g,frame,3.55,1.55,2.86)
    seal_wall_to_roof(
        g,frame,3.10,1.18,2.62,
        4.25,2.15,2.91,1.13,"beam"
    )
    g.object("垂花门莲头木构","06_廊桥园墙",.006)
    roof(frame,2.91,4.25,2.15,1.13,"垂花门",True)


hanging_flower_gate(-18.0,-10.0,4.02,math.pi/2)
hanging_flower_gate(18.0,-10.0,4.02,math.pi/2)


def moon_gate(x,y,z,width=5.0,height=3.1,angle=0):
    frame = Frame(x,y,z,angle)
    reserve(frame,width,.6,.05)
    g = Geo()

    radius = 1.22
    center_z = 1.37
    thickness = .22

    def outer_distance(a):
        dx,dz = math.cos(a),math.sin(a)
        candidates = []
        if abs(dx)>1e-7:
            candidates.append((width/2)/abs(dx))
        if dz>1e-7:
            candidates.append((height-center_z)/dz)
        elif dz<-1e-7:
            candidates.append(-center_z/dz)
        return min(candidates)

    n = 96
    for i in range(n):
        a,b = TAU*i/n,TAU*(i+1)/n
        ia = (radius*math.cos(a),center_z+radius*math.sin(a))
        ib = (radius*math.cos(b),center_z+radius*math.sin(b))
        oa = (outer_distance(a)*math.cos(a),center_z+outer_distance(a)*math.sin(a))
        ob = (outer_distance(b)*math.cos(b),center_z+outer_distance(b)*math.sin(b))

        for side in (-1,1):
            yy = side*thickness
            points = [
                frame.p(ia[0],yy,ia[1]),frame.p(oa[0],yy,oa[1]),
                frame.p(ob[0],yy,ob[1]),frame.p(ib[0],yy,ib[1]),
            ]
            if side == 1:
                points.reverse()
            g.face(points,"wall")

        g.face([
            frame.p(ia[0],-thickness,ia[1]),
            frame.p(ia[0],thickness,ia[1]),
            frame.p(ib[0],thickness,ib[1]),
            frame.p(ib[0],-thickness,ib[1]),
        ],"stone")

        g.face([
            frame.p(oa[0],thickness,oa[1]),
            frame.p(oa[0],-thickness,oa[1]),
            frame.p(ob[0],-thickness,ob[1]),
            frame.p(ob[0],thickness,ob[1]),
        ],"wall")

    # 两侧墙脚，不跨越圆洞底部
    for side in (-1,1):
        g.box((side*(width/4+.63),0,.10),
              (max(.2,width/2-1.26),.55,.20),"stone",frame)

    g.box((0,0,height+.12),(width+.08,.28,.28),"wall",frame)
    g.object("月洞粉墙","06_廊桥园墙",.006)

    for side in (-1,1):
        circle(frame.p(0,side*(thickness+.018),center_z),
               radius+.054,frame.d(0,1,0),
               "stone",.047,"06_廊桥园墙")

    roof(frame,height+.02,width+.30,1.0,.40,"月洞墙瓦",False)


moon_gate(-18.0,4.7,4.02,5.0,3.1,math.pi/2)
moon_gate(18.0,4.7,4.02,5.0,3.1,math.pi/2)


def garden_wall(x,y0,y1,z,angle=math.pi/2):
    """园林围墙一段：石脚 + 粉墙 + 压顶 + 瓦檐。
    垂花门与月洞门本来就是按"墙上的门"造的，补上墙身它们才不是孤立的门架子。"""
    length = abs(y1-y0)
    frame = Frame(x,(y0+y1)/2,z,angle)
    reserve(frame,length,.9,.06)
    g = Geo()

    g.box((0,0,.17),(length,.46,.34),"stone",frame)
    g.box((0,0,1.16),(length,.34,1.98),"wall",frame)
    g.box((0,0,2.22),(length,.54,.14),"stone",frame)
    g.box((0,0,2.46),(length,.22,.34),"wall",frame)
    g.object("园林围墙","06_廊桥园墙",.006)

    roof(frame,2.29,length+.06,.98,.34,"围墙瓦",False)


# 垂花门占 y -12.2..-7.8，月洞门占 y 2.2..7.2，墙身接在两者之间并与两端搭一点
for x in (-18.0,18.0):
    garden_wall(x,-13.4,-12.1,4.02)
    garden_wall(x,-7.9,2.3,4.02)
    garden_wall(x,7.1,8.4,4.02)


def garden_wall_ew(y, x0, x1, z, with_roof=True):
    """东西向园墙。garden_wall 默认沿南北；闭合后苑与前庭南翼用这一条。"""
    length = abs(x1-x0)
    frame = Frame((x0+x1)/2, y, z, 0)
    reserve(frame, length, .9, .06)
    g = Geo()
    g.box((0,0,.17),(length,.46,.34),"stone",frame)
    g.box((0,0,1.16),(length,.34,1.98),"wall",frame)
    g.box((0,0,2.22),(length,.54,.14),"stone",frame)
    if with_roof:
        g.box((0,0,2.46),(length,.22,.34),"wall",frame)
    g.object("园林围墙东西","06_廊桥园墙",.006)
    if with_roof:
        roof(frame,2.29,length+.06,.98,.34,"围墙瓦",False)


if ENABLE_M1_SATURATION:
    for x in (-18.0,18.0):
        garden_wall(x,-16.6,-13.4,4.02)
        garden_wall(x,8.4,22.4,4.02)
        garden_wall(x,22.4,27.2,BACK_Z)

    garden_wall_ew(-16.6,-18.0,-6.2,4.02)
    garden_wall_ew(-16.6,-6.2,-3.4,4.02,with_roof=False)
    garden_wall_ew(-16.6,3.4,6.2,4.02,with_roof=False)
    garden_wall_ew(-16.6,6.2,18.0,4.02)
    garden_wall_ew(27.2,-18.0,-4.2,BACK_Z)
    garden_wall_ew(27.2,4.2,18.0,BACK_Z)


# =============================================================================
# 13. 石阶、园路、桥梁
# =============================================================================

def stairs(name,a,b,width,steps,with_rail=True):
    a,b = Vector(a),Vector(b)
    horizontal = Vector((b.x-a.x,b.y-a.y,0))
    length = horizontal.length
    direction = horizontal.normalized()
    side = Vector((direction.y,-direction.x,0))
    angle = math.atan2(-direction.x,direction.y)
    g = Geo()

    for i in range(steps):
        t = i/(steps-1)
        center = a.lerp(b,t)
        frame = Frame(center.x,center.y,center.z-.105,angle)
        g.box((0,0,0),(width,length/steps+.045,.21),"stair_tread",frame)

        line([
            center-side*width*.49-direction*(length/steps*.48),
            center+side*width*.49-direction*(length/steps*.48),
        ],"stone",.009,"02_台基庭院")

    g.object(name,"02_台基庭院",.011)

    if with_rail:
        for sign in (-1,1):
            railing(a+side*sign*width*.47,
                    b+side*sign*width*.47,
                    .76,1.22,False)


stairs("迎仙长阶",(0,-27,3.98),(0,-15.1,COURT_Z),5.2,38)
stairs("正殿大踏跺",(0,3.9,COURT_Z),(0,7.0,MAIN_Z),6.2,15)

for side in (-1,1):
    stairs(
        "殿侧步阶",
        (side*9.5,17.0,COURT_Z),
        (side*8.0,17.0,MAIN_Z),
        1.7,10,False
    )

if ENABLE_M1_SATURATION:
    stairs("后苑北阶",(0,22.4,COURT_Z),(0,23.7,BACK_Z),3.6,8)


def garden_path(control,width=1.2):
    points = catmull([(x,y,0) for x,y in control],10)
    path,edging = Geo(),Geo()

    for a,b in zip(points[:-1],points[1:]):
        d = b-a
        if d.length < 1e-6:
            continue
        d.normalize()
        side = Vector((-d.y,d.x,0))*width/2
        quad = [a-side,b-side,b+side,a+side]
        path.face([(p.x,p.y,ground_z(p.x,p.y)+.07) for p in quad],"stone")
        PATH_SEGMENTS.append((a,b,width/2))

    for i in range(0,len(points)-1,3):
        p = points[i]
        d = points[i+1]-p
        if d.length < 1e-6:
            continue
        d.normalize()
        side = Vector((-d.y,d.x,0))
        for sign in (-1,1):
            q = p+side*sign*(width/2+.063)
            edging.ellipsoid(
                (q.x,q.y,ground_z(q.x,q.y)+.085),
                (.115,.085,.06),"stone"
            )

    path.object("曲折园路","06_廊桥园墙")
    edging.object("卵石镶边","06_廊桥园墙")


garden_path([
    (-16.5,-13),(-21,-14),(-28,-12),(-30,-5),
    (-29,6),(-26,13),(-24,15),(-20,22)
],1.28)

garden_path([
    (16.5,-13),(21.5,-13),(29,-9),(30,1),
    (29,10),(25,15),(21,22)
],1.28)

garden_path([(-19.5,-9),(-19.5,-4),(-19.5,2),(-22.5,8)],1.0)
garden_path([(18.5,-9),(22.5,-9),(23.8,-6.2)],1.1)
garden_path([(23.8,12.2),(24,14),(25,16)],1.1)


def arch_bridge(x,y,length=18,width=1.85,angle=0,deck_z=4.05,rise=1.53):
    g = Geo()
    count = 48
    sides = [[],[]]
    frame = Frame(x,y,0,angle)

    def p(t,side):
        local = Vector((side*width/2, -length/2+length*t, deck_z+rise*math.sin(math.pi*t)))
        return frame.p(local.x, local.y, local.z)

    for i in range(count):
        t0,t1 = i/count,(i+1)/count
        a,b,c,d = p(t0,-1),p(t0,1),p(t1,1),p(t1,-1)
        g.face([a,b,c,d],"bridge_deck")
        g.face([a,d,d-Vector((0,0,.22)),a-Vector((0,0,.22))],"stone")
        g.face([b,b-Vector((0,0,.22)),c-Vector((0,0,.22)),c],"stone")

    for i in range(count+1):
        t = i/count
        for index,sign in enumerate((-1,1)):
            q = p(t,sign)
            sides[index].append(q)

            if i%4 == 0:
                g.rod(q,q+Vector((0,0,.76)),.056,"ivory",sides=10)
                g.ellipsoid(q+Vector((0,0,.82)),(.095,.095,.105),"ivory")

    for points in sides:
        line([p+Vector((0,0,.72)) for p in points],
             "ivory",.050,"06_廊桥园墙")
        line([p-Vector((0,0,.29)) for p in points],
             "stone",.125,"06_廊桥园墙")

    g.object("白石虹桥","06_廊桥园墙")
    _pa = frame.p(0, -length/2, 0)
    _pb = frame.p(0, length/2, 0)
    PATH_SEGMENTS.append((_pa,_pb,width*.65))


arch_bridge(23.8,3.0)
report("廊门、园路与桥梁完成")


# =============================================================================
# 14. 湖水、自然驳岸、荷花、芦苇
# =============================================================================

pond_geo,shore = Geo(),Geo()

for px,py,rx,ry in PONDS:
    n = 144
    for i in range(n):
        a,b = TAU*i/n,TAU*(i+1)/n
        pond_geo.face([
            (px,py,WATER_Z),
            (px+rx*math.cos(a),py+ry*math.sin(a),WATER_Z),
            (px+rx*math.cos(b),py+ry*math.sin(b),WATER_Z),
        ],"water")

    for i in range(68):
        a = TAU*i/68
        x = px+rx*1.04*math.cos(a)
        y = py+ry*1.04*math.sin(a)
        z = ground_z(x,y)
        shore.ellipsoid(
            (x,y,z+.012),
            (R_LAND.uniform(.23,.53),
             R_LAND.uniform(.23,.54),
             R_LAND.uniform(.13,.30)),
            "stone"
        )
        if i%4 == 0:
            shore.ellipsoid((x,y,z+.16),(.21,.24,.05),"moss")

pond_geo.object("双池碧水","07_池水飞瀑")
shore.object("自然驳岸石","07_池水飞瀑")

# 外湖：从主岛岸线向外铺成环湖。不挖洞（挖洞会漏天空）。
# 外岛台面高于水面，自行冒出。
outer_lake = Geo()
lake_n = 80 if QUALITY != "STUDY" else 40
lake_rings = 8 if QUALITY != "STUDY" else 5
lake_rx, lake_ry = 64.0, 60.0
inner = 0.48
for j in range(lake_rings):
    t0 = inner + (1-inner)*j/lake_rings
    t1 = inner + (1-inner)*(j+1)/lake_rings
    for i in range(lake_n):
        a0, a1 = TAU*i/lake_n, TAU*(i+1)/lake_n
        def lp(t, a):
            k = 1 + .03*math.sin(a*2.7 + t*1.8)
            return (
                lake_rx*t*k*math.cos(a),
                CY + lake_ry*t*k*math.sin(a),
                WATER_Z - .08,
            )
        outer_lake.face([lp(t0,a0), lp(t0,a1), lp(t1,a1), lp(t1,a0)], "water")
outer_lake.object("外湖烟水","07_池水飞瀑")


def flower(g,center,size,key="pink_light",petals=5):
    center = Vector(center)
    for i in range(petals):
        a = TAU*i/petals
        d = Vector((math.cos(a),math.sin(a),.13))
        side = Vector((-math.sin(a),math.cos(a),0))
        middle = center+d*size*.54+Vector((0,0,size*.12))
        tip = center+d*size
        g.face([center,middle-side*size*.30,tip,middle],"pink")
        g.face([center,middle,tip,middle+side*size*.30],key)
    g.ellipsoid(center,(size*.15,size*.15,size*.075),"pollen")


lotus = Geo()

for px,py,rx,ry in PONDS:
    count = 44 if QUALITY != "STUDY" else 18
    for i in range(count):
        a = R_LAND.uniform(0,TAU)
        r = math.sqrt(R_LAND.uniform(.14,.82))
        x = px+rx*r*math.cos(a)
        y = py+ry*r*math.sin(a)

        if px>0 and abs(x-23.8)<1.12:
            continue

        radius = R_LAND.uniform(.23,.51)
        center = Vector((x,y,WATER_Z+.024))

        def edge(angle):
            rr = radius*(1+.032*math.sin(angle*7))
            return center+Vector((
                rr*math.cos(angle),rr*math.sin(angle),
                .025+.013*math.sin(angle*5)
            ))

        for j in range(24):
            a0 = .18+(TAU-.38)*j/24
            a1 = .18+(TAU-.38)*(j+1)/24
            p0,p1 = edge(a0),edge(a1)
            lotus.face([center,p0,p1],"lotus",True)

            if j%4 == 0:
                line([center+Vector((0,0,.007)),p0+Vector((0,0,.006))],
                     "leaf_light",.003,"07_池水飞瀑")

        if i%3 == 0:
            fc = center+Vector((.09,.02,R_LAND.uniform(.17,.30)))
            lotus.rod(center,fc,.013,"lotus",sides=6)

            for layer in range(3):
                rr = radius*(.85-layer*.15)
                for j in range(8):
                    a = TAU*j/8+layer*.27
                    d = Vector((math.cos(a),math.sin(a),0))
                    side = Vector((-math.sin(a),math.cos(a),0))
                    root = fc+d*.025
                    middle = fc+d*rr*.53+Vector((0,0,rr*.34))
                    tip = fc+d*rr+Vector((0,0,rr*(.13+.28*layer)))

                    lotus.face([root,middle-side*rr*.22,tip,middle],"pink",True)
                    lotus.face([root,middle,tip,middle+side*rr*.22],"pink_light",True)

            lotus.ellipsoid(fc+Vector((0,0,.095)),(.048,.048,.040),"pollen")

lotus.object("荷叶脉络与重瓣莲","07_池水飞瀑")

reeds = Geo()
for px,py,rx,ry in PONDS:
    for center_angle in (.25,2.1,4.2):
        for j in range(18):
            a = center_angle+R_GRASS.uniform(-.12,.12)
            x = px+rx*.97*math.cos(a)+R_GRASS.uniform(-.12,.12)
            y = py+ry*.97*math.sin(a)+R_GRASS.uniform(-.12,.12)
            z = max(WATER_Z-.04,ground_z(x,y))
            h = R_GRASS.uniform(.55,1.05)
            tip = Vector((x+.10*math.cos(a),y+.10*math.sin(a),z+h))
            base = Vector((x,y,z))
            reeds.rod(base,tip,.007,"grass",sides=5)
            reeds.ellipsoid(tip,(.026,.026,.15),"reed")
            reeds.leaf(base+Vector((0,0,h*.35)),
                       (math.cos(a),math.sin(a),.2),
                       .40,.022,"grass",.12)

reeds.object("池畔芦苇","09_草花庭石")


# =============================================================================
# 15. 穿孔庭石：高模岩体与精确布尔孔洞
# =============================================================================

def scholar_rock(name,x,y,z,scale=1,angle=0,seed=0):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(
        bm,subdivisions=P["rock_subdivisions"],radius=1
    )

    for v in bm.verts:
        p = v.co.copy()
        band = 1+.16*math.sin(p.z*7)+.075*math.sin(p.x*11+p.y*5)
        v.co.x = p.x*.72*band+.15*math.sin(p.z*3)
        v.co.y = p.y*.49*(1+.10*math.sin(p.z*9))
        v.co.z = (p.z+1)*1.55

    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(MAT["scholar"])

    obj = link_object(name,mesh,"09_草花庭石")

    # 在局部原点完成布尔，再变换整块庭石
    holes = [
        (-.13,.73,.22,.20),
        (.16,1.52,.27,.28),
        (-.12,2.30,.22,.19),
    ]

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    for i,(hx,hz,hrx,hrz) in enumerate(holes):
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=24,ring_count=12,
            location=(hx,0,hz)
        )
        cutter = bpy.context.object
        cutter.name = "_庭石孔洞"
        cutter.scale = (hrx,1.05,hrz)

        bpy.ops.object.transform_apply(
            location=False,rotation=False,scale=True
        )

        bpy.context.view_layer.objects.active = obj
        modifier = obj.modifiers.new("穿孔_"+str(i),"BOOLEAN")
        modifier.operation = "DIFFERENCE"
        modifier.solver = "EXACT"
        modifier.object = cutter

        try:
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        except RuntimeError:
            # 保留原始石体，不中断整个项目
            if modifier.name in obj.modifiers:
                obj.modifiers.remove(modifier)

        bpy.data.objects.remove(cutter,do_unlink=True)

    for poly in obj.data.polygons:
        poly.use_smooth = True

    bevel = obj.modifiers.new("孔缘柔化","BEVEL")
    bevel.width = .018
    bevel.segments = 2
    bevel.limit_method = "ANGLE"

    obj.location = (x,y,z)
    obj.rotation_euler.z = angle
    obj.scale = (scale,scale,scale)

    moss = Geo()
    moss.ellipsoid((x,y,z+.07),(scale*.68,scale*.49,.11),"moss")
    moss.object("庭石苔座","09_草花庭石")
    return obj


if ENABLE_SCHOLAR_ROCKS:
    report("生成穿孔庭石")
    scholar_rock("西园洞石",-19.7,9.3,ground_z(-19.7,9.3),.85,.3,SEED+1)
    scholar_rock("东园洞石",19.7,9.1,ground_z(19.7,9.1),.91,-.4,SEED+2)
    scholar_rock("桃阴庭石",-21.2,-12.5,ground_z(-21.2,-12.5),.63,.8,SEED+3)


# =============================================================================
# 16. 灯光工具与庭院陈设
# =============================================================================

def add_light(name,kind,location,power,color,size=5,target=None):
    data = bpy.data.lights.new(name,kind)
    data.energy = power
    data.color = color

    if kind == "AREA":
        data.shape = "DISK"
        data.size = size
    elif kind == "POINT":
        data.shadow_soft_size = size

    obj = link_object(name,data,"12_灯光相机")
    obj.location = location

    if target is not None:
        obj.rotation_euler = (
            Vector(target)-obj.location
        ).to_track_quat("-Z","Y").to_euler()
    return obj


def lantern(x,y,z,actual_light=False):
    g = Geo()
    g.lathe((x,y,z),[
        (.25,0),(.28,.08),(.22,.16),
        (.15,.23),(.065,.29),(.065,1.39),
    ],"bronze",24)

    g.lathe((x,y,z),[
        (.21,1.39),(.27,1.45),(.22,1.52),
    ],"bronze",24)

    radius = .245
    for i in range(6):
        a,b = TAU*i/6,TAU*(i+1)/6
        p0 = Vector((x+radius*math.cos(a),y+radius*math.sin(a),z+1.52))
        p1 = Vector((x+radius*math.cos(b),y+radius*math.sin(b),z+1.52))
        p2,p3 = p1+Vector((0,0,.56)),p0+Vector((0,0,.56))

        g.face([p0,p1,p2,p3],"lamp")
        g.rod(p0,p3,.018,"bronze",sides=6)
        g.rod(p0,p1,.021,"bronze",sides=6)
        g.rod(p3,p2,.021,"bronze",sides=6)
        g.rod(p0.lerp(p3,.52),p1.lerp(p2,.52),.009,"bronze",sides=5)

    g.lathe((x,y,z),[
        (.33,2.08),(.26,2.16),(.15,2.23),(.033,2.29),
    ],"tile",32)
    g.ellipsoid((x,y,z+2.33),(.048,.048,.061),"gold")

    for i in range(5):
        dx = (i-2)*.014
        line([
            (x+dx,y,z+1.40),
            (x+dx*.6,y+.01,z+1.09),
            (x+dx*1.1,y+.025,z+.98),
        ],"red",.0045,"10_庭院陈设")

    g.object("六角绢宫灯","10_庭院陈设")

    if actual_light:
        add_light("宫灯暖光","POINT",(x,y,z+1.78),18,(1,.43,.13),.32)


for side in (-1,1):
    for i,y in enumerate((-12.9,-7.2,-1.2,3.2)):
        lantern(side*4.8,y,COURT_Z,i%2 == 0)

for x,y in [(-29,-9),(-29,5),(-25,13),(29,-8),(29,8),(25,15)]:
    lantern(x,y,ground_z(x,y),False)


def censer(x,y,z):
    g = Geo()
    g.box((x,y,z+.15),(1.54,1.54,.30),"ivory")

    for i in range(3):
        a = TAU*i/3
        p = Vector((x+.39*math.cos(a),y+.39*math.sin(a),z+.30))
        g.rod(p,p+Vector((0,0,.53)),.092,"bronze",.072,10)

    g.lathe((x,y,z),[
        (.34,.65),(.54,.76),(.64,.95),
        (.60,1.16),(.46,1.28),(.52,1.35),(.52,1.41),
    ],"censer_bronze",48)

    g.lathe((x,y,z),[
        (.52,1.41),(.59,1.47),(.47,1.56),
        (.22,1.66),(.085,1.72),
    ],"patina",48)
    g.ellipsoid((x,y,z+1.80),(.105,.105,.125),"bronze")

    for side in (-1,1):
        line([
            (x+side*(.47+.24*math.sin(math.pi*i/20)),
             y,z+.92+.56*i/20)
            for i in range(21)
        ],"bronze",.049,"10_庭院陈设")

    for i in range(24):
        a = TAU*i/24
        line([
            (x+r*math.cos(a),y+r*math.sin(a),z+zz)
            for r,zz in [(.52,.80),(.64,.95),(.60,1.14)]
        ],"bronze",.008,"10_庭院陈设")

    g.object("古铜香鼎","10_庭院陈设",.004)


censer(-4.35,7.55,MAIN_Z)
censer(4.35,7.55,MAIN_Z)


# ── G16 燕云仪仗细部组件族：一组件一贴图 ──────────────────
def stone_paifang(x,y,z,angle=0):
    """三间四柱石牌坊：高耸挺拔、三楼歇山石檐、金字横匾。"""
    frame = Frame(x,y,z,angle)
    reserve(frame,7.2,1.8,.4)
    g = Geo()
    
    # 四根立柱与夹杆石/抱鼓座
    for sx in (-1,1):
        for lx in (1.15, 2.85):
            px = sx * lx
            # 抱鼓座基
            g.box((px,0,.22),(.48,.56,.44),"paifang_stone",frame)
            g.lathe(frame.p(px,0,.22),[(.26,-.20),(.32,-.05),(.28,.15),(.20,.26)],"baogu_stone",20)
            # 主石柱（八角挺拔）
            g.rod(frame.p(px,0,.44),frame.p(px,0,4.2 if lx<2.0 else 3.5),.135,"paifang_stone",sides=8)
            # 柱顶坐斗
            g.box((px,0,4.26 if lx<2.0 else 3.56),(.38,.38,.14),"paifang_stone",frame)

    # 上下额枋与花板
    # 中间主跨额枋
    g.box((0,0,3.45),(2.36,.24,.26),"paifang_stone",frame)
    g.box((0,0,3.95),(2.36,.22,.24),"paifang_stone",frame)
    g.box((0,-.02,3.70),(1.45,.14,.26),"door_gold",frame)  # 金字匾额
    # 左右次跨额枋
    for side in (-1,1):
        g.box((side*2.0,0,2.85),(1.70,.22,.24),"paifang_stone",frame)
        g.box((side*2.0,0,3.30),(1.70,.20,.22),"paifang_stone",frame)
        # 雀替与斜撑
        brace(g,frame,side*1.15,-.02,3.32,-side,.85)
        brace(g,frame,side*2.85,-.02,2.72,-side,.85)

    # 歇山飞檐小楼顶（自建干净石构飞檐，绝不相互穿模）
    def paifang_roof(cx, w, d, rz, rise):
        # 斗拱挑檐基座
        g.box((cx,0,rz-.08),(w*.88,d*.78,.14),"paifang_stone",frame)
        # 飞檐瓦面
        hw, hd = w/2, d/2
        # 四坡檐口斜切
        verts = [
            frame.p(cx-hw-0.22, -hd-0.20, rz+0.08),  # 0 左前角升起
            frame.p(cx+hw+0.22, -hd-0.20, rz+0.08),  # 1 右前角升起
            frame.p(cx+hw+0.22,  hd+0.20, rz+0.08),  # 2 右后角升起
            frame.p(cx-hw-0.22,  hd+0.20, rz+0.08),  # 3 左后角升起
            frame.p(cx-hw*0.45, -hd*0.35, rz+rise),  # 4 脊左前
            frame.p(cx+hw*0.45, -hd*0.35, rz+rise),  # 5 脊右前
            frame.p(cx+hw*0.45,  hd*0.35, rz+rise),  # 6 脊右后
            frame.p(cx-hw*0.45,  hd*0.35, rz+rise),  # 7 脊左后
        ]
        faces = [
            (0,1,5,4), (1,2,6,5), (2,3,7,6), (3,0,4,7),  # 四面歇山坡
            (4,5,6,7),  # 正脊顶面
        ]
        g.indexed(verts, faces, "tile", smooth=True)
        # 正脊与宝顶
        g.box((cx,0,rz+rise+.04),(w*.55,.14,.10),"tile_dark",frame)
        g.ellipsoid(frame.p(cx,0,rz+rise+.12),(.08,.08,.12),"door_gold")

    # 中楼与左右次楼
    paifang_roof(0.0, 3.20, 1.25, 4.35, 0.45)
    paifang_roof(-2.0, 2.10, 1.05, 3.65, 0.38)
    paifang_roof( 2.0, 2.10, 1.05, 3.65, 0.38)
    
    g.object("三间牌坊石构","06_廊桥园墙",.005)


def dharani_pillar(x,y,z):
    """八面石经幢：须弥座+覆莲+幢身+双檐+宝顶。"""
    g = Geo()
    g.lathe((x,y,z),[(.42,.02),(.42,.14),(.34,.22),(.30,.30)],"stele_stone",24)
    g.lathe((x,y,z+.28),[(.30,0),(.34,.10),(.30,.20),(.26,.28)],"stele_stone",24)
    g.rod((x,y,z+.56),(x,y,z+2.55),.20,"dharani",sides=8)
    for zz in (2.58,2.78):
        g.lathe((x,y,z+zz),[(.34,0),(.38,.06),(.30,.14),(.16,.20)],"dharani",8)
    g.lathe((x,y,z+2.94),[(.16,0),(.10,.10),(.04,.20),(.005,.30)],"door_gold",16)
    g.object("石经幢","10_庭院陈设",.004)


def bronze_ding(x,y,z):
    """三足夔纹铜鼎，殿庭陈设。"""
    g = Geo()
    for i in range(3):
        a = TAU*i/3 + .5
        p = Vector((x+.42*math.cos(a),y+.42*math.sin(a),z))
        g.rod(p,p+Vector((0,0,.62)),.10,"ding_bronze",.08,10)
    g.lathe((x,y,z),[(.30,.55),(.58,.72),(.70,1.00),(.66,1.30),(.50,1.48),(.54,1.56)],"ding_bronze",40)
    g.lathe((x,y,z+1.50),[(.54,0),(.60,.07),(.40,.16),(.14,.24),(.05,.32)],"ding_bronze",32)
    g.ellipsoid((x,y,z+1.90),(.10,.10,.13),"door_gold")
    for side in (-1,1):
        g.rod((x+side*.52,y,z+1.42),(x+side*.62,y,z+1.86),.055,"ding_bronze",sides=10)
    g.object("夔纹铜鼎","10_庭院陈设",.004)


def stone_lion(x,y,z,angle=0):
    """汉白玉须弥座守门石兽台：端庄挺拔、雕花束腰、鎏金宝珠。"""
    frame = Frame(x,y,z,angle)
    g = Geo()
    # 须弥台基：下枋、下枭、束腰雕花、上枋
    g.box((0,0,.14),(.88,1.08,.28),"lion_stone",frame)
    g.lathe(frame.p(0,0,.28),[(.44,0),(.46,.08),(.38,.16),(.38,.30),(.46,.38),(.44,.46)],"baogu_stone",24)
    g.box((0,0,.82),(.82,1.02,.18),"lion_stone",frame)
    # 雕花圆鼓石
    g.lathe(frame.p(0,0,.91),[(.32,0),(.38,.20),(.36,.40),(.30,.50)],"baogu_stone",24)
    # 顶座瑞兽宝珠冠
    g.lathe(frame.p(0,0,1.41),[(.26,0),(.22,.14),(.14,.24),(.04,.32)],"lion_stone",16)
    g.ellipsoid(frame.p(0,0,1.78),(.12,.12,.14),"door_gold")
    g.object("守门石狮台","10_庭院陈设",.006)


def bronze_crane(x,y,z,angle=0):
    """殿前铜鹤（立姿），face 沿局部 +Y。"""
    frame = Frame(x,y,z,angle)
    g = Geo()
    g.lathe(frame.p(0,0,0),[(.24,.02),(.24,.10),(.16,.18)],"stele_stone",16)
    for side in (-1,1):
        g.rod(frame.p(side*.07,0,.16),frame.p(side*.07,0,.62),.022,"crane_cast",sides=8)
    g.ellipsoid(frame.p(0,0,.78),(.17,.26,.20),"crane_cast")
    g.ellipsoid(frame.p(0,-.20,.82),(.13,.14,.12),"crane_cast")
    g.rod(frame.p(0,.20,.85),frame.p(0,.33,1.28),.045,"crane_cast",.030,10)
    g.ellipsoid(frame.p(0,.36,1.34),(.065,.10,.07),"crane_cast")
    g.rod(frame.p(0,.44,1.33),frame.p(0,.58,1.30),.018,"door_gold",sides=6)
    for side in (-1,1):
        g.ellipsoid(frame.p(side*.17,-.02,.86),(.16,.22,.06),"crane_cast")
    g.object("殿前铜鹤","10_庭院陈设",.005)


def sundial(x,y,z,angle=0):
    """白玉日晷：束腰座+晷盘+晷针。"""
    frame = Frame(x,y,z,angle)
    g = Geo()
    g.lathe(frame.p(0,0,0),[(.42,.02),(.42,.14),(.30,.24),(.24,.34),(.30,.44),(.24,.54)],"sundial_marble",24)
    g.lathe(frame.p(0,0,.54),[(.52,0),(.52,.10),(.46,.16)],"sundial_marble",32)
    g.box((0,0,.74),(.92,.92,.08),"sundial_marble",frame)
    g.rod(frame.p(0,0,.78),frame.p(0,.10,1.26),.018,"door_gold",sides=8)
    g.object("白玉日晷","10_庭院陈设",.004)


def bell_pavilion(x,y,z,angle=0):
    """钟亭：四柱攒尖顶+铭文铸钟。"""
    frame = Frame(x,y,z,angle)
    reserve(frame,3.2,3.2,.3)
    g = Geo()
    for sx in (-1,1):
        for sy in (-1,1):
            g.rod(frame.p(sx*1.05,sy*1.05,.10),frame.p(sx*1.05,sy*1.05,2.70),.11,"pillar_red",sides=14)
            g.lathe(frame.p(sx*1.05,sy*1.05,0),[(.22,.02),(.22,.12),(.16,.20)],"paifang_stone",16)
    for sy in (-1,1):
        g.box((0,sy*1.05,2.62),(2.60,.22,.24),"beam",frame)
    g.box((0,0,2.52),(.20,2.30,.20),"beam",frame)
    g.lathe(frame.p(0,0,.90),[(.42,0),(.50,.14),(.46,.60),(.40,1.05),(.30,1.30),(.22,1.36)],"bell_cast",32)
    g.rod(frame.p(0,0,2.26),frame.p(0,0,2.55),.05,"bell_cast",sides=10)
    g.object("钟亭木构","06_廊桥园墙",.005)
    roof(frame,2.86,3.40,3.40,.95,"钟亭",True)


def drum_pavilion(x,y,z,angle=0):
    """鼓亭：四柱攒尖顶+大鼓钉饰。"""
    frame = Frame(x,y,z,angle)
    reserve(frame,3.2,3.2,.3)
    g = Geo()
    for sx in (-1,1):
        for sy in (-1,1):
            g.rod(frame.p(sx*1.05,sy*1.05,.10),frame.p(sx*1.05,sy*1.05,2.55),.11,"pillar_red",sides=14)
            g.lathe(frame.p(sx*1.05,sy*1.05,0),[(.22,.02),(.22,.12),(.16,.20)],"paifang_stone",16)
    g.box((0,0,1.05),(1.70,.80,.16),"carved_wood",frame)
    g.lathe(frame.p(0,0,1.20),[(.52,0),(.62,.30),(.64,.62),(.58,.92),(.50,1.05)],"drum_leather",32)
    for i in range(12):
        a = TAU*i/12
        g.ellipsoid(frame.p(.585*math.cos(a),.585*math.sin(a),1.50),(.035,.035,.035),"door_gold")
    g.object("鼓亭木构","06_廊桥园墙",.005)
    roof(frame,2.72,3.40,3.40,.92,"鼓亭",True)


def well_pavilion(x,y,z,angle=0):
    """井亭：八角井栏+双柱辘轳小顶。"""
    frame = Frame(x,y,z,angle)
    reserve(frame,2.6,2.6,.2)
    g = Geo()
    g.lathe(frame.p(0,0,0),[(.78,.02),(.82,.14),(.78,.55),(.70,.68),(.62,.72)],"well_stone",8)
    g.lathe(frame.p(0,0,.60),[(.68,0),(.66,.06),(.60,.10)],"well_stone",8)
    for side in (-1,1):
        g.rod(frame.p(side*.95,0,.05),frame.p(side*.95,0,2.30),.085,"pillar_red",sides=12)
    g.rod(frame.p(-.95,0,2.05),frame.p(.95,0,2.05),.05,"carved_wood",sides=10)
    g.lathe(frame.p(0,0,1.95),[(.10,0),(.12,.14),(.10,.22)],"carved_wood",12)
    g.rod(frame.p(0,0,1.95),frame.p(0,0,.75),.008,"bronze",sides=5)
    g.object("井亭栏架","06_廊桥园墙",.005)
    roof(frame,2.45,2.90,2.90,.80,"井亭",False)


def chess_set(x,y,z,angle=0):
    """石棋桌+四鼓凳。"""
    frame = Frame(x,y,z,angle)
    reserve(frame,2.4,2.4,.2)
    g = Geo()
    g.lathe(frame.p(0,0,0),[(.30,.02),(.30,.42),(.55,.50),(.62,.56)],"stele_stone",24)
    g.box((0,0,.62),(1.15,1.15,.10),"chess_jade",frame)
    for i in range(4):
        a = TAU*i/4 + math.pi/4
        sx,sy = 1.05*math.cos(a),1.05*math.sin(a)
        g.lathe(frame.p(sx,sy,0),[(.24,.02),(.30,.16),(.26,.34),(.30,.44),(.24,.50)],"baogu_stone",20)
    g.object("石棋桌椅","10_庭院陈设",.004)


def bixi_stele(x,y,z,angle=0):
    """龟趺御碑，face 沿局部 +Y。"""
    frame = Frame(x,y,z,angle)
    reserve(frame,2.2,3.2,.2)
    g = Geo()
    g.ellipsoid(frame.p(0,0,.52),(.62,.92,.40),"stele_stone")
    g.ellipsoid(frame.p(0,.98,.62),(.24,.30,.22),"stele_stone")
    g.rod(frame.p(0,1.16,.62),frame.p(0,1.34,.68),.07,"stele_stone",sides=8)
    for side in (-1,1):
        for fy in (-.5,.5):
            g.ellipsoid(frame.p(side*.55,fy,.28),(.22,.26,.18),"stele_stone")
    g.box((0,-.10,1.75),(1.15,.28,1.90),"stele_stone",frame)
    g.lathe(frame.p(0,-.10,2.70),[(.62,0),(.50,.16),(.30,.30),(.08,.40)],"stele_stone",16)
    g.box((0,-.26,1.60),(.90,.04,1.30),"paifang_stone",frame)
    g.object("龟趺御碑","10_庭院陈设",.005)


def nine_dragon_wall(x,y,z,angle=0):
    """九龙琉璃照壁，face 沿局部 +Y。壁画独幅横展，拒绝平铺碎花。"""
    frame = Frame(x,y,z,angle)
    reserve(frame,13.2,1.8,.4)
    g = Geo()
    g.box((0,0,.42),(12.6,1.10,.84),"paifang_stone",frame)
    g.box((0,0,.92),(12.9,1.24,.16),"stele_stone",frame)
    g.box((0,0,4.68),(12.8,1.05,.28),"tile",frame)
    g.box((0,0,4.94),(12.2,.60,.22),"tile_dark",frame)
    for sx in (-1,1):
        g.box((sx*6.28,0,2.78),(.56,1.00,3.72),"paifang_stone",frame)
    g.object("九龙照壁基座","02_台基庭院",.006)
    # 壁画面板独立成物：Generated 坐标 0..1 恰好满铺，整壁只此一卷
    # （正中坐龙+两侧行龙的完整构图，龙形蛇身天然耐横向延展）
    mural_mat("dragon_wall_mural")
    panel = Geo()
    panel.box((0,0,2.78),(12.0,.72,3.60),"dragon_wall_mural",frame)
    panel.object("九龙照壁壁画","02_台基庭院",.006)


def mural_mat(key):
    """独幅壁画材质：Generated 坐标一次满铺，整壁只此一卷。"""
    if key in MAT:
        return MAT[key]
    path = os.path.join(TEXTURE_DIR, "tex-nine-dragon-mural.png")
    if not os.path.isfile(path):
        path = os.path.join(TEXTURE_DIR, "tex-nine-dragon-wall.png")
        if not os.path.isfile(path):
            return None
    m = bpy.data.materials.new(key)
    MAT[key] = m
    m.use_nodes = True
    nodes, links = m.node_tree.nodes, m.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    p = nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Roughness"].default_value = .42
    p.inputs["Specular IOR Level"].default_value = .30
    coord = nodes.new("ShaderNodeTexCoord")
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(path, check_existing=True)
    tex.projection = "BOX"
    try:
        tex.projection_blend = 0.12
    except Exception:
        pass
    bump_node = nodes.new("ShaderNodeBump")
    bump_node.inputs["Strength"].default_value = .22
    bump_node.inputs["Distance"].default_value = .06
    links.new(coord.outputs["Generated"], tex.inputs["Vector"])
    links.new(tex.outputs["Color"], p.inputs["Base Color"])
    links.new(tex.outputs["Color"], bump_node.inputs["Height"])
    links.new(bump_node.outputs["Normal"], p.inputs["Normal"])
    links.new(p.outputs["BSDF"], out.inputs["Surface"])
    return m


def canopy_stand(x,y,z):
    """仪仗伞盖：鎏金竿+团花绢伞。"""
    g = Geo()
    g.lathe((x,y,z),[(.22,.02),(.22,.10),(.15,.18)],"door_gold",16)
    g.rod((x,y,z+.14),(x,y,z+3.15),.045,"door_gold",sides=10)
    g.lathe((x,y,z+2.55),[(.06,0),(.62,.28),(.72,.42),(.60,.50),(.20,.58)],"canopy_silk",32)
    for i in range(8):
        a = TAU*i/8
        cx,cy = x+.60*math.cos(a),y+.60*math.sin(a)
        g.rod((cx,cy,z+2.98),(cx,cy,z+2.72),.010,"door_gold",sides=5)
    g.ellipsoid((x,y,z+3.22),(.06,.06,.10),"door_gold")
    g.object("仪仗伞盖","10_庭院陈设",.003)


def lakebed_shallows():
    """环岛浅水带：卵石滩+珊瑚石，半没于水面。"""
    g = Geo()
    n = 26 if QUALITY != "STUDY" else 10
    for i in range(n):
        a = TAU*i/n + .11
        rx_,ry_ = 35.6,32.6
        x = rx_*math.cos(a)
        y = 5.0 + ry_*math.sin(a)
        r = R_LAND.uniform(1.2,2.6)
        g.ellipsoid((x,y,WATER_Z-.22),(r,r*.8,.10),"lakebed")
        for j in range(3):
            aa = a + R_LAND.uniform(-.14,.14)
            cx = (rx_+R_LAND.uniform(-.6,.9))*math.cos(aa)
            cy = 5.0+(ry_+R_LAND.uniform(-.6,.9))*math.sin(aa)
            s = R_LAND.uniform(.14,.38)
            # 水下青灰层岩卵石（弃用艳橙珊瑚，免夺湖光）
            g.ellipsoid((cx,cy,WATER_Z-.16),(s,s*.8,s*.62),"rock")
    g.object("湖底卵石珊瑚","07_池水飞瀑")


def billboard_material(key, filename):
    """RGBA 贴图板材质（tools/make_billboards.py 产物，UV 直贴）。"""
    if key in MAT:
        return MAT[key]
    path = os.path.join(TEXTURE_DIR,"billboards",filename)
    if not os.path.isfile(path):
        return None
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    nodes, links = m.node_tree.nodes, m.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    p = nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Roughness"].default_value = .7
    coord = nodes.new("ShaderNodeTexCoord")
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(path, check_existing=True)
    links.new(coord.outputs["UV"], tex.inputs["Vector"])
    links.new(tex.outputs["Color"], p.inputs["Base Color"])
    links.new(tex.outputs["Alpha"], p.inputs["Alpha"])
    links.new(p.outputs["BSDF"], out.inputs["Surface"])
    try:
        m.surface_render_method = 'DITHERED'
    except Exception:
        try:
            m.blend_method = 'HASHED'
        except Exception:
            pass
    MAT[key] = m
    return m


def billboard_card(name, x,y,z, w,h, key, face_angle=0.0, flat=False, group="09_草花庭石"):
    """单面片一对象（Generated 坐标会随合并体拉伸，故不走 Geo）。"""
    mat = MAT.get(key)
    if mat is None:
        return
    if flat:
        ca,sa = math.cos(face_angle), math.sin(face_angle)
        hw,hh = w/2,h/2
        verts = [(x-hw*ca-hh*sa, y-hw*sa+hh*ca, z),
                 (x+hw*ca-hh*sa, y+hw*sa+hh*ca, z),
                 (x+hw*ca+hh*sa, y+hw*sa-hh*ca, z),
                 (x-hw*ca+hh*sa, y-hw*sa-hh*ca, z)]
    else:
        ca,sa = math.cos(face_angle), math.sin(face_angle)
        hw = w/2
        verts = [(x-hw*ca,y-hw*sa,z),(x+hw*ca,y+hw*sa,z),
                 (x+hw*ca,y+hw*sa,z+h),(x-hw*ca,y-hw*sa,z+h)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts,[],[(0,1,2,3)])
    uvl = me.uv_layers.new(name="UVMap")
    for i,uv in enumerate(((0,0),(1,0),(1,1),(0,1))):
        uvl.data[i].uv = uv
    me.materials.append(mat)
    link_object(name, me, group)


PLANTERS = []
pots = Geo()

for side in (-1,1):
    for y in (-4.8,.5):
        x = side*5.2
        pots.box((x,y,COURT_Z+.18),(1.55,2.1,.36),"stone")
        pots.box((x,y,COURT_Z+.374),(1.31,1.85,.028),"earth")
        PLANTERS.append((x,y,COURT_Z+.40))

BONSAI_POSITIONS = [
    (-5.2,-8.2,COURT_Z),
    (5.2,-8.2,COURT_Z),
    (-6.2,18.8,MAIN_Z),
    (6.2,18.8,MAIN_Z),
]

for x,y,z in BONSAI_POSITIONS:
    pots.lathe((x,y,z),[
        (.74,0),(.76,.11),(.64,.25),(.69,.35),
    ],"ivory",40)
    pots.lathe((x,y,z),[(.61,.34),(.61,.38)],"earth",36)

pots.object("白石花池盆景盆","10_庭院陈设",.009)

furniture = Geo()
for x,y in [(-24.5,14.2),(23.8,15.1),(-23.6,-10.2),(23.0,-15.2)]:
    z = ground_z(x,y)+.48
    furniture.lathe((x,y,z),[
        (.22,0),(.18,.51),(.63,.55),(.63,.65),
    ],"stone",40)

    for i in range(3):
        a = TAU*i/3+.4
        xx,yy = x+.93*math.cos(a),y+.93*math.sin(a)
        furniture.lathe((xx,yy,z),[
            (.22,0),(.26,.12),(.23,.34),(.27,.42),
        ],"ivory",28)

furniture.object("亭中石桌鼓凳","10_庭院陈设")

lived = Geo()
rng_live = random.Random(SEED+91)
for x,y,yaw in ((-4.2,-6.5,.44),(4.2,-6.5,-.44),(-12.0,-8.5,.70),(12.0,-8.5,-.70)):
    lived.box((x,y,COURT_Z+.32),(1.35,.42,.16),"stone")
    for s in (-1,1):
        lived.lathe((x+s*.52,y,COURT_Z+.18),[
            (.20,0),(.22,.10),(.18,.28),(.21,.36),
        ],"stone",16)
for x,y in ((-8.5,-4.5),(8.5,-4.5),(-14.2,5.0),(12.0,-8.5)):
    for _ in range(9):
        lx = x+rng_live.uniform(-.55,.55)
        ly = y+rng_live.uniform(-.45,.45)
        lived.face([
            (lx,ly,COURT_Z+.03),
            (lx+.16,ly+.04,COURT_Z+.03),
            (lx+.09,ly+.12,COURT_Z+.04),
        ],"wood")
for x,y in ((-10.2,-2.4),(10.2,-2.4)):
    lived.lathe((x,y,COURT_Z+.22),[
        (.28,0),(.24,.46),(.72,.50),(.72,.62),
    ],"stone",28)
    for i in range(3):
        a = TAU*i/3+.35
        lived.lathe((x+.95*math.cos(a),y+.95*math.sin(a),COURT_Z+.18),[
            (.20,0),(.24,.10),(.20,.30),(.24,.38),
        ],"stone",16)
for x,y in ((-9.6,-7.2),(9.6,-7.2),(-13.4,-3.2),(13.4,-3.2),(-5.8,-10.4),(5.8,-10.4)):
    for _ in range(14):
        lx = x+rng_live.uniform(-.7,.7)
        ly = y+rng_live.uniform(-.55,.55)
        lived.face([
            (lx,ly,COURT_Z+.03),
            (lx+.22,ly+.05,COURT_Z+.03),
            (lx+.10,ly+.16,COURT_Z+.05),
        ],"wood")
lived.object("庭院石凳残叶","10_庭院陈设")
for x,y in ((-6.5,-1.8),(6.5,-1.8),(-9.2,-6.8),(9.2,-6.8)):
    lantern(x,y,COURT_Z,False)
for x,y,ang in ((18.5,-2.0,.14),(-26.8,-4.5,.61),(-18.5,-8.2,1.66)):
    water_log = Geo()
    water_log.rod(
        (x,y,WATER_Z+.06),(x+1.8*math.cos(ang),y+1.8*math.sin(ang),WATER_Z+.02),
        .09,"wood",.05,8
    )
    water_log.object("水岸倒木","07_池水飞瀑")


# =============================================================================
# 17. 树木共享原型
# =============================================================================

TREE_LIBRARY = defaultdict(list)


def build_tree(kind,seed):
    rng = random.Random(seed)
    g = Geo()
    height = rng.uniform(3.9,5.2)
    lean = rng.uniform(-.34,.34)

    trunk = [
        Vector((0,0,0)),
        Vector((.10,0,height*.23)),
        Vector((lean,.08,height*.49)),
        Vector((lean+.12,-.04,height*.73)),
        Vector((lean+.04,.05,height)),
    ]

    for i in range(len(trunk)-1):
        radius = .17*(1-i*.19)
        g.rod(trunk[i],trunk[i+1],radius,"wood",radius*.70,9)

    if kind == "pine":
        for level in range(7):
            z = height*(.29+level*.095)
            reach = 1.84*(1-level*.094)

            for arm in range(3):
                a = TAU*arm/3+level*.94+rng.uniform(-.17,.17)
                d = Vector((math.cos(a),math.sin(a),0))
                start = Vector((lean*.45,0,z))
                elbow = start+d*reach*.55+Vector((0,0,-.08))
                end = start+d*reach+Vector((0,0,.19))

                g.rod(start,elbow,.067*(1-level*.065),"wood",.032,7)
                g.rod(elbow,end,.032,"wood",.011,6)

                for i in range(max(5,int(17*P["leaf_density"]))):
                    center = start.lerp(end,rng.uniform(.40,1))
                    center += Vector((
                        rng.uniform(-.27,.27),
                        rng.uniform(-.27,.27),
                        rng.uniform(-.04,.22),
                    ))

                    # 针叶团的低矮基底仅负责远景体积；
                    # 外层由实际针叶面片形成轮廓。
                    g.ellipsoid(center,(.24,.19,.07),"pine")

                    for j in range(10):
                        angle = rng.uniform(0,TAU)
                        g.leaf(
                            center,
                            (math.cos(angle),math.sin(angle),rng.uniform(.05,.34)),
                            rng.uniform(.15,.28),.008,
                            "pine",.033
                        )

        g.ellipsoid((lean+.04,.05,height),(.21,.21,.26),"pine")

    else:
        branch_count = 11 if kind == "blossom" else 13

        for branch in range(branch_count):
            a = TAU*branch/branch_count+rng.uniform(-.33,.33)
            z = height*rng.uniform(.36,.78)
            reach = rng.uniform(.84,1.64)

            start = Vector((lean*.4,0,z))
            elbow = start+Vector((
                math.cos(a)*reach*.55,
                math.sin(a)*reach*.55,.45
            ))
            end = start+Vector((
                math.cos(a)*reach,math.sin(a)*reach,
                rng.uniform(.82,1.25)
            ))

            g.rod(start,elbow,.065,"wood",.031,8)
            g.rod(elbow,end,.031,"wood",.0085,6)

            for twig in range(5):
                origin = elbow.lerp(end,.34+twig*.15)
                angle = a+rng.uniform(-1.6,1.6)
                tip = origin+Vector((
                    math.cos(angle)*rng.uniform(.25,.56),
                    math.sin(angle)*rng.uniform(.25,.56),
                    rng.uniform(.12,.31)
                ))
                g.rod(origin,tip,.011,"wood",.003,5)

                for i in range(max(5,int(25*P["leaf_density"]))):
                    center = origin.lerp(tip,rng.random())
                    center += Vector((
                        rng.uniform(-.17,.17),
                        rng.uniform(-.17,.17),
                        rng.uniform(-.08,.18),
                    ))

                    if kind == "blossom":
                        if i%2 == 0:
                            flower(g,center,rng.uniform(.068,.10))
                        else:
                            g.ellipsoid(center,(.043,.043,.037),"pink_light")
                    else:
                        g.leaf(
                            center,
                            (rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-.1,.7)),
                            rng.uniform(.15,.27),
                            rng.uniform(.033,.061),
                            "leaf_light" if i%4 == 0 else "leaf",
                            .12
                        )

        for i in range(max(25,int(90*P["leaf_density"]))):
            a = rng.uniform(0,TAU)
            center = Vector((
                lean+math.cos(a)*rng.uniform(0,.51),
                math.sin(a)*rng.uniform(0,.51),
                height+rng.uniform(-.13,.29),
            ))

            if kind == "blossom":
                flower(g,center,.077)
            else:
                g.leaf(center,(math.cos(a),math.sin(a),.2),
                       .20,.047,"leaf",.10)

    return g.mesh("共享树型_"+kind)


report("构建松树、花树与阔叶树原型")

for kind in ("pine","broad","blossom"):
    for variant in range(4):
        TREE_LIBRARY[kind].append(
            build_tree(kind,SEED+variant*137+len(kind)*409)
        )


def place_tree(kind,x,y,z,scale=1,angle=None):
    mesh = R_TREE.choice(TREE_LIBRARY[kind])
    obj = link_object(
        {"pine":"古松","broad":"翠树","blossom":"桃花"}[kind],
        mesh,"08_松竹花木"
    )
    obj.location = (x,y,z)
    obj.rotation_euler.z = R_TREE.uniform(0,TAU) if angle is None else angle
    obj.scale = (scale,scale,scale*R_TREE.uniform(.95,1.07))
    return obj


HERO_TREES = [
    ("pine",-29.0,11.2,.97),
    ("pine",29.0,16.4,1.03),
    ("pine",-23.1,25.0,1.08),
    ("pine",22.2,28.0,1.10),
    ("blossom",-27.3,-13.5,.70),
    ("blossom",-19.8,-18.5,.64),
    ("blossom",27.1,-12.5,.70),
    ("blossom",20.8,-16.5,.61),
]

CROWN = {"pine": 2.0, "broad": 1.9, "blossom": 1.8}

occupied = []
for kind,x,y,scale in HERO_TREES:
    if in_building(x,y,CROWN[kind]*scale):
        continue
    place_tree(kind,x,y,ground_z(x,y),scale)
    occupied.append((x,y))

target_trees = int(P["trees"]*TREE_DENSITY_MULTIPLIER)
attempts = 0

while len(occupied)<target_trees and attempts<target_trees*150:
    attempts += 1
    x = R_TREE.uniform(-32,32)
    y = R_TREE.uniform(-25,33)

    if y>13:
        kind = R_TREE.choices(["pine","broad","blossom"],[.70,.24,.06])[0]
        scale = R_TREE.uniform(.65,1.03)
    elif y < -14:
        # 南坡秋天不当桃花围墙：松竹为主，桃花只留东西两丛
        west_grove = x < -8 and -22 < y < -15
        east_grove = x > 8 and -22 < y < -15
        if SEASON == "spring":
            kind = R_TREE.choices(["pine","broad","blossom"],[.18,.22,.60])[0]
        elif west_grove or east_grove:
            kind = R_TREE.choices(["pine","broad","blossom"],[.20,.25,.55])[0]
        else:
            kind = R_TREE.choices(["pine","broad","blossom"],[.48,.42,.10])[0]
        scale = R_TREE.uniform(.48,.82)
    else:
        kind = R_TREE.choices(["pine","broad","blossom"],[.28,.48,.24])[0]
        scale = R_TREE.uniform(.44,.74)

    # 树不只树心要躲开建筑：冠幅也得躲开，否则树干穿墙、树冠顶穿屋顶
    if not valid_garden(x,y,True,CROWN[kind]*scale):
        continue
    # 中轴开阔透气：南面中轴 12 米宽礼序走廊禁生杂树，确保远眺雄奇
    if abs(x) < 5.8 and y < -11.0:
        continue
    if any((x-a)**2+(y-b)**2<1.30**2 for a,b in occupied):
        continue

    place_tree(kind,x,y,ground_z(x,y),scale)
    occupied.append((x,y))

for x,y,z in BONSAI_POSITIONS:
    place_tree(
        "pine" if y>10 else "blossom",
        x,y,z+.39,.38 if y>10 else .42
    )

report(f"园林乔木完成：{len(occupied)} 株")


# =============================================================================
# 18. 竹林、草花、落瓣、苔石
# =============================================================================

bamboo = Geo()

for cx,cy in [(-27.1,8.0),(28.0,13.0),(-20.8,27.0),(22.4,-8.5),(-24.6,-6.2)]:
    for i in range(30 if QUALITY != "STUDY" else 14):
        x = cx+R_GRASS.uniform(-1.1,1.1)
        y = cy+R_GRASS.uniform(-1.1,1.1)

        if in_building(x,y):
            continue
        if any(pond_distance(x,y,p)<1.10 for p in PONDS):
            continue

        origin = Vector((x,y,ground_z(x,y)))
        height = R_GRASS.uniform(2.7,4.5)
        lean = Vector((
            R_GRASS.uniform(-.29,.29),
            R_GRASS.uniform(-.29,.29),
            height,
        ))

        for node in range(9):
            a = origin+lean*node/9
            b = origin+lean*(node+1)/9
            bamboo.rod(a,b,.031,"bamboo",sides=7)
            bamboo.rod(a,a+Vector((0,0,.037)),.043,"leaf_light",sides=7)

            if node>3:
                for side in (-1,1):
                    angle = R_GRASS.uniform(0,TAU)
                    d = Vector((math.cos(angle),math.sin(angle),.23))
                    tip = a+d*R_GRASS.uniform(.34,.61)
                    bamboo.rod(a,tip,.007,"bamboo",.002,5)

                    for leaf_index in range(5):
                        root = a.lerp(tip,(leaf_index+1)/6)
                        direction = Vector((
                            d.y*side+d.x*.25,
                            -d.x*side+d.y*.25,-.05
                        ))
                        bamboo.leaf(
                            root,direction,R_GRASS.uniform(.21,.34),
                            .029,"leaf",.12
                        )

bamboo.object("竹林节秆披叶","08_松竹花木")

grass,flowers = Geo(),Geo()


def grass_tuft(x,y,z,scale=1):
    for blade in range(R_GRASS.randint(4,7)):
        a = R_GRASS.uniform(0,TAU)
        h = R_GRASS.uniform(.16,.42)*scale
        w = R_GRASS.uniform(.010,.020)*scale
        base = Vector((
            x+R_GRASS.uniform(-.061,.061),
            y+R_GRASS.uniform(-.061,.061),z
        ))
        side = Vector((math.cos(a),math.sin(a),0))
        bend = Vector((-math.sin(a),math.cos(a),0))*h*.43
        middle = base+Vector((0,0,h*.56))+bend*.31
        tip = base+Vector((0,0,h))+bend
        key = "grass_light" if blade%4 == 0 else "grass"

        grass.face([
            base-side*w,base+side*w,
            middle+side*w*.58,middle-side*w*.58,
        ],key)
        grass.face([
            middle-side*w*.58,middle+side*w*.58,tip
        ],key)


def wildflower(x,y,z,scale=1):
    height = R_GRASS.uniform(.17,.38)*scale
    flowers.rod((x,y,z),(x,y,z+height),.006,"grass",sides=5)
    flowers.leaf((x,y,z+height*.4),(.7,.2,.12),
                 .115*scale,.024,"leaf")
    flower(
        flowers,(x,y,z+height),.072*scale,
        "flower_white" if R_GRASS.random()<.45 else "pink_light"
    )


count = 0
for attempt in range(P["grass"]*17):
    if count>=P["grass"]:
        break
    x,y = R_GRASS.uniform(-32,32),R_GRASS.uniform(-25,33)
    if not valid_garden(x,y):
        continue
    grass_tuft(x,y,ground_z(x,y)+.024,R_GRASS.uniform(.65,1.04))
    count += 1

count = 0
for attempt in range(P["flowers"]*20):
    if count>=P["flowers"]:
        break
    x,y = R_GRASS.uniform(-31,31),R_GRASS.uniform(-24,32)
    if not valid_garden(x,y):
        continue
    wildflower(x,y,ground_z(x,y)+.028,R_GRASS.uniform(.8,1.33))
    count += 1

for x,y,z in PLANTERS:
    for i in range(42):
        xx = x+R_GRASS.uniform(-.57,.57)
        yy = y+R_GRASS.uniform(-.83,.83)
        grass_tuft(xx,yy,z,.69)
        if i%2 == 0:
            wildflower(xx,yy,z,1.08)

grass.object("草甸合批","09_草花庭石")
flowers.object("花丛合批","09_草花庭石")

petals = Geo()
for kind,x,y,scale in HERO_TREES:
    if kind != "blossom":
        continue
    for i in range(70):
        a = R_GRASS.uniform(0,TAU)
        radius = math.sqrt(R_GRASS.random())*1.8
        xx,yy = x+radius*math.cos(a),y+radius*math.sin(a)
        zz = ground_z(xx,yy)+.023
        if any(pond_distance(xx,yy,p)<1 for p in PONDS):
            zz = WATER_Z+.013

        size = R_GRASS.uniform(.022,.043)
        petals.face([
            (xx-size,yy,zz),
            (xx,yy-size*.65,zz+.004),
            (xx+size,yy,zz),
            (xx,yy+size*.65,zz+.002),
        ],"pink_light")

petals.object("桃阴落瓣","09_草花庭石")

stones = Geo()
for i in range(180 if QUALITY != "STUDY" else 70):
    x,y = R_LAND.uniform(-32,32),R_LAND.uniform(-25,33)
    if not valid_garden(x,y):
        continue
    z = ground_z(x,y)
    sx,sy,sz = (
        R_LAND.uniform(.23,.73),
        R_LAND.uniform(.21,.62),
        R_LAND.uniform(.21,.63),
    )
    stones.ellipsoid((x,y,z),(sx,sy,sz),"rock")
    if i%2 == 0:
        stones.ellipsoid(
            (x-.03,y,z+sz*.74),
            (sx*.70,sy*.72,.073),"moss"
        )

stones.object("散落苔石","09_草花庭石")


# =============================================================================
# 19. 仙鹤
# =============================================================================

def crane(x,y,z,scale=.8,angle=0,flying=False):
    frame = Frame(x,y,z,angle)
    g = Geo()

    def p(x,y,z):
        return frame.p(x*scale,y*scale,z*scale)

    def ell(center,size,key):
        g.ellipsoid(p(*center),tuple(s*scale for s in size),key)

    if not flying:
        ell((0,0,.85),(.18,.32,.23),"feather")
        ell((0,.20,.81),(.15,.20,.145),"feather_dark")

        for side in (-1,1):
            g.rod(p(side*.08,0,.04),p(side*.07,0,.74),
                  .015*scale,"feather_dark",sides=7)
            for spread in (-1,0,1):
                g.rod(
                    p(side*.08,0,.034),
                    p(side*.08+spread*.043,-.125,.02),
                    .0065*scale,"feather_dark",sides=5
                )

        line(catmull([
            p(0,-.18,1),p(0,-.27,1.24),
            p(0,-.15,1.45),p(0,-.24,1.65),
        ],8),"feather",.046*scale,"10_庭院陈设")

        ell((0,-.26,1.66),(.058,.087,.063),"feather")
        ell((0,-.26,1.712),(.035,.049,.021),"crane_red")
        g.rod(p(0,-.33,1.65),p(0,-.54,1.63),
              .021*scale,"bronze",.001,8)

        for side in (-1,1):
            ell((side*.051,-.29,1.67),(.010,.010,.010),"feather_dark")
            for i in range(7):
                g.rod(
                    p(side*.15,-.10+i*.028,.94),
                    p(side*(.16+i*.008),.29+i*.022,.70),
                    .020*scale,
                    "feather" if i<4 else "feather_dark",
                    .006*scale,6
                )
    else:
        ell((0,0,0),(.115,.33,.105),"feather")
        g.rod(p(0,-.18,0),p(0,-.64,.034),
              .028*scale,"feather",.020*scale,8)
        ell((0,-.67,.034),(.040,.065,.036),"feather")
        g.rod(p(0,-.73,.034),p(0,-.92,.02),
              .013*scale,"bronze",.001,6)

        for side in (-1,1):
            root = p(side*.1,-.04,0)
            elbow = p(side*.55,.02,.18)
            tip = p(side*1.04,.25,.30)
            g.face([root,elbow,tip,p(side*.53,.33,.02)],"feather")

            for i in range(9):
                t = i/8
                a = elbow.lerp(tip,t)
                b = a+frame.d(side*.08,.27+.10*t,-.06)*scale
                g.rod(a,b,.026*scale,
                      "feather_dark" if i>3 else "feather",
                      .0045*scale,6)

            g.rod(p(side*.044,.20,0),p(side*.063,.69,-.04),
                  .008*scale,"feather_dark",sides=5)

    g.object("远空云鹤" if flying else "池边仙鹤","10_庭院陈设")


crane(-20.1,-4.6,ground_z(-20.1,-4.6),.80,-.3)
crane(-20.6,-3.6,ground_z(-20.6,-3.6),.65,.4)
crane(28.0,7.1,ground_z(28.0,7.1),.76,.6)

if ENABLE_BIRDS:
    for x,y,z,s,a in [
        (-12,34,24,.61,-.3),
        (-9,36,25,.48,-.2),
        (-6.6,38,25.5,.37,-.1),
    ]:
        crane(x,y,z,s,a,True)
    for i in range(18):
        a = TAU*i/18
        cx, cy = 18*math.cos(a), 8+22*math.sin(a)
        if in_building(cx, cy, 3):
            continue
        crane(
            cx, cy,
            19.5+2.4*math.sin(i*1.7),
            .28+.12*(i%3),
            a+.4,
            True
        )
    for i in range(16):
        a = .4 + TAU*i/16
        cx, cy = -6+11*math.cos(a), 28+9*math.sin(a)
        if in_building(cx, cy, 3):
            continue
        crane(
            cx, cy,
            16.5+1.6*math.sin(i*1.3),
            .24+.08*(i%4),
            a-.5,
            True
        )


# =============================================================================
# 19b. 洞天扩张：外岛、桥、塔、游鱼
# =============================================================================

def satellite_island(name, cx, cy, radius, height):
    """外岛台面必须高出水面，崖脚沉入湖底。height 是岛心台面标高。"""
    g = Geo()
    n = 28 if QUALITY == "STUDY" else 48
    rings = 6 if QUALITY == "STUDY" else 10
    deck = max(height, WATER_Z + 1.05)
    verts = [(cx, cy, deck)]
    faces = []
    for j in range(1, rings+1):
        t = j/rings
        for i in range(n):
            a = TAU*i/n + .08*j
            k = 1+.06*math.sin(i*1.7+j)
            x = cx + radius*t*k*math.cos(a)
            y = cy + radius*t*k*.86*math.sin(a)
            if t < 0.62:
                z = deck - t*0.28 + .08*math.sin(i+j)
            else:
                u = (t-0.62)/0.38
                z = deck - 0.18 - u*(deck - WATER_Z + 2.55) + .10*math.sin(i+j)
            verts.append((x, y, z))
    for i in range(n):
        faces.append((0, 1+i, 1+(i+1)%n))
    for j in range(rings-1):
        a = 1+j*n
        b = a+n
        for i in range(n):
            ni = (i+1)%n
            faces.extend([(a+i, b+i, b+ni), (a+i, b+ni, a+ni)])
    g.indexed(verts, faces, "rock", True)
    g.object(name, "01_山体地形")
    return deck


def school_of_fish(px, py, count=24):
    g = Geo()
    for i in range(count):
        a = R_LAND.uniform(0, TAU)
        r = math.sqrt(R_LAND.random()) * 2.4
        x = px + r*math.cos(a)
        y = py + r*math.sin(a)
        z = WATER_Z - R_LAND.uniform(.12, .55)
        s = R_LAND.uniform(.06, .11)
        g.ellipsoid((x, y, z), (s*1.8, s*.55, s*.45), "koi")
        g.face([
            (x-s*1.6, y, z),
            (x-s*2.3, y-s*.7, z),
            (x-s*2.3, y+s*.7, z),
        ], "koi")
    g.object("池中游鱼", "07_池水飞瀑")


if ENABLE_M1_SATURATION:
    east_z = satellite_island("东塔岛", 48.0, 6.0, 7.4, 5.20)
    west_z = satellite_island("西亭岛", -47.0, 8.0, 6.8, 5.05)
    north_z = satellite_island("北崖阁岛", 4.0, 52.0, 8.2, 6.35)
    south_z = satellite_island("南迎客矶", 0.0, -46.0, 10.4, 5.25)

    hall("东塔岛琉璃塔", 48.0, 6.0, east_z+.05, 2.4, 2.4, 3.6, open_hall=True, imperial=True)
    hall("东塔岛上层", 48.0, 6.0, east_z+4.1, 1.7, 1.7, 2.2, open_hall=True, imperial=True)
    octagonal_pavilion(-47.0, 8.0, west_z+.05, 1.55, 2.05)
    hall("北崖阁", 4.0, 52.0, north_z+.08, 4.2, 3.1, 2.2, open_hall=True)
    hall("南迎客亭", 0.0, -46.0, south_z+.06, 3.2, 2.6, 1.7, open_hall=True)

    # 东桥西桥：solve_bridges 解算，两端岸上/岛内平台，桥面与岛台面齐平
    arch_bridge(37.9, 5.8, 11.6, 1.25, -1.54, 5.08, 1.15)
    arch_bridge(-37.5, 7.3, 11.1, 1.25, 1.49, 4.93, 1.15)

    stairs("南矶石阶", (0, -42.4, 5.16), (0, -26.9, 4.04), 2.4, 22)
    stairs("北崖石阶", (2.2, 34.5, 4.45), (3.4, 48.6, 6.23), 1.8, 26, False)

    se_z = satellite_island("东南散岛", 38.0, -28.0, 5.4, 4.80)
    nw_z = satellite_island("西北散岛", -36.0, 34.0, 5.8, 5.00)
    ne_z = satellite_island("东北散岛", 36.0, 36.0, 5.6, 4.95)
    sw_z = satellite_island("西南散岛", -34.0, -30.0, 5.2, 4.75)
    octagonal_pavilion(38.0, -28.0, se_z+.05, 1.25, 1.7)
    hall("西北散亭", -36.0, 34.0, nw_z+.06, 2.6, 2.4, 1.6, open_hall=True)
    hall("东北散阁", 36.0, 36.0, ne_z+.06, 2.8, 2.5, 1.8, open_hall=True)
    octagonal_pavilion(-34.0, -30.0, sw_z+.05, 1.20, 1.65)
    arch_bridge(29.9, -20.2, 16.6, 1.25, -2.38, 4.68, 1.35)
    arch_bridge(-28.6, 28.4, 12.2, 1.25, 0.91, 4.88, 1.15)
    arch_bridge(27.3, 30.6, 14.3, 1.25, -1.05, 4.83, 1.15)
    arch_bridge(-27.1, -22.1, 15.4, 1.25, 2.47, 4.63, 1.35)

    for px, py, _, _ in PONDS:
        school_of_fish(px, py, 36 if QUALITY != "STUDY" else 16)

    for i in range(12):
        lantern(48+1.6*math.cos(TAU*i/12), 6+1.6*math.sin(TAU*i/12), east_z+.2, i%3 == 0)
    for i in range(8):
        a = TAU*i/8
        lantern(-47+1.35*math.cos(a), 8+1.35*math.sin(a), west_z+.15, False)
        lantern(4+1.7*math.cos(a), 52+1.7*math.sin(a), north_z+.12, i%2 == 0)
        lantern(1.4*math.cos(a), -46+1.4*math.sin(a), south_z+.12, False)

    rocks = Geo()
    for cx, cy, z0, n in [
        (4.0, 52.0, north_z, 14),
        (0.0, -46.0, south_z, 10),
        (38.0, -28.0, se_z, 8),
        (-36.0, 34.0, nw_z, 8),
        (36.0, 36.0, ne_z, 8),
        (-34.0, -30.0, sw_z, 8),
    ]:
        for i in range(n):
            a = TAU*i/n + .4
            r = 2.2 + .7*(i%3)
            rocks.ellipsoid(
                (cx+r*math.cos(a), cy+r*.8*math.sin(a), z0+.05),
                (.35+.12*(i%3), .28+.1*(i%2), .22+.08*(i%4)),
                "rock"
            )
    rocks.object("外岛庭石", "09_草花庭石")

    for x, y, z, kind, scale in [
        (6.8, 50.2, north_z, "pine", .72),
        (1.2, 54.0, north_z, "pine", .64),
        (-2.2, -44.2, south_z, "blossom", .48),
        (2.4, -47.6, south_z, "pine", .42),
        (36.2, -26.4, se_z, "blossom", .40),
        (-34.2, 32.4, nw_z, "pine", .55),
        (46.2, 8.4, east_z, "pine", .50),
        (-45.2, 6.2, west_z, "blossom", .46),
        (34.4, 34.2, ne_z, "pine", .48),
        (-32.2, -28.4, sw_z, "blossom", .42),
        (49.6, 8.8, east_z, "blossom", .38),
        (45.4, 3.6, east_z, "pine", .44),
        (50.2, 5.2, east_z, "broad", .40),
        (46.8, 9.6, east_z, "pine", .36),
        (-48.6, 9.8, west_z, "pine", .42),
        (-44.2, 5.4, west_z, "broad", .38),
        (-49.0, 6.6, west_z, "pine", .40),
        (-45.8, 10.6, west_z, "blossom", .36),
        (2.4, 49.2, north_z, "broad", .50),
        (9.4, 53.8, north_z, "pine", .46),
        (0.4, 54.8, north_z, "blossom", .38),
        (8.8, 48.2, north_z, "pine", .42),
        (-3.6, -47.2, south_z, "pine", .36),
        (1.0, -43.8, south_z, "blossom", .34),
        (3.8, -45.4, south_z, "broad", .32),
        (-1.2, -48.6, south_z, "pine", .38),
        (39.6, -29.6, se_z, "pine", .34),
        (36.8, -25.2, se_z, "broad", .32),
        (40.2, -26.8, se_z, "pine", .30),
        (35.4, -29.0, se_z, "blossom", .33),
        (-37.6, 35.6, nw_z, "blossom", .36),
        (-33.2, 31.6, nw_z, "broad", .40),
        (-38.2, 32.8, nw_z, "pine", .38),
        (-34.8, 36.2, nw_z, "pine", .34),
        (37.6, 37.8, ne_z, "blossom", .36),
        (34.8, 33.4, ne_z, "pine", .40),
        (38.4, 34.6, ne_z, "broad", .34),
        (33.6, 37.0, ne_z, "pine", .32),
        (-35.6, -31.6, sw_z, "pine", .34),
        (-32.8, -27.6, sw_z, "broad", .32),
        (-36.2, -28.8, sw_z, "pine", .30),
        (-31.6, -31.2, sw_z, "blossom", .33),
    ]:
        place_tree(kind, x, y, z+.02, scale)

    insects = Geo()
    for i in range(48 if QUALITY != "STUDY" else 22):
        a = R_LAND.uniform(0, TAU)
        r = R_LAND.uniform(8, 22)
        x, y = r*math.cos(a), 4+r*.7*math.sin(a)
        z = 6.2 + R_LAND.uniform(0, 3.5)
        s = R_LAND.uniform(.018, .035)
        insects.ellipsoid((x, y, z), (s*1.6, s, s*.4), "gold")
        insects.face([
            (x, y, z),
            (x+s*2.4, y+s*1.1, z+.02),
            (x+s*2.4, y-s*1.1, z+.02),
        ], "pink_light")
    insects.object("庭空飞虫", "10_庭院陈设")

    extra_reeds = Geo()
    for px, py, rx, ry in PONDS:
        for i in range(28 if QUALITY != "STUDY" else 14):
            a = R_LAND.uniform(0, TAU)
            x = px + rx*1.08*math.cos(a)
            y = py + ry*1.08*math.sin(a)
            z = max(WATER_Z-.02, ground_z(x, y))
            h = R_LAND.uniform(.45, .95)
            extra_reeds.rod((x, y, z), (x+.08*math.cos(a), y+.08*math.sin(a), z+h), .006, "grass", sides=5)
            extra_reeds.ellipsoid((x, y, z+h), (.02, .02, .12), "reed")
    extra_reeds.object("池边芦荻加密", "09_草花庭石")

    # 各外岛桥头垂花门：统一由 solve_bridges 解算，落在岛内平台（t≈0.42），门向顺桥向
    hanging_flower_gate(44.9, 5.9, 5.10, -1.54)
    hanging_flower_gate(-44.1, 7.8, 4.95, 1.49)
    hanging_flower_gate(3.5, 49.2, 6.26, 0.17)
    hanging_flower_gate(0.0, -42.4, 5.16, 3.14)
    hanging_flower_gate(36.3, -26.7, 4.70, -2.38)
    hanging_flower_gate(-34.1, 32.7, 4.90, 0.91)
    hanging_flower_gate(34.2, 34.7, 4.85, -1.05)
    hanging_flower_gate(-32.5, -28.7, 4.65, 2.47)

    hall("东塔侧亭", 51.6, 3.2, east_z+.04, 2.05, 2.05, 1.45, open_hall=True)
    hall("西亭侧榭", -50.2, 10.4, west_z+.04, 2.05, 2.05, 1.4, open_hall=True)
    hall("北崖侧亭", 7.6, 54.2, north_z+.04, 2.15, 2.0, 1.5, open_hall=True)
    hall("南矶侧亭", 3.4, -48.2, south_z+.04, 2.0, 1.9, 1.35, open_hall=True)

    # G8 仙宫群：西苑东苑北崖 + 四座新外岛，体量小于正殿，避开中轴
    hall("西苑抱琴水榭", -23.6, -10.2, ground_z(-23.6, -10.2)+.07, 3.6, 2.6, 2.00, angle=.10, open_hall=True)
    hall("西苑翠微丹室", -23.4, 21.6, ground_z(-23.4, 21.6)+.07, 4.0, 3.0, 2.30, angle=-.06)
    octagonal_pavilion(-30.4, 2.4, ground_z(-30.4, 2.4)+.06, 1.35, 2.05)
    hall("西苑松风幽轩", -30.2, -5.4, ground_z(-30.2, -5.4)+.07, 3.2, 2.4, 1.90, angle=-.05, open_hall=True)
    hall("东苑流霞别馆", 23.2, 20.8, ground_z(23.2, 20.8)+.07, 4.0, 2.8, 2.25, angle=.07)
    hall("东苑含芳水轩", 23.0, -15.2, ground_z(23.0, -15.2)+.07, 3.6, 2.6, 2.00, angle=-.08, open_hall=True)
    hall("东苑连云敞榭", 30.6, 7.4, ground_z(30.6, 7.4)+.07, 3.2, 2.4, 1.85, angle=.05, open_hall=True)
    hall("北崖玄览山堂", -10.4, 33.6, ground_z(-10.4, 33.6)+.07, 4.0, 2.8, 2.20, angle=-.06)
    octagonal_pavilion(8.2, 33.8, ground_z(8.2, 33.8)+.06, 1.35, 2.05)
    hall("北崖凌飞瀑榭", -16.8, 31.2, ground_z(-16.8, 31.2)+.07, 3.4, 2.4, 1.95, angle=.08, open_hall=True)
    hall("北崖掩翠曲轩", -4.8, 34.6, ground_z(-4.8, 34.6)+.07, 2.8, 2.1, 1.75, angle=.05, open_hall=True)
    yz_z = satellite_island("瀛洲散岛", 20.0, -42.0, 9.2, 5.15)
    hall("瀛洲采芝轩", 20.0, -42.0, yz_z+.06, 3.4, 2.6, 1.90, angle=-.07, open_hall=True)
    fz_z = satellite_island("方丈浮矶", -20.0, -44.0, 8.8, 5.10)
    hall("方丈凝神阁", -20.0, -44.0, fz_z+.06, 3.6, 2.8, 2.10, angle=.06)
    pl_z = satellite_island("蓬莱霞峰", -46.0, 24.0, 6.5, 5.05)
    octagonal_pavilion(-46.0, 24.0, pl_z+.06, 1.45, 2.10)
    bx_z = satellite_island("碧虚云台", 46.0, 24.0, 6.6, 5.10)
    hall("碧虚水殿", 46.0, 24.0, bx_z+.06, 3.8, 2.8, 2.05, angle=.07, open_hall=True)
    corridor(-23.2, 4.8, COURT_Z, 2.6, roof_width=1.42, roof_rise=.36, roof_overhang=.08)
    corridor(23.2, 4.8, COURT_Z, 2.6, roof_width=1.42, roof_rise=.36, roof_overhang=.08)
    # 燕云水巷：廊桥必须踩上岛岸，不能停在水心。（solve_bridges 解算值）
    # 瀛洲北岸 ↔ 主岛东南岸
    arch_bridge(15.2, -29.9, 16.7, 1.25, -2.82, 5.03, 1.35)
    # 方丈北岸 ↔ 主岛西南岸
    arch_bridge(-15.1, -31.0, 18.8, 1.25, 2.82, 4.98, 1.35)
    # 蓬莱东岸 ↔ 主岛西岸
    arch_bridge(-36.3, 18.9, 14.6, 1.25, 1.02, 4.93, 1.15)
    # 碧虚西岸 ↔ 主岛东岸
    arch_bridge(36.1, 19.5, 14.4, 1.25, -1.10, 4.98, 1.15)

    outer_reeds = Geo()
    for cx, cy, radius in (
        (20.0, -42.0, 9.2), (-20.0, -44.0, 8.8), (0.0, -46.0, 10.4),
        (46.0, 24.0, 6.6), (-46.0, 24.0, 6.5), (38.0, -28.0, 5.4),
    ):
        for i in range(14 if QUALITY != "STUDY" else 8):
            a = TAU*i/14 + 0.18
            x = cx + (radius + 0.55)*math.cos(a)
            y = cy + (radius + 0.55)*0.86*math.sin(a)
            z = WATER_Z - 0.02
            h = R_LAND.uniform(0.55, 1.15)
            outer_reeds.rod((x, y, z), (x + 0.08*math.cos(a), y + 0.08*math.sin(a), z + h), .007, "grass", sides=5)
            outer_reeds.ellipsoid((x, y, z + h), (.022, .022, .13), "reed")
    outer_reeds.object("外湖芦荻", "09_草花庭石")

    # ── G16 燕云仪仗精修布点：中轴开门见山、空间留白、晨钟暮鼓、水岸照壁 ──
    # 1. 牌坊落座南极迎仙轴端（留出整整 12.4 米宽敞平旷的前庭大石坪）
    stone_paifang(0, -23.8, ground_z(0,-23.8)+.02, 0)
    for side in (-1,1):
        # 经幢退至两侧仪仗线，不挡正视
        dharani_pillar(side*6.8, -21.0, ground_z(side*6.8,-21.0)+.02)
        # 前庭仪门外汉白玉雕花守门台
        stone_lion(side*3.6, -14.5, COURT_Z+.02, math.pi)
        # 正殿大踏跺前设双铜鼎
        bronze_ding(side*4.8, 5.2, COURT_Z+.02)
        # 正殿高台仙禽铜鹤
        bronze_crane(side*6.4, 8.6, MAIN_Z+.02, math.pi)
    # 汉白玉日晷
    sundial(6.9, 9.6, MAIN_Z+.02, math.pi)
    # 晨钟暮鼓：端坐前庭主台基东西两翼（左钟右鼓，各得其所）
    bell_pavilion(11.8, -11.4, COURT_Z+.02, 0)
    drum_pavilion(-11.8, -11.4, COURT_Z+.02, 0)
    # 后苑清供
    well_pavilion(10.5, 25.0, BACK_Z+.02, 0)
    chess_set(-22.0, 16.0, ground_z(-22.0,16.0)+.02, .3)
    bixi_stele(-10.0, 23.2, BACK_Z+.02, math.pi)
    # 九龙琉璃照壁：移至东苑开阔湖畔，临波照影，气势非凡
    nine_dragon_wall(28.0, -18.0, ground_z(28.0,-18.0)+.02, math.pi*0.75)
    lakebed_shallows()

    # G16 贴图板：水面落瓣与浮水莲叶（保留纯净水生点缀）
    if billboard_material("bb_lotus", "tex-lotus-leaf-pad.png"):
        n_bb = 18 if QUALITY != "STUDY" else 6
        for i in range(n_bb):
            px,py,prx,pry = PONDS[i%2]
            a = TAU*i/n_bb + .37
            rr = R_LAND.uniform(.25,.85)
            x = px + prx*rr*math.cos(a)
            y = py + pry*rr*math.sin(a)
            s = R_LAND.uniform(.5,1.1)
            billboard_card("莲叶贴板", x,y,WATER_Z+.012, s,s, "bb_lotus", R_LAND.uniform(0,TAU), flat=True)
    if billboard_material("bb_petal", "tex-peach-petal-cluster.png"):
        n_bb = 24 if QUALITY != "STUDY" else 8
        for i in range(n_bb):
            px,py,prx,pry = PONDS[i%2]
            a = TAU*i/n_bb + .83
            rr = R_LAND.uniform(.30,.95)
            x = px + prx*rr*math.cos(a)
            y = py + pry*rr*math.sin(a)
            s = R_LAND.uniform(.25,.55)
            billboard_card("浮花贴板", x,y,WATER_Z+.018, s,s, "bb_petal", R_LAND.uniform(0,TAU), flat=True)
    if billboard_material("bb_reed", "tex-reed-tassel.png"):
        n_bb = 22 if QUALITY != "STUDY" else 8
        for i in range(n_bb):
            px,py,prx,pry = PONDS[i%2]
            a = TAU*i/n_bb + .19
            x = px + prx*1.04*math.cos(a)
            y = py + pry*1.04*math.sin(a)
            h = R_LAND.uniform(1.1,1.9)
            billboard_card("芦荻贴板", x,y,WATER_Z-.05, h*.8,h, "bb_reed", a+math.pi/2)

    def cloud_lamp_post(x, y, z, name):
        g = Geo()
        g.lathe((x, y, z), [
            (.18, 0), (.20, .12), (.12, .22), (.09, 2.35),
        ], "lantern_stone", 12)
        g.box((x, y, z+2.42), (.42, .42, .10), "bronze")
        g.object(name, "10_庭院陈设")
        lantern(x, y, z+2.48, False)

    posts = 36 if QUALITY != "STUDY" else 24
    for i in range(posts):
        a = TAU * i / posts
        # 主岛外缘，躲开中轴迎仙长阶和四正桥落点
        if abs(math.cos(a)) < .18 and math.sin(a) < -.55:
            continue
        r = 31.6 + 1.1 * math.sin(i * 1.7)
        x = r * math.cos(a)
        y = 5.0 + r * .90 * math.sin(a)
        cloud_lamp_post(x, y, 4.02, f"云廊灯柱_{i:02d}")

    path_lamps = 0
    for a, b, half in PATH_SEGMENTS:
        a, b = Vector((a[0], a[1], 0)), Vector((b[0], b[1], 0))
        delta = b - a
        if delta.length < 2.4:
            continue
        mid = a.lerp(b, .5)
        side = Vector((-delta.y, delta.x, 0))
        if side.length < 1e-6:
            continue
        side.normalize()
        for sign in (-1, 1):
            q = mid + side * sign * (half + .42)
            if in_building(q.x, q.y, .6):
                continue
            if abs(q.x) < 3.2 and q.y < -12:
                continue
            lantern(q.x, q.y, ground_z(q.x, q.y), False)
            path_lamps += 1
            if path_lamps >= 28:
                break
        if path_lamps >= 28:
            break


# =============================================================================
# 20. 飞瀑
# =============================================================================

FALL_ENDS = []

if ENABLE_WATERFALLS:
    fall_geo = Geo()

    for x,y,width,length in [
        (-31.2,-3.4,.98,18.5),
        (31.5,7.0,.79,16.6),
        (-10.2,32.0,.60,12.9),
        (6.4,55.4,2.05,13.5),
    ]:
        top = ground_z(x,y)
        FALL_ENDS.append((x,y,top-length))

        fall_geo.face([
            (x-width*.6,y+1.1,top+.02),
            (x+width*.6,y+1.1,top+.02),
            (x+width*.5,y,top),
            (x-width*.5,y,top),
        ],"water")

        strands = 24 if QUALITY != "STUDY" else 10
        for j in range(strands):
            offset = (j/(strands-1)-.5)*width
            points = []
            for k in range(64):
                t = k/63
                points.append((
                    x+offset+.075*math.sin(t*11+j*.6)*t,
                    y-.42*t-.045*math.sin(t*8+j),
                    top-length*t,
                ))
            line(points,"foam" if j%5 == 0 else "fall",
                 R_LAND.uniform(.011,.028),"07_池水飞瀑")

        for i in range(48):
            t = R_LAND.uniform(.13,.98)
            s = R_LAND.uniform(.01,.021)
            fall_geo.ellipsoid(
                (
                    x+R_LAND.uniform(-width,width),
                    y+R_LAND.uniform(-.53,.33),
                    top-length*t,
                ),
                (s,s,s*R_LAND.uniform(2,5)),
                "foam"
            )

    fall_geo.object("飞瀑水口与飞珠","07_池水飞瀑")


# =============================================================================
# 21. 远山
# =============================================================================

def mountain_ridge(g,x,y,z,span,thickness,height,key,rng):
    """黑神话式叠峦：主峰偏置黄金位 + 不对称肩台 + 削顶断崖 + 冲沟石肋 + 层理错台。
    阳坡凹曲舒展、阴坡陡立截落，彻底打碎圆锥感。返回脊线点供松簇散布。"""
    slices, rings = 44, 24
    peak_t = rng.uniform(0.36, 0.46) if rng.random() < .6 else rng.uniform(0.54, 0.64)
    shoulder_dir = 1 if peak_t < .5 else -1
    shoulder_t = peak_t + shoulder_dir * rng.uniform(0.25, 0.32)
    shoulder_h = height * rng.uniform(0.52, 0.62)
    table_cut = height * rng.uniform(0.86, 0.93)
    seed_k = rng.uniform(0, TAU)
    half_t = thickness / 2
    crest = []

    vertices = []
    for i in range(slices):
        t = i / (slices - 1)
        cx = x + (t - 0.5) * span
        h_main = math.exp(-((t - peak_t) ** 2) / 0.045) * height
        h_shoulder = math.exp(-((t - shoulder_t) ** 2) / 0.075) * shoulder_h
        raw_h = max(h_main, h_shoulder) * (math.sin(t * math.pi) ** 0.6)
        crest_h = min(raw_h, table_cut)
        spine_y = y + math.sin(t * math.pi * 2.2 + seed_k) * (half_t * 0.44)
        crest.append((cx, spine_y, z + crest_h))
        for j in range(rings):
            s = j / (rings - 1)
            side = s * 2 - 1
            if side < 0:
                ts = abs(side)
                y_off = -half_t * (ts ** 1.1)
                z_local = (1 - ts ** 1.4) * crest_h
            else:
                y_off = half_t * 0.8 * (side ** 0.85)
                z_local = ((1 - side) ** 0.75) * crest_h
            rib = math.sin(t * 24 + s * 4 + seed_k) * 0.13 * crest_h * (1 - abs(side))
            gully = math.sin(t * 12 + seed_k) * 0.09 * crest_h
            # 层理断崖：横向岩层错台，打出黑神话式皴法岩骨
            strata = math.sin(z_local * 1.15 + seed_k * 2.0) * 0.055 * crest_h * (abs(side) ** 1.2)
            vz = z + max(0.0, z_local + rib + gully)
            vx = cx + math.sin(s * math.pi) * math.sin(t * 17 + seed_k) * 0.5
            vertices.append((vx, spine_y + y_off + math.copysign(strata, y_off if y_off else 1), vz))

    faces = []
    for i in range(slices - 1):
        for j in range(rings - 1):
            a = i * rings + j
            b = a + 1
            c = (i + 1) * rings + j + 1
            d = (i + 1) * rings + j
            faces.extend([(a, b, c), (a, c, d)])
    g.indexed(vertices, faces, key, True)
    return crest


def distant_peak(name,x,y,z,rx,ry,height,depth,key,seed):
    rng = random.Random(seed)
    g = Geo()
    span = max(rx, ry) * rng.uniform(5.8, 7.4)
    thick = min(rx, ry) * rng.uniform(1.6, 2.2)
    crest = mountain_ridge(g, x, y, z - height * 0.08, span, thick, height, key, rng)
    if height > 8:
        mountain_ridge(
            g,
            x + rng.uniform(-span * 0.18, span * 0.18),
            y + rng.uniform(-2.4, 2.4),
            z - height * 0.16,
            span * 0.62,
            thick * 0.72,
            height * rng.uniform(0.45, 0.62),
            key,
            rng,
        )
    if key == "far_near" and KIT.get("ridge_pines", True):
        # 近远山林冠暗示：仅脊顶高处落小簇墨松，破光滑剪影、立尺度感
        # （低处/大簇会在淡色山体上糊成黑洞，已实证）
        for px, py, pz in crest:
            if rng.random() < 0.30 and pz > z + height * 0.52:
                g.ellipsoid(
                    (px + rng.uniform(-.5, .5), py + rng.uniform(-.5, .5), pz + .26),
                    (rng.uniform(.38, .68), rng.uniform(.38, .68), rng.uniform(.26, .44)),
                    "pine"
                )
    g.object(name,"11_远山云气")


for i,data in enumerate([
    (-42,42,0,6.4,5.3,10,12,"far_near"),
    (42,46,1,7.1,6.1,14,14,"far_near"),
    (-27,58,2,7.4,6.3,19,17,"far_mid"),
    (21,63,1,8.1,7.1,17,17,"far_mid"),
    (-52,73,2,8.4,8.1,23,16,"far_far"),
    (-7,80,1,10.1,8.1,26,18,"far_far"),
    (46,84,0,11.1,9.1,26,18,"far_far"),
]):
    x,y,z,rx,ry,h,d,key = data
    distant_peak("层叠远山",x,y,z,rx,ry,h,d,key,SEED+i*53)

distant_peak(
    "云外孤台",-39,29,1.8,4.5,3.7,.55,10,
    "rock",SEED+901
)

hall(
    "云外孤亭",-39,29,2.4,
    2.7,2.4,1.75,open_hall=True,register=False
)
place_tree("pine",-41.1,29.4,2.3,.69)


def _cloud_band_material():
    """带状柔边云：Generated Z 纵向渐变 × 噪波，HASHED/DITHERED 半透明。"""
    if "cloud_band" in MAT:
        return MAT["cloud_band"]
    m = bpy.data.materials.new("山脚云带")
    m.use_nodes = True
    nodes, links = m.node_tree.nodes, m.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    p = nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Base Color"].default_value = (.88, .92, .90, 1)
    p.inputs["Roughness"].default_value = 1.0
    p.inputs["Emission Color"].default_value = (.88, .92, .90, 1)
    p.inputs["Emission Strength"].default_value = 0.15
    coord = nodes.new("ShaderNodeTexCoord")
    separate = nodes.new("ShaderNodeSeparateXYZ")
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    mid = ramp.color_ramp.elements.new(0.45)
    mid.color = (.60, .60, .60, 1)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (0, 0, 0, 1)
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 2.5
    noise.inputs["Detail"].default_value = 3.0
    mix = nodes.new("ShaderNodeMath")
    mix.operation = "MULTIPLY"
    links.new(coord.outputs["Generated"], separate.inputs["Vector"])
    links.new(separate.outputs["Z"], ramp.inputs["Fac"])
    links.new(coord.outputs["Generated"], noise.inputs["Vector"])
    links.new(ramp.outputs["Color"], mix.inputs[0])
    links.new(noise.outputs["Fac"], mix.inputs[1])
    links.new(mix.outputs[0], p.inputs["Alpha"])
    links.new(p.outputs["BSDF"], output.inputs["Surface"])
    try:
        m.surface_render_method = "DITHERED"
    except Exception:
        try:
            m.blend_method = "HASHED"
        except Exception:
            pass
    MAT["cloud_band"] = m
    return m


def cloud_band(name, y_base, x0, x1, z_base, height, bulge=6.0, n=30):
    """沿远山脚拉一条竖直带状云片（面向南侧相机），遮住山体入水截面。"""
    _cloud_band_material()
    g = Geo()
    verts = []
    for i in range(n):
        t = i / (n - 1)
        x = x0 + (x1 - x0) * t
        y = y_base + bulge * math.cos((t - .5) * math.pi)
        verts.append((x, y, z_base))
        verts.append((x, y, z_base + height))
    faces = []
    for i in range(n - 1):
        b0, t0 = i * 2, i * 2 + 1
        b1, t1 = b0 + 2, t0 + 2
        faces.extend([(b0, b1, t1), (b0, t1, t0)])
    g.indexed(verts, faces, "cloud_band", True)
    g.object(name, "11_远山云气")


if KIT.get("cloud_bands", True):
    cloud_band("云带_近山前", 36.5, -52.0, 52.0, 2.55, 6.5, 7.0)
    cloud_band("云带_近中山间", 50.0, -58.0, 58.0, 2.55, 7.5, 6.0)
    cloud_band("云带_极远天外", 88.0, -70.0, 70.0, 2.55, 10.0, 8.0)

report("山水与远景完成")


# =============================================================================
# 22. 云气与空气透视
# =============================================================================

def make_cloud_material():
    m = bpy.data.materials.new("分形软边云")
    m.use_nodes = True
    nodes,links = m.node_tree.nodes,m.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    volume = nodes.new("ShaderNodeVolumePrincipled")
    volume.inputs["Color"].default_value = (.85,.90,.85,1)
    volume.inputs["Anisotropy"].default_value = .30
    volume.inputs["Emission Color"].default_value = (1.0,.93,.80,1)

    coord = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 4.6
    noise.inputs["Detail"].default_value = 4
    noise.inputs["Roughness"].default_value = .75

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = .30
    ramp.color_ramp.elements[0].color = (0,0,0,1)
    ramp.color_ramp.elements[1].position = .66
    ramp.color_ramp.elements[1].color = (.72,.72,.72,1)

    distance = nodes.new("ShaderNodeVectorMath")
    distance.operation = "DISTANCE"
    distance.inputs[1].default_value = (.5,.5,.5)

    edge = nodes.new("ShaderNodeMapRange")
    edge.clamp = True
    edge.inputs["From Min"].default_value = .19
    edge.inputs["From Max"].default_value = .50
    edge.inputs["To Min"].default_value = 1
    edge.inputs["To Max"].default_value = 0

    multiply = nodes.new("ShaderNodeMath")
    multiply.operation = "MULTIPLY"

    emit = nodes.new("ShaderNodeMath")
    emit.operation = "MULTIPLY"
    emit.inputs[1].default_value = .55

    links.new(coord.outputs["Generated"],noise.inputs["Vector"])
    links.new(coord.outputs["Generated"],distance.inputs[0])
    links.new(distance.outputs["Value"],edge.inputs["Value"])
    links.new(noise.outputs["Fac"],ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"],multiply.inputs[0])
    links.new(edge.outputs["Result"],multiply.inputs[1])
    links.new(multiply.outputs[0],volume.inputs["Density"])
    links.new(multiply.outputs[0],emit.inputs[0])
    links.new(emit.outputs[0],volume.inputs["Emission Strength"])
    links.new(volume.outputs["Volume"],output.inputs["Volume"])
    return m


def ico_mesh(name,mat,subdivisions=3):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm,subdivisions=subdivisions,radius=1)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    for poly in mesh.polygons:
        poly.use_smooth = True
    return mesh


if ENABLE_CLOUDS:
    cloud_mat = make_cloud_material()
    cloud_mesh = ico_mesh("共享云体",cloud_mat,3)

    for i in range(P["clouds"]):
        a = TAU*i/P["clouds"]+R_CLOUD.uniform(-.13,.13)
        radius = R_CLOUD.uniform(40,58)
        obj = link_object("山腰流云",cloud_mesh,"11_远山云气")
        obj.location = (
            math.cos(a)*radius,
            5+math.sin(a)*radius,
            R_CLOUD.uniform(-13,-8),
        )
        obj.scale = (
            R_CLOUD.uniform(9,16),
            R_CLOUD.uniform(5,9),
            R_CLOUD.uniform(2.0,3.4),
        )

    for x,y,z,sx,sy,sz in [
        (-34,40,2,14,5,1.5),
        (33,45,3,13,5,1.7),
        (-8,55,7,17,6,1.9),
        (16,70,11,18,7,2.0),
        (-2,27,-3,17,6,1.5),
    ]:
        obj = link_object("远山横岚",cloud_mesh,"11_远山云气")
        obj.location = (x,y,z)
        obj.scale = (sx,sy,sz)

    sea = link_object("云海托底",cloud_mesh,"11_远山云气")
    sea.location = (0,34,-7.5)
    sea.scale = (95,80,3.2)

    for x,y,z in FALL_ENDS:
        obj = link_object("瀑脚水雾",cloud_mesh,"11_远山云气")
        obj.location = (x,y,z+.7)
        obj.scale = (2.1,1.6,1.0)


def make_atmosphere():
    m = bpy.data.materials.new("高度衰减空气")
    m.use_nodes = True
    nodes,links = m.node_tree.nodes,m.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    volume = nodes.new("ShaderNodeVolumePrincipled")
    volume.inputs["Color"].default_value = (.55,.64,.62,1)
    volume.inputs["Anisotropy"].default_value = .22

    geometry = nodes.new("ShaderNodeNewGeometry")
    separate = nodes.new("ShaderNodeSeparateXYZ")
    remap = nodes.new("ShaderNodeMapRange")
    remap.clamp = True
    remap.inputs["From Min"].default_value = -12
    remap.inputs["From Max"].default_value = 31
    remap.inputs["To Min"].default_value = .0052*ATMOSPHERE_MULTIPLIER
    remap.inputs["To Max"].default_value = .00018*ATMOSPHERE_MULTIPLIER

    links.new(geometry.outputs["Position"],separate.inputs["Vector"])
    links.new(separate.outputs["Z"],remap.inputs["Value"])
    links.new(remap.outputs["Result"],volume.inputs["Density"])
    links.new(volume.outputs["Volume"],output.inputs["Volume"])
    return m


if ENABLE_AERIAL_PERSPECTIVE and QUALITY != "STUDY":
    atmosphere = make_atmosphere()
    bm = bmesh.new()
    bmesh.ops.create_cube(bm,size=1)
    mesh = bpy.data.meshes.new("空气体积边界")
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(atmosphere)

    obj = link_object("空气透视",mesh,"11_远山云气")
    obj.location = (0,40,8)
    obj.scale = (210,235,115)
    obj.display_type = "WIRE"


# =============================================================================
# 23. 世界天空与摄影灯光
# =============================================================================

world = bpy.data.worlds.new("青灰晨空")
world.use_nodes = True
scene.world = world

nodes,links = world.node_tree.nodes,world.node_tree.links
nodes.clear()

output = nodes.new("ShaderNodeOutputWorld")
background = nodes.new("ShaderNodeBackground")
background.inputs["Strength"].default_value = WORLD_STRENGTH

coord = nodes.new("ShaderNodeTexCoord")
separate = nodes.new("ShaderNodeSeparateXYZ")
remap = nodes.new("ShaderNodeMapRange")
remap.clamp = True
remap.inputs["From Min"].default_value = -.65
remap.inputs["From Max"].default_value = .65
remap.inputs["To Min"].default_value = 0
remap.inputs["To Max"].default_value = 1

ramp = nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = .02
ramp.color_ramp.elements[0].color = (.22,.12,.075,1)
ramp.color_ramp.elements[1].position = .96
ramp.color_ramp.elements[1].color = (.018,.045,.095,1)
middle = ramp.color_ramp.elements.new(.45)
middle.color = (.10,.17,.24,1)

links.new(coord.outputs["Normal"],separate.inputs["Vector"])
links.new(separate.outputs["Z"],remap.inputs["Value"])
links.new(remap.outputs["Result"],ramp.inputs["Fac"])
links.new(ramp.outputs["Color"],background.inputs["Color"])
links.new(background.outputs["Background"],output.inputs["Surface"])

if SEASON == "spring":
    sun_energy, sun_color, sun_elev = SUN_STRENGTH*0.92, (1.0,.86,.72), 28
    pink_boost, leaf_mul = 1.12, 1.08
elif SEASON == "summer":
    sun_energy, sun_color, sun_elev = SUN_STRENGTH*1.08, (1.0,.90,.78), 42
    pink_boost, leaf_mul = 0.85, 1.15
elif SEASON == "winter":
    sun_energy, sun_color, sun_elev = SUN_STRENGTH*0.72, (.82,.88,.95), 12
    pink_boost, leaf_mul = 0.20, 0.55
else:
    sun_energy, sun_color, sun_elev = SUN_STRENGTH, (1,.81,.58), 25
    pink_boost, leaf_mul = 1.0, 1.0
for key, fac in (("pink", pink_boost), ("pink_light", pink_boost),
                 ("leaf", leaf_mul), ("leaf_light", leaf_mul), ("grass", leaf_mul)):
    p = principled(MAT[key].node_tree)
    c = p.inputs["Base Color"].default_value
    p.inputs["Base Color"].default_value = (
        min(1, c[0]*fac), min(1, c[1]*fac), min(1, c[2]*max(0.7, fac*0.9)), 1
    )
sun = add_light("晨阳主光","SUN",(0,0,50),
                sun_energy,sun_color)
sun.rotation_euler = (
    math.radians(90-sun_elev),
    math.radians(-20),
    math.radians(-34),
)
sun.data.angle = math.radians(1.6)

add_light(
    "前庭柔光","AREA",(14,-39,42),
    620,(1,.72,.48),22,(0,7,11)
)
add_light(
    "西侧青天光","AREA",(-40,-3,29),
    360,(.34,.50,.68),22,(0,9,11)
)
add_light(
    "后山轮廓光","AREA",(13,38,42),
    1180,(.52,.67,.92),20,(0,14,12)
)
add_light(
    "悬山弱补光","AREA",(4,-34,-1),
    140,(.30,.42,.50),22,(0,0,-7)
)


# =============================================================================
# 24. 相机与输出
# =============================================================================

CAMERAS = []


def camera(name,location,target,lens):
    data = bpy.data.cameras.new(name)
    obj = link_object(name,data,"12_灯光相机")
    obj.location = location
    obj.rotation_euler = (
        Vector(target)-obj.location
    ).to_track_quat("-Z","Y").to_euler()

    data.type = "PERSP"
    data.lens = lens
    data.sensor_width = 36
    data.clip_start = .1
    data.clip_end = 750
    data.dof.use_dof = False

    CAMERAS.append(obj)
    return obj


main_camera = camera(
    "01_云宫山水总览",
    (66,-101,62),
    (0,8,9.3),
    CAMERA_LENS
)

camera(
    "02_重檐正殿",
    (33,-39,30),
    (0,12,14.0),
    52
)

camera(
    "03_荷塘虹桥",
    (40,-22,13.5),
    (18.4,8,8.7),
    45
)

camera(
    "04_中轴礼序",
    (0,-51,18),
    (0,11.5,13.7),
    45
)

if ENABLE_M1_SATURATION:
    camera("05_俯视总平",(0,4,128),(0,4,4.0),28)
    camera("06_正殿平视",(0,-42,22.5),(0,12.0,10.2),35)
    camera("07_东侧立面",(52,6,18),(0,10,9.8),38)
    camera("08_正殿脊吻",(8.2,6.4,18.8),(3.2,13.8,16.6),50)
    camera("09_北崖飞瀑",(12.5,41.5,11.2),(4.2,50.0,6.4),42)

scene.camera = main_camera


# =============================================================================
# 25. 合成：克制辉光
# =============================================================================

scene.use_nodes = True
nodes = scene.node_tree.nodes
links = scene.node_tree.links
nodes.clear()

layers = nodes.new("CompositorNodeRLayers")
layers.location = (-350,100)

glare = nodes.new("CompositorNodeGlare")
glare.glare_type = "FOG_GLOW"
glare.quality = "HIGH"
glare.threshold = 2.0
glare.size = 7
glare.mix = -.95
glare.location = (-100,100)

composite = nodes.new("CompositorNodeComposite")
composite.location = (150,100)

links.new(layers.outputs["Image"],glare.inputs["Image"])
links.new(glare.outputs["Image"],composite.inputs["Image"])


# =============================================================================
# 26. 合批、工程说明与批量渲染
# =============================================================================

report("合并门窗、瓦脊、栏杆与植物线饰")
flush_curves()

scene["项目名称"] = "太微 · 云宫山水长卷"
scene["质量档位"] = QUALITY
scene["随机种子"] = SEED
scene["园林乔木数量"] = len(occupied)
scene["构图原则"] = "中轴礼序、横向舒展、庭院留白、近实远虚"
scene["制作边界"] = (
    "程序化艺术场景，未经人工逐镜头修整。"
    "建筑构造为艺术化表达，非测绘与施工模型。"
)

readme = bpy.data.texts.new("太微_项目说明.txt")
readme.write(
    "太微 · 云宫山水长卷\n"
    "============================================================\n\n"
    "镜头\n"
    "01_云宫山水总览：整体布局、主山、双池、远山。\n"
    "02_重檐正殿：瓦作、斗拱、雀替、格扇与台基。\n"
    "03_荷塘虹桥：荷花、桥、驳岸、植物与庭石。\n"
    "04_中轴礼序：山门、御道、前庭与正殿。\n\n"
    "质量档位\n"
    "STUDY：布局和光照检查。\n"
    "HIGH：较完整细节和输出。\n"
    "FINAL：更密瓦片、叶片、草花，更高采样与分辨率。\n\n"
    "性能\n"
    "体积云和空气透视是主要渲染开销之一。\n"
    "GPU 需在首选项配置。\n"
    "树木共享网格，草花和小型构件合批。\n\n"
    "审美调整\n"
    "画面发灰：降低 ATMOSPHERE_MULTIPLIER。\n"
    "主殿不突出：调整主相机焦距或局部移除遮挡树木。\n"
    "画面太满：减少前景树木，而非继续增加装饰。\n"
    "金属太亮：提高 gold 材质粗糙度，不必压暗所有灯光。\n\n"
    "边界\n"
    "这是一份可继续深化的视觉制作工程。\n"
    "不是古建筑测绘、施工或文保模型。\n"
)

bpy.ops.object.select_all(action="DESELECT")
main_camera.select_set(True)
bpy.context.view_layer.objects.active = main_camera

for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == "VIEW_3D":
            space = area.spaces.active
            space.clip_end = 750
            space.shading.type = "SOLID"
            space.shading.color_type = "MATERIAL"
            space.region_3d.view_perspective = "CAMERA"

output_dir = bpy.path.abspath(OUTPUT_DIRECTORY)
scene.render.filepath = os.path.join(output_dir,"01_云宫山水总览.png")


def render_camera_set():
    os.makedirs(output_dir,exist_ok=True)
    previous_camera = scene.camera
    previous_path = scene.render.filepath

    try:
        for cam in CAMERAS:
            scene.camera = cam
            scene.render.filepath = os.path.join(output_dir,cam.name+".png")
            report("开始渲染："+cam.name)
            bpy.ops.render.render(write_still=True)
    finally:
        scene.camera = previous_camera
        scene.render.filepath = previous_path


if AUTO_SAVE:
    os.makedirs(output_dir,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(
        filepath=os.path.join(output_dir,PROJECT_FILENAME)
    )

report("场景生成完成")

print("="*76)
print("太微 · 云宫山水长卷")
print("质量档位：",QUALITY)
print("对象数量：",len(scene.objects))
print("园林乔木：",len(occupied))
print("生成耗时：",round(time.time()-START,1),"秒")
print("当前镜头：",scene.camera.name)
print("输出目录：",output_dir)
print("F12：渲染当前镜头")
print("render_camera_set()：依次渲染四个镜头")
print("="*76)

if RENDER_ALL_CAMERAS:
    render_camera_set()
elif AUTO_RENDER:
    os.makedirs(output_dir,exist_ok=True)
    bpy.ops.render.render(write_still=True)
