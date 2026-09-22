"""Taiwei Cloud Palace Roof & Timber Detail Asset Pack V5.
High-reuse roof, eave and timber-detail modules.
"""
from __future__ import annotations
import argparse, importlib.util, json, math, sys
from pathlib import Path
import bpy

CORE=Path(__file__).with_name("generate_hero_asset_pack.py")
spec=importlib.util.spec_from_file_location("taiwei_core",CORE)
core=importlib.util.module_from_spec(spec); spec.loader.exec_module(core)

ASSETS=[
 ("TW_V5_ROOF_TILE_ROW","筒瓦板瓦列","roof_system"),
 ("TW_V5_EAVE_TILE_ROW","瓦当滴水檐口列","roof_system"),
 ("TW_V5_RIDGE_STRAIGHT","正脊直段","roof_system"),
 ("TW_V5_RIDGE_CORNER","垂脊转角段","roof_system"),
 ("TW_V5_HIP_CORNER","戗脊翼角模块","roof_system"),
 ("TW_V5_COMMON_RAFTERS","椽子一开间","timber_structure"),
 ("TW_V5_FLYING_RAFTERS","飞椽一开间","timber_structure"),
 ("TW_V5_PURLIN_BAY","檩枋一开间","timber_structure"),
 ("TW_V5_BEAM_HEAD","卷草梁头","timber_detail"),
 ("TW_V5_SPARROW_BRACE","云龙雀替","timber_detail"),
 ("TW_V5_HANGING_FISH","悬鱼垂花","timber_detail"),
 ("TW_V5_FASCIA_BOARD","彩画封檐板","timber_detail"),
 ("TW_V5_DROPPED_FRIEZE","挂落花牙子","timber_detail"),
 ("TW_V5_TRANSOM_PANEL","横披窗心","door_window"),
 ("TW_V5_CLOUD_LATTICE","如意云纹棂花","door_window"),
 ("TW_V5_DIAMOND_LATTICE","菱花棂格","door_window"),
 ("TW_V5_DOOR_BAY_FRAME","殿门一开间框架","door_window"),
 ("TW_V5_COLUMN_SHAFT","朱漆檐柱","timber_structure"),
 ("TW_V5_COLUMN_CAPITAL","柱头卷杀与栌斗","timber_structure"),
 ("TW_V5_EAVE_BELL_BRACKET","檐角风铎挂架","roof_detail"),
]

def args():
    tail=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="generated_assets/TaiWei_RoofTimberPack_V5.blend")
    p.add_argument("--report",default="generated_assets/taiwei-roof-timber-v5-report.json")
    return p.parse_args(tail)

def root(a,cn,cat,loc,col):
    r=bpy.data.objects.new(a,None); col.objects.link(r); r.location=loc
    for k,v in {"asset_id":a,"name_cn":cn,"category":cat,"quality_tier":"hero_v5",
      "production_level":"hero_midpoly","parametric":True,"reusable":True,
      "protected_scene_safe":True,"source_style":"historical_chinese_palace_yanyun_grounded",
      "units":"meters","origin_policy":"asset_root_grounded"}.items(): r[k]=v
    return r

def tile_row(r,M,col,eave=False):
    tile,g=M["tile"],M["gold"]
    for i in range(12):
        x=-2.75+i*.50
        core.cyl(r.name+f"_ROUND_{i}",.17,.58,(x,0,.20),tile,col,r,20,rot=(math.pi/2,0,0))
        core.cube(r.name+f"_FLAT_{i}",(.44,.72,.08),(x+.24,.05,.06),tile,col,r,rot=(math.radians(7),0,0),bevel=.018)
        if eave:
            core.cyl(r.name+f"_WADANG_{i}",.18,.10,(x,-.36,.18),tile,col,r,24,rot=(math.pi/2,0,0))
            core.sphere(r.name+f"_BOSS_{i}",(.07,.03,.07),(x,-.42,.18),g,col,r,14,7)

def ridge_straight(r,M,col):
    t,g=M["tile"],M["gold"]
    core.cube(r.name+"_CORE",(5.8,.54,.42),(0,0,.24),t,col,r,bevel=.08)
    for i in range(13):
        x=-2.76+i*.46
        core.cyl(r.name+f"_CAP_{i}",.16,.60,(x,0,.48),t,col,r,18,rot=(math.pi/2,0,0))
    for x in (-2.80,2.80):
        core.sphere(r.name+f"_END_{x}",(.20,.20,.24),(x,0,.50),g,col,r,18,9)

def ridge_corner(r,M,col):
    t,g=M["tile"],M["gold"]
    for axis in ("x","y"):
        for i in range(7):
            q=-1.35+i*.45
            loc=(q,0,.25) if axis=="x" else (0,q,.25)
            core.cube(r.name+f"_{axis}_{i}",(.48,.46,.34) if axis=="x" else (.46,.48,.34),loc,t,col,r,bevel=.05)
    core.sphere(r.name+"_KNOT",(.30,.30,.34),(0,0,.52),g,col,r,20,10)
    for a in (0,math.pi/2):
        core.tube(r.name+f"_ORN_{a}",[(0,0,.70),(.52*math.cos(a),.52*math.sin(a),.92),(1.02*math.cos(a),1.02*math.sin(a),.72)],.04,g,col,r)

def hip_corner(r,M,col):
    t,g=M["tile"],M["gold"]
    core.cube(r.name+"_HIP",(3.8,.52,.38),(0,0,.32),t,col,r,rot=(0,math.radians(-9),0),bevel=.06)
    for i in range(8):
        x=-1.65+i*.48
        core.cube(r.name+f"_FEATHER_{i}",(.36,.74,.12),(x,0,.64+abs(x)*.12),t,col,r,rot=(0,math.radians(-10),0),bevel=.025)
    core.tube(r.name+"_UPTURN",[(1.55,0,.72),(1.90,0,1.02),(2.10,0,1.42)],.07,g,col,r)
    core.sphere(r.name+"_TIP",(.14,.14,.20),(2.12,0,1.55),g,col,r,18,9)

def rafters(r,M,col,flying=False):
    wood,g=M["wood"],M["gold"]
    for i in range(11):
        x=-2.40+i*.48
        y=-.20 if not flying else -.42
        z=.45 if not flying else .72
        core.cube(r.name+f"_RAFTER_{i}",(.16,2.4,.18),(x,y,z),wood,col,r,rot=(math.radians(-10 if not flying else -16),0,0),bevel=.018)
        if flying:
            core.cube(r.name+f"_TIP_{i}",(.20,.62,.15),(x,-1.25,1.00),g,col,r,rot=(math.radians(-18),0,0),bevel=.018)
    core.cube(r.name+"_BEAM",(5.25,.28,.26),(0,.80,.20),wood,col,r,bevel=.025)

def purlin(r,M,col):
    wood,g=M["wood"],M["gold"]
    for z,y in ((.40,.65),(1.00,.15),(1.60,-.35)):
        core.cyl(r.name+f"_PURLIN_{z}",.16,5.4,(0,y,z),wood,col,r,20,rot=(0,math.pi/2,0))
    for x in (-2.25,0,2.25):
        core.cube(r.name+f"_TIE_{x}",(.18,1.35,.22),(x,.15,1.00),g,col,r,rot=(math.radians(-9),0,0),bevel=.02)

def beam_head(r,M,col):
    wood,g=M["wood"],M["gold"]
    core.cube(r.name+"_BEAM",(2.2,.55,.52),(0,0,.52),wood,col,r,bevel=.07)
    for sy in (-1,1):
        core.tube(r.name+f"_SCROLL_{sy}",[(.55,sy*.30,.62),(.82,sy*.31,.88),(1.02,sy*.30,.70),(.88,sy*.30,.50)],.045,g,col,r)
    for i in range(5):
        core.sphere(r.name+f"_BOSS_{i}",(.07,.035,.07),(-.48+i*.24,-.31,.52),g,col,r,14,7)

def sparrow(r,M,col):
    wood,g=M["wood"],M["gold"]
    core.cube(r.name+"_BACK",(2.5,.24,.24),(0,0,1.02),wood,col,r,bevel=.035)
    core.cube(r.name+"_DROP",(.24,.26,1.35),(-1.08,0,.48),wood,col,r,bevel=.035)
    core.tube(r.name+"_DRAGON",[(-.90,-.16,.84),(-.52,-.18,1.18),(-.05,-.18,.92),(.42,-.18,1.30),(.88,-.16,1.02)],.06,g,col,r)
    for i in range(5):
        core.sphere(r.name+f"_CLOUD_{i}",(.15,.06,.08),(-.72+i*.36,-.17,.70+(i%2)*.12),g,col,r,14,7)

def hanging_fish(r,M,col):
    wood,g=M["wood"],M["gold"]
    core.cube(r.name+"_SPINE",(.18,.26,2.0),(0,0,1.10),wood,col,r,bevel=.05)
    for sy in (-1,1):
        core.tube(r.name+f"_WING_{sy}",[(0,sy*.10,1.72),(.42,sy*.14,1.48),(.72,sy*.16,1.78),(.92,sy*.14,1.42)],.055,g,col,r)
    core.sphere(r.name+"_PEARL",(.15,.10,.15),(0,-.15,.90),g,col,r,18,8)
    core.tube(r.name+"_TAIL",[(0,0,.38),(-.30,0,.16),(0,0,.02),(.30,0,.16)],.045,g,col,r)

def fascia(r,M,col):
    red,g,blue=M["red"],M["gold"],M["blue"]
    core.cube(r.name+"_BOARD",(5.2,.20,.62),(0,0,.45),red,col,r,bevel=.035)
    for i in range(8):
        x=-2.1+i*.60
        core.sphere(r.name+f"_ROSETTE_{i}",(.10,.045,.10),(x,-.13,.48),g,col,r,14,7)
        core.tube(r.name+f"_CLOUD_{i}",[(x-.20,-.14,.30),(x,-.14,.54),(x+.20,-.14,.30)],.022,blue,col,r)
    core.cube(r.name+"_TOP",(5.35,.24,.12),(0,0,.82),g,col,r,bevel=.02)

def dropped_frieze(r,M,col):
    wood,g=M["wood"],M["gold"]
    core.cube(r.name+"_TOP",(5.0,.22,.18),(0,0,1.32),wood,col,r,bevel=.025)
    for i in range(9):
        x=-2.0+i*.50
        core.cube(r.name+f"_DROP_{i}",(.10,.22,.58),(x,0,.96),wood,col,r,bevel=.018)
        core.tube(r.name+f"_ARC_{i}",[(x-.20,-.12,1.16),(x,-.13,.90),(x+.20,-.12,1.16)],.022,g,col,r)

def transom(r,M,col):
    wood,g,p=M["wood"],M["gold"],M["paper"]
    core.cube(r.name+"_PANEL",(4.2,.08,1.4),(0,.06,.80),p,col,r,bevel=.02)
    for x in (-2.0,2.0):
        core.cube(r.name+f"_SIDE_{x}",(.16,.26,1.65),(x,0,.82),wood,col,r,bevel=.025)
    for z in (.08,1.56):
        core.cube(r.name+f"_RAIL_{z}",(4.15,.26,.14),(0,0,z),wood,col,r,bevel=.02)
    for i in range(9):
        x=-1.68+i*.42
        core.cube(r.name+f"_V_{i}",(.04,.28,1.20),(x,-.08,.80),g,col,r,bevel=.007)
    for j in range(4):
        z=.32+j*.32
        core.cube(r.name+f"_H_{j}",(3.40,.28,.04),(0,-.08,z),g,col,r,bevel=.007)

def lattice_cloud(r,M,col):
    wood,g=M["wood"],M["gold"]
    core.cube(r.name+"_FRAME",(2.6,.18,2.6),(0,0,1.3),wood,col,r,bevel=.04)
    for i in range(5):
        y=.40+i*.42
        core.tube(r.name+f"_CLOUD_{i}",[(-.92,-.12,y),(-.55,-.13,y+.20),(-.18,-.13,y),(.18,-.13,y+.18),(.55,-.13,y),(.92,-.12,y+.18)],.026,g,col,r)
    for x in (-.78,-.26,.26,.78):
        core.cube(r.name+f"_V_{x}",(.035,.25,2.15),(x,-.08,1.30),g,col,r,bevel=.006)

def lattice_diamond(r,M,col):
    wood,g=M["wood"],M["gold"]
    core.cube(r.name+"_FRAME",(2.6,.18,2.6),(0,0,1.3),wood,col,r,bevel=.04)
    for k in range(-4,5):
        x=k*.36
        core.cube(r.name+f"_D1_{k}",(.045,.24,3.2),(x,-.08,1.30),g,col,r,rot=(0,0,math.radians(45)),bevel=.006)
        core.cube(r.name+f"_D2_{k}",(.045,.24,3.2),(x,-.08,1.30),g,col,r,rot=(0,0,math.radians(-45)),bevel=.006)

def door_bay(r,M,col):
    red,g=M["red"],M["gold"]
    for x in (-1.75,1.75):
        core.cube(r.name+f"_POST_{x}",(.34,.42,4.2),(x,0,2.10),red,col,r,bevel=.045)
    core.cube(r.name+"_LINTEL",(3.85,.46,.34),(0,0,3.98),red,col,r,bevel=.045)
    core.cube(r.name+"_SILL",(3.55,.42,.20),(0,0,.10),g,col,r,bevel=.03)
    for x in (-.55,.55):
        core.cube(r.name+f"_MULLION_{x}",(.14,.30,3.55),(x,0,1.92),red,col,r,bevel=.02)
    for z in (1.35,2.70):
        core.cube(r.name+f"_RAIL_{z}",(3.55,.30,.14),(0,0,z),g,col,r,bevel=.02)

def column(r,M,col):
    red,g=M["red"],M["gold"]
    core.lathe(r.name+"_BASE",[(.34,0),(.40,.10),(.31,.28)],(0,0,0),g,col,r,28)
    core.cyl(r.name+"_SHAFT",.28,4.2,(0,0,2.35),red,col,r,32)
    for z in (.48,4.18):
        core.torus(r.name+f"_RING_{z}",.30,.035,(0,0,z),g,col,r,28,8)
    core.lathe(r.name+"_CAP",[(.32,0),(.42,.12),(.52,.28),(.44,.44)],(0,0,4.50),g,col,r,24)

def capital(r,M,col):
    red,g=M["red"],M["gold"]
    core.cyl(r.name+"_NECK",.34,.70,(0,0,.42),red,col,r,28)
    core.cube(r.name+"_LU_DOU",(1.0,.92,.34),(0,0,.96),g,col,r,bevel=.05)
    for axis in ("x","y"):
        core.cube(r.name+f"_GONG_{axis}",(1.75,.28,.20) if axis=="x" else (.28,1.75,.20),(0,0,1.27),red,col,r,bevel=.025)
    for x,y in ((-.55,0),(.55,0),(0,-.55),(0,.55)):
        core.cyl(r.name+f"_DOU_{x}_{y}",.14,.16,(x,y,1.47),g,col,r,14)

def bell_bracket(r,M,col):
    wood,g,bronze=M["wood"],M["gold"],M["bronze"]
    core.cube(r.name+"_ARM",(1.5,.20,.18),(0,0,1.15),wood,col,r,rot=(0,math.radians(-12),0),bevel=.03)
    core.cube(r.name+"_WALL_PLATE",(.24,.44,1.0),(-.68,0,.62),wood,col,r,bevel=.035)
    core.torus(r.name+"_HOOK",.18,.035,(.62,0,1.12),g,col,r,24,8,rot=(math.pi/2,0,0))
    core.tube(r.name+"_CHAIN",[(.62,0,.96),(.62,0,.58)],.015,g,col,r)
    core.lathe(r.name+"_BELL",[(.06,0),(.18,.08),(.28,.28),(.34,.50)],(.62,0,.12),bronze,col,r,22)

BUILDERS=[
 lambda r,M,c:tile_row(r,M,c,False),lambda r,M,c:tile_row(r,M,c,True),
 ridge_straight,ridge_corner,hip_corner,
 lambda r,M,c:rafters(r,M,c,False),lambda r,M,c:rafters(r,M,c,True),
 purlin,beam_head,sparrow,hanging_fish,fascia,dropped_frieze,transom,lattice_cloud,lattice_diamond,
 door_bay,column,capital,bell_bracket
]

def main():
    a=args(); out=Path(a.output); rep=Path(a.report)
    out.parent.mkdir(parents=True,exist_ok=True); rep.parent.mkdir(parents=True,exist_ok=True)
    s=core.reset_scene(); s.name="TaiWei_RoofTimber_AssetPack_V5"
    col=bpy.data.collections.new("TaiWei_RoofTimber_Modules_V5"); s.collection.children.link(col)
    M={
      "tile":core.mat("TW5_MAT_BlackGlazedTile",(.022,.036,.044),.28,.08),
      "gold":core.mat("TW5_MAT_AgedGilt",(.49,.23,.038),.30,.76),
      "wood":core.mat("TW5_MAT_DarkTimber",(.095,.024,.014),.42),
      "red":core.mat("TW5_MAT_Cinnabar",(.31,.025,.014),.34),
      "blue":core.mat("TW5_MAT_MineralBlue",(.028,.095,.20),.40),
      "paper":core.mat("TW5_MAT_WarmPaper",(.66,.48,.30),.62),
      "bronze":core.mat("TW5_MAT_Bronze",(.12,.052,.018),.36,.78),
    }
    rec=[]; cols=5
    for i,((aid,cn,cat),builder) in enumerate(zip(ASSETS,BUILDERS)):
        x=(i%cols-(cols-1)/2)*7.2; y=(i//cols-1.5)*7.0
        r=root(aid,cn,cat,(x,y,0),col); builder(r,M,col)
        geom=[o for o in r.children if o.type in {"MESH","CURVE"}]
        rec.append({"asset_id":aid,"name_cn":cn,"category":cat,"quality_tier":"hero_v5",
          "geometry_objects":len(geom),"mesh_objects":sum(o.type=="MESH" for o in geom),
          "curve_objects":sum(o.type=="CURVE" for o in geom),"reusable":True,"protected_scene_safe":True})
    assert len(rec)==20 and all(x["geometry_objects"]>=5 for x in rec)
    used=sorted({m.name for o in s.objects if getattr(o,"data",None) and hasattr(o.data,"materials") for m in o.data.materials})
    report={"scene":s.name,"pack_id":"TW_ROOF_TIMBER_PACK_V5","asset_count":20,"assets":rec,
      "objects":len(s.objects),"mesh_objects":sum(o.type=="MESH" for o in s.objects),
      "curve_objects":sum(o.type=="CURVE" for o in s.objects),"declared_materials":len(M),
      "used_materials":used,"status":"hero_midpoly_reusable","protected_scenes_touched":False,
      "rebuild_contract":"deterministic_geometry_no_llm_required","blender_target":"4.2.23 LTS"}
    rep.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()))
    print("TAIWEI_ROOF_TIMBER_V5_OK",json.dumps(report,ensure_ascii=False))

if __name__=="__main__":
    main()
