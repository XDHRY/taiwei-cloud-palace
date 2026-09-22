"""Standalone Taiwei palace ornament asset factory for Blender 4.2+."""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path
import bpy

ASSETS=[
 ("TW_DG_BRACKET_01","单翘斗拱模块","dougong"),
 ("TW_DG_CORNER_01","转角铺作模块","dougong_corner"),
 ("TW_RIDGE_CHIWEN_01","鸱吻轮廓模块","ridge_ornament"),
 ("TW_RIDGE_BEASTS_01","走兽脊列模块","ridge_ornament"),
 ("TW_BALUSTRADE_01","白石栏杆模块","stone_architecture"),
 ("TW_PALACE_LANTERN_01","宫灯模块","lighting_prop"),
 ("TW_CENSER_01","青铜香炉模块","ritual_prop"),
 ("TW_PLAQUE_01","宫殿匾额模块","signage"),
]

def args():
    v=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser(); p.add_argument("--output",default="generated_assets/TaiWei_OrnamentPack.blend"); p.add_argument("--report",default="generated_assets/taiwei-ornament-report.json"); return p.parse_args(v)

def reset():
    s=bpy.context.scene
    for o in list(s.objects): bpy.data.objects.remove(o,do_unlink=True)
    for c in list(bpy.data.collections):
        if c.name!=s.collection.name: bpy.data.collections.remove(c)
    s.name="TaiWei_Ornament_AssetPack"; return s

def mat(name,c,r=.6,m=0,e=None):
    x=bpy.data.materials.new(name); x.use_nodes=True
    p=next(n for n in x.node_tree.nodes if n.type=="BSDF_PRINCIPLED")
    p.inputs["Base Color"].default_value=(*c,1); p.inputs["Roughness"].default_value=r; p.inputs["Metallic"].default_value=m
    if e: p.inputs["Emission Color"].default_value=(*e[0],1); p.inputs["Emission Strength"].default_value=e[1]
    return x

def cube(name,size):
    x,y,z=(q/2 for q in size)
    v=[(-x,-y,-z),(-x,-y,z),(-x,y,-z),(-x,y,z),(x,-y,-z),(x,-y,z),(x,y,-z),(x,y,z)]
    f=[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]
    me=bpy.data.meshes.new(name+"_Mesh"); me.from_pydata(v,[],f); me.update(); return me

def box(name,size,loc,ma,col,parent=None,rot=(0,0,0),bev=0):
    o=bpy.data.objects.new(name,cube(name,size)); col.objects.link(o); o.location=loc; o.rotation_euler=rot; o.data.materials.append(ma)
    if parent: o.parent=parent
    if bev:
        q=o.modifiers.new("EdgeSoftening","BEVEL"); q.width=bev; q.segments=2
    return o

def cyl(name,rad,h,loc,ma,col,parent=None,sides=20):
    v=[]; f=[]
    for z in (-h/2,h/2):
        for i in range(sides):
            a=math.tau*i/sides; v.append((rad*math.cos(a),rad*math.sin(a),z))
    for i in range(sides):
        n=(i+1)%sides; f.append((i,n,sides+n,sides+i))
    f += [tuple(reversed(range(sides))),tuple(range(sides,2*sides))]
    me=bpy.data.meshes.new(name+"_Mesh"); me.from_pydata(v,[],f); me.update()
    o=bpy.data.objects.new(name,me); col.objects.link(o); o.location=loc; o.data.materials.append(ma)
    if parent: o.parent=parent
    return o

def lathe(name,profile,loc,ma,col,parent=None,sides=24):
    v=[]; f=[]
    for rad,z in profile:
        for i in range(sides):
            a=math.tau*i/sides; v.append((rad*math.cos(a),rad*math.sin(a),z))
    for row in range(len(profile)-1):
        for i in range(sides):
            n=(i+1)%sides; a=row*sides+i; b=row*sides+n; c=(row+1)*sides+n; d=(row+1)*sides+i; f.append((a,b,c,d))
    me=bpy.data.meshes.new(name+"_Mesh"); me.from_pydata(v,[],f); me.update()
    o=bpy.data.objects.new(name,me); col.objects.link(o); o.location=loc; o.data.materials.append(ma)
    if parent: o.parent=parent
    return o

def root(a,n,cat,loc,col):
    r=bpy.data.objects.new(a,None); col.objects.link(r); r.location=loc
    r["asset_id"]=a; r["name_cn"]=n; r["category"]=cat; r["production_level"]="midpoly_blockout"; r["parametric"]=True; r["protected_scene_safe"]=True; r["source_style"]="historical_chinese_palace_yanyun_grounded"; return r

def bracket(r,red,gold,col):
    box(r.name+"_CAP",(2.2,.56,.28),(0,0,1.85),red,col,r,bev=.025); box(r.name+"_TIE",(1.72,.46,.26),(0,0,1.52),red,col,r,bev=.02)
    for x in (-.66,0,.66):
        cyl(f"{r.name}_DOU_{x}",.20,.18,(x,0,1.30),gold,col,r,12); box(f"{r.name}_GONG_{x}",(.78,.34,.18),(x,0,1.10),red,col,r,bev=.018)
    for x in (-.45,.45): box(f"{r.name}_ANG_{x}",(.85,.24,.16),(x,.10,.82),gold,col,r,rot=(0,math.radians(-18 if x<0 else 18),0),bev=.012)
    box(r.name+"_BASE",(1.15,.52,.30),(0,0,.52),red,col,r,bev=.02)

def corner(r,red,gold,col):
    for z,L in ((.42,1.25),(.72,1.11),(1.02,.97),(1.32,.83)):
        box(f"{r.name}_X_{z}",(L,.22,.15),(0,0,z),red,col,r,bev=.012); box(f"{r.name}_Y_{z}",(.22,L,.15),(0,0,z),red,col,r,bev=.012)
    cyl(r.name+"_CORE",.23,1.25,(0,0,.78),gold,col,r,14); box(r.name+"_TOP_X",(1.75,.32,.24),(0,0,1.58),red,col,r); box(r.name+"_TOP_Y",(.32,1.75,.24),(0,0,1.58),red,col,r)

def chiwen(r,tile,gold,col):
    box(r.name+"_BASE",(1.45,.42,.26),(0,0,.18),tile,col,r,bev=.04)
    for i in range(5): box(f"{r.name}_BODY_{i}",(1.05-i*.14,.32,.25),(0,0,.44+i*.28),tile,col,r,rot=(0,math.radians(-5+i*3),0),bev=.05)
    box(r.name+"_TAIL",(.28,.28,.95),(-.50,0,1.34),tile,col,r,rot=(0,math.radians(-28),0),bev=.05); eye=cyl(r.name+"_EYE",.07,.08,(.30,-.18,1.26),gold,col,r,12); eye.rotation_euler.x=math.pi/2

def beasts(r,tile,gold,col):
    for i in range(7):
        x=-1.65+i*.55; s=1-i*.055
        box(f"{r.name}_B_{i}",(.34*s,.24*s,.30*s),(x,0,.38),tile,col,r,bev=.06); cyl(f"{r.name}_H_{i}",.13*s,.22*s,(x+.12,0,.62),tile,col,r,12); box(f"{r.name}_G_{i}",(.09,.26,.08),(x-.10,0,.60),gold,col,r,bev=.025)
    box(r.name+"_RIDGE",(4.15,.28,.20),(0,0,.12),tile,col,r,bev=.03)

def balustrade(r,ivory,col):
    box(r.name+"_BASE",(4,.34,.22),(0,0,.16),ivory,col,r,bev=.025); box(r.name+"_HANDRAIL",(4,.30,.22),(0,0,1.52),ivory,col,r,bev=.03)
    for i in range(6): lathe(f"{r.name}_POST_{i}",[(.12,0),(.16,.12),(.12,.72),(.17,.88),(.11,1.08)],(-1.75+i*.70,0,.33),ivory,col,r,18)
    for i in range(5): box(f"{r.name}_PANEL_{i}",(.55,.18,.58),(-1.40+i*.70,0,.91),ivory,col,r,bev=.025)

def lantern(r,red,paper,gold,col):
    cyl(r.name+"_BODY",.34,.72,(0,0,1.05),paper,col,r,24)
    for z in (.66,1.44): cyl(f"{r.name}_RIM_{z}",.40,.09,(0,0,z),red,col,r,20)
    for i in range(6):
        a=math.tau*i/6; box(f"{r.name}_FRAME_{i}",(.045,.045,.78),(.35*math.cos(a),.35*math.sin(a),1.05),red,col,r)
    cyl(r.name+"_TOP",.15,.10,(0,0,1.57),gold,col,r,18); cyl(r.name+"_TASSEL",.035,.62,(0,0,.35),gold,col,r,10)

def censer(r,bronze,patina,col):
    lathe(r.name+"_BODY",[(.30,0),(.48,.12),(.56,.42),(.48,.70),(.34,.82)],(0,0,.42),bronze,col,r,28)
    for i in range(3):
        a=math.tau*i/3; cyl(f"{r.name}_LEG_{i}",.055,.52,(.36*math.cos(a),.36*math.sin(a),.24),patina,col,r,12)
    for s in (-1,1):
        q=cyl(f"{r.name}_EAR_{s}",.12,.08,(s*.56,0,1.10),bronze,col,r,16); q.rotation_euler.x=math.pi/2
    lathe(r.name+"_LID",[(.46,0),(.42,.10),(.22,.24),(.10,.36)],(0,0,1.20),patina,col,r,24)

def plaque(r,red,gold,col):
    box(r.name+"_BOARD",(2.8,.18,.82),(0,0,.88),red,col,r,bev=.08)
    for x in (-1.28,1.28):
        q=cyl(f"{r.name}_BOSS_{x}",.09,.08,(x,-.13,.88),gold,col,r,16); q.rotation_euler.x=math.pi/2
    for x in (-1.08,1.08): box(f"{r.name}_HANGER_{x}",(.07,.07,.62),(x,0,1.60),gold,col,r)

def main():
    a=args(); out=Path(a.output); rep=Path(a.report); out.parent.mkdir(parents=True,exist_ok=True); rep.parent.mkdir(parents=True,exist_ok=True)
    s=reset(); col=bpy.data.collections.new("TaiWei_Ornament_Modules"); s.collection.children.link(col)
    red=mat("TW_MAT_Cinnabar",(.40,.055,.035),.50); gold=mat("TW_MAT_DullGilt",(.55,.31,.07),.36,.72); tile=mat("TW_MAT_DarkGlazedTile",(.055,.075,.085),.42)
    ivory=mat("TW_MAT_WhiteStone",(.62,.66,.60),.58); paper=mat("TW_MAT_LanternPaper",(.78,.20,.045),.58,0,((1,.24,.05),1.0)); bronze=mat("TW_MAT_Bronze",(.19,.105,.035),.44,.72); patina=mat("TW_MAT_Patina",(.07,.20,.16),.64,.48)
    specs=[(bracket,(red,gold)),(corner,(red,gold)),(chiwen,(tile,gold)),(beasts,(tile,gold)),(balustrade,(ivory,)),(lantern,(red,paper,gold)),(censer,(bronze,patina)),(plaque,(red,gold))]
    rec=[]
    for i,((aid,n,cat),(fn,mats)) in enumerate(zip(ASSETS,specs)):
        r=root(aid,n,cat,((i%4-1.5)*6.2,(i//4-.5)*5.2,0),col); fn(r,*mats,col); rec.append({"asset_id":aid,"name_cn":n,"category":cat,"child_objects":len(r.children)})
    report={"scene":s.name,"asset_count":len(rec),"expected_asset_count":8,"assets":rec,"objects":len(s.objects),"mesh_objects":sum(o.type=="MESH" for o in s.objects),"materials":len(bpy.data.materials),"status":"midpoly_blockout","protected_scenes_touched":False,"rebuild_contract":"deterministic_geometry_no_llm_required"}
    assert len(rec)==8 and all(x["child_objects"]>0 for x in rec)
    rep.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8"); bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve())); print("TAIWEI_ORNAMENT_FACTORY_OK",json.dumps(report,ensure_ascii=False))
if __name__=="__main__": main()
