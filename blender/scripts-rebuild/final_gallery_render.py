"""Render one of twelve high-quality Taiwei final-gallery shots."""
from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path
import bpy
from mathutils import Vector

SHOTS = {
  1: ("01-cloud-palace-overview", "01_云宫山水总览", None),
  2: ("02-main-hall-three-quarter", "02_重檐正殿", None),
  3: ("03-lotus-rainbow-bridge", "03_荷塘虹桥", None),
  4: ("04-central-axis-ceremony", "04_中轴礼序", None),
  5: ("05-master-plan-high-view", "05_俯视总平", None),
  6: ("06-main-hall-eye-level", "06_正殿平视", None),
  7: ("07-east-elevation", "07_东侧立面", None),
  8: ("08-roof-ridge-detail", "08_正殿脊吻", None),
  9: ("09-waterfall-full-drop", "09_北崖飞瀑", None),
 10: ("10-cloud-sea-side-light", None, ((-68.0,-52.0,38.0),(0.0,10.0,10.0),58)),
 11: ("11-gate-borrowed-landscape", None, ((-30.0,-23.0,15.5),(0.0,12.0,11.0),62)),
 12: ("12-waterfall-environment", None, ((78.0,25.0,16.0),(35.2,7.3,-2.8),70)),
}

def parse():
    argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser()
    p.add_argument("--shot",type=int,required=True,choices=range(1,13))
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--width",type=int,default=2560)
    p.add_argument("--height",type=int,default=1440)
    p.add_argument("--samples",type=int,default=384)
    return p.parse_args(argv)

def make_camera(scene,name,loc,target,lens):
    data=bpy.data.cameras.new("FINAL_"+name)
    cam=bpy.data.objects.new("FINAL_"+name,data)
    scene.collection.objects.link(cam)
    cam.location=loc
    cam.rotation_euler=(Vector(target)-cam.location).to_track_quat("-Z","Y").to_euler()
    data.lens=lens
    data.sensor_width=36
    data.clip_start=.05
    data.clip_end=1800
    data.dof.use_dof=False
    return cam

def main():
    cfg=parse()
    scene=bpy.context.scene
    file_name,existing,custom=SHOTS[cfg.shot]
    if existing:
        cam=bpy.data.objects.get(existing)
        if cam is None or cam.type!="CAMERA":
            raise RuntimeError(f"missing camera {existing}")
    else:
        loc,target,lens=custom
        cam=make_camera(scene,file_name,loc,target,lens)
    scene.camera=cam
    scene.render.engine="CYCLES"
    scene.cycles.device="CPU"
    scene.cycles.samples=cfg.samples
    scene.cycles.use_denoising=True
    scene.cycles.use_adaptive_sampling=True
    scene.cycles.adaptive_threshold=.012
    scene.cycles.max_bounces=12
    scene.cycles.diffuse_bounces=4
    scene.cycles.glossy_bounces=5
    scene.cycles.transmission_bounces=6
    scene.cycles.volume_bounces=2
    scene.render.resolution_x=cfg.width
    scene.render.resolution_y=cfg.height
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.image_settings.color_mode="RGB"
    scene.render.image_settings.color_depth="16"
    scene.render.film_transparent=False
    cfg.out.mkdir(parents=True,exist_ok=True)
    out=(cfg.out/(file_name+".png")).resolve()
    scene.render.filepath=str(out)
    started=time.time()
    bpy.ops.render.render(write_still=True)
    print("FINAL_GALLERY",json.dumps({
      "shot":cfg.shot,"file":str(out),"camera":cam.name,
      "resolution":[cfg.width,cfg.height],"samples":cfg.samples,
      "seconds":round(time.time()-started,2)
    },ensure_ascii=False),flush=True)

if __name__=="__main__":
    main()
