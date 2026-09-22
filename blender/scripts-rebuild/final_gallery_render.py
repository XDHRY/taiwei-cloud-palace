"""Render one of 36 high-quality Taiwei 4K gallery shots."""
from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path
import bpy
from mathutils import Vector

SHOTS = {
  1: ("01-cloud-palace-overview","01_云宫山水总览",None),
  2: ("02-main-hall-three-quarter","02_重檐正殿",None),
  3: ("03-lotus-rainbow-bridge","03_荷塘虹桥",None),
  4: ("04-central-axis-ceremony","04_中轴礼序",None),
  5: ("05-master-plan-high-view","05_俯视总平",None),
  6: ("06-main-hall-eye-level","06_正殿平视",None),
  7: ("07-east-elevation","07_东侧立面",None),
  8: ("08-roof-ridge-detail","08_正殿脊吻",None),
  9: ("09-waterfall-full-drop","09_北崖飞瀑",None),

 10: ("10-cloud-sea-southwest",None,((-78,-60,42),(0,8,10),58)),
 11: ("11-cloud-sea-southeast",None,((78,-58,38),(0,10,9),58)),
 12: ("12-north-high-palace",None,((0,85,50),(0,10,12),62)),
 13: ("13-west-elevation",None,((-58,5,20),(0,10,10),48)),
 14: ("14-east-low-elevation",None,((62,-8,10),(0,10,8),52)),
 15: ("15-gate-borrowed-landscape",None,((-32,-24,15.5),(0,12,10.5),62)),

 16: ("16-rainbow-bridge-west-low",None,((24,-30,6.2),(10,-2,6),52)),
 17: ("17-rainbow-bridge-east-low",None,((50,-18,8),(12,-3,6),58)),
 18: ("18-lotus-water-level",None,((28,-12,3.2),(10,3,6),60)),
 19: ("19-main-hall-tele-front",None,((0,-70,20),(0,12,11),85)),
 20: ("20-main-hall-west",None,((-38,-30,24),(0,12,11),58)),
 21: ("21-main-hall-east",None,((38,-30,24),(0,12,11),58)),
 22: ("22-main-hall-low-hero",None,((0,-30,8),(0,12,11),46)),

 23: ("23-roof-close-west",None,((-8,0,22),(2,13,16),92)),
 24: ("24-roof-close-east",None,((10,3,22),(2,13,16),92)),
 25: ("25-central-axis-high",None,((0,-75,42),(0,12,9),70)),
 26: ("26-central-axis-low",None,((0,-65,8),(0,12,9),50)),
 27: ("27-mountain-west-context",None,((-90,30,55),(0,15,15),72)),
 28: ("28-mountain-east-context",None,((90,28,50),(0,15,15),72)),

 29: ("29-waterfall-environment",None,((78,25,16),(35.2,7.3,-2.8),70)),
 30: ("30-waterfall-side",None,((70,-8,8),(35.2,7.3,-3.0),62)),
 31: ("31-waterfall-low",None,((75,12,-2.0),(35.4,7.2,-5.0),55)),
 32: ("32-waterfall-high",None,((65,18,20),(35.3,7.3,-3.0),68)),

 33: ("33-cloud-sea-north",None,((0,100,25),(0,10,8),64)),
 34: ("34-cliff-silhouette-west",None,((-70,60,25),(0,12,8),68)),
 35: ("35-palace-poster-wide",None,((80,-110,65),(0,10,11),65)),
 36: ("36-palace-poster-tele",None,((50,-85,35),(0,12,11),82)),
}
HERO_SHOTS={1,2,3,4,9,15,18,19,22,25,29,35,36}

def parse():
    argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser()
    p.add_argument("--shot",type=int,required=True,choices=range(1,37))
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--width",type=int,default=3840)
    p.add_argument("--height",type=int,default=2160)
    p.add_argument("--samples",type=int,default=256)
    return p.parse_args(argv)

def make_camera(scene,name,loc,target,lens):
    data=bpy.data.cameras.new("FINAL4K_"+name)
    cam=bpy.data.objects.new("FINAL4K_"+name,data)
    scene.collection.objects.link(cam)
    cam.location=loc
    cam.rotation_euler=(Vector(target)-cam.location).to_track_quat("-Z","Y").to_euler()
    data.lens=lens
    data.sensor_width=36
    data.clip_start=.04
    data.clip_end=2200
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

    samples=max(cfg.samples,384 if cfg.shot in HERO_SHOTS else cfg.samples)
    scene.render.engine="CYCLES"
    scene.cycles.device="CPU"
    scene.cycles.samples=samples
    scene.cycles.use_denoising=True
    scene.cycles.use_adaptive_sampling=True
    scene.cycles.adaptive_threshold=.010
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
    print("FINAL_4K_GALLERY",json.dumps({
      "shot":cfg.shot,"file":str(out),"camera":cam.name,
      "resolution":[cfg.width,cfg.height],"samples":samples,
      "seconds":round(time.time()-started,2)
    },ensure_ascii=False),flush=True)

if __name__=="__main__":
    main()
