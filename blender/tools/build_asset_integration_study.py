"""Build a low-cost cross-pack integration study from generated Taiwei .blend packs."""
from __future__ import annotations
import argparse, importlib.util, json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("taiwei_asset_runtime",HERE/"asset_library_runtime.py")
rt=importlib.util.module_from_spec(spec); spec.loader.exec_module(rt)

PACKS={
 "v2":"generated_assets/TaiWei_HeroAssetPack_V2.blend",
 "v3":"generated_assets/TaiWei_ExpansionAssetPack_V3.blend",
 "v4":"generated_assets/TaiWei_SiteGardenPack_V4.blend",
 "v5":"generated_assets/TaiWei_RoofTimberPack_V5.blend",
}
SELECT={
 "v2":["TW_HERO_LANTERN_01","TW_HERO_CENSER_01","TW_HERO_BALUSTRADE_01"],
 "v3":["TW_V3_STONE_LION_MALE","TW_V3_STONE_LION_FEMALE","TW_V3_PALACE_GATE","TW_V3_DRUM_STONE"],
 "v4":["TW_V4_TERRACE_STEPS","TW_V4_IMPERIAL_RAMP","TW_V4_BALUSTRADE_STRAIGHT",
       "TW_V4_MOON_GATE","TW_V4_WHITE_WALL","TW_V4_SCREEN_WALL","TW_V4_BRONZE_VAT","TW_V4_ARCH_BRIDGE"],
 "v5":["TW_V5_COLUMN_SHAFT","TW_V5_COLUMN_CAPITAL","TW_V5_EAVE_TILE_ROW","TW_V5_SPARROW_BRACE"],
}

def args():
    tail=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="generated_assets/TaiWei_AssetIntegration_Study.blend")
    p.add_argument("--report",default="generated_assets/taiwei-asset-integration-report.json")
    p.add_argument("--review-dir",default="docs/assets/integration_study")
    return p.parse_args(tail)

def reset():
    s=bpy.context.scene
    for o in list(bpy.data.objects): bpy.data.objects.remove(o,do_unlink=True)
    for c in list(bpy.data.collections):
        if c.name!=s.collection.name:bpy.data.collections.remove(c)
    s.name="TaiWei_Asset_Integration_Study"
    return s

def mat(name,color,rough=.6,metal=.0):
    m=bpy.data.materials.new(name);m.use_nodes=True
    b=next(n for n in m.node_tree.nodes if n.type=="BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value=(*color,1);b.inputs["Roughness"].default_value=rough;b.inputs["Metallic"].default_value=metal
    return m

def cube(name,size,loc,material,col):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.object;o.name=name;o.scale=(size[0]/2,size[1]/2,size[2]/2)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if material:o.data.materials.append(material)
    for uc in list(o.users_collection):uc.objects.unlink(o)
    col.objects.link(o)
    return o

def look_at(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()

def area(name,loc,energy,size,color,target):
    d=bpy.data.lights.new(name,"AREA");d.energy=energy;d.size=size;d.color=color
    o=bpy.data.objects.new(name,d);bpy.context.scene.collection.objects.link(o);o.location=loc;look_at(o,target)

def setup_render(s):
    s.render.engine="BLENDER_EEVEE_NEXT"
    s.render.resolution_x=1600;s.render.resolution_y=900;s.render.resolution_percentage=100
    s.render.image_settings.file_format="PNG";s.render.image_settings.color_mode="RGB"
    if s.world is None:s.world=bpy.data.worlds.new("IntegrationWorld")
    s.world.color=(.018,.024,.031)
    area("Key",(-14,-18,22),4200,12,(1,.74,.50),(0,1,1.6))
    area("Fill",(15,-4,15),2500,10,(.42,.62,1),(0,1,1.4))
    area("Rim",(0,18,20),3200,11,(.70,.84,1),(0,2,1.8))
    d=bpy.data.cameras.new("IntegrationCamera");d.lens=54
    cam=bpy.data.objects.new("IntegrationCamera",d);s.collection.objects.link(cam);s.camera=cam
    return cam

def render(s,cam,path,loc,target,lens=54):
    cam.location=loc;cam.data.lens=lens;look_at(cam,target)
    s.render.filepath=str(Path(path).resolve());bpy.ops.render.render(write_still=True)

def main():
    a=args();out=Path(a.output);rep=Path(a.report);review=Path(a.review_dir)
    out.parent.mkdir(parents=True,exist_ok=True);rep.parent.mkdir(parents=True,exist_ok=True);review.mkdir(parents=True,exist_ok=True)
    s=reset()
    col=bpy.data.collections.new("Integrated_Assets");s.collection.children.link(col)
    loaded={}
    for key,path in PACKS.items():
        p=Path(path)
        if not p.exists() or p.stat().st_size<100000:
            raise RuntimeError(f"Pack binary missing or still LFS pointer: {path}")
        loaded.update(rt.append_selected_assets(path,SELECT[key],col))

    ground_mat=mat("Study_Stone_Paving",(.21,.22,.20),.78)
    water_mat=mat("Study_Water",(.025,.10,.14),.24,.05)
    cube("COURT_GROUND",(18,18,.18),(0,0,-.10),ground_mat,col)
    cube("BRIDGE_WATER",(10,4,.06),(0,-7,.0),water_mat,col)

    # Main ceremonial axis.
    rt.place(loaded["TW_V3_PALACE_GATE"],(0,5.4,0),(0,0,0),1.0)
    rt.place(loaded["TW_V4_TERRACE_STEPS"],(0,1.1,0),(0,0,0),1.05)
    rt.place(loaded["TW_V4_IMPERIAL_RAMP"],(0,2.9,0),(0,0,0),.92)
    rt.place(loaded["TW_V3_STONE_LION_MALE"],(-2.25,3.25,0),(0,0,-math.pi/2),.95)
    rt.place(loaded["TW_V3_STONE_LION_FEMALE"],(2.25,3.25,0),(0,0,-math.pi/2),.95)
    rt.place(loaded["TW_V3_DRUM_STONE"],(-3.65,4.75,0),(0,0,-math.pi/2),.90)

    # Side walls/gates make scale inconsistencies immediately visible.
    rt.place(loaded["TW_V4_MOON_GATE"],(-6.6,4.8,0),(0,0,0),.95)
    rt.place(loaded["TW_V4_WHITE_WALL"],(-6.6,.7,0),(0,0,math.pi/2),.92)
    rt.place(loaded["TW_V4_SCREEN_WALL"],(6.4,4.4,0),(0,0,0),.90)

    # Repeated modules check that roots behave as movable scene assets.
    rt.place(loaded["TW_V4_BALUSTRADE_STRAIGHT"],(-4.0,.2,0),(0,0,math.pi/2),.92)
    rt.place(loaded["TW_HERO_BALUSTRADE_01"],(4.0,.2,0),(0,0,math.pi/2),.92)
    rt.place(loaded["TW_V4_BRONZE_VAT"],(-4.4,3.0,0),(0,0,0),.82)
    rt.place(loaded["TW_HERO_CENSER_01"],(4.4,3.0,0),(0,0,0),.82)
    rt.place(loaded["TW_HERO_LANTERN_01"],(-3.25,5.15,0),(0,0,0),.78)

    # Timber/roof family placed as a scale-reference rack near the gate.
    rt.place(loaded["TW_V5_COLUMN_SHAFT"],(-1.8,6.3,0),(0,0,0),.88)
    rt.place(loaded["TW_V5_COLUMN_CAPITAL"],(-1.8,6.3,4.15),(0,0,0),.88)
    rt.place(loaded["TW_V5_EAVE_TILE_ROW"],(0,7.0,4.75),(0,0,0),.78)
    rt.place(loaded["TW_V5_SPARROW_BRACE"],(1.95,6.4,3.15),(0,0,0),.82)

    # Bridge is isolated at the foreground water strip for a dedicated camera.
    rt.place(loaded["TW_V4_ARCH_BRIDGE"],(0,-7.0,0),(0,0,0),1.0)

    cam=setup_render(s)
    render(s,cam,review/"01_courtyard_axis.png",(0,-11,8.0),(0,2.7,1.6),52)
    render(s,cam,review/"02_gate_scale.png",(-10,-2,6.2),(0,4.1,1.8),58)
    render(s,cam,review/"03_bridge_context.png",(7,-14,5.0),(0,-7,.9),60)

    bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()))
    roots=[o for o in s.objects if o.get("asset_id")]
    report={
      "scene":s.name,"selected_asset_count":len(roots),"selected_asset_ids":sorted(o["asset_id"] for o in roots),
      "source_packs":PACKS,"review_frames":3,
      "cross_pack_load_ok":len(roots)==sum(len(v) for v in SELECT.values()),
      "protected_scene_safe":True
    }
    assert report["cross_pack_load_ok"],(len(roots),sum(len(v) for v in SELECT.values()))
    rep.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("TAIWEI_ASSET_INTEGRATION_OK",json.dumps(report,ensure_ascii=False))

if __name__=="__main__":main()
