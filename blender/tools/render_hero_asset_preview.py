"""Render focused visual review frames for Taiwei Hero Asset Pack V2."""
from __future__ import annotations
import argparse, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

GROUPS = [
    ("01_roof_hero.png", [
        "TW_HERO_CHIWEN_01","TW_HERO_BEAST_DRAGON_01","TW_HERO_BEAST_PHOENIX_01",
        "TW_HERO_BEAST_LION_01","TW_HERO_BEAST_QILIN_01","TW_HERO_BEAST_TIANMA_01",
        "TW_HERO_BEAST_HAIMA_01","TW_HERO_EAVES_TILE_01","TW_HERO_WIND_BELL_01"
    ]),
    ("02_timber_architecture.png", [
        "TW_HERO_DOUGONG_01","TW_HERO_CORNER_DOUGONG_01","TW_HERO_GESHAN_DOOR_01",
        "TW_HERO_LATTICE_WINDOW_01","TW_HERO_CAISSON_01"
    ]),
    ("03_stone_architecture.png", [
        "TW_HERO_COLUMN_BASE_01","TW_HERO_HUABIAO_01","TW_HERO_SUTRA_PILLAR_01",
        "TW_HERO_BALUSTRADE_01"
    ]),
    ("04_ritual_props.png", [
        "TW_HERO_LANTERN_01","TW_HERO_CENSER_01","TW_HERO_PLAQUE_01",
        "TW_HERO_SCREEN_01","TW_HERO_BRONZE_CRANE_01","TW_HERO_LOTUS_PEDESTAL_01"
    ]),
]

def args():
    tail=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="docs/assets/hero_pack_v2")
    p.add_argument("--width",type=int,default=1600)
    p.add_argument("--height",type=int,default=900)
    return p.parse_args(tail)

def look_at(obj,target):
    direction=Vector(target)-obj.location
    obj.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()

def add_area(name,loc,energy,size,color,target):
    d=bpy.data.lights.new(name,"AREA"); d.energy=energy; d.shape="DISK"; d.size=size; d.color=color
    o=bpy.data.objects.new(name,d); bpy.context.scene.collection.objects.link(o); o.location=loc; look_at(o,target)
    return o

def add_camera():
    d=bpy.data.cameras.new("HeroPackReviewCamera"); d.lens=56
    o=bpy.data.objects.new("HeroPackReviewCamera",d)
    bpy.context.scene.collection.objects.link(o); bpy.context.scene.camera=o
    return o

def setup():
    s=bpy.context.scene
    s.render.engine="BLENDER_EEVEE_NEXT"
    s.render.resolution_percentage=100
    s.render.image_settings.file_format="PNG"
    s.render.image_settings.color_mode="RGB"
    s.render.film_transparent=False
    if s.world is None: s.world=bpy.data.worlds.new("HeroPackWorld")
    s.world.color=(.018,.022,.032)
    add_area("Key",(-11,-17,20),3300,10,(1.0,.72,.48),(0,0,1.5))
    add_area("Fill",(13,-6,13),2400,9,(.42,.60,1.0),(0,0,1.4))
    add_area("Rim",(0,15,18),2800,8,(.66,.80,1.0),(0,0,1.8))
    add_area("Top",(0,0,24),1500,9,(1.0,.92,.78),(0,0,0))
    return s,add_camera()

def descendants(root):
    out=[]
    stack=list(root.children)
    while stack:
        o=stack.pop(); out.append(o); stack.extend(o.children)
    return out

def set_group_visibility(roots, selected):
    wanted=set(selected)
    for r in roots:
        visible=r in wanted
        r.hide_render=not visible
        for o in descendants(r):
            o.hide_render=not visible

def compact_layout(selected):
    n=len(selected)
    cols=3 if n<=6 else 4
    rows=math.ceil(n/cols)
    spacing_x=4.5; spacing_y=4.2
    for i,r in enumerate(selected):
        x=(i%cols-(cols-1)/2)*spacing_x
        y=(i//cols-(rows-1)/2)*spacing_y
        r.location=(x,y,0)

def bounds(selected):
    pts=[]
    for r in selected:
        for o in descendants(r):
            if o.type not in {"MESH","CURVE"} or o.hide_render: continue
            for c in o.bound_box:
                pts.append(o.matrix_world @ Vector(c))
    if not pts:
        return Vector((0,0,1)),Vector((10,10,5))
    mn=Vector((min(p.x for p in pts),min(p.y for p in pts),min(p.z for p in pts)))
    mx=Vector((max(p.x for p in pts),max(p.y for p in pts),max(p.z for p in pts)))
    return (mn+mx)/2, mx-mn

def add_floor():
    bpy.ops.mesh.primitive_plane_add(size=80, location=(0,0,-.18))
    o=bpy.context.object; o.name="HeroReviewFloor"
    m=bpy.data.materials.new("HeroReviewFloorMat"); m.use_nodes=True
    p=next(n for n in m.node_tree.nodes if n.type=="BSDF_PRINCIPLED")
    p.inputs["Base Color"].default_value=(.055,.06,.07,1)
    p.inputs["Roughness"].default_value=.82
    o.data.materials.append(m)
    return o

def render_group(cam,out,name,roots,selected):
    set_group_visibility(roots,selected)
    compact_layout(selected)
    center,span=bounds(selected)
    extent=max(span.x,span.y*1.15,span.z*1.55,4.0)
    dist=extent*1.45
    cam.location=center+Vector((0,-dist,dist*.54))
    cam.data.lens=58
    look_at(cam,center+Vector((0,0,span.z*.04)))
    bpy.context.scene.render.filepath=str((out/name).resolve())
    bpy.ops.render.render(write_still=True)

def main():
    a=args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    roots=[o for o in bpy.context.scene.objects if o.get("asset_id")]
    assert len(roots)==24, len(roots)
    by_id={o["asset_id"]:o for o in roots}
    s,cam=setup(); floor=add_floor()
    s.render.resolution_x=a.width; s.render.resolution_y=a.height
    for name,ids in GROUPS:
        selected=[by_id[i] for i in ids]
        floor.hide_render=False
        render_group(cam,out,name,roots,selected)
    print("TAIWEI_HERO_PREVIEW_OK",len(roots),str(out))

if __name__=="__main__":
    main()
