# -*- coding: utf-8 -*-
"""Read-only gap audit on the currently loaded blend. Never clears the scene."""
import bpy
import json
import os
from mathutils import Vector

OUT = os.environ.get(
    "TAIWEI_GAP_OUT",
    bpy.path.abspath("//diag/gap_measure.json"),
)
SHOT = os.environ.get(
    "TAIWEI_GAP_SHOT",
    bpy.path.abspath("//diag/gap_east_elevation.png"),
)

os.makedirs(os.path.dirname(OUT), exist_ok=True)


def world_z_range(obj):
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    zs = [p.z for p in corners]
    return min(zs), max(zs), obj.location.copy()


def pick(substr):
    return [o for o in bpy.data.objects if substr in o.name and o.type == "MESH"]


groups = {}
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    name = o.name
    key = None
    for tag in ("_台基殿身", "_柱梁斗拱", "_屋面封檐", "_分行筒瓦"):
        if tag in name:
            key = name.split(tag)[0]
            groups.setdefault(key, {})
            groups[key][tag[1:]] = o.name
            break

rows = []
for hall, parts in sorted(groups.items()):
    row = {"hall": hall, "parts": parts}
    wall = bpy.data.objects.get(parts.get("台基殿身", ""))
    wood = bpy.data.objects.get(parts.get("柱梁斗拱雀替", parts.get("柱梁斗拱", "")))
    if wood is None:
        for k, n in parts.items():
            if "柱梁" in k:
                wood = bpy.data.objects.get(n)
    roof = bpy.data.objects.get(parts.get("屋面封檐", ""))
    if wall:
        z0, z1, loc = world_z_range(wall)
        row["wall_z"] = [round(z0, 3), round(z1, 3)]
        row["wall_xy"] = [round(loc.x, 2), round(loc.y, 2)]
    if wood:
        z0, z1, _ = world_z_range(wood)
        row["wood_z"] = [round(z0, 3), round(z1, 3)]
    if roof:
        z0, z1, _ = world_z_range(roof)
        row["roof_z"] = [round(z0, 3), round(z1, 3)]
    if "wall_z" in row and "roof_z" in row:
        row["gap_wall_top_to_roof_bottom"] = round(row["roof_z"][0] - row["wall_z"][1], 3)
    if "wood_z" in row and "roof_z" in row:
        row["gap_wood_top_to_roof_bottom"] = round(row["roof_z"][0] - row["wood_z"][1], 3)
    rows.append(row)

rows.sort(key=lambda r: abs(r.get("gap_wall_top_to_roof_bottom") or 0), reverse=True)

# corridor / pavilion / garden wall by name fragments
extras = []
for frag in ("回廊", "八角", "园林围墙", "月洞"):
    objs = pick(frag)
    if not objs:
        continue
    zs = [world_z_range(o) for o in objs]
    extras.append({
        "frag": frag,
        "count": len(objs),
        "zmin": round(min(z[0] for z in zs), 3),
        "zmax": round(max(z[1] for z in zs), 3),
        "names": [o.name for o in objs[:8]],
    })

report = {
    "object_count": len(bpy.data.objects),
    "halls": rows,
    "extras": extras,
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
print("WROTE", OUT)
print("HALLS", len(rows))
for r in rows[:12]:
    print(
        " ",
        r["hall"][:20],
        "wall", r.get("wall_z"),
        "roof", r.get("roof_z"),
        "gap", r.get("gap_wall_top_to_roof_bottom"),
    )

# East elevation still of 太微正殿
hall = bpy.data.objects.get("太微正殿_台基殿身")
target = Vector((0.0, 13.8, 10.0))
if hall:
    target = hall.matrix_world.translation.copy()
    target.z = (world_z_range(hall)[1] + 1.2)

cam_data = bpy.data.cameras.new("GAP_EAST")
cam_data.type = "ORTHO"
cam_data.ortho_scale = 18.0
cam_data.clip_end = 400
cam_obj = bpy.data.objects.new("GAP_EAST", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
cam_obj.location = (target.x + 22.0, target.y, target.z + 0.4)
cam_obj.rotation_euler = (1.5708, 0.0, 1.5708)

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.eevee.taa_render_samples = 16
scene.camera = cam_obj
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = SHOT
# keep existing engine; just still
bpy.ops.render.render(write_still=True)
print("SHOT", SHOT)
print("GAP_MEASURE_DONE")
