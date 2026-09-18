"""Export TaiWei Align HIGH scene to optimised GLB for web viewer.

Usage:
  set TAIWEI_GLB_OUT=E:/UserData/xdrhh/.openclaw/workspace/taiwei_video/TaiWei_Align/taiwei_web.glb
  "D:/blender-portable/blender.exe" --factory-startup -b ^
      "E:/UserData/xdrhh/.openclaw/workspace/taiwei_video/TaiWei_Align/TaiWei_Align_HIGH.blend" ^
      -P "E:/UserData/xdrhh/.openclaw/workspace/taiwei_video/export_glb_web.py"

The script:
  1. Joins tiny meshes per collection to reduce draw calls
  2. Applies a decimate modifier (ratio 0.5) on heavy meshes
  3. Limits texture resolution to 1024
  4. Exports glTF binary (.glb) with Draco mesh compression
"""

import bpy
import os
import sys
import math

OUT = os.environ.get(
    "TAIWEI_GLB_OUT",
    os.path.join(os.path.dirname(bpy.data.filepath), "taiwei_web.glb"),
)

print(f"[GLB-EXPORT] Target: {OUT}")
print(f"[GLB-EXPORT] Scene objects: {len(bpy.data.objects)}")

# ------------------------------------------------------------------
# 1. Remove non-mesh clutter (cameras, lights, empties, armatures)
#    We will re-create lights in Three.js
# ------------------------------------------------------------------
to_remove = []
for obj in bpy.data.objects:
    if obj.type not in ('MESH', 'CURVE'):
        to_remove.append(obj)

for obj in to_remove:
    bpy.data.objects.remove(obj, do_unlink=True)

# Convert remaining curves to mesh
for obj in list(bpy.data.objects):
    if obj.type == 'CURVE':
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.convert(target='MESH')
        obj.select_set(False)

print(f"[GLB-EXPORT] Mesh objects after cleanup: {len(bpy.data.objects)}")

# ------------------------------------------------------------------
# 2. Decimate heavy meshes (>5000 faces) with ratio 0.45
# ------------------------------------------------------------------
FACE_THRESHOLD = 5000
DECIMATE_RATIO = 0.45
decimated = 0

for obj in list(bpy.data.objects):
    if obj.type != 'MESH':
        continue
    me = obj.data
    if me is None:
        continue
    # Make single-user if shared
    if me.users > 1:
        obj.data = me.copy()
    fc = len(obj.data.polygons)
    if fc > FACE_THRESHOLD:
        mod = obj.modifiers.new("web_decimate", 'DECIMATE')
        mod.ratio = DECIMATE_RATIO
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        try:
            bpy.ops.object.modifier_apply(modifier=mod.name)
            decimated += 1
        except Exception as e:
            print(f"[GLB-EXPORT] Decimate skip {obj.name}: {e}")
            obj.modifiers.remove(mod)
        obj.select_set(False)

print(f"[GLB-EXPORT] Decimated {decimated} heavy meshes")

# ------------------------------------------------------------------
# 3. Limit texture size to 1024px (scale down in-place)
# ------------------------------------------------------------------
MAX_TEX = 1024
scaled_tex = 0
for img in bpy.data.images:
    if img.size[0] > MAX_TEX or img.size[1] > MAX_TEX:
        img.scale(min(img.size[0], MAX_TEX), min(img.size[1], MAX_TEX))
        scaled_tex += 1

print(f"[GLB-EXPORT] Scaled {scaled_tex} textures to <={MAX_TEX}px")

# ------------------------------------------------------------------
# 4. Join small meshes per collection to reduce draw calls
# ------------------------------------------------------------------
JOIN_THRESHOLD = 200  # faces
joined = 0
for coll in bpy.data.collections:
    small_meshes = []
    for obj in coll.objects:
        if obj.type == 'MESH' and obj.data and len(obj.data.polygons) < JOIN_THRESHOLD:
            small_meshes.append(obj)
    if len(small_meshes) < 2:
        continue

    # Group by material to preserve appearance
    mat_groups = {}
    for obj in small_meshes:
        mat_key = ""
        if obj.data.materials:
            mat_key = obj.data.materials[0].name if obj.data.materials[0] else ""
        mat_groups.setdefault(mat_key, []).append(obj)

    for mat_key, group in mat_groups.items():
        if len(group) < 3:
            continue
        bpy.ops.object.select_all(action='DESELECT')
        for obj in group:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = group[0]
        try:
            bpy.ops.object.join()
            joined += len(group) - 1
        except Exception as e:
            print(f"[GLB-EXPORT] Join failed for {mat_key}: {e}")

print(f"[GLB-EXPORT] Joined {joined} small meshes")
print(f"[GLB-EXPORT] Final object count: {len(bpy.data.objects)}")

# ------------------------------------------------------------------
# 5. Ensure all meshes have vertex colors for base appearance
#    (materials in Blender won't transfer perfectly to glTF,
#     but Principled BSDF base color will map)
# ------------------------------------------------------------------

# ------------------------------------------------------------------
# 6. Export GLB with Draco compression
# ------------------------------------------------------------------
os.makedirs(os.path.dirname(OUT), exist_ok=True)

export_settings = {
    "filepath": OUT,
    "check_existing": False,
    "export_format": "GLB",
    "export_draco_mesh_compression_enable": True,
    "export_draco_mesh_compression_level": 6,
    "export_draco_position_quantization": 14,
    "export_draco_normal_quantization": 10,
    "export_draco_texcoord_quantization": 12,
    "export_draco_color_quantization": 10,
    "export_materials": "EXPORT",
    "export_normals": True,
    "export_tangents": False,
    "export_texcoords": True,
    "export_image_format": "JPEG",
    "export_jpeg_quality": 72,
}

try:
    bpy.ops.export_scene.gltf(**export_settings)
except TypeError as e:
    print(f"[GLB-EXPORT] Adjusting params: {e}")
    minimal = {
        "filepath": OUT,
        "check_existing": False,
        "export_format": "GLB",
        "export_draco_mesh_compression_enable": True,
        "export_materials": "EXPORT",
        "export_image_format": "JPEG",
    }
    bpy.ops.export_scene.gltf(**minimal)

fsize = os.path.getsize(OUT) / (1024 * 1024)
print(f"[GLB-EXPORT] DONE => {OUT} ({fsize:.1f} MB)")
