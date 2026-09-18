# -*- coding: utf-8 -*-
"""
太微仙宫 Blender -> UE5 自动化切片导出脚本
将 TaiWei_Expand.blend 的 12 个模块化集合逐一导出为 UE5 规范的 FBX 资产
"""
import bpy
import os
import sys

OUTPUT_DIR = r"D:\UnrealProjects\Assets_FBX"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"[UE5 Exporter] 正在初始化导出任务，目标路径: {OUTPUT_DIR}")

# 需要导出的静态网格集合列表
TARGET_COLLECTIONS = [
    "01_山体地形",
    "02_台基庭院",
    "03_殿阁木构",
    "04_琉璃瓦作",
    "05_门窗雕饰",
    "06_廊桥园墙",
    "07_池水飞瀑",
    "08_松竹花木",
    "09_草花庭石",
    "10_庭院陈设",
]

total_exported = 0

for coll_name in TARGET_COLLECTIONS:
    coll = bpy.data.collections.get(coll_name)
    if not coll:
        print(f"[跳过] 集合未找到: {coll_name}")
        continue

    # 取消全选
    bpy.ops.object.select_all(action='DESELECT')
    
    # 获取该集合中的所有网格对象
    objects_in_coll = [obj for obj in coll.all_objects if obj.type == 'MESH']
    if not objects_in_coll:
        print(f"[跳过] 集合内无网格对象: {coll_name}")
        continue
        
    for obj in objects_in_coll:
        obj.select_set(True)
        
    bpy.context.view_layer.objects.active = objects_in_coll[0]
    
    out_fbx = os.path.join(OUTPUT_DIR, f"{coll_name}.fbx")
    print(f"[导出中] {coll_name} -> {out_fbx} (包含 {len(objects_in_coll)} 个网格)")
    
    # 针对虚幻引擎 FBX 规范进行导出设置：
    # 1. forward='-Z', up='Y' 或者全局自动适配
    # 2. apply_unit_scale=True (适配 UE 厘米单位)
    # 3. use_selection=True (仅导出当前集合)
    bpy.ops.export_scene.fbx(
        filepath=out_fbx,
        use_selection=True,
        global_scale=1.0,
        apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_ALL',
        axis_forward='-Z',
        axis_up='Y',
        bake_space_transform=True,
        object_types={'MESH'},
        use_mesh_modifiers=True,
        mesh_smooth_type='FACE',
        add_leaf_bones=False,
        primary_bone_axis='Y',
        secondary_bone_axis='X',
        use_armature_deform_only=True,
        bake_anim=False
    )
    total_exported += len(objects_in_coll)

print(f"[UE5 Exporter] 导出完成！共导出 {total_exported} 个网格对象至 {OUTPUT_DIR}")
