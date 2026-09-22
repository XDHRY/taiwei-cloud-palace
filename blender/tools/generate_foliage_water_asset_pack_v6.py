"""Taiwei Cloud Palace Foliage & Water Garden Asset Pack V6.
Low-cost, high-impact softscape modules built from deterministic geometry.
"""
from __future__ import annotations
import argparse, importlib.util, json, math, sys
from pathlib import Path
import bpy

CORE=Path(__file__).with_name("generate_hero_asset_pack.py")
spec=importlib.util.spec_from_file_location("taiwei_core",CORE)
core=importlib.util.module_from_spec(spec); spec.loader.exec_module(core)

ASSETS=[
 ("TW_V6_WILLOW_BRANCH","垂柳枝条","foliage"),
 ("TW_V6_WILLOW_CROWN","垂柳冠层簇","foliage"),
 ("TW_V6_BAMBOO_CLUMP","修竹丛","foliage"),
 ("TW_V6_BAMBOO_SPRAY","竹叶枝片","foliage"),
 ("TW_V6_PINE_BRANCH","古松枝","foliage"),
 ("TW_V6_PINE_CROWN","古松冠层簇","foliage"),
 ("TW_V6_PLUM_BRANCH","梅花枝","foliage"),
 ("TW_V6_MAPLE_BRANCH","红枫枝","foliage"),
 ("TW_V6_LOTUS_LEAF_CLUSTER","荷叶簇","water_garden"),
 ("TW_V6_LOTUS_FLOWER_CLUSTER","荷花簇","water_garden"),
 ("TW_V6_REED_CLUMP","芦苇丛","water_garden"),
 ("TW_V6_IRIS_CLUMP","鸢尾草丛","water_garden"),
 ("TW_V6_WISTERIA_VINE","紫藤垂蔓","foliage"),
 ("TW_V6_MOSS_PATCH","青苔石面簇","ground_detail"),
 ("TW_V6_FERN_CLUMP","蕨草簇","ground_detail"),
 ("TW_V6_POND_STONE_EDGE","池岸叠石直段","water_edge"),
 ("TW_V6_POND_CORNER","荷池转角模块","water_edge"),
 ("TW_V6_WATER_LILY_CLUSTER","睡莲叶簇","water_garden"),
 ("TW_V6_ORNAMENTAL_GRASS","细叶观赏草","ground_detail"),
 ("TW_V6_FALLEN_LEAVES","落叶散布簇","ground_detail"),
]

def args():
    tail=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="generated_assets/TaiWei_FoliageWaterGardenPack_V6.blend")
    p.add_argument("--report",default="generated_assets/taiwei-foliage-water-v6-report.json")
    return p.parse_args(tail)

def root(a,cn,cat,loc,col):
    r=bpy.data.objects.new(a,None); col.objects.link(r); r.location=loc
    for k,v in {"asset_id":a,"name_cn":cn,"category":cat,"quality_tier":"hero_v6",
      "production_level":"hero_midpoly","parametric":True,"reusable":True,
      "protected_scene_safe":True,"source_style":"historical_chinese_palace_yanyun_grounded",
      "units":"meters","origin_policy":"asset_root_grounded"}.items(): r[k]=v
    return r

def leaf(name,size,loc,rot,mat,col,parent,pointed=True):
    w,l=size
    verts=[(0,0,.025),(-w*.52,l*.18,0),(-w*.38,l*.58,0),(0,l,0),
           (w*.38,l*.58,0),(w*.52,l*.18,0),(0,l*.44,.035)]
    faces=[(0,1,2,6),(0,6,5),(6,2,3,4,5)]
    o=core.mesh_obj(name,verts,faces,mat,col,parent)
    o.location=loc; o.rotation_euler=rot
    for p in o.data.polygons:p.use_smooth=True
    return o

def petal(name,size,loc,rot,mat,col,parent):
    return leaf(name,(size*.70,size),loc,rot,mat,col,parent)

def branch(name,pts,rad,M,col,r):
    return core.tube(name,pts,rad,M["bark"],col,r)

def willow_branch(r,M,col):
    branch(r.name+"_BRANCH",[(-1.1,0,1.5),(-.55,0,1.35),(0,0,1.05),(.55,0,.68),(1.0,0,.18)],.055,M,col,r)
    for s in (-1,1):
        for i in range(8):
            t=i/7
            x=-.80+1.55*t; z=1.33-1.00*t
            branch(r.name+f"_TWIG_{s}_{i}",[(x,0,z),(x+.06,s*.22,z-.28),(x+.02,s*.34,z-.55)],.015,M,col,r)
            for k in range(3):
                leaf(r.name+f"_LEAF_{s}_{i}_{k}",(.075,.26),
                     (x+.03,s*(.20+.07*k),z-.25-.15*k),
                     (math.radians(20*s),math.radians((i*13+k*19)%28-14),math.radians(75*s)),
                     M["leaf_light"] if (i+k)%2 else M["leaf"],col,r)

def willow_crown(r,M,col):
    for j in range(5):
        a=math.tau*j/5
        branch(r.name+f"_ARM_{j}",[(0,0,1.2),(.55*math.cos(a),.55*math.sin(a),1.65),
                                   (1.15*math.cos(a),1.15*math.sin(a),1.55)],.055,M,col,r)
        for i in range(6):
            rr=.55+i*.12
            x=rr*math.cos(a); y=rr*math.sin(a); z=1.48-i*.18
            branch(r.name+f"_DROP_{j}_{i}",[(x,y,z),(x+.05*math.sin(a),y-.05*math.cos(a),z-.48)],.012,M,col,r)
            for k in range(3):
                leaf(r.name+f"_LEAF_{j}_{i}_{k}",(.065,.23),(x,y,z-.10-k*.15),
                     (math.radians(25),0,a+math.pi/2),M["leaf"],col,r)

def bamboo_clump(r,M,col):
    for i in range(7):
        x=-.55+i*.18; y=((i*37)%5-2)*.08; h=2.5+((i*19)%5)*.16
        core.cyl(r.name+f"_CULM_{i}",.035,h,(x,y,h/2),M["bamboo"],col,r,14)
        for n in range(1,6):
            z=h*n/6
            core.torus(r.name+f"_NODE_{i}_{n}",.038,.008,(x,y,z),M["bamboo_dark"],col,r,14,5)
        for n in (2,3,4,5):
            z=h*n/6
            s=-1 if (i+n)%2 else 1
            branch(r.name+f"_BRANCH_{i}_{n}",[(x,y,z),(x+s*.35,y+.08,z+.18)],.012,M,col,r)
            for k in range(3):
                leaf(r.name+f"_LEAF_{i}_{n}_{k}",(.055,.30),(x+s*(.20+.11*k),y+.08,z+.13+k*.03),
                     (0,math.radians((k-1)*16),math.radians(84*s)),M["leaf"],col,r)

def bamboo_spray(r,M,col):
    branch(r.name+"_STEM",[(-.9,0,.20),(-.35,0,.48),(.25,0,.78),(.90,0,1.12)],.025,M,col,r)
    for i in range(9):
        x=-.68+i*.18; z=.31+i*.105; s=-1 if i%2 else 1
        for k in range(2):
            leaf(r.name+f"_LEAF_{i}_{k}",(.06,.34),(x,s*(.06+.08*k),z),
                 (math.radians(8*s),0,math.radians(72*s+(k*16))),
                 M["leaf_light"] if (i+k)%3==0 else M["leaf"],col,r)

def pine_branch(r,M,col):
    branch(r.name+"_BRANCH",[(-1.0,0,.32),(-.45,0,.58),(.18,0,.72),(.95,0,.82)],.07,M,col,r)
    for i in range(8):
        x=-.70+i*.21; z=.44+i*.055
        for j in range(8):
            a=math.tau*j/8
            leaf(r.name+f"_NEEDLE_{i}_{j}",(.018,.34),(x,.02,z),
                 (math.radians(20*math.sin(a)),math.radians(55),a),
                 M["pine"],col,r)

def pine_crown(r,M,col):
    for arm in range(6):
        a=math.tau*arm/6
        branch(r.name+f"_ARM_{arm}",[(0,0,.82),(.55*math.cos(a),.55*math.sin(a),1.02),
                                     (1.18*math.cos(a),1.18*math.sin(a),1.05)],.07,M,col,r)
        for i in range(5):
            rr=.48+i*.14
            for j in range(6):
                q=math.tau*j/6
                leaf(r.name+f"_N_{arm}_{i}_{j}",(.018,.30),
                     (rr*math.cos(a),rr*math.sin(a),1.00+(j%2)*.06),
                     (math.radians(32),math.radians(52),q+a),M["pine"],col,r)

def plum_branch(r,M,col):
    branch(r.name+"_MAIN",[(-1.05,0,.20),(-.62,0,.62),(-.18,0,.52),(.20,0,1.05),(.88,0,1.34)],.055,M,col,r)
    for i in range(8):
        x=-.72+i*.21; z=.50+i*.10
        s=-1 if i%2 else 1
        branch(r.name+f"_TWIG_{i}",[(x,0,z),(x+.15,s*.15,z+.35)],.018,M,col,r)
        for k in range(2):
            cx=x+.08+k*.10; cy=s*(.10+.04*k); cz=z+.18+k*.10
            for p in range(5):
                a=math.tau*p/5
                core.sphere(r.name+f"_BLOSSOM_{i}_{k}_{p}",(.045,.025,.055),
                            (cx+.05*math.cos(a),cy-.03,cz+.05*math.sin(a)),M["blossom"],col,r,12,6)
            core.sphere(r.name+f"_CENTER_{i}_{k}",(.025,.018,.025),(cx,cy-.04,cz),M["gold"],col,r,10,5)

def maple_branch(r,M,col):
    branch(r.name+"_BRANCH",[(-1.0,0,.25),(-.45,0,.55),(.20,0,.72),(.95,0,1.12)],.05,M,col,r)
    for i in range(11):
        x=-.76+i*.16; z=.38+i*.07; s=-1 if i%2 else 1
        for k in range(3):
            a=math.radians(-30+30*k)
            leaf(r.name+f"_LEAF_{i}_{k}",(.10,.30),(x,s*(.10+.05*k),z),
                 (math.radians(12*s),0,math.radians(65*s)+a),
                 M["maple"] if (i+k)%3 else M["maple_gold"],col,r)

def lotus_leaf_cluster(r,M,col):
    for i in range(8):
        a=math.tau*i/8; rr=.25+.12*(i%3); h=.20+.12*(i%4)
        core.cyl(r.name+f"_STEM_{i}",.018,h,(rr*math.cos(a),rr*math.sin(a),h/2),M["stem"],col,r,10)
        core.sphere(r.name+f"_LEAF_{i}",(.28,.24,.025),(rr*math.cos(a),rr*math.sin(a),h),M["lotus_leaf"],col,r,24,5)

def lotus_flower_cluster(r,M,col):
    for fidx,(x,y,h) in enumerate(((-.28,0,.62),(.22,.12,.82),(.06,-.24,.52))):
        core.cyl(r.name+f"_STEM_{fidx}",.018,h,(x,y,h/2),M["stem"],col,r,10)
        for ring,(rad,count,scale) in enumerate(((.18,8,1.0),(.10,6,.78))):
            for i in range(count):
                a=math.tau*i/count
                petal(r.name+f"_PETAL_{fidx}_{ring}_{i}",.30*scale,
                      (x+rad*math.cos(a),y+rad*math.sin(a),h+.02+ring*.08),
                      (math.radians(-18+ring*8),0,a),M["lotus_pink"],col,r)
        core.sphere(r.name+f"_SEEDPOD_{fidx}",(.07,.07,.04),(x,y,h+.14),M["gold"],col,r,14,6)

def reed_clump(r,M,col):
    for i in range(18):
        x=((i*37)%11-5)*.055; y=((i*17)%9-4)*.05; h=1.2+((i*13)%7)*.10
        core.cyl(r.name+f"_STEM_{i}",.010,h,(x,y,h/2),M["stem"],col,r,8)
        if i%2==0:
            core.sphere(r.name+f"_HEAD_{i}",(.035,.035,.16),(x,y,h+.10),M["reed"],col,r,14,7)
        leaf(r.name+f"_LEAF_{i}",(.035,.42),(x,y,h*.45),
             (math.radians(18),0,math.radians((i*29)%160-80)),M["leaf"],col,r)

def iris_clump(r,M,col):
    for i in range(14):
        a=math.tau*i/14
        leaf(r.name+f"_BLADE_{i}",(.045,.70),(0,0,.05),
             (math.radians(15+(i%4)*6),math.radians((i%3)*8),a),
             M["leaf_light"] if i%3 else M["leaf"],col,r)
    for j in range(3):
        x=(-.16+j*.16); h=.72+j*.08
        core.cyl(r.name+f"_FLOWER_STEM_{j}",.012,h,(x,0,h/2),M["stem"],col,r,8)
        for p in range(5):
            a=math.tau*p/5
            petal(r.name+f"_FLOWER_{j}_{p}",.20,(x+.08*math.cos(a),0,h+.03),
                  (math.radians(-12),0,a),M["iris"],col,r)

def wisteria(r,M,col):
    branch(r.name+"_VINE",[(-1.0,0,1.30),(-.45,0,1.42),(.15,0,1.28),(.90,0,1.50)],.035,M,col,r)
    for i in range(7):
        x=-.72+i*.24
        branch(r.name+f"_DROP_{i}",[(x,0,1.35),(x+.04,0,.72)],.010,M,col,r)
        for k in range(5):
            core.sphere(r.name+f"_FLOWER_{i}_{k}",(.045,.035,.065),
                        (x+(.02 if k%2 else -.02),-.035,1.17-k*.105),
                        M["wisteria"] if k%2 else M["wisteria_light"],col,r,12,6)
        leaf(r.name+f"_LEAF_{i}",(.07,.25),(x,.05,1.31),(0,0,math.radians(78 if i%2 else -78)),M["leaf"],col,r)

def moss_patch(r,M,col):
    core.cube(r.name+"_STONE",(1.7,1.15,.18),(0,0,.09),M["stone"],col,r,bevel=.06)
    for i in range(12):
        a=math.tau*i/12; rr=.15+.05*(i%5)
        core.sphere(r.name+f"_MOSS_{i}",(.18+.03*(i%3),.13+.02*(i%2),.025),
                    (rr*math.cos(a)*2.3,rr*math.sin(a)*1.5,.20),M["moss"],col,r,16,5)

def fern_clump(r,M,col):
    for arm in range(9):
        a=math.tau*arm/9
        branch(r.name+f"_RACHIS_{arm}",[(0,0,.05),(.35*math.cos(a),.35*math.sin(a),.30),(.72*math.cos(a),.72*math.sin(a),.42)],.012,M,col,r)
        for k in range(5):
            rr=.18+k*.11
            for s in (-1,1):
                leaf(r.name+f"_PINNA_{arm}_{k}_{s}",(.035,.18),
                     (rr*math.cos(a),rr*math.sin(a),.18+k*.05),
                     (math.radians(25),0,a+s*math.radians(58)),M["fern"],col,r)

def pond_edge(r,M,col,corner=False):
    for i in range(8):
        x=-1.75+i*.50; y=.0; z=.16+((i*7)%3)*.025
        core.cube(r.name+f"_STONE_{i}",(.58,.72,.26),(x,y,z),M["stone"],col,r,
                  rot=(0,math.radians((i%3-1)*4),math.radians((i%4-2)*2)),bevel=.05)
    core.cube(r.name+"_WATER",(4.2,1.6,.05),(0,.68,.02),M["water"],col,r,bevel=.02)
    if corner:
        for i in range(5):
            y=.30+i*.45
            core.cube(r.name+f"_TURN_{i}",(.72,.55,.25),(-2.02,y,.15),M["stone"],col,r,
                      rot=(0,0,math.radians((i-2)*3)),bevel=.05)

def water_lily(r,M,col):
    core.cube(r.name+"_WATER",(2.2,1.6,.035),(0,0,.02),M["water"],col,r,bevel=.02)
    for i in range(10):
        a=math.tau*i/10; rr=.25+.08*(i%4)
        core.sphere(r.name+f"_PAD_{i}",(.20,.18,.018),(rr*math.cos(a)*2,rr*math.sin(a)*1.4,.08),M["lotus_leaf"],col,r,22,5)

def grass(r,M,col):
    for i in range(24):
        a=math.tau*i/24
        leaf(r.name+f"_BLADE_{i}",(.025,.62),(0,0,.03),
             (math.radians(18+(i%5)*4),math.radians((i%3)*5),a),
             M["grass"] if i%3 else M["leaf_light"],col,r)

def fallen_leaves(r,M,col):
    for i in range(18):
        a=math.tau*i/18; rr=.30+.035*(i%7)
        leaf(r.name+f"_LEAF_{i}",(.07,.22),(rr*math.cos(a)*1.8,rr*math.sin(a)*1.2,.03+.004*(i%3)),
             (math.radians(86+(i%3)*2),math.radians((i*11)%20-10),a+math.radians((i*17)%70)),
             M["maple"] if i%3 else M["maple_gold"],col,r)

BUILDERS=[
 willow_branch,willow_crown,bamboo_clump,bamboo_spray,pine_branch,pine_crown,plum_branch,maple_branch,
 lotus_leaf_cluster,lotus_flower_cluster,reed_clump,iris_clump,wisteria,moss_patch,fern_clump,
 lambda r,M,c:pond_edge(r,M,c,False),lambda r,M,c:pond_edge(r,M,c,True),
 water_lily,grass,fallen_leaves
]

def main():
    a=args(); out=Path(a.output); rep=Path(a.report)
    out.parent.mkdir(parents=True,exist_ok=True); rep.parent.mkdir(parents=True,exist_ok=True)
    s=core.reset_scene(); s.name="TaiWei_FoliageWaterGarden_AssetPack_V6"
    col=bpy.data.collections.new("TaiWei_FoliageWaterGarden_Modules_V6"); s.collection.children.link(col)
    M={
      "bark":core.mat("TW6_MAT_Bark",(.065,.028,.012),.70),
      "leaf":core.mat("TW6_MAT_LeafDeep",(.055,.18,.045),.60),
      "leaf_light":core.mat("TW6_MAT_LeafLight",(.13,.31,.075),.58),
      "pine":core.mat("TW6_MAT_PineNeedle",(.035,.12,.055),.62),
      "bamboo":core.mat("TW6_MAT_Bamboo",(.24,.34,.095),.52),
      "bamboo_dark":core.mat("TW6_MAT_BambooNode",(.10,.18,.045),.60),
      "blossom":core.mat("TW6_MAT_PlumBlossom",(.88,.52,.56),.48),
      "maple":core.mat("TW6_MAT_MapleRed",(.46,.055,.025),.58),
      "maple_gold":core.mat("TW6_MAT_MapleGold",(.62,.24,.035),.56),
      "lotus_leaf":core.mat("TW6_MAT_LotusLeaf",(.065,.23,.11),.52),
      "lotus_pink":core.mat("TW6_MAT_LotusPink",(.78,.24,.34),.46),
      "stem":core.mat("TW6_MAT_Stem",(.10,.26,.07),.60),
      "reed":core.mat("TW6_MAT_ReedHead",(.33,.18,.07),.72),
      "iris":core.mat("TW6_MAT_Iris",(.24,.12,.54),.48),
      "wisteria":core.mat("TW6_MAT_Wisteria",(.34,.12,.48),.48),
      "wisteria_light":core.mat("TW6_MAT_WisteriaLight",(.54,.26,.66),.46),
      "moss":core.mat("TW6_MAT_Moss",(.08,.22,.055),.82),
      "fern":core.mat("TW6_MAT_Fern",(.055,.19,.075),.64),
      "grass":core.mat("TW6_MAT_Grass",(.16,.28,.07),.67),
      "stone":core.mat("TW6_MAT_PondStone",(.40,.42,.38),.72),
      "water":core.mat("TW6_MAT_Water",(.025,.12,.16),.22,.05),
      "gold":core.mat("TW6_MAT_FlowerGold",(.58,.28,.05),.34,.55),
    }
    rec=[]; cols=5
    for i,((aid,cn,cat),builder) in enumerate(zip(ASSETS,BUILDERS)):
        x=(i%cols-(cols-1)/2)*6.4; y=(i//cols-1.5)*6.1
        r=root(aid,cn,cat,(x,y,0),col); builder(r,M,col)
        geom=[o for o in r.children if o.type in {"MESH","CURVE"}]
        rec.append({"asset_id":aid,"name_cn":cn,"category":cat,"quality_tier":"hero_v6",
          "geometry_objects":len(geom),"mesh_objects":sum(o.type=="MESH" for o in geom),
          "curve_objects":sum(o.type=="CURVE" for o in geom),"reusable":True,"protected_scene_safe":True})
    assert len(rec)==20 and all(x["geometry_objects"]>=5 for x in rec)
    used=sorted({m.name for o in s.objects if getattr(o,"data",None) and hasattr(o.data,"materials") for m in o.data.materials})
    report={"scene":s.name,"pack_id":"TW_FOLIAGE_WATER_GARDEN_PACK_V6","asset_count":20,"assets":rec,
      "objects":len(s.objects),"mesh_objects":sum(o.type=="MESH" for o in s.objects),
      "curve_objects":sum(o.type=="CURVE" for o in s.objects),"declared_materials":len(M),
      "used_materials":used,"status":"hero_midpoly_reusable","protected_scenes_touched":False,
      "rebuild_contract":"deterministic_geometry_no_llm_required","blender_target":"4.2.23 LTS"}
    rep.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()))
    print("TAIWEI_FOLIAGE_WATER_V6_OK",json.dumps(report,ensure_ascii=False))

if __name__=="__main__":
    main()
