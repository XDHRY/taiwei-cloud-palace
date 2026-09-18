# -*- coding: utf-8 -*-
"""QA driver: build the TaiWei scene, save it, render previews, print metrics."""

import json
import math
import os
import time
import traceback

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

WORKSPACE = "E:/UserData/xdrhh/.openclaw/workspace"
GENERATOR = os.path.join(WORKSPACE, "taiwei_cloud_palace_generator.py")
OUT_DIR = os.environ.get(
    "TAIWEI_QA_OUT", os.path.join(WORKSPACE, "taiwei_qa_output")
)
PREVIEW = os.environ.get("TAIWEI_QA_PREVIEW", "1") == "1"
PREVIEW_SAMPLES = int(os.environ.get("TAIWEI_QA_SAMPLES", "16"))
PREVIEW_SCALE = int(os.environ.get("TAIWEI_QA_SCALE", "35"))

os.makedirs(OUT_DIR, exist_ok=True)
START = time.time()


def log(message):
    print(f"[QA {time.time() - START:7.1f}s] {message}", flush=True)


# ---------------------------------------------------------------- build scene
log("executing generator")
source = open(GENERATOR, encoding="utf-8").read()
GEN = {"__name__": "__main__"}
exec(compile(source, GENERATOR, "exec"), GEN)
CAMERAS = GEN["CAMERAS"]
log("generator finished")

scene = bpy.context.scene

# ------------------------------------------------------------------- metrics
report = {"counts": {}, "geometry": {}, "materials": [], "cameras": [], "issues": []}

objects = list(bpy.data.objects)
report["counts"]["objects"] = len(objects)
report["counts"]["meshes"] = sum(1 for o in objects if o.type == "MESH")
report["counts"]["curves"] = sum(1 for o in objects if o.type == "CURVE")
report["counts"]["lights"] = sum(1 for o in objects if o.type == "LIGHT")
report["counts"]["cameras"] = sum(1 for o in objects if o.type == "CAMERA")
report["counts"]["collections"] = len(scene.collection.children)

total_verts = total_polys = 0
empty_mesh = []
nan_mesh = []
no_material = []

for obj in objects:
    if obj.type == "MESH":
        mesh = obj.data
        if len(mesh.vertices) == 0 or len(mesh.polygons) == 0:
            empty_mesh.append(obj.name)
            continue
        total_verts += len(mesh.vertices)
        total_polys += len(mesh.polygons)
        if not mesh.materials:
            no_material.append(obj.name)
        for vertex in mesh.vertices:
            co = vertex.co
            if not all(math.isfinite(v) for v in (co.x, co.y, co.z)):
                nan_mesh.append(obj.name)
                break
    elif obj.type == "CURVE":
        if len(obj.data.splines) == 0:
            empty_mesh.append(obj.name)

report["geometry"]["total_vertices"] = total_verts
report["geometry"]["total_polygons"] = total_polys
report["counts"]["empty_objects"] = len(empty_mesh)
report["counts"]["nan_objects"] = len(nan_mesh)
report["counts"]["mesh_without_material"] = len(no_material)
if empty_mesh:
    report["issues"].append({"level": "warn", "kind": "empty_geometry",
                             "detail": empty_mesh[:20]})
if nan_mesh:
    report["issues"].append({"level": "error", "kind": "nan_vertices",
                             "detail": nan_mesh[:20]})
if no_material:
    report["issues"].append({"level": "warn", "kind": "mesh_without_material",
                             "detail": no_material[:20]})

for mat in bpy.data.materials:
    entry = {"name": mat.name, "users": mat.users}
    if mat.use_nodes:
        entry["nodes"] = len(mat.node_tree.nodes)
        entry["principled"] = any(
            n.type == "BSDF_PRINCIPLED" for n in mat.node_tree.nodes
        )
        if not entry["principled"]:
            report["issues"].append(
                {"level": "warn", "kind": "material_without_principled",
                 "detail": mat.name}
            )
    report["materials"].append(entry)

# --------------------------------------------------------------- scene bounds
low = Vector((1e9, 1e9, 1e9))
high = Vector((-1e9, -1e9, -1e9))
for obj in objects:
    if obj.type not in {"MESH", "CURVE"}:
        continue
    if obj.name.startswith(("空气透视", "山腰流云", "远山横岚", "瀑脚水雾")):
        continue
    for corner in obj.bound_box:
        point = obj.matrix_world @ Vector(corner)
        for axis in range(3):
            low[axis] = min(low[axis], point[axis])
            high[axis] = max(high[axis], point[axis])

report["geometry"]["content_min"] = [round(v, 2) for v in low]
report["geometry"]["content_max"] = [round(v, 2) for v in high]

corners = [
    Vector((x, y, z))
    for x in (low.x, high.x)
    for y in (low.y, high.y)
    for z in (low.z, high.z)
]

# ------------------------------------------------------------------- cameras
for cam_obj in [o for o in objects if o.type == "CAMERA"]:
    cam = cam_obj.data
    cos = []
    inside = 0
    for corner in corners:
        co = world_to_camera_view(scene, cam_obj, corner)
        cos.append(co)
        if 0.0 <= co.x <= 1.0 and 0.0 <= co.y <= 1.0 and co.z > 0:
            inside += 1

    xs = [c.x for c in cos]
    ys = [c.y for c in cos]
    entry = {
        "name": cam_obj.name,
        "lens": round(cam.lens, 1),
        "coverage": round(inside / len(corners), 3),
        "frame_x": [round(min(xs), 2), round(max(xs), 2)],
        "frame_y": [round(min(ys), 2), round(max(ys), 2)],
        "distance_to_target": round(
            (Vector((0, 8, 9.3)) - cam_obj.location).length, 1
        ),
    }
    report["cameras"].append(entry)
    if entry["coverage"] < 0.15:
        report["issues"].append(
            {"level": "warn", "kind": "camera_may_crop_content",
             "detail": cam_obj.name, "coverage": entry["coverage"]}
        )

# ------------------------------------------------------------------ save file
blend_path = os.path.join(OUT_DIR, "TaiWei_QA.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
report["blend"] = blend_path
log("saved blend: " + blend_path)

# ------------------------------------------------------------ preview renders
if PREVIEW:
    scene.render.resolution_percentage = PREVIEW_SCALE
    scene.cycles.samples = PREVIEW_SAMPLES
    scene.cycles.use_denoising = True
    scene.cycles.use_adaptive_sampling = False

    cameras = list(CAMERAS)
    rendered = []
    for cam_obj in cameras:
        scene.camera = cam_obj
        path = os.path.join(OUT_DIR, "preview_" + cam_obj.name + ".png")
        scene.render.filepath = path
        began = time.time()
        try:
            bpy.ops.render.render(write_still=True)
            ok = os.path.exists(path) and os.path.getsize(path) > 2000
            rendered.append({
                "camera": cam_obj.name,
                "file": path,
                "bytes": os.path.getsize(path) if os.path.exists(path) else 0,
                "seconds": round(time.time() - began, 1),
                "ok": bool(ok),
            })
            log(f"rendered {cam_obj.name} in {time.time() - began:.1f}s")
        except Exception as exc:  # noqa: BLE001
            rendered.append({"camera": cam_obj.name, "error": repr(exc),
                             "seconds": round(time.time() - began, 1)})
            report["issues"].append(
                {"level": "error", "kind": "render_failed",
                 "detail": cam_obj.name, "error": repr(exc)}
            )
    report["renders"] = rendered

report["seconds"] = round(time.time() - START, 1)
report_path = os.path.join(OUT_DIR, "qa_report.json")
with open(report_path, "w", encoding="utf-8") as handle:
    json.dump(report, handle, ensure_ascii=False, indent=2)

print("QA_JSON_BEGIN")
print(json.dumps({k: v for k, v in report.items() if k != "materials"},
                 ensure_ascii=False, indent=2))
print("QA_JSON_END")
log("done")
