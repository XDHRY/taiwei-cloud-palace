#!/usr/bin/env python3
"""Validate Taiwei asset-pack catalog without requiring Blender."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CATALOG=ROOT/"blender"/"asset-packs.json"

def main():
    data=json.loads(CATALOG.read_text(encoding="utf-8"))
    assert data["project"]=="taiwei-cloud-palace"
    assert data["schema_version"]>=4
    packs=data.get("packs",[])
    assert len(packs)>=4

    pack_ids=set()
    asset_ids=set()
    total=0
    summary=[]

    for pack in packs:
        pid=pack["id"]
        assert pid not in pack_ids, f"duplicate pack id: {pid}"
        pack_ids.add(pid)
        assert pack.get("protected_scene_safe") is True, pid
        assert pack.get("rebuild_contract")=="deterministic_geometry_no_llm_required", pid

        factory=ROOT/pack["factory"]
        assert factory.is_file(), f"missing factory for {pid}: {factory}"
        preview=pack.get("preview_renderer")
        if preview:
            assert (ROOT/preview).is_file(), f"missing preview renderer for {pid}: {preview}"

        blend=pack.get("blend","")
        report=pack.get("report","")
        assert blend.startswith("generated_assets/") and blend.endswith(".blend"), (pid,blend)
        assert report.startswith("generated_assets/") and report.endswith(".json"), (pid,report)

        assets=pack.get("assets",[])
        assert assets, f"empty asset pack: {pid}"
        local=set()
        categories=set()
        for a in assets:
            aid=a["id"]
            assert aid not in local, f"duplicate id inside {pid}: {aid}"
            assert aid not in asset_ids, f"global duplicate asset id: {aid}"
            local.add(aid); asset_ids.add(aid)
            assert a.get("name_cn"), (pid,aid)
            assert a.get("category"), (pid,aid)
            categories.add(a["category"])
        total += len(assets)
        summary.append((pid,len(assets),len(categories)))

    assert total>=72, f"expected at least 72 cataloged assets, got {total}"
    print("TAIWEI_ASSET_CATALOG_OK")
    print("schema_version",data["schema_version"])
    print("pack_count",len(packs))
    print("asset_count",total)
    for pid,count,cats in summary:
        print(pid,count,"assets",cats,"categories")

if __name__=="__main__":
    main()
