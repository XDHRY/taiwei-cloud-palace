"""Taiwei Cloud Palace Expansion Asset Pack V3.
Adds reusable architectural, ceremonial and roof-detail families.
"""
from __future__ import annotations
import argparse, importlib.util, json, math, sys
from pathlib import Path
import bpy

CORE_PATH=Path(__file__).with_name("generate_hero_asset_pack.py")
spec=importlib.util.spec_from_file_location("taiwei_hero_core",CORE_PATH)
core=importlib.util.module_from_spec(spec); spec.loader.exec_module(core)

ASSETS=[
 ("TW_V3_STONE_LION_MALE","御道石狮·雄","stone_sculpture"),
 ("TW_V3_STONE_LION_FEMALE","御道石狮·雌","stone_sculpture"),
 ("TW_V3_XUMI_BASE","须弥座·仰覆莲","stone_architecture"),
 ("TW_V3_DRUM_STONE","抱鼓石门枕","stone_architecture"),
 ("TW_V3_PALACE_GATE","朱漆宫门扇","door_window"),
 ("TW_V3_DOOR_STUD_PANEL","鎏金门钉板","door_window"),
 ("TW_V3_DRAGON_THRONE","云龙御座","interior_prop"),
 ("TW_V3_THRONE_FOOTSTOOL","御座踏脚","interior_prop"),
 ("TW_V3_INCENSE_TABLE","螭龙香几","interior_prop"),
 ("TW_V3_FLOOR_LAMP","落地宫灯","lighting_prop"),
 ("TW_V3_BRONZE_DING","饕餮纹铜鼎","ritual_prop"),
 ("TW_V3_BRONZE_ZUN","兽面铜尊","ritual_prop"),
 ("TW_V3_RITUAL_DRUM","宫廷建鼓","ritual_prop"),
 ("TW_V3_BRONZE_BELL","编钟单体","ritual_prop"),
 ("TW_V3_RIDGE_FINIAL","屋脊宝顶","roof_detail"),
 ("TW_V3_ROOF_BAOPING","琉璃宝瓶脊饰","roof_detail"),
 ("TW_V3_DRAGON_GARGOYLE","螭首吐水","roof_detail"),
 ("TW_V3_CLOUD_PARAPET","云纹桥栏板","stone_architecture"),
 ("TW_V3_CEILING_COFFERTILE","彩绘天花方胜格","interior_architecture"),
 ("TW_V3_DOUGONG_VARIANT","重昂斗拱变体","dougong"),
]

def args():
    tail=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="generated_assets/TaiWei_ExpansionAssetPack_V3.blend")
    p.add_argument("--report",default="generated_assets/taiwei-expansion-v3-report.json")
    return p.parse_args(tail)

def root(a,cn,cat,loc,col):
    r=bpy.data.objects.new(a,None); col.objects.link(r); r.location=loc
    r["asset_id"]=a; r["name_cn"]=cn; r["category"]=cat
    r["production_level"]="hero_midpoly"; r["quality_tier"]="hero_v3"
    r["parametric"]=True; r["reusable"]=True; r["protected_scene_safe"]=True
    r["source_style"]="historical_chinese_palace_yanyun_grounded"
    r["units"]="meters"; r["origin_policy"]="asset_root_grounded"
    return r

def lion(r,M,col,female=False):
    stone,gold=M["stone"],M["gold"]
    core.cube(r.name+"_BASE",(1.62,1.26,.34),(0,0,.17),stone,col,r,bevel=.055)

    # Seated guardian-lion proportions: tall chest, tucked haunches, compact head.
    core.sphere(r.name+"_HAUNCH",(.48,.36,.52),(-.12,0,.76),stone,col,r,30,15)
    core.sphere(r.name+"_CHEST",(.38,.31,.62),(.18,0,1.18),stone,col,r,30,15)
    core.sphere(r.name+"_HEAD",(.39,.34,.36),(.31,0,1.82),stone,col,r,30,15)
    core.sphere(r.name+"_MUZZLE",(.25,.24,.15),(.61,-.01,1.70),stone,col,r,24,12)
    core.cube(r.name+"_LOWER_JAW",(.34,.29,.085),(.61,0,1.55),stone,col,r,bevel=.035)
    core.cube(r.name+"_MOUTH_GAP",(.25,.04,.045),(.72,-.155,1.61),gold,col,r,bevel=.012)
    for sx in (-1,1):
        core.sphere(r.name+f"_FANG_{sx}",(.032,.025,.07),(.66+sx*.075,-.17,1.56),gold,col,r,12,6)

    # Brow ridge, eyes and ears replace the earlier toy-like round face.
    for sy in (-1,1):
        core.sphere(r.name+f"_EYE_{sy}",(.048,.034,.045),(.50,sy*.27,1.87),gold,col,r,16,8)
        core.cube(r.name+f"_BROW_{sy}",(.18,.045,.055),(.46,sy*.285,1.96),stone,col,r,
                  rot=(math.radians(8),0,math.radians(-10*sy)),bevel=.018)
        core.sphere(r.name+f"_EAR_{sy}",(.10,.055,.13),(.13,sy*.29,2.02),stone,col,r,18,9)
        core.tube(r.name+f"_WHISKER_{sy}",[(.62,sy*.16,1.69),(.83,sy*.27,1.61),(.96,sy*.33,1.49)],.018,gold,col,r)

    # Layered curled mane, intentionally asymmetric in height to improve silhouette.
    for ring,(rad_y,rad_z,count,scale) in enumerate(((.30,.34,12,1.0),(.24,.27,10,.82))):
        for k in range(count):
            a=math.tau*k/count
            core.sphere(r.name+f"_MANE_{ring}_{k}",
                        (.12*scale,.085*scale,.13*scale),
                        (.13-ring*.03,rad_y*math.cos(a),1.83+rad_z*math.sin(a)),
                        stone,col,r,16,8)

    # Front legs stay vertical; rear haunches are massed, giving a seated rather than puppy pose.
    for sy in (-1,1):
        core.cyl(r.name+f"_FORELEG_{sy}",.075,.76,(.30,sy*.19,.63),stone,col,r,16)
        core.sphere(r.name+f"_FOREPAW_{sy}",(.16,.12,.075),(.38,sy*.19,.25),stone,col,r,18,8)
        core.sphere(r.name+f"_HINDPAW_{sy}",(.22,.15,.10),(-.31,sy*.24,.27),stone,col,r,18,8)

    core.tube(r.name+"_TAIL",[(-.42,0,.74),(-.57,.16,1.02),(-.50,.25,1.38),(-.30,.20,1.62)],.060,stone,col,r)
    for i in range(4):
        core.sphere(r.name+f"_CHEST_CURL_{i}",(.10,.065,.11),(.16,-.31,.92+i*.18),gold,col,r,14,7)

    if female:
        core.sphere(r.name+"_CUB_BODY",(.18,.14,.17),(.40,-.34,.45),stone,col,r,20,10)
        core.sphere(r.name+"_CUB_HEAD",(.13,.11,.12),(.50,-.35,.61),stone,col,r,18,9)
        for sy in (-1,1):
            core.sphere(r.name+f"_CUB_EAR_{sy}",(.04,.025,.05),(.44,sy*.04-.35,.72),stone,col,r,12,6)
    else:
        core.sphere(r.name+"_BALL",(.24,.24,.24),(.42,-.34,.39),gold,col,r,28,14)
        for i in range(8):
            a=math.tau*i/8
            core.torus(r.name+f"_BALL_RING_{i}",.16,.014,(.42,-.34,.39),stone,col,r,16,6,rot=(0,a,0))

def xumi(r,M,col):
    stone,gold=M["stone"],M["gold"]
    core.cube(r.name+"_PLINTH",(2.70,2.15,.28),(0,0,.14),stone,col,r,bevel=.06)
    core.cube(r.name+"_LOWER",(2.35,1.82,.26),(0,0,.42),stone,col,r,bevel=.05)
    core.cube(r.name+"_WAIST",(1.92,1.46,.48),(0,0,.79),stone,col,r,bevel=.04)
    core.cube(r.name+"_UPPER",(2.28,1.78,.25),(0,0,1.16),stone,col,r,bevel=.05)
    core.cube(r.name+"_TOP",(2.58,2.02,.22),(0,0,1.40),stone,col,r,bevel=.06)
    for side in (-1,1):
        for i in range(5):
            x=-.72+i*.36
            core.sphere(r.name+f"_LOTUS_{side}_{i}",(.16,.07,.11),(x,side*.91,1.18),gold,col,r,16,7)
    for i in range(6):
        core.tube(r.name+f"_CLOUD_{i}",[(-.74+i*.30,-.75,.70),(-.60+i*.30,-.79,.86),(-.46+i*.30,-.75,.70)],.026,gold,col,r)

def drum_stone(r,M,col):
    stone,gold=M["stone"],M["gold"]
    core.cube(r.name+"_SOCKET",(1.45,.92,.34),(0,0,.17),stone,col,r,bevel=.05)
    q=core.cyl(r.name+"_DRUM",.62,.34,(0,0,1.02),stone,col,r,32,rot=(math.pi/2,0,0))
    core.torus(r.name+"_RIM",.49,.055,(0,-.18,1.02),gold,col,r,28,8,rot=(math.pi/2,0,0))
    core.sphere(r.name+"_BOSS",(.13,.05,.13),(0,-.23,1.02),gold,col,r,18,8)
    for i in range(8):
        a=math.tau*i/8
        core.sphere(r.name+f"_NAIL_{i}",(.045,.025,.045),(.45*math.cos(a),-.23,1.02+.45*math.sin(a)),gold,col,r,12,6)
    core.tube(r.name+"_CLOUD",[(-.42,-.22,.93),(-.10,-.25,1.22),(.18,-.25,.92),(.44,-.22,1.18)],.035,gold,col,r)

def gate(r,M,col):
    red,gold,wood=M["red"],M["gold"],M["wood"]
    w,h=3.0,4.4
    core.cube(r.name+"_LEAF",(w,.22,h),(0,0,h/2),red,col,r,bevel=.04)
    for x in (-w/2+.16,w/2-.16):
        core.cube(r.name+f"_SIDE_{x}",(.18,.32,h),(x,0,h/2),wood,col,r,bevel=.025)
    for z in (.18,h-.18,h*.50):
        core.cube(r.name+f"_RAIL_{z}",(w,.32,.16),(0,0,z),wood,col,r,bevel=.025)
    for row in range(7):
        for colx in range(5):
            x=-1.08+colx*.54; z=.48+row*.55
            core.sphere(r.name+f"_STUD_{row}_{colx}",(.075,.045,.075),(x,-.15,z),gold,col,r,14,7)
    core.torus(r.name+"_RING",.23,.035,(.58,-.19,2.02),gold,col,r,26,8,rot=(math.pi/2,0,0))
    core.sphere(r.name+"_KNOCKER",(.12,.055,.12),(.58,-.21,2.02),gold,col,r,16,8)

def stud_panel(r,M,col):
    red,gold=M["red"],M["gold"]
    core.cube(r.name+"_PANEL",(2.2,.18,2.2),(0,0,1.1),red,col,r,bevel=.05)
    for row in range(5):
        for cx in range(5):
            x=-.74+cx*.37; z=.36+row*.37
            core.sphere(r.name+f"_STUD_{row}_{cx}",(.085,.05,.085),(x,-.13,z),gold,col,r,16,8)
    for qx,qz in ((-.92,.18),(.92,.18),(-.92,2.02),(.92,2.02)):
        core.sphere(r.name+f"_CORNER_{qx}_{qz}",(.08,.05,.08),(qx,-.13,qz),gold,col,r,14,7)

def throne(r,M,col):
    red,gold,wood=M["red"],M["gold"],M["wood"]
    core.cube(r.name+"_SEAT",(2.35,1.42,.25),(0,0,1.18),wood,col,r,bevel=.06)
    core.cube(r.name+"_BACK",(2.25,.24,2.30),(0,.58,2.35),red,col,r,bevel=.08)
    for x in (-1.05,1.05):
        core.lathe(r.name+f"_POST_{x}",[(.12,0),(.17,.12),(.13,2.1),(.18,2.25),(.10,2.45)],(x,.52,1.10),gold,col,r,18)
    for x in (-1.28,1.28):
        core.cube(r.name+f"_ARM_{x}",(.24,1.16,.18),(x,0,1.62),gold,col,r,bevel=.04)
        core.lathe(r.name+f"_LEG_{x}",[(.10,0),(.16,.10),(.12,.90),(.17,1.02)],(x,0,.08),wood,col,r,18)
    core.tube(r.name+"_DRAGON_BODY",[(-.76,.42,2.16),(-.35,.40,2.66),(0,.39,2.36),(.34,.40,2.76),(.78,.42,2.24)],.065,gold,col,r)
    for sx in (-1,1):
        core.sphere(r.name+f"_DRAGON_HEAD_{sx}",(.16,.08,.14),(sx*.79,.40,2.24),gold,col,r,18,8)

def footstool(r,M,col):
    red,gold,wood=M["red"],M["gold"],M["wood"]
    core.cube(r.name+"_TOP",(1.65,.78,.18),(0,0,.72),red,col,r,bevel=.05)
    for x in (-.68,.68):
        core.cube(r.name+f"_LEG_{x}",(.17,.62,.72),(x,0,.34),wood,col,r,bevel=.04)
    for y in (-.27,.27):
        core.cube(r.name+f"_BRACE_{y}",(1.22,.12,.12),(0,y,.34),gold,col,r,bevel=.02)

def incense_table(r,M,col):
    wood,gold=M["wood"],M["gold"]
    core.cube(r.name+"_TOP",(1.55,1.04,.16),(0,0,1.58),wood,col,r,bevel=.08)
    for x in (-.58,.58):
        for y in (-.34,.34):
            core.lathe(r.name+f"_LEG_{x}_{y}",[(.08,0),(.12,.12),(.08,1.30),(.14,1.42)],(x,y,.08),wood,col,r,16)
    for sy in (-1,1):
        core.tube(r.name+f"_CHILONG_{sy}",[(-.58,sy*.46,1.28),(-.24,sy*.50,1.46),(.16,sy*.50,1.24),(.56,sy*.46,1.46)],.035,gold,col,r)

def floor_lamp(r,M,col):
    wood,gold,paper=M["wood"],M["gold"],M["paper"]
    core.lathe(r.name+"_BASE",[(.42,0),(.48,.10),(.31,.28),(.22,.42)],(0,0,0),wood,col,r,28)
    core.cyl(r.name+"_SHAFT",.07,2.15,(0,0,1.50),gold,col,r,16)
    core.cyl(r.name+"_LANTERN",.42,.90,(0,0,2.80),paper,col,r,6)
    for z in (2.30,3.30):
        core.cyl(r.name+f"_RIM_{z}",.48,.10,(0,0,z),wood,col,r,6)
    for i in range(6):
        a=math.tau*i/6
        core.cube(r.name+f"_FRAME_{i}",(.045,.045,.92),(.39*math.cos(a),.39*math.sin(a),2.80),gold,col,r)
    core.lathe(r.name+"_CAP",[(.20,0),(.28,.10),(.16,.26),(.07,.39)],(0,0,3.38),gold,col,r,20)

def ding(r,M,col):
    bronze,patina,gold=M["bronze"],M["patina"],M["gold"]
    core.lathe(r.name+"_BODY",[(.40,0),(.66,.18),(.78,.55),(.70,.90),(.54,1.06)],(0,0,.48),bronze,col,r,36)
    for i in range(3):
        a=math.tau*i/3
        core.cyl(r.name+f"_LEG_{i}",.10,.82,(.52*math.cos(a),.52*math.sin(a),.20),bronze,col,r,16)
    for sy in (-1,1):
        core.torus(r.name+f"_EAR_{sy}",.28,.05,(sy*.72,0,1.46),bronze,col,r,28,8,rot=(math.pi/2,0,0))
    for i in range(8):
        a=math.tau*i/8
        core.sphere(r.name+f"_TAOTIE_{i}",(.07,.035,.07),(.65*math.cos(a),-.08,.95+.10*math.sin(a)),gold,col,r,12,6)
    core.torus(r.name+"_PATINA_RING",.61,.035,(0,0,.86),patina,col,r,30,8)

def zun(r,M,col):
    bronze,patina,gold=M["bronze"],M["patina"],M["gold"]
    core.lathe(r.name+"_VESSEL",[(.28,0),(.42,.20),(.38,.64),(.52,.86),(.34,1.18),(.60,1.48)],(0,0,.10),bronze,col,r,36)
    core.torus(r.name+"_MOUTH",.56,.045,(0,0,1.58),gold,col,r,30,8)
    for sy in (-1,1):
        core.sphere(r.name+f"_MASK_{sy}",(.16,.06,.18),(sy*.30,-.37,.82),patina,col,r,18,9)
    for z in (.38,.92,1.28):
        core.torus(r.name+f"_BAND_{z}",.39 if z<1 else .43,.025,(0,0,z),gold,col,r,28,8)

def ritual_drum(r,M,col):
    red,gold,wood=M["red"],M["gold"],M["wood"]
    q=core.cyl(r.name+"_DRUM",.68,.86,(0,0,1.56),red,col,r,32,rot=(math.pi/2,0,0))
    for sy in (-1,1):
        core.torus(r.name+f"_RIM_{sy}",.62,.06,(0,sy*.46,1.56),gold,col,r,30,8,rot=(math.pi/2,0,0))
    for i in range(14):
        a=math.tau*i/14
        core.sphere(r.name+f"_NAIL_{i}",(.055,.03,.055),(.57*math.cos(a),-.46,1.56+.57*math.sin(a)),gold,col,r,12,6)
    core.cube(r.name+"_BEAM",(2.18,.18,.18),(0,0,2.50),wood,col,r,bevel=.04)
    for x in (-.92,.92):
        core.cube(r.name+f"_POST_{x}",(.20,.34,2.35),(x,0,1.30),wood,col,r,bevel=.04)
    core.cube(r.name+"_BASE",(2.38,.82,.18),(0,0,.10),wood,col,r,bevel=.05)

def bell(r,M,col):
    bronze,gold=M["bronze"],M["gold"]
    core.lathe(r.name+"_BELL",[(.12,0),(.36,.12),(.54,.45),(.66,.92),(.60,1.18)],(0,0,.32),bronze,col,r,30)
    for z in (.66,1.06,1.38):
        core.torus(r.name+f"_BAND_{z}",.58 if z<1.2 else .46,.035,(0,0,z),gold,col,r,28,8)
    for row,z in enumerate((.72,1.02)):
        for i in range(8):
            a=math.tau*i/8
            core.sphere(r.name+f"_NIPPLE_{row}_{i}",(.045,.045,.045),(.56*math.cos(a),.56*math.sin(a),z),gold,col,r,10,5)
    core.torus(r.name+"_HANGER",.16,.035,(0,0,1.74),gold,col,r,22,8,rot=(math.pi/2,0,0))

def finial(r,M,col):
    tile,gold=M["tile"],M["gold"]
    core.lathe(r.name+"_BASE",[(.72,0),(.80,.18),(.62,.34),(.48,.54)],(0,0,0),tile,col,r,36)
    for z,rad in ((.62,.42),(.84,.34),(1.08,.27),(1.31,.20)):
        core.torus(r.name+f"_RING_{z}",rad,.045,(0,0,z),gold,col,r,28,8)
    core.lathe(r.name+"_SPIRE",[(.24,0),(.18,.28),(.12,.58),(.06,.90),(.02,1.18)],(0,0,1.35),gold,col,r,28)

def baoping(r,M,col):
    tile,gold=M["tile"],M["gold"]
    core.lathe(r.name+"_BOTTLE",[(.22,0),(.42,.18),(.52,.50),(.44,.86),(.26,1.12),(.18,1.32),(.28,1.48)],(0,0,.10),tile,col,r,32)
    core.torus(r.name+"_NECK_RING",.25,.04,(0,0,1.42),gold,col,r,28,8)
    core.sphere(r.name+"_PEARL",(.14,.14,.16),(0,0,1.82),gold,col,r,20,10)
    for sy in (-1,1):
        core.tube(r.name+f"_RIBBON_{sy}",[(0,0,1.56),(sy*.32,0,1.44),(sy*.52,0,1.20)],.025,gold,col,r)

def gargoyle(r,M,col):
    stone,gold=M["stone"],M["gold"]
    core.sphere(r.name+"_HEAD",(.46,.36,.34),(0,0,.78),stone,col,r,28,14)
    core.sphere(r.name+"_SNOUT",(.34,.26,.20),(.38,0,.69),stone,col,r,22,10)
    core.cube(r.name+"_MOUTH",(.40,.26,.09),(.50,0,.57),gold,col,r,bevel=.04)
    for sy in (-1,1):
        core.sphere(r.name+f"_EYE_{sy}",(.065,.045,.065),(.18,sy*.30,.87),gold,col,r,16,8)
        core.tube(r.name+f"_HORN_{sy}",[(0,sy*.22,1.00),(-.18,sy*.34,1.24),(-.34,sy*.36,1.32)],.035,stone,col,r)
    core.cyl(r.name+"_SPOUT",.12,.78,(.72,0,.58),stone,col,r,18,rot=(0,math.pi/2,0))

def parapet(r,M,col):
    stone,gold=M["stone"],M["gold"]
    core.cube(r.name+"_BASE",(4.8,.38,.24),(0,0,.12),stone,col,r,bevel=.04)
    core.cube(r.name+"_TOP",(4.8,.32,.22),(0,0,1.54),stone,col,r,bevel=.05)
    for i in range(7):
        x=-2.10+i*.70
        core.lathe(r.name+f"_POST_{i}",[(.11,0),(.17,.10),(.12,.90),(.18,1.08)],(x,0,.28),stone,col,r,18)
    for i in range(6):
        x=-1.75+i*.70
        core.cube(r.name+f"_PANEL_{i}",(.58,.18,.66),(x,0,.92),stone,col,r,bevel=.035)
        core.tube(r.name+f"_CLOUD_{i}",[(x-.22,-.11,.86),(x-.08,-.12,1.10),(x+.10,-.12,.88),(x+.24,-.11,1.06)],.026,gold,col,r)

def ceiling_tile(r,M,col):
    wood,gold,blue,red=M["wood"],M["gold"],M["blue"],M["red"]
    core.cube(r.name+"_FRAME",(3.1,3.1,.16),(0,0,.08),wood,col,r,bevel=.05)
    core.cube(r.name+"_FIELD",(2.76,2.76,.10),(0,0,.12),blue,col,r,bevel=.03)
    for a in (math.pi/4,-math.pi/4):
        core.cube(r.name+f"_DIAG_{a}",(3.10,.12,.08),(0,0,.19),gold,col,r,rot=(0,0,a),bevel=.01)
    for x in (-.92,0,.92):
        core.cube(r.name+f"_V_{x}",(.08,2.76,.07),(x,0,.20),gold,col,r)
    for y in (-.92,0,.92):
        core.cube(r.name+f"_H_{y}",(2.76,.08,.07),(0,y,.20),gold,col,r)
    core.torus(r.name+"_CENTER",.48,.065,(0,0,.24),red,col,r,32,8)
    for i in range(12):
        a=math.tau*i/12
        core.petallike if False else None
        core.sphere(r.name+f"_PETAL_{i}",(.16,.07,.08),(.54*math.cos(a),.54*math.sin(a),.27),gold,col,r,16,7)

def dougong_variant(r,M,col):
    red,gold=M["red"],M["gold"]
    for lv in range(5):
        z=.26+lv*.29; span=1.10+lv*.34
        core.cube(r.name+f"_GONG_{lv}",(span,.34,.16),(0,0,z),red,col,r,bevel=.022)
        for sx in (-1,1):
            core.cyl(r.name+f"_DOU_{lv}_{sx}",.15,.16,(sx*span*.32,0,z+.17),gold,col,r,14)
    for sx in (-1,1):
        for k,ang in enumerate((18,32)):
            core.cube(r.name+f"_ANG_{sx}_{k}",(1.10,.22,.16),(sx*(.32+k*.17),.04,1.40+k*.22),gold,col,r,rot=(0,math.radians(-ang*sx),0),bevel=.018)
    core.cube(r.name+"_CAP",(2.65,.48,.24),(0,0,1.95),red,col,r,bevel=.03)
    core.cube(r.name+"_BASE",(1.22,.58,.30),(0,0,.12),red,col,r,bevel=.03)

BUILDERS=[
 lambda r,M,c:lion(r,M,c,False),
 lambda r,M,c:lion(r,M,c,True),
 xumi,drum_stone,gate,stud_panel,throne,footstool,incense_table,floor_lamp,
 ding,zun,ritual_drum,bell,finial,baoping,gargoyle,parapet,ceiling_tile,dougong_variant
]

def main():
    a=args(); out=Path(a.output); rep=Path(a.report)
    out.parent.mkdir(parents=True,exist_ok=True); rep.parent.mkdir(parents=True,exist_ok=True)
    s=core.reset_scene(); s.name="TaiWei_Expansion_AssetPack_V3"
    col=bpy.data.collections.new("TaiWei_Expansion_Modules_V3"); s.collection.children.link(col)
    M={
      "red":core.mat("TW3_MAT_Cinnabar_Lacquer",(.31,.025,.014),.32),
      "gold":core.mat("TW3_MAT_Aged_Gilt",(.50,.24,.040),.28,.78),
      "tile":core.mat("TW3_MAT_Deep_Glazed_Tile",(.025,.040,.048),.26,.08),
      "stone":core.mat("TW3_MAT_Weathered_WhiteStone",(.61,.63,.58),.50),
      "paper":core.mat("TW3_MAT_Warm_Paper",(.73,.15,.028),.50,0,((1.0,.17,.03),1.6)),
      "bronze":core.mat("TW3_MAT_Ritual_Bronze",(.12,.052,.018),.34,.80),
      "patina":core.mat("TW3_MAT_Patina",(.030,.145,.105),.56,.54),
      "wood":core.mat("TW3_MAT_Rosewood",(.095,.022,.012),.40),
      "blue":core.mat("TW3_MAT_Mineral_Blue",(.030,.095,.20),.38),
    }
    rec=[]; cols=5
    for i,((aid,cn,cat),builder) in enumerate(zip(ASSETS,BUILDERS)):
        x=(i%cols-(cols-1)/2)*7.2; y=(i//cols-1.5)*7.0
        r=root(aid,cn,cat,(x,y,0),col); builder(r,M,col)
        geom=[o for o in r.children if o.type in {"MESH","CURVE"}]
        rec.append({"asset_id":aid,"name_cn":cn,"category":cat,"quality_tier":"hero_v3",
                    "geometry_objects":len(geom),
                    "mesh_objects":sum(o.type=="MESH" for o in geom),
                    "curve_objects":sum(o.type=="CURVE" for o in geom),
                    "reusable":True,"protected_scene_safe":True})
    assert len(rec)==20 and all(x["geometry_objects"]>=5 for x in rec)
    used=sorted({m.name for o in s.objects if getattr(o,"data",None) and hasattr(o.data,"materials") for m in o.data.materials})
    report={"scene":s.name,"pack_id":"TW_EXPANSION_ASSET_PACK_V3","asset_count":20,"assets":rec,
            "objects":len(s.objects),"mesh_objects":sum(o.type=="MESH" for o in s.objects),
            "curve_objects":sum(o.type=="CURVE" for o in s.objects),"declared_materials":len(M),
            "used_materials":used,"status":"hero_midpoly_reusable","protected_scenes_touched":False,
            "rebuild_contract":"deterministic_geometry_no_llm_required","blender_target":"4.2.23 LTS"}
    rep.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()))
    print("TAIWEI_EXPANSION_V3_OK",json.dumps(report,ensure_ascii=False))

if __name__=="__main__":
    main()
