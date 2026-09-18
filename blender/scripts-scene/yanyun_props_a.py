"""燕云化组件 A：水巷灵魂 —— 垂柳 / 乌篷船 / 水埠头 / 浮萍带。
在 TaiWei_YanYun.blend 上增量添加（不清场），保存回写 + 渲验证帧。
blender -b TaiWei_YanYun.blend -P yanyun_props_a.py
"""
import bpy
import bmesh
import math
import os
import random
from mathutils import Vector

TAU = math.tau
R = random.Random(20260913)
BLEND_OUT = os.environ.get(
    "TAIWEI_BLEND_OUT",
    "E:/UserData/xdrhh/.openclaw/workspace/taiwei_video/TaiWei_YanYun.blend",
)
DIAG = "E:/UserData/xdrhh/.openclaw/workspace/taiwei_video/diag/"
SKIP_SHOTS = os.environ.get("TAIWEI_SKIP_SHOTS", "0") in ("1", "true", "True")

scene = bpy.context.scene
PROPS = bpy.data.collections.get("13_燕云水巷")
if PROPS is None:
    PROPS = bpy.data.collections.new("13_燕云水巷")
    scene.collection.children.link(PROPS)
else:
    for obj in list(PROPS.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


# ---------- 精简几何工具 ----------
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

    def leaf(self, center, direction, length, width, mat_index=0):
        c = Vector(center)
        d = Vector(direction).normalized()
        side = d.cross(Vector((0, 0, 1)))
        if side.length < 0.1:
            side = Vector((1, 0, 0))
        side.normalize()
        tip = c + d * length
        mid = c + d * (length * 0.5) + Vector((0, 0, length * 0.06))
        vs = [self.bm.verts.new(c), self.bm.verts.new(mid + side * width),
              self.bm.verts.new(tip), self.bm.verts.new(mid - side * width)]
        f = self.bm.faces.new(vs)
        f.material_index = mat_index

    def object(self, name, materials):
        mesh = bpy.data.meshes.new(name)
        self.bm.to_mesh(mesh)
        self.bm.free()
        for m in materials:
            mesh.materials.append(m)
        obj = bpy.data.objects.new(name, mesh)
        PROPS.objects.link(obj)
        return obj


def new_mat(name, color, rough=0.8, metallic=0.0, subsurface=0.0,
            emission=None, strength=0.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metallic
    p.inputs["Subsurface Weight"].default_value = subsurface
    if emission:
        p.inputs["Emission Color"].default_value = (*emission, 1)
        p.inputs["Emission Strength"].default_value = strength
    return m


MAT_WILLOW_BARK = new_mat("柳皮苍裂", (0.16, 0.11, 0.05), 0.92)
MAT_WILLOW_LEAF = new_mat("柳叶嫩碧", (0.30, 0.44, 0.13), 0.7, subsurface=0.06)
MAT_WILLOW_LEAF_D = new_mat("柳叶背灰", (0.18, 0.30, 0.11), 0.75)
MAT_BOAT_WOOD = new_mat("船板旧木", (0.115, 0.07, 0.035), 0.85)
MAT_BOAT_AWNING = new_mat("乌篷炭褐", (0.045, 0.038, 0.030), 0.9)
MAT_BAMBOO_POLE = new_mat("竹篙", (0.35, 0.38, 0.14), 0.7)
MAT_DUCKWEED = new_mat("浮萍墨碧", (0.055, 0.16, 0.05), 0.55)
MAT_DUCKWEED_L = new_mat("浮萍浅碧", (0.14, 0.28, 0.07), 0.6)
MAT_STONE = bpy.data.materials.get("青石") or new_mat("青石", (0.23, 0.30, 0.265), 0.81)
MAT_MOSS = bpy.data.materials.get("苔青") or new_mat("苔青", (0.12, 0.235, 0.055), 0.99)
MAT_ROPE = new_mat("缆绳麻", (0.32, 0.26, 0.15), 0.95)


# ---------- 射线落地 ----------
DG = bpy.context.evaluated_depsgraph_get()


def drop_z(x, y, from_z=25.0):
    hit, loc, *_ = scene.ray_cast(DG, Vector((x, y, from_z)), Vector((0, 0, -1)))
    return loc.z if hit else None


def water_at(x, y):
    """该点正下方是否是水（命中 z 在 3.5-3.7 之间的面）。"""
    z = drop_z(x, y)
    return z is not None and 3.45 < z < 3.75


def catmull_rom(points, steps=6):
    pts = [points[0]] + list(points) + [points[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        a, b, c, d = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for j in range(steps):
            t = j / steps
            out.append(0.5 * (
                2 * b
                + (-a + c) * t
                + (2 * a - 5 * b + 4 * c - d) * t * t
                + (-a + 3 * b - 3 * c + d) * t * t * t
            ))
    out.append(points[-1])
    return out


# ---------- 垂柳 ----------
def willow(x, y, lean_dir, scale=1.0, seed=0):
    """lean_dir: 倾斜朝向（弧度，指向水面）。干用样条，叶沿垂枝衰减。"""
    rng = random.Random(seed)
    z0 = drop_z(x, y)
    if z0 is None:
        return None
    g = Geo()
    h = rng.uniform(4.2, 5.6) * scale
    ld = Vector((math.cos(lean_dir), math.sin(lean_dir), 0))
    side = Vector((-ld.y, ld.x, 0))
    origin = Vector((x, y, z0))

    keys = [
        origin,
        origin + ld * (h * 0.22) + Vector((0, 0, h * 0.18)) + side * rng.uniform(-0.12, 0.12),
        origin + ld * (h * 0.42) + Vector((0, 0, h * 0.38)) + side * rng.uniform(-0.18, 0.18),
        origin + ld * (h * 0.28) + Vector((0, 0, h * 0.68)) + side * rng.uniform(-0.10, 0.10),
        origin + ld * (h * 0.12) + Vector((0, 0, h)),
    ]
    spine = catmull_rom(keys, 5)
    for i in range(len(spine) - 1):
        t0, t1 = i / (len(spine) - 1), (i + 1) / (len(spine) - 1)
        r0 = 0.34 * scale * (1.35 - 1.05 * t0)
        r1 = 0.34 * scale * (1.35 - 1.05 * t1)
        g.rod(spine[i], spine[i + 1], max(0.04, r0), max(0.03, r1), 8, 0)
    top = spine[-1]

    water_n = rng.randint(6, 7)
    for bi in range(water_n):
        a = lean_dir + rng.uniform(-0.42, 0.42)
        bd = Vector((math.cos(a), math.sin(a), 0))
        start = top + bd * rng.uniform(0.05, 0.18) + Vector((0, 0, rng.uniform(-0.12, 0.08)))
        reach = rng.uniform(2.6, 3.8) * scale
        elbow = start + bd * (reach * 0.42) + Vector((0, 0, rng.uniform(-0.08, 0.12)))
        end = start + bd * reach + Vector((0, 0, rng.uniform(-0.55, -0.12)))
        g.rod(start, elbow, 0.055 * scale, 0.028 * scale, 7, 0)
        g.rod(elbow, end, 0.028 * scale, 0.012 * scale, 6, 0)
        for _ in range(rng.randint(11, 16)):
            t = rng.uniform(0.25, 1.0)
            o = elbow.lerp(end, t)
            drop = rng.uniform(2.0, 3.2) * scale
            midp = o + Vector((rng.uniform(-0.14, 0.14), rng.uniform(-0.14, 0.14), -drop * 0.55))
            tip = o + Vector((rng.uniform(-0.22, 0.22), rng.uniform(-0.22, 0.22), -drop))
            g.rod(o, midp, 0.008, 0.005, 5, 0)
            g.rod(midp, tip, 0.005, 0.002, 5, 0)
            steps = max(4, int(drop / 0.16))
            for si in range(steps):
                tt = si / steps
                if rng.random() > max(0.08, 0.72 - 1.15 * (tt ** 1.45)):
                    continue
                lp = o.lerp(tip, tt)
                la = rng.uniform(0, TAU)
                g.leaf(lp, (math.cos(la) * 0.22, math.sin(la) * 0.22, -1.0),
                       rng.uniform(0.13, 0.22), 0.020,
                       1 if si % 3 else 2)

    a = lean_dir + math.pi + rng.uniform(-0.35, 0.35)
    bd = Vector((math.cos(a), math.sin(a), 0))
    end = top + bd * rng.uniform(1.1, 1.6) * scale + Vector((0, 0, rng.uniform(0.08, 0.28)))
    g.rod(top, end, 0.04 * scale, 0.014 * scale, 6, 0)
    return g.object("垂柳", [MAT_WILLOW_BARK, MAT_WILLOW_LEAF, MAT_WILLOW_LEAF_D])


# ---------- 乌篷船 ----------
def wupeng_boat(x, y, angle=0.0, seed=0):
    rng = random.Random(seed)
    g = Geo()
    length = rng.uniform(4.2, 5.0)
    half = length / 2
    beam = 1.05
    depth = 0.42
    stations = 9

    # 船体放样：U 形截面，两端收窄上翘
    def half_w(t):
        return (beam / 2) * max(0.06, math.sin(math.pi * min(1, max(0.02, t * 0.96 + 0.02)))) ** 0.7

    def keel_z(t):
        return -depth + (0.38 * (abs(t - 0.5) * 2) ** 2.6)

    rings = []
    for i in range(stations):
        t = i / (stations - 1)
        lx = (t - 0.5) * length
        w = half_w(t)
        kz = keel_z(t)
        gunwale = kz + depth * 1.25
        ring = [(-w * 0.96, gunwale), (-w, kz + depth * 0.62),
                (-w * 0.55, kz), (w * 0.55, kz),
                (w, kz + depth * 0.62), (w * 0.96, gunwale)]
        rings.append([(lx, ly, lz) for ly, lz in ring])
    for i in range(stations - 1):
        for j in range(5):
            g.face([rings[i][j], rings[i + 1][j],
                    rings[i + 1][j + 1], rings[i][j + 1]], 0)
    g.face([rings[0][j] for j in reversed(range(6))], 0)
    g.face([rings[-1][j] for j in range(6)], 0)

    # 乌篷：中部 55% 拱棚
    for i in range(2, stations - 3):
        t0 = i / (stations - 1)
        t1 = (i + 1) / (stations - 1)
        x0 = (t0 - 0.5) * length
        x1 = (t1 - 0.5) * length
        w0 = half_w(t0) * 0.98
        w1 = half_w(t1) * 0.98
        gz0 = keel_z(t0) + depth * 1.25
        gz1 = keel_z(t1) + depth * 1.25
        seg = 6
        arc0 = [(x0, -w0 + 2 * w0 * k / seg,
                 gz0 + math.sin(math.pi * k / seg) * 0.72) for k in range(seg + 1)]
        arc1 = [(x1, -w1 + 2 * w1 * k / seg,
                 gz1 + math.sin(math.pi * k / seg) * 0.72) for k in range(seg + 1)]
        for k in range(seg):
            g.face([arc0[k], arc1[k], arc1[k + 1], arc0[k + 1]], 1)

    # 船头竹篙 + 船尾小橹
    g.rod((-half + 0.3, 0.25, 0.1), (-half + 0.75, 0.4, 1.5), 0.028, 0.02, 6, 2)
    g.rod((half - 0.2, -0.2, 0.15), (half + 0.85, -0.35, 0.75), 0.03, 0.018, 6, 2)

    obj = g.object("乌篷船", [MAT_BOAT_WOOD, MAT_BOAT_AWNING, MAT_BAMBOO_POLE])
    obj.location = (x, y, 3.62)
    obj.rotation_euler = (math.radians(rng.uniform(4, 8)),
                          math.radians(rng.uniform(-2, 2)), angle)

    # 缆绳：船头 → 岸边木桩
    bow = Vector((x - math.cos(angle) * half, y - math.sin(angle) * half, 3.75))
    # 朝船头方向找岸
    sx, sy = x, y
    for step in range(1, 40):
        tx = x - math.cos(angle) * (half + step * 0.3)
        ty = y - math.sin(angle) * (half + step * 0.3)
        if not water_at(tx, ty):
            sx, sy = tx, ty
            break
    sz = drop_z(sx, sy) or 3.8
    g2 = Geo()
    stake_top = Vector((sx, sy, sz + 0.55))
    g2.rod((sx, sy, sz - 0.1), stake_top, 0.05, 0.04, 7, 1)
    mid = bow.lerp(stake_top, 0.5) + Vector((0, 0, -0.22))
    g2.rod(bow, mid, 0.016, 0.014, 5, 1)
    g2.rod(mid, stake_top, 0.014, 0.016, 5, 1)
    g2.object("船缆与木桩", [MAT_BOAT_WOOD, MAT_ROPE])
    return obj


# ---------- 水埠头 ----------
def water_steps(x, y, angle=0.0):
    """岸 → 水 4 级石阶。angle 指向水面。"""
    g = Geo()
    top_z = drop_z(x, y)
    if top_z is None:
        return
    d = Vector((math.cos(angle), math.sin(angle), 0))
    for i in range(4):
        c = Vector((x, y, 0)) + d * (0.34 * (i + 0.5))
        cz = top_z - 0.17 * (i + 0.62)
        g.box((c.x, c.y, cz), (1.5, 0.34, 0.30), 0, angle)
        # 阶面苔痕条（贴面薄片）
        g.box((c.x, c.y, cz + 0.153), (1.44, 0.30, 0.012), 1, angle)
    # 两侧垂带石
    side = Vector((-d.y, d.x, 0))
    for s in (-1, 1):
        c0 = Vector((x, y, 0)) + side * (0.82 * s) + d * 0.68
        g.box((c0.x, c0.y, top_z - 0.35), (0.16, 1.5, 0.24), 0, angle)
    g.object("水埠头石阶", [MAT_STONE, MAT_MOSS])


# ---------- 浮萍带 ----------
def duckweed_cluster(cx, cy, radius, count):
    g = Geo()
    placed = 0
    tries = 0
    while placed < count and tries < count * 6:
        tries += 1
        a = rng_a = R.uniform(0, TAU)
        rr = radius * (R.random() ** 0.55)
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
        if not water_at(x, y):
            continue
        rad = R.uniform(0.035, 0.075)
        sides = 7
        cxfs = [Vector((x + math.cos(TAU * i / sides) * rad * R.uniform(0.8, 1.1),
                        y + math.sin(TAU * i / sides) * rad * R.uniform(0.8, 1.1),
                        3.615)) for i in range(sides)]
        f = g.bm.faces.new([g.bm.verts.new(v) for v in cxfs])
        f.material_index = 1 if placed % 4 == 0 else 0
        placed += 1
    g.object("浮萍聚落", [MAT_DUCKWEED, MAT_DUCKWEED_L])


# ---------- 落位执行 ----------
# 垂柳贴水岸，不进仪门中轴、不压正殿东立面
willow(22.8, 8.6, lean_dir=math.radians(-95), scale=0.92, seed=11)
willow(24.5, 4.0, lean_dir=math.radians(185), scale=0.88, seed=12)
willow(-22.4, 8.2, lean_dir=math.radians(-80), scale=0.92, seed=13)
willow(-24.0, 2.5, lean_dir=math.radians(-5), scale=0.88, seed=14)
willow(19.6, -6.8, lean_dir=math.radians(70), scale=0.95, seed=15)
willow(-19.8, -6.6, lean_dir=math.radians(110), scale=0.95, seed=16)
willow(14.8, -27.2, lean_dir=math.radians(-80), scale=0.82, seed=17)
willow(-15.2, -27.6, lean_dir=math.radians(-100), scale=0.82, seed=18)

# 乌篷船：东西池各两艘 + 湾角一艘，斜泊不挡仪门
wupeng_boat(17.0, 4.2, angle=math.radians(115), seed=21)
wupeng_boat(23.0, -3.5, angle=math.radians(55), seed=22)
wupeng_boat(-17.5, 3.0, angle=math.radians(250), seed=23)
wupeng_boat(-11.0, -5.2, angle=math.radians(300), seed=24)
wupeng_boat(26.4, 6.8, angle=math.radians(200), seed=25)
wupeng_boat(-25.8, 5.6, angle=math.radians(20), seed=26)
# 南岛廊桥湾：斜泊，不挡迎仙长阶
wupeng_boat(16.4, -36.2, angle=math.radians(140), seed=27)
wupeng_boat(-16.8, -37.4, angle=math.radians(40), seed=28)
wupeng_boat(38.8, 18.6, angle=math.radians(250), seed=29)
wupeng_boat(-39.2, 19.2, angle=math.radians(70), seed=30)

# 水埠头：近建筑/路径，不挡仪门视线
water_steps(9.0, -7.9, angle=math.radians(78))
water_steps(-16.0, 8.6, angle=math.radians(-82))
water_steps(20.5, 8.3, angle=math.radians(-95))
water_steps(18.8, -2.2, angle=math.radians(8))
water_steps(-26.2, -4.8, angle=math.radians(35))
water_steps(-18.8, -8.0, angle=math.radians(95))
water_steps(12.4, -26.2, angle=math.radians(-90))
water_steps(-12.6, -26.4, angle=math.radians(-90))
water_steps(18.6, -38.2, angle=math.radians(90))
water_steps(-18.8, -39.0, angle=math.radians(90))
water_steps(41.2, 21.4, angle=math.radians(200))
water_steps(-41.4, 21.6, angle=math.radians(-20))

# 浮萍：池角聚集
duckweed_cluster(25.5, 8.5, 3.2, 90)
duckweed_cluster(-25.0, 7.8, 3.0, 80)
duckweed_cluster(25.8, -6.5, 2.6, 70)
duckweed_cluster(-24.5, -6.8, 2.8, 70)
duckweed_cluster(15.2, -32.4, 2.4, 55)
duckweed_cluster(-15.4, -33.2, 2.4, 55)

print("PROPS_A_DONE")
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

    cam_data = bpy.data.cameras.new("验证相机")
    cam = bpy.data.objects.new("验证相机", cam_data)
    scene.collection.objects.link(cam)

    def look(cam_obj, target):
        cam_obj.rotation_euler = (
            Vector(target) - cam_obj.location).to_track_quat("-Z", "Y").to_euler()

    cam.location = (30, -14, 8.5)
    look(cam, (16, 5, 4.5))
    cam.data.lens = 40
    scene.camera = cam
    scene.render.filepath = DIAG + "props_a_east.png"
    bpy.ops.render.render(write_still=True)

    cam.location = (-28, -13, 9.0)
    look(cam, (-16, 4, 4.5))
    cam.data.lens = 40
    scene.render.filepath = DIAG + "props_a_west.png"
    bpy.ops.render.render(write_still=True)

    cam.location = (0, -58, 26)
    look(cam, (0, 6, 6.5))
    cam.data.lens = 42
    scene.render.filepath = DIAG + "props_a_wide.png"
    bpy.ops.render.render(write_still=True)
    print("ALL_DONE")
