# -*- coding: utf-8 -*-
"""桥/门几何权威解算：端点落区判定 + 新参数求解。
复刻 generator 的 ground_z / 主岛椭圆 / 卫星岛台面公式。"""
import math

WATER_Z = 3.58
RX, RY, CY = 34.5, 31.5, 5.0
PONDS = [(-23.8, -0.8, 4.9, 8.5), (23.8, 3.0, 5.2, 8.8)]


def ground_z(x, y):
    z = 4.02
    z += .13 * math.sin(x * .31) * math.cos(y * .25)
    z += .075 * math.sin(x * .87 + y * .51)
    z += 2.7 * math.exp(-((x + 26) ** 2 / 28 + (y - 19) ** 2 / 48))
    z += 3.3 * math.exp(-((x - 26) ** 2 / 29 + (y - 22) ** 2 / 46))
    z += 1.8 * math.exp(-((x + 8) ** 2 / 95 + (y - 32) ** 2 / 17))
    if abs(x) < 17.5 and -16.5 < y < 26:
        z = 4.02
    for px, py, prx, pry in PONDS:
        d = math.hypot((x - px) / prx, (y - py) / pry)
        if d < 1:
            z -= 2.0 * (1 - d * d) ** .60
    return z


def island_t(x, y, cx, cy, r):
    return math.hypot((x - cx) / r, (y - cy) / (r * .86))


def island_z(x, y, cx, cy, r, deck):
    t = island_t(x, y, cx, cy, r)
    if t >= 1.0:
        return None, t
    if t < .62:
        z = deck - t * .28
    else:
        u = (t - .62) / .38
        z = deck - .18 - u * (deck - WATER_Z + 2.55)
    return z, t


def main_t(x, y):
    return math.hypot(x / RX, (y - CY) / RY)


def bridge_ends(x, y, L, A):
    dx, dy = -math.sin(A), math.cos(A)
    return (x - dx * L / 2, y - dy * L / 2), (x + dx * L / 2, y + dy * L / 2)


ISLANDS = {
    "东塔岛": (48.0, 6.0, 7.4, 5.20), "西亭岛": (-47.0, 8.0, 6.8, 5.05),
    "北崖阁岛": (4.0, 52.0, 8.2, 6.35), "南迎客矶": (0.0, -46.0, 10.4, 5.25),
    "东南散岛": (38.0, -28.0, 5.4, 4.80), "西北散岛": (-36.0, 34.0, 5.8, 5.00),
    "东北散岛": (36.0, 36.0, 5.6, 4.95), "西南散岛": (-34.0, -30.0, 5.2, 4.75),
    "瀛洲散岛": (20.0, -42.0, 9.2, 5.15), "方丈浮矶": (-20.0, -44.0, 8.8, 5.10),
    "蓬莱霞峰": (-46.0, 24.0, 6.5, 5.05), "碧虚云台": (46.0, 24.0, 6.6, 5.10),
}

BRIDGES = [
    ("东桥", "东塔岛", 33.8, 12.6, 24.0, math.pi / 2, 3.85, 1.35),
    ("西桥", "西亭岛", -32.8, 7.0, 23.5, math.pi / 2, 3.70, 1.35),
    ("东南桥", "东南散岛", 22.0, -22.8, 20.0, 1.05, 3.40, 1.15),
    ("西北桥", "西北散岛", -28.5, 21.5, 24.0, 2.45, 3.50, 1.20),
    ("东北桥", "东北散岛", 21.5, 26.8, 28.0, 0.95, 3.55, 1.18),
    ("西南桥", "西南散岛", -20.5, -18.8, 24.0, 3.95, 3.35, 1.12),
    ("瀛洲桥", "瀛洲散岛", 15.0, -31.6, 16.8, 3.90, 3.85, 1.05),
    ("方丈桥", "方丈浮矶", -15.0, -32.8, 17.2, 2.47, 3.85, 1.05),
    ("蓬莱桥", "蓬莱霞峰", -38.2, 16.2, 22.0, 0.55, 3.90, 1.10),
    ("碧虚桥", "碧虚云台", 38.4, 15.6, 22.0, 2.55, 3.90, 1.10),
]

GATES = [
    ("东塔", "东塔岛", 41.6, 12.4, math.pi), ("西亭", "西亭岛", -41.2, 7.6, 0.0),
    ("北崖", "北崖阁岛", 4.8, 45.6, math.pi), ("南矶", "南迎客矶", 0.0, -41.6, 0.0),
    ("东南", "东南散岛", 33.2, -23.4, 2.2), ("西北", "西北散岛", -31.2, 30.2, 5.5),
    ("东北", "东北散岛", 31.4, 32.2, 3.9), ("西南", "西南散岛", -29.6, -25.8, 0.8),
]


def zone(x, y, iname):
    cx, cy, r, deck = ISLANDS[iname]
    z, t = island_z(x, y, cx, cy, r, deck)
    if z is not None:
        return f"岛t={t:.2f} z差={z:.2f}", z
    if main_t(x, y) < 0.93:
        return f"主岛t={main_t(x, y):.2f}", ground_z(x, y)
    if main_t(x, y) < 1.0:
        return f"主岛缘t={main_t(x, y):.2f}", ground_z(x, y)
    return "水面", WATER_Z


print("=" * 100)
print("现状桥端点判定")
for name, iname, x, y, L, A, dz, rise in BRIDGES:
    (x1, y1), (x2, y2) = bridge_ends(x, y, L, A)
    z1s, z1 = zone(x1, y1, iname)
    z2s, z2 = zone(x2, y2, iname)
    print(f"{name:5s} 端1({x1:6.1f},{y1:6.1f}) {z1s:16s} deck差={dz - z1:+.2f} | "
          f"端2({x2:6.1f},{y2:6.1f}) {z2s:16s} deck差={dz - z2:+.2f}")

print("=" * 100)
print("现状门判定")
for name, iname, x, y, A in GATES:
    z = {"东塔岛": 5.20, "西亭岛": 5.05, "北崖阁岛": 6.35, "南迎客矶": 5.25,
         "东南散岛": 4.80, "西北散岛": 5.00, "东北散岛": 4.95, "西南散岛": 4.75}[iname]
    zs, gz = zone(x, y, iname)
    print(f"{name:4s}门 ({x:6.1f},{y:6.1f}) {zs:18s} 门z={z + .02:.2f} 脚下z={gz:.2f} 高差={z + .02 - gz:+.2f}")

print("=" * 100)
print("新参数求解（桥+门统一方案）")
for name, iname, *_ in BRIDGES:
    cx, cy, r, deck = ISLANDS[iname]
    d = math.hypot(cx, cy - CY)
    mx_, my_ = cx / d, (cy - CY) / d      # 主岛心→岛方向
    dx, dy = -mx_, -my_                   # 岛→主岛心方向
    # 桥落点：岛 t=0.58（靠主岛一侧）
    lx, ly = cx + .58 * r * dx, cy + .58 * r * .86 * dy
    zl = deck - .58 * .28
    # 岸上起点：沿椭圆角搜索，避开山坡，保证桥面不被岸头埋掉
    th0 = math.atan2(my_, mx_)
    best = None
    for k in range(-40, 41):
        th = th0 + k * 0.02
        ex, ey = RX * .93 * math.cos(th), CY + RY * .93 * math.sin(th)
        Lc = math.hypot(lx - ex, ly - ey)
        if Lc > 23:
            continue
        zsc = ground_z(ex, ey)
        cost = max(0, zsc - (zl + .25)) * 10 + abs(k) * 0.05 + max(0, Lc - 18) * 0.3
        if best is None or cost < best[0]:
            best = (cost, ex, ey, zsc, Lc)
    _, sx, sy, zs, L = best
    mx, my = (lx + sx) / 2, (ly + sy) / 2
    A = math.atan2(-(lx - sx), (ly - sy))
    deck_z = zl + .04
    bury = zs - deck_z
    rise = 1.15 + (0.20 if L > 15 else 0)
    # 门：岛 t=0.42，桥面方向
    gx, gy = cx + .42 * r * dx, cy + .42 * r * .86 * dy
    gz = deck - .42 * .28 + .02
    print(f"{name:5s} arch_bridge({mx:.1f},{my:.1f},{L:.1f},1.25,{A:.2f},{deck_z:.2f},{rise:.2f})  "
          f"岸z={zs:.2f}(埋{bury:+.2f}) 落点z={zl:.2f}")
    print(f"      门 hanging_flower_gate({gx:.1f},{gy:.1f},{gz:.2f},{A:.2f})")

print("=" * 100)
print("楼梯岛（北崖/南矶）修正")
for iname, sx, sy, sz, ex, ey, ez in [
    ("北崖阁岛", 2.2, 34.5, 4.2, 3.4, 48.6, 6.45),
    ("南迎客矶", 0.0, -42.4, 5.35, 0.0, -28.2, 3.98),
]:
    cx, cy, r, deck = ISLANDS[iname]
    zs, zs_t = zone(sx, sy, iname)[1], None
    ze = zone(ex, ey, iname)[1]
    print(f"{iname}: 阶脚({sx},{sy}) 现z={sz} 地z={zs:.2f} 差{sz - zs:+.2f} | "
          f"阶顶({ex},{ey}) 现z={ez} 地z={ze:.2f} 差{ez - ze:+.2f}")
    # 门放阶顶靠岛心 t=0.40
    dx, dy = (ex - cx), (ey - cy)
    dd = math.hypot(dx / r, dy / (r * .86))
    ux, uy = dx / dd, dy / dd
    gx, gy = cx + .40 * ux, cy + .40 * uy
    gz = deck - .40 * .28 + .02
    A = math.atan2(-(gx - ex) * -1, (gy - ey))  # 通道顺登岛方向
    print(f"   门 hanging_flower_gate({gx:.1f},{gy:.1f},{gz:.2f},{A:.2f})")
