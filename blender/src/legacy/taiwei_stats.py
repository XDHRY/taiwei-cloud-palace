# -*- coding: utf-8 -*-
"""Build the scene and report geometry with unique-mesh accounting."""

import json
import os
import time

import bpy

WORKSPACE = "E:/UserData/xdrhh/.openclaw/workspace"
GENERATOR = os.path.join(WORKSPACE, "taiwei_cloud_palace_generator.py")

START = time.time()
GEN = {"__name__": "__main__"}
exec(compile(open(GENERATOR, encoding="utf-8").read(), GENERATOR, "exec"), GEN)
BUILD_SECONDS = time.time() - START

scene = bpy.context.scene

unique_meshes = {}
curve_objects = [o for o in bpy.data.objects if o.type == "CURVE"]
mesh_objects = [o for o in bpy.data.objects if o.type == "MESH"]

for obj in mesh_objects:
    mesh = obj.data
    entry = unique_meshes.setdefault(
        mesh.name, {"verts": len(mesh.vertices), "polys": len(mesh.polygons),
                    "instances": 0}
    )
    entry["instances"] += 1

unique_verts = sum(m["verts"] for m in unique_meshes.values())
unique_polys = sum(m["polys"] for m in unique_meshes.values())
instance_verts = sum(m["verts"] * m["instances"] for m in unique_meshes.values())
instance_polys = sum(m["polys"] * m["instances"] for m in unique_meshes.values())

curve_verts = sum(
    len(o.data.splines) * 8 for o in curve_objects
)

heavy_unique = sorted(
    ({"mesh": k, "polys": v["polys"], "verts": v["verts"], "instances": v["instances"]}
     for k, v in unique_meshes.items()),
    key=lambda d: -d["polys"],
)[:12]

summary = {
    "quality": GEN["QUALITY"],
    "build_seconds": round(BUILD_SECONDS, 1),
    "objects_total": len(bpy.data.objects),
    "mesh_objects": len(mesh_objects),
    "unique_mesh_datablocks": len(unique_meshes),
    "curve_objects": len(curve_objects),
    "curve_splines_total": sum(len(o.data.splines) for o in curve_objects),
    "unique_verts": unique_verts,
    "unique_polys": unique_polys,
    "instanced_verts": instance_verts,
    "instanced_polys": instance_polys,
    "instance_ratio": round(instance_polys / max(1, unique_polys), 2),
    "heaviest_unique_meshes": heavy_unique,
}

# Render-cost proxies
summary["volumes"] = [
    o.name for o in bpy.data.objects
    if o.type == "MESH" and any(
        mat and mat.use_nodes and any(
            n.type == "BSDF_PRINCIPLED" or n.bl_idname == "ShaderNodeVolumePrincipled"
            for n in mat.node_tree.nodes
        )
        for mat in o.data.materials
    ) and any("云" in (m.name if m else "") or "空气" in (m.name if m else "")
              for m in o.data.materials)
]
summary["cycles_device"] = scene.cycles.device
summary["resolution"] = [scene.render.resolution_x, scene.render.resolution_y]
summary["resolution_percentage"] = scene.render.resolution_percentage
summary["samples"] = scene.cycles.samples
summary["adaptive_threshold"] = round(scene.cycles.adaptive_threshold, 4)
summary["volume_bounces"] = scene.cycles.volume_bounces
summary["light_count"] = len([o for o in bpy.data.objects if o.type == "LIGHT"])

print("STATS_JSON_BEGIN")
print(json.dumps(summary, ensure_ascii=False, indent=2))
print("STATS_JSON_END")
