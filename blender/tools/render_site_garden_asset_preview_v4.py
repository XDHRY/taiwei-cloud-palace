"""Render focused low-cost review frames for Taiwei Site & Garden Asset Pack V4."""
from __future__ import annotations
import argparse, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

GROUPS=[
 ("01_terrace_and_balustrade.png",[
   "TW_V4_TERRACE_STEPS","TW_V4_IMPERIAL_RAMP","TW_V4_TERRACE_CORNER",
   "TW_V4_BALUSTRADE_STRAIGHT","TW_V4_BALUSTRADE_CORNER"]),
 ("02_walls_and_gates.png",[
   "TW_V4_MOON_GATE","TW_V4_WHITE_WALL","TW_V4_SCREEN_WALL","TW_V4_GATE_FRAME"]),
 ("03_garden_props.png",[
   "TW_V4_STONE_BASIN","TW_V4_BRONZE_VAT","TW_V4_LOTUS_PLANTER",
   "TW_V4_TREE_PLANTER","TW_V4_STONE_LANTERN"]),
 ("04_rockery.png",["TW_V4_TAIHU_ROCK","TW_V4_ROCKERY_CLUSTER"]),
 ("05_bridge_and_ground.png",[
   "TW_V4_ARCH_BRIDGE","TW_V4_PAVING_SET","TW_V4_DRAIN_CHANNEL","TW_V4_BEAST_SCUPPER"]),
]

def args():
    tail=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="docs/assets/site_garden_pack_v4")
    p.add_argument("--width",type=int,default=1600)
    p.add_argument("--height",type=int,default=900)
    return p.parse_args(tail)

def look_at(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()

def area(name,loc,energy,size,color,target):
    d=bpy.data.lights.new(name,"AREA"); d.energy=energy; d.shape="DISK"; d.size=size; d.color=color
    o=bpy.data.objects.new(name,d); bpy.context.scene.collection.objects.link(o); o.location=loc; look_at(o,target)
    return o

def setup(w,h):
    s=bpy.context.scene; s.render.engine="BLENDER_EEVEE_NEXT"
    s.render.resolution_x=w; s.render.resolution_y=h; s.render.resolution_percentage=100
    s.render.image_settings.file_format="PNG"; s.render.image_settings.color_mode="RGB"
    if s.world is None: s.world=bpy.data.worlds.new("V4ReviewWorld")
    s.world.color=(.016,.020,.028)
    area("V4Key",(-13,-18,20),3500,11,(1.0,.74,.50),(0,0,1.3))
    area("V4Fill",(14,-6,13),2300,9,(.42,.62,1.0),(0,0,1.3))
    area("V4Rim",(0,16,19),2700,9,(.68,.82,1.0),(0,0,1.6))
    d=bpy.data.cameras.new("V4ReviewCamera"); d.lens=58
    cam=bpy.data.objects.new("V4ReviewCamera",d); s.collection.objects.link(cam); s.camera=cam
    bpy.ops.mesh.primitive_plane_add(size=90,location=(0,0,-.20))
    floor=bpy.context.object
    m=bpy.data.materials.new("V4ReviewFloorMat"); m.use_nodes=True
    bsdf=next(n for n in m.node_tree.nodes if n.type=="BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value=(.045,.050,.055,1); bsdf.inputs["Roughness"].default_value=.86
    floor.data.materials.append(m)
    return s,cam

def descendants(root):
    out=[]; stack=list(root.children)
    while stack:
        o=stack.pop(); out.append(o); stack.extend(o.children)
    return out

def set_vis(roots,selected):
    wanted=set(selected)
    for r in roots:
        show=r in wanted; r.hide_render=not show
        for o in descendants(r): o.hide_render=not show

def layout(selected):
    n=len(selected); cols=3 if n<=6 else 4; rows=math.ceil(n/cols)
    sx,sy=5.6,4.7
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

def render(s,cam,out,name,roots,selected):
    set_vis(roots,selected); layout(selected)
    center,span=bounds(selected)
    extent=max(span.x,span.y*1.15,span.z*1.55,4.5)
    cam.location=center+Vector((0,-extent*1.45,extent*.56))
    cam.data.lens=60
    look_at(cam,center+Vector((0,0,span.z*.04)))
    s.render.filepath=str((out/name).resolve()); bpy.ops.render.render(write_still=True)

def main():
    a=args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    roots=[o for o in bpy.context.scene.objects if o.get("asset_id")]
    assert len(roots)==20,len(roots)
    by={o["asset_id"]:o for o in roots}
    s,cam=setup(a.width,a.height)
    for name,ids in GROUPS:
        assert all(i in by for i in ids)
        render(s,cam,out,name,roots,[by[i] for i in ids])
    print("TAIWEI_SITE_GARDEN_V4_PREVIEW_OK",len(roots),str(out))

if __name__=="__main__":
    main()
