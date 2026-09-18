"""悬浮审计：对每个建筑/雕饰对象向下打射线，找底面与支撑面的高差。

用法：在生成器之后同一 Blender 会话运行。
报告 gap > 0.45 的对象（排除屋面/瓦作/桥/栏杆等天然悬空类别）。
"""
import bpy
from mathutils import Vector

SKIP_SUBSTR = ("瓦", "檐", "椽", "桥", "栏", "望", "山", "水", "瀑", "云", "雾",
               "鹤", "鱼", "树", "草", "花", "荷", "芦", "笠", "脊", "吻", "风铃")
AUDIT_GROUPS = {"03_殿阁木构", "05_门窗雕饰", "10_庭院陈设"}


def support_gap(scene, deps, obj, min_z, cx, cy):
    origin = Vector((cx, cy, min_z + 40.0))
    direction = Vector((0, 0, -1))
    for _ in range(24):
        hit, loc, _n, _i, hit_obj, _m = scene.ray_cast(
            deps, origin, direction, distance=80
        )
        if not hit:
            return None
        if hit_obj is not obj:
            return min_z - loc.z
        origin = Vector((cx, cy, loc.z - 0.02))
    return None


def main():
    scene = bpy.context.scene
    deps = bpy.context.evaluated_depsgraph_get()
    rows = []
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        groups = {c.name for c in obj.users_collection}
        if not (groups & AUDIT_GROUPS):
            continue
        if any(s in obj.name for s in SKIP_SUBSTR):
            continue
        bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
        min_z = min(v.z for v in bb)
        cx = sum(v.x for v in bb) / 8
        cy = sum(v.y for v in bb) / 8
        gap = support_gap(scene, deps, obj, min_z, cx, cy)
        if gap is None:
            rows.append((999.0, obj.name, min_z, cx, cy))
        elif gap > 0.45:
            rows.append((gap, obj.name, min_z, cx, cy))
    rows.sort(reverse=True)
    print("=== FLOAT AUDIT ===")
    for gap, name, z, x, y in rows[:40]:
        print(f"gap={gap:6.2f} z={z:6.2f} at({x:6.1f},{y:6.1f}) {name}")
    print(f"=== {len(rows)} suspects ===")


main()
