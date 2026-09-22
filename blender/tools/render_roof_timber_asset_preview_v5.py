"""Render focused review frames for Taiwei Roof & Timber Asset Pack V5."""
from __future__ import annotations
import argparse, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

GROUPS=[
 ("01_roof_system.png",[
  "TW_V5_ROOF_TILE_ROW","TW_V5_EAVE_TILE_ROW","TW_V5_RIDGE_STRAIGHT",
  "TW_V5_RIDGE_CORNER","TW_V5_HIP_CORNER"]),
 ("02_rafters_and_purlins.png",[
  "TW_V5_COMMON_RAFTERS","TW_V5_FLYING_RAFTERS","TW_V5_PURLIN_BAY",
  "TW_V5_COLUMN_SHAFT","TW_V5_COLUMN_CAPITAL"]),
 ("03_carved_timber.png",[
  "TW_V5_BEAM_HEAD","TW_V5_SPARROW_BRACE","TW_V5_HANGING_FISH",
  "TW_V5_FASCIA_BOARD","TW_V5_DROPPED_FRIEZE"]),
 ("04_doors_and_lattice.png",[
  "TW_V5_TRANSOM_PANEL","TW_V5_CLOUD_LATTICE","TW_V5_DIAMOND_LATTICE","TW_V5_DOOR_BAY_FRAME"]),
 ("05_eave_bell_bracket.png",["TW_V5_EAVE_BELL_BRACKET"]),
]

def args():
    tail=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser(); p.add_argument("--out",default="docs/assets/roof_timber_pack_v5")
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
    if s.world is None:s.world=bpy.data.worlds.new("V5World")
    s.world.color=(.016,.020,.029)
    light("V5Key",(-13,-18,19),3400,10,(1,.73,.49),(0,0,1.3))
    light("V5Fill",(14,-7,13),2200,9,(.42,.60,1),(0,0,1.2))
    light("V5Rim",(0,15,18),2600,9,(.67,.81,1),(0,0,1.6))
    d=bpy.data.cameras.new("V5Camera"); d.lens=58
    cam=bpy.data.objects.new("V5Camera",d); s.collection.objects.link(cam); s.camera=cam
    bpy.ops.mesh.primitive_plane_add(size=90,location=(0,0,-.20))
    floor=bpy.context.object
    m=bpy.data.materials.new("V5Floor");m.use_nodes=True
    b=next(n for n in m.node_tree.nodes if n.type=="BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value=(.045,.050,.056,1);b.inputs["Roughness"].default_value=.86
    floor.data.materials.append(m)
    return s,cam

def children(r):
    out=[];stack=list(r.children)
    while stack:o=stack.pop();out.append(o);stack.extend(o.children)
    return out

def show(roots,selected):
    want=set(selected)
    for r in roots:
        v=r in want;r.hide_render=not v
        for o in children(r):o.hide_render=not v

def layout(sel):
    n=len(sel);cols=3 if n<=6 else 4;rows=math.ceil(n/cols)
    for i,r in enumerate(sel):r.location=((i%cols-(cols-1)/2)*5.4,(i//cols-(rows-1)/2)*4.6,0)
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
    ext=max(span.x,span.y*1.15,span.z*1.6,4.2)
    cam.location=center+Vector((0,-ext*1.48,ext*.58));cam.data.lens=60
    look_at(cam,center+Vector((0,0,span.z*.04)))
    s.render.filepath=str((out/name).resolve());bpy.ops.render.render(write_still=True)

def main():
    a=args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    roots=[o for o in bpy.context.scene.objects if o.get("asset_id")];assert len(roots)==20
    by={o["asset_id"]:o for o in roots};s,cam=setup(a.width,a.height)
    for name,ids in GROUPS:
        assert all(i in by for i in ids)
        render(s,cam,out,name,roots,[by[i] for i in ids])
    print("TAIWEI_ROOF_TIMBER_V5_PREVIEW_OK",len(roots),str(out))

if __name__=="__main__":main()
