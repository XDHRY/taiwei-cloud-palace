"""Render a cheap multi-angle Taiwei contact set in GitHub Actions.

This is deliberately a composition/material review pass, not the final film.
It opens an already-built STUDY .blend, switches to Eevee Next, and renders a
stable set of cameras so visual regressions are visible on every public CI run.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import bpy

OUT = Path(os.environ.get("TAIWEI_REVIEW_OUT", "ci_artifacts/review")).resolve()
OUT.mkdir(parents=True, exist_ok=True)

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = int(os.environ.get("TAIWEI_REVIEW_WIDTH", "560"))
scene.render.resolution_y = int(os.environ.get("TAIWEI_REVIEW_HEIGHT", "315"))
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_depth = "8"

# Review mode must stay cheap on GitHub-hosted CPU runners. Eevee temporal
# sampling defaults are tuned for interactive quality, so cap them here when
# the property exists; final/high renders remain untouched.
try:
    scene.render.image_settings.color_mode = "RGB"
except Exception:
    pass

# Blender 4.2 Eevee final renders default to 64 TAA samples. On the software
# renderer that made a single CI frame take ~18 minutes, so pin review quality
# explicitly. This touches only the disposable CI copy, never delivery renders.
if hasattr(scene, "eevee") and scene.eevee is not None:
    if hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = int(os.environ.get("TAIWEI_REVIEW_SAMPLES", "4"))
    if hasattr(scene.eevee, "volumetric_samples"):
        scene.eevee.volumetric_samples = 16
    if hasattr(scene.eevee, "shadow_step_count"):
        scene.eevee.shadow_step_count = 2
    if hasattr(scene.eevee, "use_raytracing"):
        scene.eevee.use_raytracing = False

# Keep the same AgX grading baked by the generator. The review set is meant to
# expose composition, silhouette, material separation and atmosphere quickly.
preferred = [
    "01_云宫山水总览",
    "02_重檐正殿",
    "03_荷塘虹桥",
    "09_北崖飞瀑",
]
all_cameras = {o.name: o for o in scene.objects if o.type == "CAMERA"}
selected = [all_cameras[n] for n in preferred if n in all_cameras]
if not selected:
    selected = sorted(all_cameras.values(), key=lambda o: o.name)[:4]
if not selected:
    raise RuntimeError("Taiwei review found no cameras")

rows = []
for cam in selected:
    scene.camera = cam
    safe = cam.name.replace("/", "_")
    path = OUT / f"{safe}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    rows.append({
        "camera": cam.name,
        "file": path.name,
        "location": [round(v, 4) for v in cam.location],
        "lens": round(cam.data.lens, 3),
    })
    print("TAIWEI_REVIEW_RENDERED", cam.name, path, flush=True)

report = {
    "blender_version": bpy.app.version_string,
    "engine": scene.render.engine,
    "resolution": [scene.render.resolution_x, scene.render.resolution_y],
    "objects": len(scene.objects),
    "cameras_total": len(all_cameras),
    "shots": rows,
}
(OUT / "review.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print("TAIWEI_REVIEW", json.dumps(report, ensure_ascii=False), flush=True)
