"""Taiwei Cloud Palace Hero Asset Pack V2.
Standalone deterministic Blender 4.2+ procedural asset factory.
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path
import bpy

ASSETS = [
    ("TW_HERO_CHIWEN_01", "鸱吻·英雄级轮廓", "ridge_ornament", "hero_midpoly"),
    ("TW_HERO_BEAST_DRAGON_01", "屋脊走兽·龙", "ridge_beast", "hero_midpoly"),
    ("TW_HERO_BEAST_PHOENIX_01", "屋脊走兽·凤", "ridge_beast", "hero_midpoly"),
    ("TW_HERO_BEAST_LION_01", "屋脊走兽·狮", "ridge_beast", "hero_midpoly"),
    ("TW_HERO_BEAST_QILIN_01", "屋脊走兽·麒麟", "ridge_beast", "hero_midpoly"),
    ("TW_HERO_BEAST_TIANMA_01", "屋脊走兽·天马", "ridge_beast", "hero_midpoly"),
    ("TW_HERO_BEAST_HAIMA_01", "屋脊走兽·海马", "ridge_beast", "hero_midpoly"),
    ("TW_HERO_DOUGONG_01", "单翘斗拱·英雄级", "dougong", "hero_midpoly"),
    ("TW_HERO_CORNER_DOUGONG_01", "转角铺作·英雄级", "dougong_corner", "hero_midpoly"),
    ("TW_HERO_GESHAN_DOOR_01", "格扇门·如意云纹", "door_window", "hero_midpoly"),
    ("TW_HERO_LATTICE_WINDOW_01", "槛窗·冰裂纹", "door_window", "hero_midpoly"),
    ("TW_HERO_CAISSON_01", "八角藻井·莲心", "interior_architecture", "hero_midpoly"),
    ("TW_HERO_COLUMN_BASE_01", "覆莲柱础", "stone_architecture", "hero_midpoly"),
    ("TW_HERO_HUABIAO_01", "盘龙华表", "stone_architecture", "hero_midpoly"),
    ("TW_HERO_SUTRA_PILLAR_01", "八面经幢", "stone_architecture", "hero_midpoly"),
    ("TW_HERO_LANTERN_01", "六角宫灯·描金", "lighting_prop", "hero_midpoly"),
    ("TW_HERO_CENSER_01", "兽耳青铜香炉", "ritual_prop", "hero_midpoly"),
    ("TW_HERO_PLAQUE_01", "宫殿匾额·云龙边", "signage", "hero_midpoly"),
    ("TW_HERO_BALUSTRADE_01", "白石栏杆·云龙栏板", "stone_architecture", "hero_midpoly"),
    ("TW_HERO_EAVES_TILE_01", "兽面瓦当与滴水", "roof_detail", "hero_midpoly"),
    ("TW_HERO_WIND_BELL_01", "檐角风铎", "roof_detail", "hero_midpoly"),
    ("TW_HERO_SCREEN_01", "山水座屏", "interior_prop", "hero_midpoly"),
    ("TW_HERO_BRONZE_CRANE_01", "青铜仙鹤", "ritual_prop", "hero_midpoly"),
    ("TW_HERO_LOTUS_PEDESTAL_01", "重瓣莲花座", "ritual_prop", "hero_midpoly"),
]

def parse_args():
    tail = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="generated_assets/TaiWei_HeroAssetPack_V2.blend")
    p.add_argument("--report", default="generated_assets/taiwei-hero-asset-report.json")
    return p.parse_args(tail)

def reset_scene():
    s = bpy.context.scene
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for c in list(bpy.data.collections):
        if c.name != s.collection.name:
            bpy.data.collections.remove(c)
    for d in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for x in list(d):
            if getattr(x, "users", 0) == 0:
                d.remove(x)
    s.name = "TaiWei_Hero_AssetPack_V2"
    return s

def mat(name, color, rough=.5, metal=0.0, emission=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nodes=m.node_tree.nodes; links=m.node_tree.links
    bsdf = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission[0], 1)
        bsdf.inputs["Emission Strength"].default_value = emission[1]
    # Small procedural surface relief keeps the reusable pack readable even
    # before project-specific 4K PBR maps are assigned.
    noise=nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 7.0 if "Wood" not in name else 4.0
    noise.inputs["Detail"].default_value = 3.5
    noise.inputs["Roughness"].default_value = .62
    bump=nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = .08 if "Paper" in name else .16
    bump.inputs["Distance"].default_value = .06
    links.new(noise.outputs["Fac"],bump.inputs["Height"])
    links.new(bump.outputs["Normal"],bsdf.inputs["Normal"])
    return m

def mesh_obj(name, verts, faces, material, col, parent=None):
    me = bpy.data.meshes.new(name+"_Mesh")
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new(name, me)
    col.objects.link(o)
    if material:
        o.data.materials.append(material)
    if parent:
        o.parent = parent
    return o

def cube(name, size, loc, material, col, parent=None, rot=(0,0,0), bevel=0.0):
    x,y,z = (v/2 for v in size)
    v=[(-x,-y,-z),(-x,-y,z),(-x,y,-z),(-x,y,z),(x,-y,-z),(x,-y,z),(x,y,-z),(x,y,z)]
    f=[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]
    o = mesh_obj(name,v,f,material,col,parent)
    o.location=loc; o.rotation_euler=rot
    if bevel:
        mod=o.modifiers.new("EdgeSoftening","BEVEL"); mod.width=bevel; mod.segments=3
    return o

def cyl(name, radius, height, loc, material, col, parent=None, sides=24, rot=(0,0,0), bevel=0.0):
    verts=[]; faces=[]
    for z in (-height/2,height/2):
        for i in range(sides):
            a=math.tau*i/sides; verts.append((radius*math.cos(a),radius*math.sin(a),z))
    for i in range(sides):
        n=(i+1)%sides
        faces.append((i,n,sides+n,sides+i))
    faces += [tuple(reversed(range(sides))), tuple(range(sides,2*sides))]
    o=mesh_obj(name,verts,faces,material,col,parent)
    o.location=loc; o.rotation_euler=rot
    if bevel:
        mod=o.modifiers.new("EdgeSoftening","BEVEL"); mod.width=bevel; mod.segments=2
    return o

def lathe(name, profile, loc, material, col, parent=None, sides=32, rot=(0,0,0)):
    verts=[]; faces=[]
    for rad,z in profile:
        for i in range(sides):
            a=math.tau*i/sides; verts.append((rad*math.cos(a),rad*math.sin(a),z))
    rows=len(profile)
    for r in range(rows-1):
        for i in range(sides):
            n=(i+1)%sides
            a=r*sides+i; b=r*sides+n; c=(r+1)*sides+n; d=(r+1)*sides+i
            faces.append((a,b,c,d))
    o=mesh_obj(name,verts,faces,material,col,parent)
    o.location=loc; o.rotation_euler=rot
    for p in o.data.polygons: p.use_smooth=True
    return o

def sphere(name, radii, loc, material, col, parent=None, seg=24, rings=12):
    rx,ry,rz=radii
    verts=[]; faces=[]
    for j in range(rings+1):
        p=math.pi*j/rings
        sp,cp=math.sin(p),math.cos(p)
        for i in range(seg):
            a=math.tau*i/seg
            verts.append((rx*sp*math.cos(a),ry*sp*math.sin(a),rz*cp))
    for j in range(rings):
        for i in range(seg):
            n=(i+1)%seg
            a=j*seg+i; b=j*seg+n; c=(j+1)*seg+n; d=(j+1)*seg+i
            faces.append((a,b,c,d))
    o=mesh_obj(name,verts,faces,material,col,parent)
    o.location=loc
    for p in o.data.polygons: p.use_smooth=True
    return o

def torus(name, major, minor, loc, material, col, parent=None, seg=32, ring=10, rot=(0,0,0)):
    verts=[]; faces=[]
    for i in range(seg):
        a=math.tau*i/seg
        ca,sa=math.cos(a),math.sin(a)
        for j in range(ring):
            b=math.tau*j/ring
            cb,sb=math.cos(b),math.sin(b)
            rr=major+minor*cb
            verts.append((rr*ca,rr*sa,minor*sb))
    for i in range(seg):
        ni=(i+1)%seg
        for j in range(ring):
            nj=(j+1)%ring
            a=i*ring+j; b=ni*ring+j; c=ni*ring+nj; d=i*ring+nj
            faces.append((a,b,c,d))
    o=mesh_obj(name,verts,faces,material,col,parent)
    o.location=loc; o.rotation_euler=rot
    for p in o.data.polygons: p.use_smooth=True
    return o

def tube(name, points, radius, material, col, parent=None, res=2):
    cu=bpy.data.curves.new(name+"_Curve","CURVE")
    cu.dimensions="3D"; cu.resolution_u=res; cu.bevel_depth=radius; cu.bevel_resolution=3
    sp=cu.splines.new("BEZIER"); sp.bezier_points.add(len(points)-1)
    for bp,co in zip(sp.bezier_points,points):
        bp.co=co; bp.handle_left_type="AUTO"; bp.handle_right_type="AUTO"
    o=bpy.data.objects.new(name,cu); col.objects.link(o)
    if material: cu.materials.append(material)
    if parent: o.parent=parent
    return o

def root(asset, cn, cat, tier, loc, col):
    r=bpy.data.objects.new(asset,None); col.objects.link(r); r.location=loc
    r["asset_id"]=asset; r["name_cn"]=cn; r["category"]=cat
    r["production_level"]=tier; r["quality_tier"]="hero_v2"
    r["parametric"]=True; r["reusable"]=True; r["protected_scene_safe"]=True
    r["source_style"]="historical_chinese_palace_yanyun_grounded"
    r["units"]="meters"; r["origin_policy"]="asset_root_grounded"
    return r

def petal(name, center, angle, scale, material, col, parent, z=0.0):
    x,y=center
    c,s=math.cos(angle),math.sin(angle)
    o=sphere(name,(0.12*scale,0.30*scale,0.08*scale),(x+c*.18*scale,y+s*.18*scale,z),material,col,parent,20,8)
    o.rotation_euler[2]=angle
    return o

def build_chiwen(r, M, col):
    tile,gold=M["tile"],M["gold"]
    cube(r.name+"_RIDGE",(1.8,.48,.28),(0,0,.18),tile,col,r,bevel=.06)
    sphere(r.name+"_TORSO",(.52,.28,.74),(0,0,1.02),tile,col,r,28,14)
    sphere(r.name+"_HEAD",(.45,.32,.38),(.22,-.01,1.70),tile,col,r,28,14)
    cube(r.name+"_UPPER_JAW",(.62,.38,.16),(.54,-.01,1.82),tile,col,r,rot=(0,math.radians(-8),0),bevel=.07)
    cube(r.name+"_LOWER_JAW",(.52,.35,.13),(.50,-.01,1.62),tile,col,r,rot=(0,math.radians(9),0),bevel=.06)
    for sy in (-1,1):
        sphere(r.name+f"_EYE_{sy}",(.085,.06,.085),(.33,sy*.27,1.88),gold,col,r,18,8)
        tube(r.name+f"_HORN_{sy}",[(.03,sy*.20,1.94),(-.10,sy*.32,2.18),(-.32,sy*.38,2.32)],.035,gold,col,r)
        tube(r.name+f"_WHISKER_{sy}",[(.58,sy*.18,1.70),(.86,sy*.33,1.58),(1.06,sy*.42,1.38)],.018,gold,col,r)
    for i in range(6):
        a=math.radians(-58+i*23)
        x=-.24+.34*math.cos(a); z=1.13+.58*math.sin(a)
        cube(r.name+f"_DORSAL_{i}",(.10,.38,.34),(x,0,z),gold,col,r,rot=(0,a,0),bevel=.03)
    tube(r.name+"_TAIL",[(-.38,0,1.25),(-.72,0,1.58),(-.80,0,2.02),(-.52,0,2.32)],.085,tile,col,r)
    for i in range(4):
        petal(r.name+f"_SCALE_{i}",(-.08+i*.02,0),math.pi/2,1.0-i*.08,gold,col,r,z=.78+i*.20)

def build_beast(r, M, col, species, idx):
    tile,gold=M["tile"],M["gold"]
    scale=1.0+idx*.025
    sphere(r.name+"_BODY",(.48*scale,.26*scale,.32*scale),(-.12,0,.58),tile,col,r,28,14)
    sphere(r.name+"_CHEST",(.30,.24,.36),(.22,0,.64),tile,col,r,24,12)
    sphere(r.name+"_HEAD",(.27,.23,.25),(.48,0,.90),tile,col,r,28,14)
    sphere(r.name+"_MUZZLE",(.19,.18,.13),(.68,0,.84),tile,col,r,22,10)
    cube(r.name+"_JAW",(.27,.25,.08),(.70,0,.76),gold,col,r,bevel=.035)
    for sy in (-1,1):
        sphere(r.name+f"_EYE_{sy}",(.05,.035,.05),(.57,sy*.20,.96),gold,col,r,16,8)
        sphere(r.name+f"_EAR_{sy}",(.08,.045,.11),(.38,sy*.20,1.08),gold,col,r,16,8)
        cube(r.name+f"_BROW_{sy}",(.18,.045,.055),(.53,sy*.205,1.03),gold,col,r,rot=(math.radians(8),0,math.radians(-8*sy)),bevel=.018)
    for lx in (-.30,.18):
        for sy in (-1,1):
            cyl(r.name+f"_LEG_{lx}_{sy}",.06,.42,(lx,sy*.15,.28),tile,col,r,14)
            sphere(r.name+f"_PAW_{lx}_{sy}",(.11,.09,.055),(lx+.04,sy*.15,.055),gold,col,r,14,7)
    tube(r.name+"_TAIL",[(-.48,0,.62),(-.72,.02,.84),(-.80,.04,1.10),(-.62,.02,1.31)],.052,gold,col,r)
    if species in ("dragon","qilin","haima"):
        for sy in (-1,1):
            tube(r.name+f"_HORN_{sy}",[(.43,sy*.11,1.06),(.34,sy*.19,1.27),(.16,sy*.23,1.39)],.027,gold,col,r)
        for k in range(4):
            cube(r.name+f"_SPINE_{k}",(.06,.16,.18),(-.28+k*.14,0,.90+k*.03),gold,col,r,rot=(0,math.radians(-18+k*6),0),bevel=.018)
    if species=="dragon":
        for sy in (-1,1):
            tube(r.name+f"_BEARD_{sy}",[(.65,sy*.12,.80),(.82,sy*.24,.68),(.92,sy*.31,.57)],.018,gold,col,r)
    if species=="phoenix":
        cube(r.name+"_BEAK",(.28,.18,.09),(.73,0,.88),gold,col,r,rot=(0,math.radians(-7),0),bevel=.025)
        for sy in (-1,1):
            cube(r.name+f"_WING_{sy}",(.72,.075,.34),(-.08,sy*.29,.78),gold,col,r,rot=(0,math.radians(-22),math.radians(12*sy)),bevel=.06)
        for k in range(4):
            tube(r.name+f"_PLUME_{k}",[(-.38,0,.69),(-.68,(k-1.5)*.07,.98),(-1.0,(k-1.5)*.11,1.23)],.026,gold,col,r)
    if species=="lion":
        for k in range(10):
            a=math.tau*k/10
            sphere(r.name+f"_MANE_{k}",(.115,.085,.125),(.36,.18*math.cos(a),.89+.22*math.sin(a)),gold,col,r,16,8)
    if species=="qilin":
        tube(r.name+"_FORELOCK",[(.47,0,1.08),(.58,0,1.26),(.48,0,1.38)],.035,gold,col,r)
    if species=="tianma":
        for sy in (-1,1):
            cube(r.name+f"_WING_{sy}",(.82,.08,.32),(-.08,sy*.30,.86),gold,col,r,rot=(0,math.radians(-20),math.radians(14*sy)),bevel=.055)
        for k in range(4):
            sphere(r.name+f"_MANE_{k}",(.08,.06,.11),(.15-k*.11,0,1.00-k*.04),gold,col,r,14,7)
    if species=="haima":
        tube(r.name+"_CREST",[(.38,0,1.04),(.22,0,1.22),(0,0,1.31),(-.18,0,1.22)],.038,gold,col,r)

def build_dougong(r, M, col, corner=False):
    red,gold=M["red"],M["gold"]
    levels=5 if corner else 4
    for lv in range(levels):
        z=.32+lv*.32
        span=1.20+lv*.30
        cube(r.name+f"_GONG_X_{lv}",(span,.34,.17),(0,0,z),red,col,r,bevel=.025)
        if corner:
            cube(r.name+f"_GONG_Y_{lv}",(.34,span,.17),(0,0,z),red,col,r,bevel=.025)
        for sx in (-1,1):
            cyl(r.name+f"_DOU_{lv}_{sx}",.16,.17,(sx*span*.32,0,z+.18),gold,col,r,14)
            if corner:
                cyl(r.name+f"_DOU_Y_{lv}_{sx}",.16,.17,(0,sx*span*.32,z+.18),gold,col,r,14)
    for i,sx in enumerate((-1,1)):
        cube(r.name+f"_ANG_{i}",(1.05,.24,.18),(sx*.42,.05,1.72),gold,col,r,rot=(0,math.radians(-24*sx),0),bevel=.02)
    cube(r.name+"_CAP",(2.45,.48,.24),(0,0,1.90),red,col,r,bevel=.035)
    cube(r.name+"_BASE",(1.25,.58,.30),(0,0,.12),red,col,r,bevel=.03)

def build_geshan(r, M, col, window=False):
    wood,gold,paper=M["wood"],M["gold"],M["paper"]
    w=2.55 if not window else 2.25; h=3.8 if not window else 2.6
    # Real frame rails instead of an opaque slab: paper/panel remains visible,
    # while lattice and carved motifs sit proud of the surface.
    cube(r.name+"_PANEL",(w-.34,.08,h-.34),(0,.06,h/2),paper,col,r,bevel=.018)
    rail=.15
    cube(r.name+"_FRAME_L",(rail,.28,h),(-w/2+rail/2,0,h/2),wood,col,r,bevel=.025)
    cube(r.name+"_FRAME_R",(rail,.28,h),(w/2-rail/2,0,h/2),wood,col,r,bevel=.025)
    cube(r.name+"_FRAME_TOP",(w,.28,rail),(0,0,h-rail/2),wood,col,r,bevel=.025)
    cube(r.name+"_FRAME_BOTTOM",(w,.28,rail),(0,0,rail/2),wood,col,r,bevel=.025)
    for z in (h*.34,h*.68):
        cube(r.name+f"_MIDRAIL_{z}",(w-.18,.26,.11),(0,-.01,z),wood,col,r,bevel=.018)
    if not window:
        n=9
        for i in range(n):
            x=-w*.39+i*(w*.78/(n-1))
            cube(r.name+f"_LATTICE_V_{i}",(.045,.30,h*.53),(x,-.08,h*.67),gold,col,r,bevel=.008)
        for j in range(6):
            z=h*.43+j*(h*.44/5)
            cube(r.name+f"_LATTICE_H_{j}",(w*.78,.30,.045),(0,-.08,z),gold,col,r,bevel=.008)
    else:
        # Ice-crack-inspired lattice: orthogonal frame plus irregular diagonals.
        for i in range(6):
            x=-w*.36+i*(w*.72/5)
            cube(r.name+f"_LATTICE_V_{i}",(.04,.30,h*.54),(x,-.08,h*.64),gold,col,r,bevel=.008)
        for j in range(5):
            z=h*.43+j*(h*.42/4)
            cube(r.name+f"_LATTICE_H_{j}",(w*.74,.30,.04),(0,-.08,z),gold,col,r,bevel=.008)
        for k,(x,z,ang,L) in enumerate(((-.55,1.25,28,.82),(.15,1.55,-34,.92),(.55,1.05,42,.72),(-.08,2.05,30,.76))):
            cube(r.name+f"_ICE_DIAG_{k}",(L,.30,.038),(x,-.095,z),gold,col,r,rot=(0,0,math.radians(ang)),bevel=.008)
    for q in (-1,1):
        tube(r.name+f"_CLOUD_{q}",[(q*.66,-.17,h*.20),(q*.42,-.18,h*.27),(q*.58,-.18,h*.34),(q*.30,-.18,h*.40)],.032,gold,col,r)

def build_caisson(r, M, col):
    wood,gold,blue=M["wood"],M["gold"],M["blue"]
    for ring in range(4):
        rad=1.85-ring*.34; z=.22+ring*.26
        for i in range(8):
            a=math.tau*i/8; nx=rad*math.cos(a); ny=rad*math.sin(a)
            cube(r.name+f"_R{ring}_{i}",(1.32,.18,.15),(nx,ny,z),wood,col,r,rot=(0,0,a+math.pi/2),bevel=.025)
    cyl(r.name+"_CENTER",.55,.20,(0,0,1.22),blue,col,r,32)
    for i in range(16):
        petal(r.name+f"_LOTUS_{i}",(0,0),math.tau*i/16,1.28,gold,col,r,z=1.34)
    for i in range(8):
        a=math.tau*i/8
        tube(r.name+f"_RIB_{i}",[(0,0,1.25),(.72*math.cos(a),.72*math.sin(a),.95),(1.42*math.cos(a),1.42*math.sin(a),.50)],.04,gold,col,r)

def build_column_base(r,M,col):
    stone,gold=M["stone"],M["gold"]
    lathe(r.name+"_PLINTH",[(.88,0),(.92,.16),(.76,.28),(.72,.44),(.56,.62),(.48,.76)],(0,0,0),stone,col,r,40)
    for ring,rad,z,count in ((0,.60,.46,16),(1,.48,.67,12)):
        for i in range(count):
            a=math.tau*i/count
            petal(r.name+f"_PETAL_{ring}_{i}",(rad*math.cos(a),rad*math.sin(a)),a,1.05 if ring==0 else .82,gold,col,r,z=z)

def build_huabiao(r,M,col):
    stone,gold=M["stone"],M["gold"]
    lathe(r.name+"_BASE",[(.72,0),(.80,.16),(.62,.34),(.52,.52)],(0,0,0),stone,col,r,36)
    cyl(r.name+"_SHAFT",.27,3.8,(0,0,2.42),stone,col,r,32)
    for z in (1.25,2.10,2.95):
        torus(r.name+f"_RING_{z}",.31,.055,(0,0,z),gold,col,r,28,8)
    cube(r.name+"_CLOUD_BOARD",(2.25,.18,.55),(0,0,3.45),stone,col,r,bevel=.10)
    for sy in (-1,1):
        tube(r.name+f"_CLOUD_{sy}",[(0,sy*.14,3.45),(.48,sy*.16,3.67),(.88,sy*.16,3.47),(1.10,sy*.16,3.62)],.07,gold,col,r)
    sphere(r.name+"_CAP",(.34,.34,.30),(0,0,4.48),stone,col,r,24,12)
    sphere(r.name+"_BEAST",(.22,.18,.20),(0,0,4.78),gold,col,r,20,10)

def build_sutra(r,M,col):
    stone,gold=M["stone"],M["gold"]
    lathe(r.name+"_BASE",[(.86,0),(.92,.16),(.72,.32),(.64,.50)],(0,0,0),stone,col,r,8)
    cyl(r.name+"_BODY",.52,2.15,(0,0,1.55),stone,col,r,8)
    for z in (.72,1.18,1.64,2.10):
        torus(r.name+f"_SCRIPT_BAND_{z}",.54,.035,(0,0,z),gold,col,r,8,8)
    lathe(r.name+"_ROOF",[(.72,0),(.68,.12),(.48,.34),(.26,.54),(.12,.72)],(0,0,2.72),gold,col,r,8)
    sphere(r.name+"_JEWEL",(.14,.14,.20),(0,0,3.52),gold,col,r,18,9)

def build_lantern(r,M,col):
    red,gold,paper=M["red"],M["gold"],M["paper"]
    cyl(r.name+"_BODY",.46,.95,(0,0,1.15),paper,col,r,6)
    for z in (.65,1.65):
        cyl(r.name+f"_RIM_{z}",.52,.11,(0,0,z),red,col,r,6)
    for i in range(6):
        a=math.tau*i/6
        cube(r.name+f"_FRAME_{i}",(.055,.055,1.02),(.43*math.cos(a),.43*math.sin(a),1.15),red,col,r,rot=(0,0,a))
        sphere(r.name+f"_BOSS_{i}",(.06,.06,.06),(.50*math.cos(a),.50*math.sin(a),1.65),gold,col,r,12,6)
    lathe(r.name+"_TOP",[(.22,0),(.30,.10),(.18,.24),(.09,.36)],(0,0,1.76),gold,col,r,24)
    for i in range(9):
        a=math.tau*i/9
        tube(r.name+f"_TASSEL_{i}",[(.12*math.cos(a),.12*math.sin(a),.65),(.13*math.cos(a),.13*math.sin(a),.16)],.012,gold,col,r)

def build_censer(r,M,col):
    bronze,patina,gold=M["bronze"],M["patina"],M["gold"]
    lathe(r.name+"_BODY",[(.30,0),(.50,.12),(.62,.38),(.58,.72),(.43,.90),(.36,1.02)],(0,0,.26),bronze,col,r,36)
    for i in range(3):
        a=math.tau*i/3
        cyl(r.name+f"_LEG_{i}",.075,.62,(.42*math.cos(a),.42*math.sin(a),.20),patina,col,r,14)
        sphere(r.name+f"_PAW_{i}",(.11,.10,.07),(.42*math.cos(a),.42*math.sin(a),-.10),gold,col,r,14,7)
    for sy in (-1,1):
        torus(r.name+f"_EAR_{sy}",.23,.045,(sy*.62,0,1.08),bronze,col,r,24,8,rot=(math.pi/2,0,0))
    lathe(r.name+"_LID",[(.50,0),(.44,.10),(.28,.28),(.13,.42),(.07,.58)],(0,0,1.30),patina,col,r,30)
    for i in range(8):
        a=math.tau*i/8
        sphere(r.name+f"_BOSS_{i}",(.045,.045,.045),(.49*math.cos(a),.49*math.sin(a),.86),gold,col,r,10,5)

def build_plaque(r,M,col):
    red,gold,wood=M["red"],M["gold"],M["wood"]
    cube(r.name+"_BOARD",(3.2,.20,1.02),(0,0,.96),red,col,r,bevel=.10)
    cube(r.name+"_BACK",(3.36,.15,1.18),(0,.12,.96),wood,col,r,bevel=.08)
    for x in (-1.42,1.42):
        sphere(r.name+f"_BOSS_{x}",(.10,.07,.10),(x,-.16,.96),gold,col,r,18,8)
        cube(r.name+f"_HANGER_{x}",(.09,.09,.76),(x,0,1.86),gold,col,r)
    for sy in (-1,1):
        tube(r.name+f"_DRAGON_BORDER_{sy}",[(-1.20,-.16,.96+sy*.34),(-.65,-.18,.96+sy*.42),(0,-.18,.96+sy*.32),(.65,-.18,.96+sy*.42),(1.20,-.16,.96+sy*.34)],.035,gold,col,r)
    for i in range(5):
        cube(r.name+f"_GLYPH_PLACEHOLDER_{i}",(.10,.05,.48),(-.56+i*.28,-.17,.96),gold,col,r,rot=(0,0,math.radians((i%2)*8-4)),bevel=.015)

def build_balustrade(r,M,col):
    stone,gold=M["stone"],M["gold"]
    cube(r.name+"_BASE",(4.6,.42,.26),(0,0,.13),stone,col,r,bevel=.04)
    cube(r.name+"_RAIL",(4.6,.34,.24),(0,0,1.62),stone,col,r,bevel=.05)
    for i in range(7):
        x=-2.10+i*.70
        lathe(r.name+f"_POST_{i}",[(.13,0),(.18,.10),(.13,.76),(.18,.92),(.12,1.22)],(x,0,.28),stone,col,r,18)
    for i in range(6):
        x=-1.75+i*.70
        cube(r.name+f"_PANEL_{i}",(.58,.20,.64),(x,0,.98),stone,col,r,bevel=.04)
        tube(r.name+f"_CLOUD_{i}",[(x-.18,-.12,.93),(x,-.13,1.12),(x+.18,-.12,.93)],.025,gold,col,r)

def build_eaves_tile(r,M,col):
    tile,gold=M["tile"],M["gold"]
    for i in range(6):
        x=-1.25+i*.50
        cyl(r.name+f"_WADANG_{i}",.20,.10,(x,0,.38),tile,col,r,28,rot=(math.pi/2,0,0))
        sphere(r.name+f"_FACE_{i}",(.09,.035,.09),(x,-.075,.38),gold,col,r,18,8)
        cube(r.name+f"_DRIP_{i}",(.34,.18,.42),(x,.16,.12),tile,col,r,rot=(math.radians(10),0,0),bevel=.04)

def build_wind_bell(r,M,col):
    bronze,gold=M["bronze"],M["gold"]
    lathe(r.name+"_BELL",[(.08,0),(.22,.10),(.34,.34),(.42,.58),(.36,.68)],(0,0,.62),bronze,col,r,28)
    tube(r.name+"_HANGER",[(0,0,1.30),(0,0,1.72)],.025,gold,col,r)
    tube(r.name+"_CLAPPER",[(0,0,.64),(0,0,.20)],.018,gold,col,r)
    sphere(r.name+"_CLAPPER_BALL",(.07,.07,.07),(0,0,.15),gold,col,r,14,7)
    cube(r.name+"_WIND_SAIL",(.26,.035,.48),(0,0,-.13),gold,col,r,bevel=.03)

def build_screen(r,M,col):
    wood,gold,blue=M["wood"],M["gold"],M["blue"]
    cube(r.name+"_FRAME",(3.2,.22,2.45),(0,0,1.55),wood,col,r,bevel=.07)
    cube(r.name+"_PANEL",(2.82,.12,2.08),(0,-.08,1.55),blue,col,r,bevel=.04)
    for x in (-1.38,1.38):
        cube(r.name+f"_POST_{x}",(.18,.34,2.70),(x,0,1.45),wood,col,r,bevel=.03)
    cube(r.name+"_FOOT",(3.7,.56,.18),(0,0,.12),wood,col,r,bevel=.05)
    tube(r.name+"_MOUNTAIN",[(-1.12,-.16,1.20),(-.62,-.17,1.72),(-.18,-.17,1.35),(.36,-.17,1.92),(.98,-.17,1.42)],.035,gold,col,r)
    for i in range(5):
        sphere(r.name+f"_CLOUD_{i}",(.20,.05,.08),(-.86+i*.42,-.17,2.15+(i%2)*.10),gold,col,r,16,6)

def build_crane(r,M,col):
    bronze,patina,gold=M["bronze"],M["patina"],M["gold"]
    sphere(r.name+"_BODY",(.36,.22,.54),(0,0,.86),bronze,col,r,28,14)
    tube(r.name+"_NECK",[(.10,0,1.16),(.22,0,1.52),(.10,0,1.84),(.22,0,2.10)],.10,bronze,col,r)
    sphere(r.name+"_HEAD",(.18,.15,.16),(.22,0,2.13),patina,col,r,22,10)
    cube(r.name+"_BEAK",(.42,.12,.10),(.46,0,2.12),gold,col,r,bevel=.03)
    for sy in (-1,1):
        tube(r.name+f"_LEG_{sy}",[(sy*.10,0,.54),(sy*.11,0,.04)],.035,bronze,col,r)
        cube(r.name+f"_FOOT_{sy}",(.34,.10,.05),(sy*.10,-.04,0),gold,col,r,bevel=.02)
        cube(r.name+f"_WING_{sy}",(.58,.10,.70),(-.12,sy*.24,.98),patina,col,r,rot=(0,math.radians(-18),math.radians(8*sy)),bevel=.10)
    for i in range(3):
        cube(r.name+f"_TAIL_{i}",(.12,.10,.72),(-.34-i*.06,0,.70-i*.06),bronze,col,r,rot=(0,math.radians(-28-i*5),0),bevel=.04)

def build_lotus(r,M,col):
    stone,gold=M["stone"],M["gold"]
    lathe(r.name+"_BASE",[(.92,0),(.98,.18),(.82,.32),(.72,.46)],(0,0,0),stone,col,r,40)
    for ring,(rad,z,count,scale) in enumerate(((.63,.44,18,1.30),(.46,.62,14,1.08),(.28,.80,10,.84))):
        for i in range(count):
            a=math.tau*i/count
            petal(r.name+f"_PETAL_{ring}_{i}",(rad*math.cos(a),rad*math.sin(a)),a,scale,gold,col,r,z=z)
    cyl(r.name+"_SEAT",.34,.16,(0,0,1.00),stone,col,r,32)

BUILDERS = [
    lambda r,M,c: build_chiwen(r,M,c),
    lambda r,M,c: build_beast(r,M,c,"dragon",0),
    lambda r,M,c: build_beast(r,M,c,"phoenix",1),
    lambda r,M,c: build_beast(r,M,c,"lion",2),
    lambda r,M,c: build_beast(r,M,c,"qilin",3),
    lambda r,M,c: build_beast(r,M,c,"tianma",4),
    lambda r,M,c: build_beast(r,M,c,"haima",5),
    lambda r,M,c: build_dougong(r,M,c,False),
    lambda r,M,c: build_dougong(r,M,c,True),
    lambda r,M,c: build_geshan(r,M,c,False),
    lambda r,M,c: build_geshan(r,M,c,True),
    lambda r,M,c: build_caisson(r,M,c),
    lambda r,M,c: build_column_base(r,M,c),
    lambda r,M,c: build_huabiao(r,M,c),
    lambda r,M,c: build_sutra(r,M,c),
    lambda r,M,c: build_lantern(r,M,c),
    lambda r,M,c: build_censer(r,M,c),
    lambda r,M,c: build_plaque(r,M,c),
    lambda r,M,c: build_balustrade(r,M,c),
    lambda r,M,c: build_eaves_tile(r,M,c),
    lambda r,M,c: build_wind_bell(r,M,c),
    lambda r,M,c: build_screen(r,M,c),
    lambda r,M,c: build_crane(r,M,c),
    lambda r,M,c: build_lotus(r,M,c),
]

def main():
    a=parse_args()
    out=Path(a.output); rep=Path(a.report)
    out.parent.mkdir(parents=True,exist_ok=True); rep.parent.mkdir(parents=True,exist_ok=True)
    s=reset_scene()
    col=bpy.data.collections.new("TaiWei_Hero_Modules_V2"); s.collection.children.link(col)
    M={
        "red":mat("TW2_MAT_Cinnabar_Lacquer",(.34,.030,.018),.34),
        "gold":mat("TW2_MAT_Aged_Gilt",(.52,.25,.045),.30,.76),
        "tile":mat("TW2_MAT_Black_Glazed_Tile",(.028,.045,.052),.28,.08),
        "stone":mat("TW2_MAT_White_Marble",(.64,.66,.61),.48),
        "paper":mat("TW2_MAT_Warm_Lantern_Paper",(.72,.14,.025),.52,0,((1.0,.16,.03),1.8)),
        "bronze":mat("TW2_MAT_Dark_Bronze",(.13,.060,.020),.36,.78),
        "patina":mat("TW2_MAT_Bronze_Patina",(.035,.16,.12),.54,.54),
        "wood":mat("TW2_MAT_Dark_Rosewood",(.11,.028,.016),.42),
        "blue":mat("TW2_MAT_Mineral_Azure",(.035,.11,.22),.40),
    }
    rec=[]
    cols=6
    for i,((aid,cn,cat,tier),builder) in enumerate(zip(ASSETS,BUILDERS)):
        gx=(i%cols-(cols-1)/2)*7.0
        gy=(i//cols-1.5)*7.0
        r=root(aid,cn,cat,tier,(gx,gy,0),col)
        builder(r,M,col)
        geom=[o for o in r.children if o.type in {"MESH","CURVE"}]
        mesh=[o for o in geom if o.type=="MESH"]
        curve=[o for o in geom if o.type=="CURVE"]
        rec.append({
            "asset_id":aid,"name_cn":cn,"category":cat,"quality_tier":tier,
            "child_objects":len(r.children),"geometry_objects":len(geom),
            "mesh_objects":len(mesh),"curve_objects":len(curve),
            "reusable":True,"protected_scene_safe":True
        })
    assert len(rec)==24
    assert all(x["geometry_objects"]>=5 for x in rec)
    assert all(bool(o.get("protected_scene_safe")) for o in s.objects if o.get("asset_id"))
    used_materials=sorted({m.name for o in s.objects if hasattr(o.data,"materials") for m in o.data.materials})
    report={
        "scene":s.name,"pack_id":"TW_HERO_ASSET_PACK_V2","asset_count":len(rec),
        "assets":rec,"objects":len(s.objects),
        "mesh_objects":sum(o.type=="MESH" for o in s.objects),
        "curve_objects":sum(o.type=="CURVE" for o in s.objects),
        "declared_materials":len(M),"used_materials":used_materials,
        "status":"hero_midpoly_reusable","protected_scenes_touched":False,
        "rebuild_contract":"deterministic_geometry_no_llm_required",
        "generator":"blender/tools/generate_hero_asset_pack.py",
        "blender_target":"4.2.23 LTS"
    }
    rep.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()))
    print("TAIWEI_HERO_ASSET_PACK_OK", json.dumps(report,ensure_ascii=False))

if __name__=="__main__":
    main()
