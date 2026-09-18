# -*- coding: utf-8 -*-
"""CI smoke assertions executed after the STUDY generator in the same Blender process."""
import math
import os
from pathlib import Path

import bpy

scene = bpy.context.scene

EXPECTED_COLLECTIONS = {
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
}
EXPECTED_CAMERAS = {
    "01_云宫山水总览",
    "02_重檐正殿",
    "04_中轴礼序",
    "06_正殿平视",
    "07_东侧立面",
    "08_正殿脊吻",
}

collections = set(bpy.data.collections.keys())
missing_collections = sorted(EXPECTED_COLLECTIONS - collections)
assert not missing_collections, f"missing collections: {missing_collections}"

cameras = {o.name for o in bpy.data.objects if o.type == "CAMERA"}
missing_cameras = sorted(EXPECTED_CAMERAS - cameras)
assert not missing_cameras, f"missing cameras: {missing_cameras}"
assert scene.camera is not None, "active scene camera is missing"

objects = list(scene.objects)
meshes = [o for o in objects if o.type == "MESH"]
assert len(objects) >= 250, f"unexpectedly small STUDY scene: {len(objects)} objects"
assert len(meshes) >= 150, f"unexpectedly small STUDY mesh set: {len(meshes)} meshes"
assert len(bpy.data.materials) >= 40, f"too few materials: {len(bpy.data.materials)}"
assert scene.render.engine == "CYCLES", f"unexpected render engine: {scene.render.engine}"

empty_meshes = [o.name for o in meshes if o.data is None or len(o.data.vertices) == 0]
assert not empty_meshes, f"empty meshes: {empty_meshes[:20]}"

bad_transforms = []
for obj in objects:
    values = list(obj.location) + list(obj.rotation_euler) + list(obj.scale)
    if not all(math.isfinite(float(v)) for v in values):
        bad_transforms.append(obj.name)
assert not bad_transforms, f"non-finite transforms: {bad_transforms[:20]}"

missing_images = []
for image in bpy.data.images:
    if image.source != "FILE" or image.packed_file:
        continue
    path = Path(bpy.path.abspath(image.filepath))
    if not path.exists():
        missing_images.append((image.name, str(path)))
assert not missing_images, f"missing external images: {missing_images[:20]}"
assert len([img for img in bpy.data.images if img.source == "FILE"]) >= 10, "texture binding smoke loaded too few images"

output_dir = Path(bpy.path.abspath(os.environ["TAIWEI_OUTPUT_DIRECTORY"]))
project_file = output_dir / os.environ.get("TAIWEI_PROJECT_FILENAME", "TaiWei_Cloud_Palace.blend")
assert project_file.exists(), f"saved STUDY blend missing: {project_file}"
assert project_file.stat().st_size > 1_000_000, f"saved STUDY blend suspiciously small: {project_file.stat().st_size}"

print("TAIWEI_CI_SMOKE_OK", {
    "objects": len(objects),
    "meshes": len(meshes),
    "materials": len(bpy.data.materials),
    "images": len([img for img in bpy.data.images if img.source == "FILE"]),
    "cameras": len(cameras),
    "blend_bytes": project_file.stat().st_size,
})
