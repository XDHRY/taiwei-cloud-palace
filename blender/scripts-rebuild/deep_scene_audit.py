import bpy
import os
from mathutils import Vector

def audit_scene():
    print("=================== DEEP SCENE AUDIT ===================")
    
    # 1. Image and Texture Check
    print("\n--- 1. IMAGE & TEXTURE AUDIT ---")
    missing_images = []
    zero_size_images = []
    for img in bpy.data.images:
        if img.source == 'FILE':
            filepath = bpy.path.abspath(img.filepath)
            if not os.path.exists(filepath):
                missing_images.append((img.name, img.filepath))
            elif img.size[0] == 0 or img.size[1] == 0:
                zero_size_images.append((img.name, img.size))
    print(f"Total Images: {len(bpy.data.images)}")
    print(f"Missing Image Files ({len(missing_images)}):")
    for name, path in missing_images:
        print(f"  [MISSING] {name}: {path}")
    print(f"Zero-size Images ({len(zero_size_images)}):")
    for name, sz in zero_size_images:
        print(f"  [ZERO] {name}: {sz}")

    # 2. Material & Shader Node Check
    print("\n--- 2. MATERIAL & SHADER NODE AUDIT ---")
    materials_without_nodes = []
    materials_with_unlinked_output = []
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            materials_without_nodes.append(mat.name)
            continue
        output_nodes = [n for n in mat.node_tree.nodes if n.type == 'OUTPUT_MATERIAL']
        if not output_nodes or not any(n.inputs['Surface'].is_linked for n in output_nodes):
            materials_with_unlinked_output.append(mat.name)
    print(f"Total Materials: {len(bpy.data.materials)}")
    print(f"Materials without nodes ({len(materials_without_nodes)}): {materials_without_nodes[:10]}")
    print(f"Materials with unlinked surface output ({len(materials_with_unlinked_output)}): {materials_with_unlinked_output[:10]}")

    # 3. Object & Transform Check (Non-uniform scale, huge scales)
    print("\n--- 3. OBJECT TRANSFORM & SCALE AUDIT ---")
    unapplied_scale = []
    negative_scale = []
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            s = obj.scale
            if s.x < 0 or s.y < 0 or s.z < 0:
                negative_scale.append(obj.name)
            # check non-uniform
            if abs(s.x - 1.0) > 0.01 or abs(s.y - 1.0) > 0.01 or abs(s.z - 1.0) > 0.01:
                unapplied_scale.append((obj.name, (round(s.x, 2), round(s.y, 2), round(s.z, 2))))
    print(f"Total Meshes: {len([o for o in bpy.data.objects if o.type == 'MESH'])}")
    print(f"Negative Scale Objects ({len(negative_scale)}): {negative_scale[:10]}")
    print(f"Unapplied Scale Objects ({len(unapplied_scale)}): {len(unapplied_scale)} items")
    if unapplied_scale:
        print(f"  Examples: {unapplied_scale[:5]}")

    # 4. Mesh Geometry Integrity Check
    print("\n--- 4. MESH GEOMETRY INTEGRITY AUDIT ---")
    empty_meshes = []
    degenerate_faces = []
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.data:
            me = obj.data
            if len(me.vertices) == 0:
                empty_meshes.append(obj.name)
            # Check for loose vertices or edges if any
    print(f"Empty Meshes ({len(empty_meshes)}): {empty_meshes}")

    # 5. Lighting & World Check
    print("\n--- 5. LIGHTING & WORLD AUDIT ---")
    lights = [o for o in bpy.data.objects if o.type == 'LIGHT']
    print(f"Total Lights: {len(lights)}")
    for l in lights:
        print(f"  Light: {l.name} | Type: {l.data.type} | Energy: {l.data.energy} | Color: {l.data.color[:]} | Loc: {tuple(round(c, 2) for c in l.location)}")
    
    world = bpy.context.scene.world
    if world and world.use_nodes:
        bg_nodes = [n for n in world.node_tree.nodes if n.type == 'BACKGROUND']
        for bg in bg_nodes:
            color = bg.inputs['Color'].default_value[:] if not bg.inputs['Color'].is_linked else "LINKED"
            strength = bg.inputs['Strength'].default_value if not bg.inputs['Strength'].is_linked else "LINKED"
            print(f"  World Background: Color={color} | Strength={strength}")
    else:
        print("  World: No nodes")

    # 6. Cameras & Clip Distances
    print("\n--- 6. CAMERA & CLIP DISTANCE AUDIT ---")
    cameras = [o for o in bpy.data.objects if o.type == 'CAMERA']
    print(f"Total Cameras: {len(cameras)}")
    for c in cameras:
        cam = c.data
        print(f"  Camera: {c.name} | Lens: {round(cam.lens, 1)}mm | Clip: {cam.clip_start}m .. {cam.clip_end}m | Loc: {tuple(round(v, 2) for v in c.location)}")
        if cam.clip_end < 250:
            print(f"    [WARN] Clip end ({cam.clip_end}m) may clip far mountains!")

    # 7. Collection / Hierarchy Check
    print("\n--- 7. COLLECTION / HIERARCHY AUDIT ---")
    for col in bpy.data.collections:
        print(f"  Collection '{col.name}': {len(col.objects)} objects")

    print("\n=================== AUDIT COMPLETED ===================")

if __name__ == "__main__":
    audit_scene()
