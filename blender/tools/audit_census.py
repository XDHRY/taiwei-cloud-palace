# audit_census.py — 在 Blender 内做只读场景普查(不保存)
import bpy, json
from collections import Counter

s = bpy.context.scene
out = {}
out['engine'] = s.render.engine
out['res'] = [s.render.resolution_x, s.render.resolution_y]
out['frame_range'] = [s.frame_start, s.frame_end]
out['view_transform'] = s.view_settings.view_transform
try:
    out['taa_samples'] = s.eevee.taa_render_samples
except Exception:
    pass
try:
    out['eevee'] = {'taa': s.eevee.taa_render_samples}
except Exception:
    pass

objs = list(bpy.data.objects)
out['n_objects'] = len(objs)

# 1) 按首词归类统计
cat = Counter()
for o in objs:
    key = o.name.split('_')[0].split('.')[0]
    cat[key] += 1
out['categories_top40'] = cat.most_common(40)

# 2) 类型统计
out['types'] = Counter(o.type for o in objs).most_common()

# 3) 相机清单
out['cameras'] = [[o.name, [round(v,1) for v in o.location]] for o in objs if o.type=='CAMERA']

# 4) 灯清单
out['lights'] = [[o.name, o.data.type, round(o.data.energy,1)] for o in objs if o.type=='LIGHT'][:30]

# 5) 斗拱相关对象
dg = [o.name for o in objs if ('斗拱' in o.name or '栱' in o.name)]
out['dougong_objs'] = [len(dg), dg[:8]]

# 6) 山/云/水 对象
def binfo(o):
    bb = [o.matrix_world @ __import__('mathutils').Vector(c) for c in o.bound_box]
    lo=[round(min(v[i] for v in bb),1) for i in range(3)]
    hi=[round(max(v[i] for v in bb),1) for i in range(3)]
    return lo, hi
mnt = [o for o in objs if '山' in o.name]
out['mountains'] = [[o.name, *binfo(o)] for o in mnt][:20]
cld = [o.name for o in objs if ('云' in o.name or '岚' in o.name or '雾' in o.name)]
out['clouds'] = [len(cld), cld[:12]]
wtr = [o for o in objs if ('水' in o.name or '池' in o.name or '湖' in o.name or '波' in o.name)]
out['waters'] = [[o.name, *binfo(o)] for o in wtr][:12]

# 7) 桥/亭/廊/楼/阁/塔/坊/门 主体建筑清单(去重前40)
arch = [o for o in objs if any(k in o.name for k in ('桥','亭','廊','楼','阁','塔','坊','门','殿','斋','轩','舫','榭')) and o.type=='MESH']
arch_main = {}
for o in arch:
    base = o.name.split('.')[0]
    if base not in arch_main:
        arch_main[base] = binfo(o)
out['arch_count'] = len(arch)
out['arch_main_first40'] = [[k, *v] for k,v in list(arch_main.items())[:40]]

# 8) 材质清单(按对象数)
mat_use = Counter()
for o in objs:
    if o.type=='MESH':
        for sl in o.material_slots:
            if sl.material: mat_use[sl.material.name]+=1
out['materials_top30'] = mat_use.most_common(30)

# 9) 地面/铺地/岛 对象
gnd = [o for o in objs if any(k in o.name for k in ('地','岛','岸','径','铺装','广场')) and o.type=='MESH']
out['grounds'] = [[o.name, *binfo(o)] for o in gnd][:15]

# 10) 世界设置
w = bpy.data.worlds[0] if bpy.data.worlds else None
if w and w.use_nodes:
    bg = [nd for nd in w.node_tree.nodes if nd.type=='BACKGROUND']
    out['world_bg'] = [[round(c,3) for c in bg[0].inputs[0].default_value[:3]], round(bg[0].inputs[1].default_value,2)] if bg else None

print('CENSUS_JSON_BEGIN')
print(json.dumps(out, ensure_ascii=False, default=str))
print('CENSUS_JSON_END')
