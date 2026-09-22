"""Render focused low-cost review frames for Taiwei Expansion Asset Pack V3."""
from __future__ import annotations
import argparse, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

GROUPS=[
 ("01_gate_and_stone.png",[
   "TW_V3_STONE_LION_MALE","TW_V3_STONE_LION_FEMALE","TW_V3_XUMI_BASE",
   "TW_V3_DRUM_STONE","TW_V3_PALACE_GATE","TW_V3_DOOR_STUD_PANEL"]),
 ("02_throne_and_interior.png",[
   "TW_V3_DRAGON_THRONE","TW_V3_THRONE_FOOTSTOOL","TW_V3_INCENSE_TABLE",
   "TW_V3_FLOOR_LAMP","TW_V3_CEILING_COFFERTILE"]),
 ("03_ritual_bronze.png",[
   "TW_V3_BRONZE_DING","TW_V3_BRONZE_ZUN","TW_V3_RITUAL_DRUM","TW_V3_BRONZE_BELL"]),
 ("04_roof_details.png",[
   "TW_V3_RIDGE_FINIAL","TW_V3_ROOF_BAOPING","TW_V3_DRAGON_GARGOYLE","TW_V3_DOUGONG_VARIANT"]),
 ("05_bridge_parapet.png",["TW_V3_CLOUD_PARAPET"]),
]

def parse_args():
    tail=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="docs/assets/expansion_pack_v3")
    p.add_argument("--width",type=int,default=1600)
    p.add_argument("--height",type=int,default=900)
    return p.parse_args(tail)

def look_at(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()

def area(name,loc,energy,size,color,target):
    d=bpy.data.lights.new(name,"AREA"); d.energy=energy; d.shape="DISK"; d.size=size; d.color=color
    o=bpy.data.objects.new(name,d); bpy.context.scene.collection.objects.link(o); o.location=loc; look_at(o,target)
    return o

def setup(width,height):
    s=bpy.context.scene
    s.render.engine="BLENDER_EEVEE_NEXT"
    s.render.resolution_x=width; s.render.resolution_y=height; s.render.resolution_percentage=100
    s.render.image_settings.file_format="PNG"; s.render.image_settings.color_mode="RGB"
    if s.world is None: s.world=bpy.data.worlds.new("V3ReviewWorld")
    s.world.color=(.015,.019,.028)
    area("V3_Key",(-12,-16,20),3500,10,(1.0,.72,.48),(0,0,1.4))
    area("V3_Fill",(13,-7,13),2300,9,(.40,.58,1.0),(0,0,1.4))
    area("V3_Rim",(0,15,19),2800,9,(.66,.80,1.0),(0,0,1.7))
    d=bpy.data.cameras.new("V3ReviewCamera"); d.lens=58
    cam=bpy.data.objects.new("V3ReviewCamera",d); s.collection.objects.link(cam); s.camera=cam
    bpy.ops.mesh.primitive_plane_add(size=80,location=(0,0,-.20))
    floor=bpy.context.object; floor.name="V3ReviewFloor"
    m=bpy.data.materials.new("V3ReviewFloorMat"); m.use_nodes=True
    bsdf=next(n for n in m.node_tree.nodes if n.type=="BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value=(.045,.050,.058,1); bsdf.inputs["Roughness"].default_value=.84
    floor.data.materials.append(m)
    return s,cam,floor

def descendants(root):
    out=[]; stack=list(root.children)
    while stack:
        o=stack.pop(); out.append(o); stack.extend(o.children)
    return out

def visibility(roots,selected):
    wanted=set(selected)
    for r in roots:
        show=r in wanted; r.hide_render=not show
        for o in descendants(r): o.hide_render=not show

def layout(selected):
    n=len(selected)
    if n==1:
        selected[0].location=(0,0,0)
    else:
        cols=3 if n<=6 else 4; rows=math.ceil(n/cols)
        sx,sy=4.6,4.2
        for i,r in enumerate(selected):
            r.location=((i%cols-(cols-1)/2)*sx,(i//cols-(rows-1)/2)*sy,0)
    bpy.context.view_layer.update()

def bounds(selected):
    pts=[]
    for r in selected:
        for o in descendants(r):
            if o.type not in {"MESH","CURVE"} or o.hide_render: continue
            for c in o.bound_box: pts.append(o.matrix_world @ Vector(c))
    assert pts
    mn=Vector((min(p.x for p in pts),min(p.y for p in pts),min(p.z for p in pts)))
    mx=Vector((max(p.x for p in pts),max(p.y for p in pts),max(p.z for p in pts)))
    return (mn+mx)/2,mx-mn

def render_group(s,cam,out,name,roots,selected):
    visibility(roots,selected); layout(selected)
    center,span=bounds(selected)
    extent=max(span.x,span.y*1.12,span.z*1.55,3.8)
    cam.location=center+Vector((0,-extent*1.48,extent*.58))
    cam.data.lens=60 if len(selected)>1 else 66
    look_at(cam,center+Vector((0,0,span.z*.04)))
    s.render.filepath=str((out/name).resolve())
    bpy.ops.render.render(write_still=True)

def main():
    a=parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    roots=[o for o in bpy.context.scene.objects if o.get("asset_id")]
    assert len(roots)==20,len(roots)
    by_id={o["asset_id"]:o for o in roots}
    s,cam,_=setup(a.width,a.height)
    for name,ids in GROUPS:
        assert all(i in by_id for i in ids),(name,ids)
        render_group(s,cam,out,name,roots,[by_id[i] for i in ids])
    print("TAIWEI_EXPANSION_V3_PREVIEW_OK",len(roots),str(out))

if __name__=="__main__":
    main()
