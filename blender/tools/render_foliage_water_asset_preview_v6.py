"""Focused review frames for Taiwei Foliage & Water Garden Pack V6."""
from __future__ import annotations
import argparse, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

GROUPS=[
 ("01_willow_bamboo.png",["TW_V6_WILLOW_BRANCH","TW_V6_WILLOW_CROWN","TW_V6_BAMBOO_CLUMP","TW_V6_BAMBOO_SPRAY"]),
 ("02_pine_plum_maple.png",["TW_V6_PINE_BRANCH","TW_V6_PINE_CROWN","TW_V6_PLUM_BRANCH","TW_V6_MAPLE_BRANCH"]),
 ("03_lotus_and_reeds.png",["TW_V6_LOTUS_LEAF_CLUSTER","TW_V6_LOTUS_FLOWER_CLUSTER","TW_V6_REED_CLUMP","TW_V6_IRIS_CLUMP","TW_V6_WATER_LILY_CLUSTER"]),
 ("04_vines_groundcover.png",["TW_V6_WISTERIA_VINE","TW_V6_MOSS_PATCH","TW_V6_FERN_CLUMP","TW_V6_ORNAMENTAL_GRASS","TW_V6_FALLEN_LEAVES"]),
 ("05_pond_edge.png",["TW_V6_POND_STONE_EDGE","TW_V6_POND_CORNER"]),
]

def args():
    tail=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser(); p.add_argument("--out",default="docs/assets/foliage_water_pack_v6")
    p.add_argument("--width",type=int,default=1600); p.add_argument("--height",type=int,default=900)
    return p.parse_args(tail)

def look_at(o,t): o.rotation_euler=(Vector(t)-o.location).to_track_quat("-Z","Y").to_euler()
def light(name,loc,e,size,color,target):
    d=bpy.data.lights.new(name,"AREA"); d.energy=e; d.size=size; d.color=color
    o=bpy.data.objects.new(name,d); bpy.context.scene.collection.objects.link(o); o.location=loc; look_at(o,target)

def setup(w,h):
    s=bpy.context.scene; s.render.engine="BLENDER_EEVEE_NEXT"
    s.render.resolution_x=w; s.render.resolution_y=h; s.render.resolution_percentage=100
    s.render.image_settings.file_format="PNG"; s.render.image_settings.color_mode="RGB"
    if s.world is None:s.world=bpy.data.worlds.new("V6World")
    s.world.color=(.020,.026,.032)
    light("V6Key",(-11,-16,18),3200,11,(1,.78,.55),(0,0,1.0))
    light("V6Fill",(13,-7,12),2200,9,(.44,.64,1),(0,0,1.0))
    light("V6Rim",(0,15,16),2200,9,(.70,.84,1),(0,0,1.2))
    d=bpy.data.cameras.new("V6Camera"); d.lens=58
    cam=bpy.data.objects.new("V6Camera",d); s.collection.objects.link(cam); s.camera=cam
    bpy.ops.mesh.primitive_plane_add(size=80,location=(0,0,-.12))
    floor=bpy.context.object
    m=bpy.data.materials.new("V6Floor");m.use_nodes=True
    b=next(n for n in m.node_tree.nodes if n.type=="BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value=(.045,.052,.055,1);b.inputs["Roughness"].default_value=.86
    floor.data.materials.append(m)
    return s,cam

def children(r):
    out=[];stack=list(r.children)
    while stack:o=stack.pop();out.append(o);stack.extend(o.children)
    return out

def show(roots,sel):
    want=set(sel)
    for r in roots:
        v=r in want;r.hide_render=not v
        for o in children(r):o.hide_render=not v

def layout(sel):
    n=len(sel);cols=3 if n<=6 else 4;rows=math.ceil(n/cols)
    for i,r in enumerate(sel):
        r.location=((i%cols-(cols-1)/2)*4.6,(i//cols-(rows-1)/2)*4.2,0)
    bpy.context.view_layer.update()

def bounds(sel):
    pts=[]
    for r in sel:
        for o in children(r):
            if o.type not in {"MESH","CURVE"} or o.hide_render:continue
            for c in o.bound_box:pts.append(o.matrix_world@Vector(c))
    mn=Vector((min(p.x for p in pts),min(p.y for p in pts),min(p.z for p in pts)))
    mx=Vector((max(p.x for p in pts),max(p.y for p in pts),max(p.z for p in pts)))
    return (mn+mx)/2,mx-mn

def render(s,cam,out,name,roots,sel):
    show(roots,sel);layout(sel);center,span=bounds(sel)
    ext=max(span.x,span.y*1.1,span.z*1.65,3.8)
    cam.location=center+Vector((0,-ext*1.50,ext*.58));cam.data.lens=58
    look_at(cam,center+Vector((0,0,span.z*.05)))
    s.render.filepath=str((out/name).resolve());bpy.ops.render.render(write_still=True)

def main():
    a=args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    roots=[o for o in bpy.context.scene.objects if o.get("asset_id")];assert len(roots)==20
    by={o["asset_id"]:o for o in roots};s,cam=setup(a.width,a.height)
    for name,ids in GROUPS:
        assert all(i in by for i in ids)
        render(s,cam,out,name,roots,[by[i] for i in ids])
    print("TAIWEI_FOLIAGE_WATER_V6_PREVIEW_OK",len(roots),str(out))

if __name__=="__main__":main()
