"""Focused review frames for Taiwei Interior & Ceremonial Pack V7."""
from __future__ import annotations
import argparse, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

GROUPS=[
 ("01_seating.png",["TW_V7_HORSESHOE_CHAIR","TW_V7_ARMCHAIR","TW_V7_BENCH","TW_V7_ROUND_STOOL","TW_V7_FOOTREST"]),
 ("02_tables.png",["TW_V7_KANG_TABLE","TW_V7_INCENSE_STAND","TW_V7_CONSOLE_TABLE","TW_V7_ALTAR_TABLE"]),
 ("03_storage_screen.png",["TW_V7_BOOKCASE","TW_V7_SCROLL_RACK","TW_V7_FOLDING_SCREEN"]),
 ("04_ceremonial_textile.png",["TW_V7_CANOPY_FRAME","TW_V7_CURTAIN_PAIR","TW_V7_RITUAL_BANNER","TW_V7_STANDARD_POLE"]),
 ("05_lighting_decor.png",["TW_V7_CANDLE_STAND","TW_V7_BRAZIER","TW_V7_PORCELAIN_VASE","TW_V7_CARPET"]),
]

def args():
    tail=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser();p.add_argument("--out",default="docs/assets/interior_ceremonial_pack_v7")
    p.add_argument("--width",type=int,default=1600);p.add_argument("--height",type=int,default=900);return p.parse_args(tail)
def look(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat("-Z","Y").to_euler()
def light(name,loc,e,size,color,target):
    d=bpy.data.lights.new(name,"AREA");d.energy=e;d.size=size;d.color=color
    o=bpy.data.objects.new(name,d);bpy.context.scene.collection.objects.link(o);o.location=loc;look(o,target)
def setup(w,h):
    s=bpy.context.scene;s.render.engine="BLENDER_EEVEE_NEXT";s.render.resolution_x=w;s.render.resolution_y=h;s.render.resolution_percentage=100
    s.render.image_settings.file_format="PNG";s.render.image_settings.color_mode="RGB"
    if s.world is None:s.world=bpy.data.worlds.new("V7World")
    s.world.color=(.016,.020,.028)
    light("V7Key",(-12,-17,18),3400,10,(1,.73,.49),(0,0,1.2));light("V7Fill",(13,-6,12),2200,9,(.42,.61,1),(0,0,1.1));light("V7Rim",(0,15,16),2400,9,(.68,.82,1),(0,0,1.4))
    d=bpy.data.cameras.new("V7Camera");d.lens=58;cam=bpy.data.objects.new("V7Camera",d);s.collection.objects.link(cam);s.camera=cam
    bpy.ops.mesh.primitive_plane_add(size=80,location=(0,0,-.12));floor=bpy.context.object
    m=bpy.data.materials.new("V7Floor");m.use_nodes=True;b=next(n for n in m.node_tree.nodes if n.type=="BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value=(.045,.050,.055,1);b.inputs["Roughness"].default_value=.86;floor.data.materials.append(m);return s,cam
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
    for i,r in enumerate(sel):r.location=((i%cols-(cols-1)/2)*4.5,(i//cols-(rows-1)/2)*4.2,0)
    bpy.context.view_layer.update()
def bounds(sel):
    pts=[]
    for r in sel:
        for o in children(r):
            if o.type not in {"MESH","CURVE"} or o.hide_render:continue
            for c in o.bound_box:pts.append(o.matrix_world@Vector(c))
    mn=Vector((min(p.x for p in pts),min(p.y for p in pts),min(p.z for p in pts)));mx=Vector((max(p.x for p in pts),max(p.y for p in pts),max(p.z for p in pts)))
    return (mn+mx)/2,mx-mn
def render(s,cam,out,name,roots,sel):
    show(roots,sel);layout(sel);center,span=bounds(sel);ext=max(span.x,span.y*1.15,span.z*1.6,3.8)
    cam.location=center+Vector((0,-ext*1.48,ext*.58));cam.data.lens=60;look(cam,center+Vector((0,0,span.z*.04)))
    s.render.filepath=str((out/name).resolve());bpy.ops.render.render(write_still=True)
def main():
    a=args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True);roots=[o for o in bpy.context.scene.objects if o.get("asset_id")];assert len(roots)==20
    by={o["asset_id"]:o for o in roots};s,cam=setup(a.width,a.height)
    for name,ids in GROUPS:
        assert all(i in by for i in ids);render(s,cam,out,name,roots,[by[i] for i in ids])
    print("TAIWEI_INTERIOR_CEREMONIAL_V7_PREVIEW_OK",len(roots),str(out))
if __name__=="__main__":main()
