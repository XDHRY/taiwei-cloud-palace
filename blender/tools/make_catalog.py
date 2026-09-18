# -*- coding: utf-8 -*-
import os
import json
import re

LIB_DIR = r"E:\UserData\xdrhh\.openclaw\workspace\taiwei_video\asset_library"
PROMPT_JSON = r"E:\UserData\xdrhh\.openclaw\workspace\taiwei_video\research\texture_prompts_v3.json"

prompt_map = {}
if os.path.exists(PROMPT_JSON):
    try:
        data = json.load(open(PROMPT_JSON, "r", encoding="utf-8"))
        items = data if isinstance(data, list) else data.get("textures", data.get("items", []))
        for it in items:
            tid = it.get("id", "")
            p = it.get("prompt", "")
            m = re.search(r"of ([^()]+?)\s*\(", p)
            zh = m.group(1).strip() if m else tid
            prompt_map[tid] = zh
    except Exception as e:
        print("Error loading prompts:", e)

bindings_map = {
    "tex-liuli-blue": "tile/tile_light/tile_dark 蓝琉璃屋面",
    "tex-banwa": "roof 板瓦底瓦",
    "tex-tile-back": "roof 筒瓦背垄",
    "tex-pavilion-wadang": "wadang 攒尖亭瓦当",
    "tex-bluestone": "stone 阶基青石",
    "tex-white-marble": "ivory 汉白玉构件",
    "tex-bridge-white-stone": "bridge_deck 桥面白石",
    "tex-stair-tread-stone": "stair_tread 踏跺条石",
    "tex-balustrade-post-relief": "balustrade 栏板望柱雕石",
    "tex-paifang-bluestone": "paifang_stone 牌坊青石",
    "tex-drum-stone-baogu": "baogu_stone 抱鼓石",
    "tex-stone-lantern-carving": "lantern_stone 石灯笼青石",
    "tex-well-curb-stone": "well_stone 井栏石",
    "tex-chessboard-stone-table": "chess_jade 棋枰玉石",
    "tex-cliff-rock": "rock 崖壁山岩",
    "tex-moss-rock-close": "scholar 近景苔石",
    "tex-stratified-rock-mid": "far_near/far_mid 中景叠层山岩",
    "tex-moss-stone": "moss 青苔石面",
    "tex-lakebed-pebbles": "lakebed 湖底卵石",
    "tex-underwater-coral-rock": "coral 水底珊瑚石",
    "tex-stone-lion-guardian": "lion_stone 守门石狮白玉",
    "tex-bixi-turtle-stele": "stele_stone 龟趺御碑石",
    "tex-sundial-marble": "sundial_marble 白玉日晷",
    "tex-dharani-pillar-script": "dharani 经幢刻纹石",
    "tex-walnut": "wood 门窗隔扇核桃木",
    "tex-chuihua-carved-wood": "carved_wood 垂花门雕木",
    "tex-cinnabar": "red 朱红立柱/额枋",
    "tex-pillar-vermilion-close": "pillar_red 金柱朱漆",
    "tex-ancient-pine-bark": "古松树皮(备用)",
    "tex-gilt-bronze": "gold 鎏金构件/宝顶",
    "tex-doorknocker-taotie-gold": "door_gold 门环饕餮鎏金",
    "tex-windchime-bronze-plate": "bell_bronze 风铃铁马铜片",
    "tex-censer-beast-face": "censer_bronze 古铜香鼎饕餮纹",
    "tex-temple-bell-inscriptions": "bell_cast 铸钟铭文铜",
    "tex-cauldron-bronze-motif": "ding_bronze 夔纹铜鼎",
    "tex-drum-head-leather": "drum_leather 鼓亭大鼓皮革",
    "tex-crane-bronze-cast": "crane_cast 铜鹤铸羽",
    "tex-cloud-bronze": "bronze 云纹青铜构件",
    "tex-patina-bronze": "patina 氧化绿锈青铜",
    "tex-canopy-brocade-silk": "canopy_silk 仪仗伞盖团花绢",
    "tex-ceremonial-banner-fabric": "banner_silk 仪仗幡旗织金",
    "tex-lush-grassland": "grass/grass_light 宫苑草地",
    "tex-velvet-moss-ground": "earth 天鹅绒苔地",
    "tex-crane-feather-down": "feather 仙鹤羽翼",
    "tex-koi-fish-scales": "koi 锦鲤金鳞",
    "tex-water-ripples": "water 水面二段涟漪Normal/Bump",
    "tex-waterfall-sheet": "fall 飞瀑水幕",
    "tex-nine-dragon-wall": "dragon_wall 九龙琉璃照壁",
    "tex-caisson-paint": "beam 梁枋彩画",
    "tex-lattice-paper": "window 透光明瓦格纸",
    "tex-lattice-wood": "darkwood 隔扇暗木格心",
    "tex-lotus-leaf-pad": "bb_lotus 浮水莲叶贴板",
    "tex-peach-petal-cluster": "bb_petal 水面浮花瓣贴板",
    "tex-reed-tassel": "bb_reed 驳岸芦荻立板",
    "tex-distant-mountain-mist": "bb_farhill 极远山岫立板",
    "tex-bamboo-leaf-cluster": "bb_bamboo 竹叶贴板(备用)",
    "tex-pine-needle-cluster": "bb_pine 松针贴板(备用)",
    "tex-wispy-mist-sheet": "bb_mist 山岚薄雾(备用)",
    "tex-volume-cumulus-cloud": "bb_cumulus 祥云体积块(备用)",
    "tex-night-milkyway-nebula": "bb_milkyway 星汉夜穹(备用)",
}

catalog = []
md_lines = [
    "# 太微云宫 · 全量 AI 美术资产总库目录",
    "",
    "本资产总库收录太微云宫项目全部生图贴图、工程图鉴与氛围参考，分门别类归档以备后续开发复用。",
    "",
]

for root_dir, dirs, files in os.walk(LIB_DIR):
    pngs = [f for f in files if f.endswith(".png")]
    if not pngs:
        continue
    rel_category = os.path.relpath(root_dir, LIB_DIR).replace("\\", "/")
    md_lines.append(f"## {rel_category} ({len(pngs)} 项)")
    md_lines.append("| 文件名 | 中文名称 | 资产类型 | 当前绑定组件 / 规划用途 |")
    md_lines.append("|---|---|---|---|")

    for f in sorted(pngs):
        base_id = os.path.splitext(f)[0]
        zh_name = prompt_map.get(base_id, "")
        if not zh_name:
            if "guide-" in f:
                zh_name = "工程图鉴 · " + f.replace("guide-", "").replace(".png", "")
            elif "atm-" in f:
                zh_name = "氛围参考 · " + f.replace("atm-", "").replace(".png", "")
            else:
                zh_name = base_id

        kind = "texture" if "textures" in rel_category else ("guide" if "guides" in rel_category else "atmosphere")
        bound = bindings_map.get(base_id, "高阶扩展备用")

        catalog.append({
            "file": f"{rel_category}/{f}",
            "zh": zh_name,
            "kind": kind,
            "bound": bound
        })
        md_lines.append(f"| `{f}` | {zh_name} | {kind} | {bound} |")
    md_lines.append("")

# Write catalog.json
with open(os.path.join(LIB_DIR, "catalog.json"), "w", encoding="utf-8") as f:
    json.dump(catalog, f, ensure_ascii=False, indent=2)

# Write ASSET_CATALOG.md
with open(os.path.join(LIB_DIR, "ASSET_CATALOG.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(md_lines))

# Write report
report_path = r"E:\UserData\xdrhh\.openclaw\workspace\taiwei_video\research\asset_library_report.md"
with open(report_path, "w", encoding="utf-8") as f:
    f.write(f"# 资产库构建完成报告\n\n总入库资产：{len(catalog)} 项\n\n- 贴图库：81 项（9大类）\n- 工程图鉴：20 项\n- 氛围参考：8 项\n\n索引文件：\n- JSON: `{os.path.join(LIB_DIR, 'catalog.json')}`\n- Markdown: `{os.path.join(LIB_DIR, 'ASSET_CATALOG.md')}`\n")

print(f"Catalog generated: {len(catalog)} total assets indexed!")
