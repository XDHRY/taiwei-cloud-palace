"""Render lightweight review frames for Taiwei Hero Asset Pack V2."""
from __future__ import annotations
import argparse, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

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
    d=bpy.data.cameras.new("HeroPackReviewCamera")
    d.lens=52
    o=bpy.data.objects.new("HeroPackReviewCamera",d)
    bpy.context.scene.collection.objects.link(o)
    bpy.context.scene.camera=o
    return o

def setup():
    s=bpy.context.scene
    s.render.engine="BLENDER_EEVEE_NEXT"
    s.render.resolution_percentage=100
    s.render.image_settings.file_format="PNG"
    s.render.image_settings.color_mode="RGB"
    s.render.film_transparent=False
    if s.world is None: s.world=bpy.data.worlds.new("HeroPackWorld")
    s.world.color=(.012,.016,.025)
    add_area("Key",(-18,-24,30),2600,14,(1.0,.72,.48),(0,0,1.5))
    add_area("Fill",(22,-8,20),1800,12,(.40,.58,1.0),(0,0,1.4))
    add_area("Rim",(0,24,28),2200,11,(.65,.78,1.0),(0,0,1.8))
    return s,add_camera()

def render(cam,out,name,loc,target,lens=52):
    cam.location=loc; cam.data.lens=lens; look_at(cam,target)
    bpy.context.scene.render.filepath=str((out/name).resolve())
    bpy.ops.render.render(write_still=True)

def main():
    a=args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    roots=[o for o in bpy.context.scene.objects if o.get("asset_id")]
    assert len(roots)==24, len(roots)
    assert all(o.get("reusable") for o in roots)
    s,cam=setup()
    s.render.resolution_x=a.width; s.render.resolution_y=a.height
    render(cam,out,"01_overview.png",(0,-48,27),(0,0,1.5),55)
    render(cam,out,"02_roof_ornaments.png",(0,-31,10),(0,-10.5,1.2),60)
    render(cam,out,"03_architecture.png",(0,-25,11),(0,-3.5,1.4),58)
    render(cam,out,"04_ritual_and_stone.png",(0,-18,13),(0,7.0,1.4),58)
    print("TAIWEI_HERO_PREVIEW_OK",len(roots),str(out))

if __name__=="__main__":
    main()
