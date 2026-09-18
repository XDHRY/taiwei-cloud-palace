"""燕云化组件 B：宫观陈设 —— 香炉青烟 / 石经幢 / 道家符幡 / 盆景石臼。
在 TaiWei_YanYun.blend 增量添加（幂等），保存 + 渲验证帧（含乌篷船特写）。
blender -b TaiWei_YanYun.blend -P yanyun_props_b.py
"""
import bpy
import bmesh
import math
import os
import random
from mathutils import Vector

TAU = math.tau
R = random.Random(20260914)
BLEND_OUT = os.environ.get(
    "TAIWEI_BLEND_OUT",
    "E:/UserData/xdrhh/.openclaw/workspace/taiwei_video/TaiWei_YanYun.blend",
)
DIAG = "E:/UserData/xdrhh/.openclaw/workspace/taiwei_video/diag/"
SKIP_SHOTS = os.environ.get("TAIWEI_SKIP_SHOTS", "0") in ("1", "true", "True")

scene = bpy.context.scene
PROPS = bpy.data.collections.get("14_燕云陈设")
if PROPS is None:
    PROPS = bpy.data.collections.new("14_燕云陈设")
    scene.collection.children.link(PROPS)
else:
    for obj in list(PROPS.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


class Geo:
    def __init__(self):
        self.bm = bmesh.new()

    def face(self, verts, mat_index=0):
        vs = [self.bm.verts.new(tuple(v)) for v in verts]
        f = self.bm.faces.new(vs)
        f.material_index = mat_index
        return f

    def rod(self, a, b, r1, r2=None, sides=8, mat_index=0):
        a, b = Vector(a), Vector(b)
        if r2 is None:
            r2 = r1 * 0.7
        d = b - a
        if d.length < 1e-6:
            return
        q = d.to_track_quat("Z", "Y")
        ring1, ring2 = [], []
        for i in range(sides):
            ang = TAU * i / sides
            off = Vector((math.cos(ang), math.sin(ang), 0))
            ring1.append(self.bm.verts.new(a + q @ (off * r1)))
            ring2.append(self.bm.verts.new(b + q @ (off * r2)))
        for i in range(sides):
            f = self.bm.faces.new((ring1[i], ring1[(i + 1) % sides],
                                   ring2[(i + 1) % sides], ring2[i]))
            f.material_index = mat_index
        f = self.bm.faces.new(ring1[::-1]); f.material_index = mat_index
        f = self.bm.faces.new(ring2); f.material_index = mat_index

    def box(self, center, size, mat_index=0, rot_z=0.0):
        cx, cy, cz = center
        sx, sy, sz = size[0] / 2, size[1] / 2, size[2] / 2
        base = [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
                (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)]
        c, s = math.cos(rot_z), math.sin(rot_z)
        verts = []
        for x, y, z in base:
            verts.append(self.bm.verts.new((cx + x * c - y * s,
                                            cy + x * s + y * c, cz + z)))
        for fidx in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
                     (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
            f = self.bm.faces.new([verts[i] for i in fidx])
            f.material_index = mat_index

    def lathe(self, center, profile, sides=16, mat_index=0):
        cx, cy, cz = center
        rings = []
        for radius, zoff in profile:
            ring = []
            for i in range(sides):
                ang = TAU * i / sides
                ring.append(self.bm.verts.new(
                    (cx + radius * math.cos(ang), cy + radius * math.sin(ang),
                     cz + zoff)))
            rings.append(ring)
        for k in range(len(rings) - 1):
            for i in range(sides):
                f = self.bm.faces.new((rings[k][i], rings[k][(i + 1) % sides],
                                       rings[k + 1][(i + 1) % sides],
                                       rings[k + 1][i]))
                f.material_index = mat_index

    def ellipsoid(self, center, radii, mat_index=0, seg=10, rings_n=6):
        cx, cy, cz = center
        rx, ry, rz = radii
        grid = []
        for ri in range(rings_n + 1):
            phi = math.pi * ri / rings_n
            ring = []
            for si in range(seg):
                th = TAU * si / seg
                ring.append(self.bm.verts.new((
                    cx + rx * math.sin(phi) * math.cos(th),
                    cy + ry * math.sin(phi) * math.sin(th),
                    cz + rz * math.cos(phi))))
            grid.append(ring)
        for ri in range(rings_n):
            for si in range(seg):
                a, b = grid[ri][si], grid[ri][(si + 1) % seg]
                c, d = grid[ri + 1][(si + 1) % seg], grid[ri + 1][si]
                try:
                    f = self.bm.faces.new((a, b, c, d))
                    f.material_index = mat_index
                except ValueError:
                    pass

    def object(self, name, materials):
        mesh = bpy.data.meshes.new(name)
        self.bm.to_mesh(mesh)
        self.bm.free()
        for m in materials:
            mesh.materials.append(m)
        obj = bpy.data.objects.new(name, mesh)
        PROPS.objects.link(obj)
        return obj


def new_mat(name, color, rough=0.8, metallic=0.0, emission=None, strength=0.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metallic
    if emission:
        p.inputs["Emission Color"].default_value = (*emission, 1)
        p.inputs["Emission Strength"].default_value = strength
    return m


MAT_STONE = bpy.data.materials.get("青石") or new_mat("青石", (0.23, 0.30, 0.265), 0.81)
MAT_IVORY = bpy.data.materials.get("暖白石") or new_mat("暖白石", (0.74, 0.79, 0.69), 0.48)
MAT_BRONZE = bpy.data.materials.get("旧铜") or new_mat("旧铜", (0.19, 0.13, 0.055), 0.46, 0.68)
MAT_GOLD = bpy.data.materials.get("哑光鎏金") or new_mat("哑光鎏金", (0.65, 0.405, 0.12), 0.35, 0.75)
MAT_BAMBOO = bpy.data.materials.get("竹秆") or new_mat("竹秆", (0.18, 0.27, 0.065), 0.74)
MAT_FAN_YELLOW = new_mat("符幡杏黄绢", (0.72, 0.55, 0.16), 0.82, emission=(0.5, 0.36, 0.1), strength=0.12)
MAT_FAN_RUNE = new_mat("符箓石青", (0.05, 0.16, 0.17), 0.7)
MAT_PINE = bpy.data.materials.get("松针墨绿") or new_mat("松针墨绿", (0.021, 0.085, 0.043), 0.89)
MAT_WOOD = bpy.data.materials.get("古木与树皮") or new_mat("古木与树皮", (0.11, 0.057, 0.023), 0.89)
MAT_MOSS = bpy.data.materials.get("苔青") or new_mat("苔青", (0.12, 0.235, 0.055), 0.99)
MAT_WATER_S = new_mat("盆盂静水", (0.10, 0.16, 0.13), 0.12)


# ---------- 香炉青烟（体积雾小柱，上细下稳） ----------
def incense_smoke(x, y, z):
    m = bpy.data.materials.get("青烟体积")
    if m is None:
        m = bpy.data.materials.new("青烟体积")
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        nodes, links = nt.nodes, nt.links
        out = nodes.new("ShaderNodeOutputMaterial")
        vol = nodes.new("ShaderNodeVolumePrincipled")
        vol.inputs["Color"].default_value = (0.62, 0.68, 0.66, 1)
        vol.inputs["Anisotropy"].default_value = 0.3
        geom = nodes.new("ShaderNodeTexCoord")
        sep = nodes.new("ShaderNodeSeparateXYZ")
        links.new(geom.outputs["Generated"], sep.inputs["Vector"])
        ramp = nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
        ramp.color_ramp.elements[0].position = 0.05
        ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
        ramp.color_ramp.elements[1].position = 0.85
        links.new(sep.outputs["Z"], ramp.inputs["Fac"])
        mult = nodes.new("ShaderNodeMath")
        mult.operation = "MULTIPLY"
        mult.inputs[1].default_value = 0.16
        links.new(ramp.outputs["Color"], mult.inputs[0])
        links.new(mult.outputs[0], vol.inputs["Density"])
        links.new(vol.outputs["Volume"], out.inputs["Volume"])
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z + 1.5))
    o = bpy.context.object
    o.name = "香炉青烟"
    o.scale = (0.42, 0.42, 1.6)
    bpy.ops.object.transform_apply(scale=True)
    for c in list(o.users_collection):
        c.objects.unlink(o)
    PROPS.objects.link(o)
    o.data.materials.append(m)
    o.display_type = "WIRE"


# ---------- 石经幢 ----------
def jingchuang(x, y, z, seed=0):
    rng = random.Random(seed)
    g = Geo()
    # 须弥座
    g.box((x, y, z + 0.14), (1.05, 1.05, 0.28), 0)
    g.lathe((x, y, z + 0.28), [(0.52, 0), (0.46, 0.10), (0.40, 0.16), (0.34, 0.30)], 8, 1)
    # 幢身八棱（略收分），高 1.7
    g.lathe((x, y, z + 0.58), [(0.30, 0), (0.28, 0.85), (0.26, 1.70)], 8, 1)
    # 天盖 + 仰莲 + 宝珠
    g.lathe((x, y, z + 2.28), [(0.44, 0), (0.40, 0.10), (0.20, 0.16)], 8, 1)
    g.lathe((x, y, z + 2.44), [(0.13, 0), (0.17, 0.10), (0.08, 0.24), (0.02, 0.36)], 12, 2)
    g.object("石经幢", [MAT_STONE, MAT_IVORY, MAT_GOLD])


# ---------- 符幡竹竿 ----------
def banner_pole(x, y, z, height=4.2, seed=0):
    rng = random.Random(seed)
    g = Geo()
    g.rod((x, y, z - 0.15), (x, y, z + height), 0.045, 0.026, 8, 0)
    # 顶部横竿 + 幡面（杏黄绢 + 石青符带）
    g.rod((x - 0.42, y, z + height - 0.06), (x + 0.42, y, z + height - 0.06),
          0.02, 0.02, 6, 0)
    top = z + height - 0.10
    g.face([(x - 0.34, y, top), (x + 0.34, y, top),
            (x + 0.34, y + 0.012, top - 1.9), (x - 0.34, y + 0.012, top - 1.9)], 1)
    for k in range(3):
        zz = top - 0.35 - k * 0.52
        g.face([(x - 0.22, y - 0.006, zz), (x + 0.22, y - 0.006, zz),
                (x + 0.22, y - 0.006, zz - 0.30), (x - 0.22, y - 0.006, zz - 0.30)], 2)
    # 幡尾开叉（燕尾）
    g.face([(x - 0.34, y, top - 1.9), (x, y, top - 2.25), (x + 0.34, y, top - 1.9)], 1)
    g.object("道幡", [MAT_BAMBOO, MAT_FAN_YELLOW, MAT_FAN_RUNE])


# ---------- 盆景石臼 ----------
def penjing(x, y, z, seed=0):
    rng = random.Random(seed)
    g = Geo()
    g.lathe((x, y, z), [(0.30, 0), (0.34, 0.06), (0.30, 0.24), (0.26, 0.30)], 14, 0)
    g.lathe((x, y, z + 0.30), [(0.24, 0), (0.24, -0.02)], 14, 3)   # 盆内静水
    g.ellipsoid((x + 0.05, y, z + 0.32), (0.16, 0.13, 0.05), 4)     # 苔球
    # 小迎客松
    lean = rng.uniform(-0.2, 0.2)
    g.rod((x - 0.04, y + 0.02, z + 0.30), (x - 0.04 + lean, y + 0.02, z + 0.85),
          0.035, 0.022, 7, 1)
    for k, zz in enumerate((0.55, 0.68, 0.80)):
        g.ellipsoid((x - 0.04 + lean * (zz / 0.85) + 0.06, y + 0.02, z + zz),
                    (0.17 - k * 0.04, 0.13 - k * 0.03, 0.045), 2)
    g.object("盆景石臼", [MAT_STONE, MAT_WOOD, MAT_PINE, MAT_WATER_S, MAT_MOSS])


# ---------- 落位 ----------
incense_smoke(-4.35, 7.55, 7.2 + 0.95)
incense_smoke(4.35, 7.55, 7.2 + 0.95)

jingchuang(-6.2, -9.6, 5.5, seed=31)
jingchuang(6.2, -9.6, 5.5, seed=32)

banner_pole(-8.6, 8.8, 7.2, 4.4, seed=33)
banner_pole(8.6, 8.8, 7.2, 4.4, seed=34)
banner_pole(-13.2, -13.8, 5.5, 3.9, seed=35)
banner_pole(13.2, -13.8, 5.5, 3.9, seed=36)

penjing(-9.4, -2.2, 5.5, seed=41)
penjing(9.4, -2.2, 5.5, seed=42)
penjing(-8.2, 19.5, 6.45, seed=43)
penjing(8.2, 19.5, 6.45, seed=44)
penjing(21.9, 12.8, 4.1, seed=45)
penjing(-20.8, -15.9, 4.4, seed=46)

print("PROPS_B_DONE")
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

    cam_data = bpy.data.cameras.new("验证相机B")
    cam = bpy.data.objects.new("验证相机B", cam_data)
    scene.collection.objects.link(cam)

    def look(target):
        cam.rotation_euler = (
            Vector(target) - cam.location).to_track_quat("-Z", "Y").to_euler()

    cam.location = (0, -16, 8.8)
    look((0, 8, 8.2))
    cam.data.lens = 42
    scene.camera = cam
    scene.render.filepath = DIAG + "props_b_court.png"
    bpy.ops.render.render(write_still=True)

    cam.location = (22.5, -2.5, 5.6)
    look((17.0, 4.2, 4.0))
    cam.data.lens = 45
    scene.render.filepath = DIAG + "props_b_boat.png"
    bpy.ops.render.render(write_still=True)
    print("ALL_DONE")
