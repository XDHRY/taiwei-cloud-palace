"""Taiwei Cloud Palace Interior & Ceremonial Furniture Asset Pack V7."""
from __future__ import annotations
import argparse, importlib.util, json, math, sys
from pathlib import Path
import bpy

CORE=Path(__file__).with_name("generate_hero_asset_pack.py")
spec=importlib.util.spec_from_file_location("taiwei_core",CORE)
core=importlib.util.module_from_spec(spec); spec.loader.exec_module(core)

ASSETS=[
 ("TW_V7_HORSESHOE_CHAIR","明式圈椅","furniture"),
 ("TW_V7_ARMCHAIR","宫廷扶手椅","furniture"),
 ("TW_V7_KANG_TABLE","炕桌","furniture"),
 ("TW_V7_INCENSE_STAND","高束腰香几","furniture"),
 ("TW_V7_CONSOLE_TABLE","翘头条案","furniture"),
 ("TW_V7_ALTAR_TABLE","朱漆供案","furniture"),
 ("TW_V7_BENCH","榫卯长凳","furniture"),
 ("TW_V7_ROUND_STOOL","鼓形圆凳","furniture"),
 ("TW_V7_FOOTREST","御用脚踏","furniture"),
 ("TW_V7_BOOKCASE","多宝格书架","furniture"),
 ("TW_V7_SCROLL_RACK","卷轴架","furniture"),
 ("TW_V7_FOLDING_SCREEN","六扇折屏","interior_prop"),
 ("TW_V7_CANOPY_FRAME","宝盖华盖架","ceremonial"),
 ("TW_V7_CURTAIN_PAIR","宫廷帷幔一对","ceremonial"),
 ("TW_V7_RITUAL_BANNER","云龙仪仗旗","ceremonial"),
 ("TW_V7_STANDARD_POLE","鎏金仪仗杆","ceremonial"),
 ("TW_V7_CANDLE_STAND","落地烛台","lighting_prop"),
 ("TW_V7_BRAZIER","兽足火盆","ritual_prop"),
 ("TW_V7_PORCELAIN_VASE","青花宫瓶","decor_prop"),
 ("TW_V7_CARPET","团龙宫毯","decor_prop"),
]

def args():
    tail=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser();p.add_argument("--output",default="generated_assets/TaiWei_InteriorCeremonialPack_V7.blend")
    p.add_argument("--report",default="generated_assets/taiwei-interior-ceremonial-v7-report.json");return p.parse_args(tail)

def root(a,cn,cat,loc,col):
    r=bpy.data.objects.new(a,None);col.objects.link(r);r.location=loc
    for k,v in {"asset_id":a,"name_cn":cn,"category":cat,"quality_tier":"hero_v7","production_level":"hero_midpoly",
      "parametric":True,"reusable":True,"protected_scene_safe":True,
      "source_style":"historical_chinese_palace_yanyun_grounded","units":"meters","origin_policy":"asset_root_grounded"}.items():r[k]=v
    return r

def leg(name,x,y,h,M,col,r,mat="wood"):
    core.lathe(name,[(.055,0),(.08,.08),(.055,h-.12),(.075,h)],(x,y,.04),M[mat],col,r,14)

def horseshoe(r,M,col):
    w=M["wood"];g=M["gold"]
    core.cube(r.name+"_SEAT",(1.12,.92,.16),(0,0,.82),w,col,r,bevel=.05)
    for x in (-.45,.45):
        for y in (-.32,.32):leg(r.name+f"_LEG_{x}_{y}",x,y,.78,M,col,r)
    for x in (-.48,.48):core.cube(r.name+f"_POST_{x}",(.09,.11,1.12),(x,.35,1.36),w,col,r,bevel=.025)
    core.tube(r.name+"_HORSESHOE",[(-.48,.35,1.94),(-.24,.37,2.15),(0,.38,2.22),(.24,.37,2.15),(.48,.35,1.94)],.065,w,col,r)
    core.cube(r.name+"_BACK_SPLAT",(.28,.08,.74),(0,.37,1.53),g,col,r,bevel=.04)
    for x in (-.53,.53):core.cube(r.name+f"_ARM_{x}",(.08,.72,.10),(x,0,1.30),w,col,r,bevel=.03)

def armchair(r,M,col):
    w,g=M["wood"],M["gold"]
    core.cube(r.name+"_SEAT",(1.22,.96,.16),(0,0,.82),w,col,r,bevel=.05)
    for x in (-.48,.48):
        for y in (-.34,.34):leg(r.name+f"_LEG_{x}_{y}",x,y,.78,M,col,r)
    core.cube(r.name+"_BACK",(1.05,.10,.95),(0,.38,1.50),w,col,r,bevel=.04)
    core.cube(r.name+"_CENTER",(0.38,.07,.72),(0,.32,1.52),g,col,r,bevel=.04)
    for x in (-.54,.54):core.cube(r.name+f"_ARM_{x}",(.10,.76,.12),(x,0,1.30),w,col,r,bevel=.03)

def kang_table(r,M,col):
    w,g=M["wood"],M["gold"]
    core.cube(r.name+"_TOP",(1.65,1.02,.15),(0,0,.68),w,col,r,bevel=.06)
    for x in (-.66,.66):
        for y in (-.35,.35):leg(r.name+f"_LEG_{x}_{y}",x,y,.62,M,col,r)
    for y in (-.42,.42):core.cube(r.name+f"_APRON_{y}",(1.34,.08,.22),(0,y,.52),g,col,r,bevel=.025)

def incense_stand(r,M,col):
    w,g=M["wood"],M["gold"]
    core.cube(r.name+"_TOP",(.86,.86,.13),(0,0,1.34),w,col,r,bevel=.08)
    core.cube(r.name+"_WAIST",(.62,.62,.18),(0,0,1.16),g,col,r,bevel=.05)
    for x in (-.29,.29):
        for y in (-.29,.29):leg(r.name+f"_LEG_{x}_{y}",x,y,1.18,M,col,r)
    for side in (-1,1):core.tube(r.name+f"_CLOUD_{side}",[(-.30,side*.34,.92),(0,side*.36,1.08),(.30,side*.34,.92)],.025,g,col,r)

def console(r,M,col):
    w,g=M["wood"],M["gold"]
    core.cube(r.name+"_TOP",(2.7,.72,.15),(0,0,1.34),w,col,r,bevel=.05)
    for x in (-1.05,1.05):
        for y in (-.24,.24):leg(r.name+f"_LEG_{x}_{y}",x,y,1.28,M,col,r)
    for x in (-1.34,1.34):core.cube(r.name+f"_UPTURN_{x}",(.12,.74,.24),(x,0,1.50),g,col,r,rot=(0,0,math.radians(7*x)),bevel=.03)
    core.cube(r.name+"_APRON",(2.25,.08,.25),(0,-.33,1.12),g,col,r,bevel=.03)

def altar(r,M,col):
    w,g,red=M["wood"],M["gold"],M["red"]
    core.cube(r.name+"_TOP",(3.0,.96,.18),(0,0,1.50),red,col,r,bevel=.055)
    for x in (-1.18,1.18):
        for y in (-.34,.34):leg(r.name+f"_LEG_{x}_{y}",x,y,1.43,M,col,r)
    core.cube(r.name+"_FRONT_APRON",(2.55,.08,.36),(0,-.46,1.22),g,col,r,bevel=.03)
    for i in range(5):core.sphere(r.name+f"_BOSS_{i}",(.06,.035,.06),(-.80+i*.40,-.51,1.24),g,col,r,12,6)

def bench(r,M,col):
    w,g=M["wood"],M["gold"]
    core.cube(r.name+"_SEAT",(2.5,.62,.15),(0,0,.72),w,col,r,bevel=.05)
    for x in (-.95,.95):
        for y in (-.20,.20):leg(r.name+f"_LEG_{x}_{y}",x,y,.66,M,col,r)
    core.cube(r.name+"_STRETCHER",(1.95,.10,.12),(0,0,.32),g,col,r,bevel=.02)

def round_stool(r,M,col):
    w,g=M["wood"],M["gold"]
    core.cyl(r.name+"_SEAT",.52,.16,(0,0,.82),w,col,r,28)
    for i in range(6):
        a=math.tau*i/6
        leg(r.name+f"_LEG_{i}",.36*math.cos(a),.36*math.sin(a),.78,M,col,r)
    core.torus(r.name+"_RING",.36,.035,(0,0,.36),g,col,r,24,8)

def footrest(r,M,col):
    w,g=M["wood"],M["gold"]
    core.cube(r.name+"_TOP",(1.35,.66,.14),(0,0,.52),w,col,r,bevel=.05)
    for x in (-.52,.52):
        for y in (-.20,.20):leg(r.name+f"_LEG_{x}_{y}",x,y,.46,M,col,r)
    core.cube(r.name+"_FRONT",(1.12,.08,.18),(0,-.31,.38),g,col,r,bevel=.025)

def bookcase(r,M,col):
    w,g=M["wood"],M["gold"]
    for x in (-1.15,1.15):core.cube(r.name+f"_SIDE_{x}",(.16,.55,3.0),(x,0,1.50),w,col,r,bevel=.035)
    for z in (.14,.78,1.42,2.06,2.70):core.cube(r.name+f"_SHELF_{z}",(2.45,.60,.12),(0,0,z),w,col,r,bevel=.025)
    for x in (-.38,.38):core.cube(r.name+f"_DIV_{x}",(.10,.54,2.55),(x,0,1.45),g,col,r,bevel=.02)

def scroll_rack(r,M,col):
    w,g=M["wood"],M["gold"]
    for x in (-.80,.80):core.cube(r.name+f"_POST_{x}",(.14,.46,2.0),(x,0,1.0),w,col,r,bevel=.035)
    for z in (.45,1.05,1.65):core.cube(r.name+f"_BAR_{z}",(1.72,.18,.12),(0,0,z),w,col,r,bevel=.025)
    for i in range(6):
        x=-.60+i*.24;core.cyl(r.name+f"_SCROLL_{i}",.07,.48,(x,-.16,.76+(i%3)*.58),g,col,r,16,rot=(math.pi/2,0,0))

def screen(r,M,col):
    w,g,blue=M["wood"],M["gold"],M["blue"]
    for i in range(6):
        x=-2.0+i*.80
        core.cube(r.name+f"_PANEL_{i}",(.72,.10,2.65),(x,0,1.45),blue,col,r,bevel=.04)
        core.cube(r.name+f"_L_{i}",(.08,.18,2.82),(x-.34,0,1.45),w,col,r,bevel=.02)
        core.cube(r.name+f"_R_{i}",(.08,.18,2.82),(x+.34,0,1.45),w,col,r,bevel=.02)
        core.tube(r.name+f"_MOUNTAIN_{i}",[(x-.25,-.08,1.10),(x,-.09,1.60),(x+.24,-.08,1.26)],.025,g,col,r)

def canopy(r,M,col):
    red,g=M["red"],M["gold"]
    for x in (-1.25,1.25):
        for y in (-.85,.85):core.cube(r.name+f"_POST_{x}_{y}",(.10,.10,3.0),(x,y,1.50),g,col,r,bevel=.02)
    core.cube(r.name+"_TOP",(2.85,2.05,.16),(0,0,3.06),red,col,r,bevel=.06)
    for sy in (-1,1):core.tube(r.name+f"_VALANCE_{sy}",[(-1.25,sy*.98,2.92),(-.60,sy*1.0,2.70),(0,sy*1.0,2.90),(.60,sy*1.0,2.70),(1.25,sy*.98,2.92)],.035,g,col,r)

def curtain(r,M,col):
    red,g=M["fabric_red"],M["gold"]
    for side in (-1,1):
        x=side*.82
        core.cube(r.name+f"_DROP_{side}",(.62,.06,2.45),(x,0,1.45),red,col,r,bevel=.035)
        for i in range(5):
            core.tube(r.name+f"_FOLD_{side}_{i}",[(x-.22+i*.11,-.045,.28),(x-.22+i*.11,-.06,2.62)],.015,g,col,r)
        core.torus(r.name+f"_TIE_{side}",.12,.022,(x,-.08,1.18),g,col,r,18,6,rot=(math.pi/2,0,0))
    core.cube(r.name+"_PELMET",(2.25,.12,.32),(0,0,2.82),M["red"],col,r,bevel=.04)

def banner(r,M,col):
    red,g=M["fabric_red"],M["gold"]
    core.cube(r.name+"_FIELD",(1.1,.055,2.1),(0,0,1.55),red,col,r,bevel=.025)
    core.cube(r.name+"_TOP",(1.28,.10,.12),(0,0,2.64),g,col,r,bevel=.02)
    core.tube(r.name+"_DRAGON",[(-.36,-.05,1.42),(-.10,-.06,1.85),(.18,-.06,1.52),(.38,-.05,1.92)],.035,g,col,r)
    for i in range(5):core.tube(r.name+f"_TAIL_{i}",[( -.44+i*.22,0,.50),(-.44+i*.22,0,.16)],.018,g,col,r)

def standard(r,M,col):
    g,red=M["gold"],M["red"]
    core.lathe(r.name+"_BASE",[(.30,0),(.38,.10),(.24,.30)],(0,0,0),g,col,r,22)
    core.cyl(r.name+"_POLE",.045,3.1,(0,0,1.80),red,col,r,14)
    for z in (.40,3.15):core.torus(r.name+f"_RING_{z}",.065,.012,(0,0,z),g,col,r,14,5)
    core.sphere(r.name+"_FINIAL",(.11,.11,.14),(0,0,3.48),g,col,r,18,8)

def candle(r,M,col):
    g,red=M["gold"],M["red"]
    core.lathe(r.name+"_BASE",[(.34,0),(.42,.10),(.26,.32),(.18,.48)],(0,0,0),g,col,r,24)
    core.cyl(r.name+"_SHAFT",.055,1.65,(0,0,1.30),g,col,r,14)
    core.cyl(r.name+"_CANDLE",.085,.72,(0,0,2.48),red,col,r,18)
    core.sphere(r.name+"_FLAME",(.045,.035,.10),(0,0,2.91),M["flame"],col,r,14,7)
    for z in (1.25,1.75):core.torus(r.name+f"_RING_{z}",.10,.018,(0,0,z),g,col,r,16,6)

def brazier(r,M,col):
    b,g=M["bronze"],M["gold"]
    core.lathe(r.name+"_BOWL",[(.32,0),(.60,.14),(.72,.44),(.64,.68)],(0,0,.42),b,col,r,30)
    for i in range(3):
        a=math.tau*i/3;core.cyl(r.name+f"_LEG_{i}",.07,.55,(.42*math.cos(a),.42*math.sin(a),.28),b,col,r,12)
    core.torus(r.name+"_RIM",.66,.04,(0,0,1.08),g,col,r,26,8)
    for i in range(5):core.sphere(r.name+f"_COAL_{i}",(.12,.10,.08),(-.28+i*.14,0,1.02),M["coal"],col,r,14,7)

def vase(r,M,col):
    blue,white,g=M["blue"],M["white"],M["gold"]
    core.lathe(r.name+"_BODY",[(.20,0),(.42,.14),(.58,.56),(.48,1.05),(.27,1.28),(.18,1.52),(.25,1.66)],(0,0,.08),white,col,r,36)
    for z,rad in ((.42,.47),(.82,.52),(1.18,.34)):
        core.torus(r.name+f"_BLUE_BAND_{z}",rad,.025,(0,0,z),blue,col,r,28,8)
    for side in (-1,1):core.tube(r.name+f"_VINE_{side}",[(side*.30,-.40,.52),(side*.12,-.44,.78),(side*.30,-.42,1.02)],.022,blue,col,r)
    core.torus(r.name+"_RIM",.23,.035,(0,0,1.76),g,col,r,26,8)

def carpet(r,M,col):
    red,g,blue=M["fabric_red"],M["gold"],M["blue"]
    core.cube(r.name+"_FIELD",(3.4,2.25,.06),(0,0,.03),red,col,r,bevel=.035)
    core.tube(r.name+"_BORDER",[(-1.52,-.98,.07),(1.52,-.98,.07),(1.52,.98,.07),(-1.52,.98,.07),(-1.52,-.98,.07)],.025,g,col,r)
    core.torus(r.name+"_CENTER",.55,.045,(0,0,.09),g,col,r,32,8)
    for i in range(8):
        a=math.tau*i/8;core.sphere(r.name+f"_CLOUD_{i}",(.10,.07,.035),(.72*math.cos(a),.50*math.sin(a),.09),blue,col,r,14,6)

BUILDERS=[horseshoe,armchair,kang_table,incense_stand,console,altar,bench,round_stool,footrest,bookcase,
 scroll_rack,screen,canopy,curtain,banner,standard,candle,brazier,vase,carpet]

def main():
    a=args();out=Path(a.output);rep=Path(a.report);out.parent.mkdir(parents=True,exist_ok=True);rep.parent.mkdir(parents=True,exist_ok=True)
    s=core.reset_scene();s.name="TaiWei_InteriorCeremonial_AssetPack_V7"
    col=bpy.data.collections.new("TaiWei_InteriorCeremonial_Modules_V7");s.collection.children.link(col)
    M={
      "wood":core.mat("TW7_MAT_DarkRosewood",(.085,.020,.012),.40),
      "gold":core.mat("TW7_MAT_AgedGilt",(.50,.24,.04),.30,.76),
      "red":core.mat("TW7_MAT_Cinnabar",(.31,.024,.014),.34),
      "fabric_red":core.mat("TW7_MAT_ImperialTextile",(.42,.025,.018),.62),
      "blue":core.mat("TW7_MAT_MineralBlue",(.025,.085,.20),.40),
      "bronze":core.mat("TW7_MAT_Bronze",(.11,.047,.016),.36,.78),
      "white":core.mat("TW7_MAT_Porcelain",(.80,.82,.78),.26),
      "flame":core.mat("TW7_MAT_Flame",(.95,.34,.03),.20,0,((1,.15,.02),3.0)),
      "coal":core.mat("TW7_MAT_Coal",(.025,.018,.015),.90),
    }
    rec=[];cols=5
    for i,((aid,cn,cat),builder) in enumerate(zip(ASSETS,BUILDERS)):
        x=(i%cols-(cols-1)/2)*6.5;y=(i//cols-1.5)*6.2
        r=root(aid,cn,cat,(x,y,0),col);builder(r,M,col)
        geom=[o for o in r.children if o.type in {"MESH","CURVE"}]
        rec.append({"asset_id":aid,"name_cn":cn,"category":cat,"quality_tier":"hero_v7","geometry_objects":len(geom),
          "mesh_objects":sum(o.type=="MESH" for o in geom),"curve_objects":sum(o.type=="CURVE" for o in geom),
          "reusable":True,"protected_scene_safe":True})
    assert len(rec)==20 and all(x["geometry_objects"]>=5 for x in rec)
    used=sorted({m.name for o in s.objects if getattr(o,"data",None) and hasattr(o.data,"materials") for m in o.data.materials})
    report={"scene":s.name,"pack_id":"TW_INTERIOR_CEREMONIAL_PACK_V7","asset_count":20,"assets":rec,
      "objects":len(s.objects),"mesh_objects":sum(o.type=="MESH" for o in s.objects),"curve_objects":sum(o.type=="CURVE" for o in s.objects),
      "declared_materials":len(M),"used_materials":used,"status":"hero_midpoly_reusable","protected_scenes_touched":False,
      "rebuild_contract":"deterministic_geometry_no_llm_required","blender_target":"4.2.23 LTS"}
    rep.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()))
    print("TAIWEI_INTERIOR_CEREMONIAL_V7_OK",json.dumps(report,ensure_ascii=False))

if __name__=="__main__":main()
