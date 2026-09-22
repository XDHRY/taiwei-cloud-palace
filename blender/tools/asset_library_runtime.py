"""Cross-pack asset loading helpers for Taiwei Cloud Palace."""
from __future__ import annotations
from pathlib import Path
import bpy

def descendants(root):
    out=[]; stack=list(root.children)
    while stack:
        o=stack.pop(); out.append(o); stack.extend(o.children)
    return out

def append_selected_assets(blend_path, asset_ids, target_collection):
    blend_path=str(Path(blend_path).resolve())
    wanted=set(asset_ids)
    with bpy.data.libraries.load(blend_path, link=False) as (src,dst):
        dst.objects=list(src.objects)
    loaded=[o for o in dst.objects if o is not None]
    roots={o.get("asset_id"):o for o in loaded if o.get("asset_id")}
    missing=wanted-set(roots)
    if missing:
        raise RuntimeError(f"Missing assets in {blend_path}: {sorted(missing)}")

    selected=[]
    for aid in asset_ids:
        root=roots[aid]
        selected.append(root)
        for o in [root,*descendants(root)]:
            if len(o.users_collection)==0:
                target_collection.objects.link(o)
    # Unselected objects were loaded into bpy.data but remain unlinked. Remove
    # them to keep the integration study compact and deterministic.
    keep=set()
    for r in selected:
        keep.add(r); keep.update(descendants(r))
    for o in loaded:
        if o not in keep and len(o.users_collection)==0:
            bpy.data.objects.remove(o,do_unlink=True)
    return {r["asset_id"]:r for r in selected}

def place(root, location, rotation=(0,0,0), scale=1.0):
    root.location=location
    root.rotation_euler=rotation
    root.scale=(scale,scale,scale)
    root["integration_study"]=True
    return root
