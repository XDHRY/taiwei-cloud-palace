"""Taiwei Cloud Palace Site & Garden Asset Pack V4.
High-leverage reusable environment modules for palace terraces, walls, bridges,
paving, drainage and garden dressing.
"""
from __future__ import annotations
import argparse, importlib.util, json, math, sys
from pathlib import Path
import bpy

CORE=Path(__file__).with_name("generate_hero_asset_pack.py")
spec=importlib.util.spec_from_file_location("taiwei_core",CORE)
core=importlib.util.module_from_spec(spec); spec.loader.exec_module(core)

ASSETS=[
 ("TW_V4_TERRACE_STEPS","白石五级踏步","stone_architecture"),
 ("TW_V4_IMPERIAL_RAMP","云龙御路斜坡","stone_architecture"),
 ("TW_V4_TERRACE_CORNER","台基转角","stone_architecture"),
 ("TW_V4_BALUSTRADE_STRAIGHT","望柱栏杆直段","stone_architecture"),
 ("TW_V4_BALUSTRADE_CORNER","望柱栏杆转角","stone_architecture"),
 ("TW_V4_ARCH_BRIDGE","单孔拱桥模块","bridge"),
 ("TW_V4_MOON_GATE","月洞门墙段","wall_gate"),
 ("TW_V4_WHITE_WALL","粉墙黛瓦直段","wall_gate"),
 ("TW_V4_SCREEN_WALL","琉璃影壁","wall_gate"),
 ("TW_V4_GATE_FRAME","宫墙门框","wall_gate"),
 ("TW_V4_STONE_BASIN","莲纹石水盆","garden_prop"),
 ("TW_V4_BRONZE_VAT","鎏金铜缸","garden_prop"),
 ("TW_V4_LOTUS_PLANTER","莲纹圆花盆","garden_prop"),
 ("TW_V4_TREE_PLANTER","方形海棠花台","garden_prop"),
 ("TW_V4_TAIHU_ROCK","太湖石单体","rockery"),
 ("TW_V4_ROCKERY_CLUSTER","叠石假山簇","rockery"),
 ("TW_V4_STONE_LANTERN","石灯笼","garden_prop"),
 ("TW_V4_PAVING_SET","御道铺地组合","ground_detail"),
 ("TW_V4_DRAIN_CHANNEL","青石排水明沟","ground_detail"),
 ("TW_V4_BEAST_SCUPPER","螭首散水","ground_detail"),
]

def args():
    tail=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="generated_assets/TaiWei_SiteGardenPack_V4.blend")
    p.add_argument("--report",default="generated_assets/taiwei-site-garden-v4-report.json")
    return p.parse_args(tail)

def root(a,cn,cat,loc,col):
    r=bpy.data.objects.new(a,None); col.objects.link(r); r.location=loc
    for k,v in {
      "asset_id":a,"name_cn":cn,"category":cat,"production_level":"hero_midpoly",
      "quality_tier":"hero_v4","parametric":True,"reusable":True,
      "protected_scene_safe":True,"source_style":"historical_chinese_palace_yanyun_grounded",
      "units":"meters","origin_policy":"asset_root_grounded"}.items(): r[k]=v
    return r

def cloud_line(name,x0,y,z,w,M,col,r):
    return core.tube(name,[(x0-w*.5,y,z),(x0-w*.25,y,z+.14),(x0,y,z-.02),(x0+w*.25,y,z+.16),(x0+w*.5,y,z)],.025,M["gold"],col,r)

def steps(r,M,col):
    s=M["stone"]
    for i in range(5):
        core.cube(r.name+f"_STEP_{i}",(3.4,1.10+i*.42,.18),(0,-i*.21,.09+i*.18),s,col,r,bevel=.025)
    for x in (-1.78,1.78):
        core.cube(r.name+f"_SIDE_{x}",(.20,2.82,1.05),(x,-.45,.52),s,col,r,rot=(math.radians(-16),0,0),bevel=.04)
    for i in range(3):
        cloud_line(r.name+f"_SIDE_CLOUD_{i}",0,-1.48,.36+i*.18,1.5,M,col,r)

def imperial_ramp(r,M,col):
    s,g=M["stone"],M["gold"]
    core.cube(r.name+"_SLAB",(3.05,4.20,.22),(0,0,.42),s,col,r,rot=(math.radians(10),0,0),bevel=.04)
    core.cube(r.name+"_BORDER_L",(.18,4.30,.18),(-1.52,0,.55),g,col,r,rot=(math.radians(10),0,0),bevel=.03)
    core.cube(r.name+"_BORDER_R",(.18,4.30,.18),(1.52,0,.55),g,col,r,rot=(math.radians(10),0,0),bevel=.03)
    core.tube(r.name+"_DRAGON_SPINE",[(0,-1.55,.20),(-.38,-.85,.42),(.28,-.15,.48),(-.30,.65,.62),(0,1.55,.78)],.085,g,col,r)
    for i,y in enumerate((-1.20,-.55,.10,.75,1.40)):
        for sx in (-1,1):
            core.sphere(r.name+f"_CLOUD_{i}_{sx}",(.20,.08,.09),(sx*.62,y,.40+y*.10),g,col,r,16,7)

def terrace_corner(r,M,col):
    s,g=M["stone"],M["gold"]
    core.cube(r.name+"_PLATFORM",(3.0,3.0,.46),(0,0,.23),s,col,r,bevel=.05)
    core.cube(r.name+"_CAP_X",(3.2,.30,.22),(0,-1.42,.61),s,col,r,bevel=.04)
    core.cube(r.name+"_CAP_Y",(.30,3.2,.22),(-1.42,0,.61),s,col,r,bevel=.04)
    for x,y in ((-1.42,-1.42),(-.72,-1.42),(0,-1.42),(.72,-1.42),(-1.42,-.72),(-1.42,0),(-1.42,.72)):
        core.sphere(r.name+f"_BOSS_{x}_{y}",(.07,.07,.07),(x,y,.53),g,col,r,12,6)

def balustrade(r,M,col,corner=False):
    s,g=M["stone"],M["gold"]
    core.cube(r.name+"_BASE",(4.6,.42,.24),(0,0,.12),s,col,r,bevel=.04)
    core.cube(r.name+"_TOP",(4.6,.34,.22),(0,0,1.55),s,col,r,bevel=.05)
    for i in range(7):
        x=-2.10+i*.70
        core.lathe(r.name+f"_POST_{i}",[(.11,0),(.17,.10),(.12,.92),(.18,1.08)],(x,0,.28),s,col,r,18)
    for i in range(6):
        x=-1.75+i*.70
        core.cube(r.name+f"_PANEL_{i}",(.56,.18,.64),(x,0,.92),s,col,r,bevel=.035)
        cloud_line(r.name+f"_CLOUD_{i}",x,-.11,.90,.44,M,col,r)
    if corner:
        core.cube(r.name+"_BASE_Y",(.42,3.1,.24),(-2.10,1.34,.12),s,col,r,bevel=.04)
        core.cube(r.name+"_TOP_Y",(.34,3.1,.22),(-2.10,1.34,1.55),s,col,r,bevel=.05)
        for j in range(1,5):
            y=j*.64
            core.lathe(r.name+f"_YPOST_{j}",[(.11,0),(.17,.10),(.12,.92),(.18,1.08)],(-2.10,y,.28),s,col,r,18)

def bridge(r,M,col):
    s,g=M["stone"],M["gold"]
    # True single-span semicircular arch: voussoir blocks carry the deck,
    # rather than the previous row of isolated rectangular piers.
    arch_r=1.56
    arch_center_z=.40
    for side_x in (-2.48,2.48):
        core.cube(r.name+f"_ABUTMENT_{side_x}",(.92,2.08,1.72),(side_x,0,.86),s,col,r,bevel=.045)

    for i in range(15):
        a=math.pi*i/14
        x=arch_r*math.cos(a)
        z=arch_center_z+arch_r*math.sin(a)
        # Wedge-like blocks approximated by narrow beveled ashlar units aligned to the arch tangent.
        core.cube(r.name+f"_VOUSSOIR_{i}",(.38,2.06,.34),(x,0,z),s,col,r,
                  rot=(0,-(a-math.pi/2),0),bevel=.025)

    core.cube(r.name+"_DECK",(5.95,2.30,.30),(0,0,2.12),s,col,r,bevel=.05)
    core.cube(r.name+"_SPANDREL_L",(1.08,2.05,.62),(-2.02,0,1.68),s,col,r,bevel=.035)
    core.cube(r.name+"_SPANDREL_R",(1.08,2.05,.62),(2.02,0,1.68),s,col,r,bevel=.035)

    for sy in (-1,1):
        core.cube(r.name+f"_RAIL_{sy}",(5.95,.22,.22),(0,sy*1.04,2.93),s,col,r,bevel=.04)
        for i in range(9):
            x=-2.60+i*.65
            core.lathe(r.name+f"_POST_{sy}_{i}",
                       [(.07,0),(.11,.07),(.075,.58),(.12,.68)],
                       (x,sy*1.04,2.32),s,col,r,14)
        # Front/back arch accent follows the actual masonry curvature.
        pts=[]
        for j in range(13):
            a=math.pi*j/12
            pts.append((arch_r*math.cos(a),sy*1.08,arch_center_z+arch_r*math.sin(a)))
        core.tube(r.name+f"_ARCH_TRIM_{sy}",pts,.036,g,col,r)

def moon_gate(r,M,col):
    wall,tile,g,s=M["wall"],M["tile"],M["gold"],M["stone"]
    # Opening diameter ~= 2.84 m. Side walls begin outside the circular reveal.
    core.cube(r.name+"_LEFT",(1.18,.46,3.55),(-2.08,0,1.78),wall,col,r,bevel=.025)
    core.cube(r.name+"_RIGHT",(1.18,.46,3.55),(2.08,0,1.78),wall,col,r,bevel=.025)
    core.cube(r.name+"_TOP",(5.34,.46,.64),(0,0,3.30),wall,col,r,bevel=.025)

    # Continuous circular reveal instead of visibly segmented floating blocks.
    core.torus(r.name+"_STONE_REVEAL",1.43,.105,(0,-.015,1.62),s,col,r,48,12,
               rot=(math.pi/2,0,0))
    core.torus(r.name+"_GILT_INNER_LINE",1.30,.026,(0,-.135,1.62),g,col,r,48,8,
               rot=(math.pi/2,0,0))

    # Small springing stones visually tie the ring back into the wall.
    for sx in (-1,1):
        core.cube(r.name+f"_SPRINGER_{sx}",(.34,.52,.38),(sx*1.43,0,1.62),s,col,r,
                  rot=(0,0,math.radians(45*sx)),bevel=.035)

    for i in range(12):
        x=-2.53+i*.46
        rise=.025*(1-(abs(i-5.5)/5.5))
        core.cube(r.name+f"_CAP_TILE_{i}",(.49,.68,.13),(x,0,3.66+rise),tile,col,r,
                  rot=(0,math.radians((i-5.5)*.6),0),bevel=.022)

def white_wall(r,M,col):
    wall,tile=M["wall"],M["tile"]
    core.cube(r.name+"_WALL",(5.2,.40,3.0),(0,0,1.5),wall,col,r,bevel=.02)
    core.cube(r.name+"_PLINTH",(5.35,.52,.32),(0,0,.16),M["stone"],col,r,bevel=.03)
    for i in range(12):
        x=-2.53+i*.46
        core.cube(r.name+f"_CAP_{i}",(.49,.66,.13),(x,0,3.08),tile,col,r,rot=(0,math.radians((i-5.5)*.5),0),bevel=.02)
    for x in (-2.52,2.52):
        core.cube(r.name+f"_END_{x}",(.16,.54,3.18),(x,0,1.59),M["stone"],col,r,bevel=.025)

def screen_wall(r,M,col):
    wall,tile,g,red=M["wall"],M["tile"],M["gold"],M["red"]
    core.cube(r.name+"_BODY",(5.0,.48,3.2),(0,0,1.75),wall,col,r,bevel=.04)
    core.cube(r.name+"_PLINTH",(5.45,.72,.45),(0,0,.23),M["stone"],col,r,bevel=.05)
    core.cube(r.name+"_FRAME",(4.25,.10,2.10),(0,-.30,1.88),red,col,r,bevel=.04)
    core.cube(r.name+"_FIELD",(3.92,.08,1.78),(0,-.37,1.88),M["blue"],col,r,bevel=.025)
    core.tube(r.name+"_DRAGON",[(-1.38,-.43,1.78),(-.72,-.45,2.28),(-.10,-.45,1.78),(.65,-.45,2.36),(1.35,-.43,1.82)],.065,g,col,r)
    for i in range(12):
        x=-2.53+i*.46
        core.cube(r.name+f"_CAP_{i}",(.49,.70,.13),(x,0,3.46),tile,col,r,bevel=.02)

def gate_frame(r,M,col):
    red,g,tile=M["red"],M["gold"],M["tile"]
    for x in (-1.55,1.55):
        core.cube(r.name+f"_POST_{x}",(.42,.52,4.0),(x,0,2.0),red,col,r,bevel=.05)
        core.lathe(r.name+f"_BASE_{x}",[(.27,0),(.34,.10),(.28,.28)],(x,0,0),g,col,r,20)
    core.cube(r.name+"_LINTEL",(3.65,.56,.44),(0,0,3.74),red,col,r,bevel=.05)
    core.cube(r.name+"_TRANSOM",(3.9,.62,.22),(0,0,4.10),g,col,r,bevel=.035)
    for i in range(8):
        x=-1.65+i*.47
        core.cube(r.name+f"_TILE_{i}",(.50,.70,.14),(x,0,4.34),tile,col,r,bevel=.025)

def basin(r,M,col):
    s,g=M["stone"],M["gold"]
    core.lathe(r.name+"_BASIN",[(.55,0),(.72,.16),(.82,.38),(.76,.62),(.62,.78)],(0,0,0),s,col,r,36)
    core.torus(r.name+"_RIM",.72,.055,(0,0,.82),g,col,r,32,8)
    for i in range(12):
        a=math.tau*i/12
        core.sphere(r.name+f"_LOTUS_{i}",(.13,.07,.07),(.64*math.cos(a),.64*math.sin(a),.52),g,col,r,16,7)

def bronze_vat(r,M,col):
    b,p,g=M["bronze"],M["patina"],M["gold"]
    core.lathe(r.name+"_VAT",[(.58,0),(.86,.18),(1.0,.56),(.94,1.02),(.78,1.22)],(0,0,.12),b,col,r,40)
    core.torus(r.name+"_RIM",.91,.06,(0,0,1.34),g,col,r,34,8)
    for sy in (-1,1):
        core.torus(r.name+f"_HANDLE_{sy}",.26,.045,(sy*.95,0,.82),b,col,r,26,8,rot=(math.pi/2,0,0))
    for z in (.46,.90):
        core.torus(r.name+f"_PATINA_{z}",.87 if z<.7 else .91,.028,(0,0,z),p,col,r,30,8)

def round_planter(r,M,col):
    s,g=M["stone"],M["gold"]
    core.lathe(r.name+"_POT",[(.44,0),(.62,.10),(.72,.42),(.66,.82),(.76,.98)],(0,0,.08),s,col,r,32)
    core.torus(r.name+"_RIM",.72,.05,(0,0,1.08),g,col,r,30,8)
    for i in range(12):
        a=math.tau*i/12
        core.sphere(r.name+f"_PETAL_{i}",(.12,.055,.075),(.62*math.cos(a),.62*math.sin(a),.62),g,col,r,14,7)

def square_planter(r,M,col):
    s,g=M["stone"],M["gold"]
    core.cube(r.name+"_BODY",(1.6,1.6,.82),(0,0,.48),s,col,r,bevel=.08)
    core.cube(r.name+"_RIM",(1.82,1.82,.18),(0,0,.98),g,col,r,bevel=.06)
    for side in (-1,1):
        for i in range(3):
            x=-.45+i*.45
            core.sphere(r.name+f"_FLOWER_X_{side}_{i}",(.10,.05,.10),(x,side*.82,.56),g,col,r,14,7)
            core.sphere(r.name+f"_FLOWER_Y_{side}_{i}",(.10,.05,.10),(side*.82,x,.56),g,col,r,14,7)

def rock_piece(name,loc,scale,M,col,r,seed=0):
    x,y,z=scale
    o=core.sphere(name,(x,y,z),loc,M["rock"],col,r,28,15)
    # Deterministic multi-frequency erosion. This keeps CI reproducible while
    # breaking the smooth "stacked potatoes" silhouette of ordinary UV spheres.
    for idx,v in enumerate(o.data.vertices):
        px,py,pz=v.co.x,v.co.y,v.co.z
        f=(1.0
           +.18*math.sin((px*3.7+py*5.1+pz*2.9)*2.2+seed*1.37)
           +.09*math.sin((px*7.3-py*4.2+pz*6.1)*2.8+seed*.73)
           +.05*math.cos((px-py+pz)*13.0+idx*.17))
        f=max(.70,min(1.30,f))
        v.co.x*=f*(1.0+.05*math.sin(pz*8+seed))
        v.co.y*=f*(1.0+.04*math.cos(px*9+seed*.5))
        v.co.z*=f
    for p in o.data.polygons: p.use_smooth=True
    o.rotation_euler=(math.radians((seed*7)%23-11),
                      math.radians((seed*11)%31-15),
                      math.radians((seed*13)%37-18))
    return o

def taihu(r,M,col):
    masses=[
      ((0,0,.58),(.58,.40,.74)),((-.22,.03,1.16),(.43,.31,.62)),
      ((.18,-.04,1.66),(.36,.28,.58)),((-.15,.03,2.12),(.28,.22,.48)),
      ((.22,.00,2.52),(.20,.18,.34)),((.34,.02,1.12),(.22,.18,.36))
    ]
    for i,(loc,sc) in enumerate(masses):
        rock_piece(r.name+f"_MASS_{i}",loc,sc,M,col,r,i+1)
    # Shallow dark recess discs read as erosion holes at scene distance
    # without the debug-like silhouette of explicit torus rings.
    for i,(x,z,rad) in enumerate(((-.16,.92,.14),(.16,1.43,.12),(-.04,1.88,.105),(.18,2.20,.075))):
        core.cyl(r.name+f"_EROSION_RECESS_{i}",rad,.028,(x,-.355,z),M["dark"],col,r,24,
                 rot=(math.pi/2,0,0))
    core.cube(r.name+"_BASE",(1.38,.96,.18),(0,0,.09),M["stone"],col,r,bevel=.05)

def rockery(r,M,col):
    masses=[
      ((-.92,.10,.42),(.72,.50,.58)),((-.38,-.10,.70),(.58,.42,.90)),
      ((.24,.10,.54),(.76,.48,.72)),((.86,-.05,.38),(.54,.38,.50)),
      ((.02,.08,1.33),(.44,.31,.72)),((-.54,.02,1.47),(.36,.27,.58)),
      ((.52,-.04,1.20),(.33,.25,.52)),((-.06,0,1.91),(.28,.21,.45)),
      ((.28,.03,2.24),(.18,.16,.31)),((-.80,.02,1.02),(.28,.22,.38))
    ]
    for i,(loc,sc) in enumerate(masses):
        rock_piece(r.name+f"_ROCK_{i}",loc,sc,M,col,r,i+11)
    # Add a few exposed ledges to create readable stratification.
    for i,(x,z,w) in enumerate(((-.55,.82,.72),(.18,1.05,.82),(-.12,1.58,.62))):
        core.cube(r.name+f"_LEDGE_{i}",(w,.64,.12),(x,-.02,z),M["rock"],col,r,
                  rot=(math.radians((i-1)*5),math.radians((i%2)*7-3),math.radians((i-1)*6)),
                  bevel=.05)
    core.cube(r.name+"_GROUND",(3.0,1.9,.14),(0,0,.07),M["stone"],col,r,bevel=.08)

def stone_lantern(r,M,col):
    s=M["stone"]
    core.lathe(r.name+"_BASE",[(.40,0),(.48,.10),(.34,.28),(.28,.40)],(0,0,0),s,col,r,24)
    core.cyl(r.name+"_SHAFT",.16,1.10,(0,0,.95),s,col,r,12)
    core.cube(r.name+"_BOX",(.76,.76,.62),(0,0,1.72),s,col,r,bevel=.05)
    for axis,sign in ((0,-1),(0,1),(1,-1),(1,1)):
        loc=[0,0,1.72]; loc[axis]=sign*.39
        core.cube(r.name+f"_WINDOW_{axis}_{sign}",(.28,.06,.30) if axis==1 else (.06,.28,.30),tuple(loc),M["dark"],col,r,bevel=.02)
    core.lathe(r.name+"_ROOF",[(.62,0),(.58,.12),(.38,.34),(.16,.52)],(0,0,2.06),s,col,r,20)
    core.sphere(r.name+"_FINIAL",(.10,.10,.16),(0,0,2.70),s,col,r,16,8)

def paving(r,M,col):
    s,g=M["stone"],M["dark"]
    idx=0
    for row in range(4):
        for c in range(5):
            x=-1.6+c*.8+(row%2)*.18; y=-1.15+row*.76
            core.cube(r.name+f"_PAVER_{idx}",(.74,.70,.09),(x,y,.045),s,col,r,bevel=.015); idx+=1
    for i in range(6):
        a=math.tau*i/6
        core.cube(r.name+f"_CENTER_PATTERN_{i}",(.54,.09,.06),(.1*math.cos(a),.1*math.sin(a),.11),g,col,r,rot=(0,0,a),bevel=.01)

def drain_channel(r,M,col):
    s,g=M["stone"],M["dark"]
    core.cube(r.name+"_BED",(4.6,1.0,.18),(0,0,.09),s,col,r,bevel=.025)
    core.cube(r.name+"_CHANNEL",(4.35,.40,.08),(0,0,.19),g,col,r,bevel=.02)
    for i in range(11):
        x=-2.0+i*.40
        core.cube(r.name+f"_GRATE_{i}",(.10,.82,.09),(x,0,.26),s,col,r,bevel=.012)
    for sy in (-1,1):
        core.cube(r.name+f"_EDGE_{sy}",(4.6,.18,.20),(0,sy*.48,.24),s,col,r,bevel=.02)

def scupper(r,M,col):
    s,g=M["stone"],M["gold"]
    core.sphere(r.name+"_HEAD",(.42,.32,.34),(0,0,.72),s,col,r,26,13)
    core.sphere(r.name+"_SNOUT",(.30,.25,.18),(.37,0,.62),s,col,r,22,10)
    core.cyl(r.name+"_SPOUT",.11,.90,(.78,0,.55),s,col,r,18,rot=(0,math.pi/2,0))
    for sy in (-1,1):
        core.sphere(r.name+f"_EYE_{sy}",(.06,.04,.06),(.18,sy*.26,.83),g,col,r,14,7)
        core.tube(r.name+f"_HORN_{sy}",[(0,sy*.18,.96),(-.16,sy*.28,1.14),(-.32,sy*.30,1.20)],.03,s,col,r)
    core.cube(r.name+"_MOUNT",(1.0,.80,.24),(-.25,0,.18),s,col,r,bevel=.04)

BUILDERS=[
 steps,imperial_ramp,terrace_corner,
 lambda r,M,c:balustrade(r,M,c,False),
 lambda r,M,c:balustrade(r,M,c,True),
 bridge,moon_gate,white_wall,screen_wall,gate_frame,basin,bronze_vat,round_planter,
 square_planter,taihu,rockery,stone_lantern,paving,drain_channel,scupper
]

def main():
    a=args(); out=Path(a.output); rep=Path(a.report)
    out.parent.mkdir(parents=True,exist_ok=True); rep.parent.mkdir(parents=True,exist_ok=True)
    s=core.reset_scene(); s.name="TaiWei_SiteGarden_AssetPack_V4"
    col=bpy.data.collections.new("TaiWei_SiteGarden_Modules_V4"); s.collection.children.link(col)
    M={
      "stone":core.mat("TW4_MAT_Weathered_WhiteStone",(.60,.62,.58),.53),
      "gold":core.mat("TW4_MAT_Aged_Gilt",(.48,.22,.038),.30,.74),
      "tile":core.mat("TW4_MAT_Black_Tile",(.023,.036,.042),.30,.08),
      "wall":core.mat("TW4_MAT_Lime_Plaster",(.73,.72,.66),.72),
      "red":core.mat("TW4_MAT_Cinnabar",(.30,.024,.014),.34),
      "blue":core.mat("TW4_MAT_Mineral_Blue",(.030,.090,.19),.40),
      "bronze":core.mat("TW4_MAT_Bronze",(.115,.050,.017),.37,.78),
      "patina":core.mat("TW4_MAT_Patina",(.030,.14,.10),.58,.52),
      "rock":core.mat("TW4_MAT_Taihu_Rock",(.33,.34,.31),.70),
      "dark":core.mat("TW4_MAT_Recess",(.018,.022,.024),.85),
    }
    rec=[]; cols=5
    for i,((aid,cn,cat),builder) in enumerate(zip(ASSETS,BUILDERS)):
        x=(i%cols-(cols-1)/2)*7.4; y=(i//cols-1.5)*7.2
        r=root(aid,cn,cat,(x,y,0),col); builder(r,M,col)
        geom=[o for o in r.children if o.type in {"MESH","CURVE"}]
        rec.append({"asset_id":aid,"name_cn":cn,"category":cat,"quality_tier":"hero_v4",
                    "geometry_objects":len(geom),"mesh_objects":sum(o.type=="MESH" for o in geom),
                    "curve_objects":sum(o.type=="CURVE" for o in geom),
                    "reusable":True,"protected_scene_safe":True})
    assert len(rec)==20 and all(x["geometry_objects"]>=5 for x in rec)
    used=sorted({m.name for o in s.objects if getattr(o,"data",None) and hasattr(o.data,"materials") for m in o.data.materials})
    report={"scene":s.name,"pack_id":"TW_SITE_GARDEN_PACK_V4","asset_count":20,"assets":rec,
            "objects":len(s.objects),"mesh_objects":sum(o.type=="MESH" for o in s.objects),
            "curve_objects":sum(o.type=="CURVE" for o in s.objects),"declared_materials":len(M),
            "used_materials":used,"status":"hero_midpoly_reusable","protected_scenes_touched":False,
            "rebuild_contract":"deterministic_geometry_no_llm_required","blender_target":"4.2.23 LTS"}
    rep.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()))
    print("TAIWEI_SITE_GARDEN_V4_OK",json.dumps(report,ensure_ascii=False))

if __name__=="__main__":
    main()
