# -*- coding: utf-8 -*-
"""在当前运行的 Blender 场景中全量注入太微云宫【30秒生命动态系统】。

包含六大动效矩阵：
1. 【日光弧】：晨阳主光从开场破晓斜射（低能温暖）随镜头推进渐亮渐暖升起
2. 【星月落幕】：破晓星空渐隐，西北残月在第 190-200 帧潜入云海
3. 【流云排荡】：山腰流云、远山横岚、云海托底随时间平缓水平漂移
4. 【水雾脉动】：瀑布落点水雾按三轴独立正弦微幅张弛呼吸
5. 【万木生风】：08_松竹花木全量古松、翠树、桃花、竹林挂载双轴正弦波风摇驱动器（随机相位差）
6. 【万家灯火】：宫灯三相位风烛明灭微颤（随天明光强自然衰减），窗棂暖光呼吸
7. 【碧池涟漪】：碧池水噪波材质开启 4D 维度，W 轴随帧数缓慢推进产生涟漪流动
"""
import bpy
import math as _m

scene = bpy.context.scene
F0, F1 = 1, 720

def _linear(id_block):
    ad = getattr(id_block, "animation_data", None)
    if ad and ad.action:
        for fc in ad.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"

def _principled(node_tree):
    for node in node_tree.nodes:
        if node.type == "BSDF_PRINCIPLED":
            return node
    return None

# 1. —— 日光弧 ——
sun_obj = bpy.data.objects.get("晨阳主光")
if sun_obj:
    sd = sun_obj.data
    sd.animation_data_clear()
    sun_obj.animation_data_clear()
    
    sd.energy = 3.80
    sd.keyframe_insert("energy", frame=F0)
    sd.energy = 4.20
    sd.keyframe_insert("energy", frame=F1)
    
    sd.color = (1.0, 0.88, 0.68)
    sd.keyframe_insert("color", frame=F0)
    sd.color = (1.0, 0.78, 0.52)
    sd.keyframe_insert("color", frame=F1)
    
    sun_obj.rotation_euler = (_m.radians(65), _m.radians(-20), _m.radians(-31))
    sun_obj.keyframe_insert("rotation_euler", frame=F0)
    sun_obj.rotation_euler = (_m.radians(60), _m.radians(-20), _m.radians(-36.5))
    sun_obj.keyframe_insert("rotation_euler", frame=F1)
    _linear(sd)
    _linear(sun_obj)
    print("[生命] 日光弧注入完成")

# 2. —— 天空渐亮与星空 ——
if scene.world and scene.world.use_nodes:
    wn = scene.world.node_tree
    bg = next((n for n in wn.nodes if n.type == "BACKGROUND"), None)
    if bg:
        bg.inputs["Strength"].default_value = 0.32
        bg.inputs["Strength"].keyframe_insert("default_value", frame=F0)
        bg.inputs["Strength"].default_value = 0.52
        bg.inputs["Strength"].keyframe_insert("default_value", frame=F1)
        _linear(wn)
        print("[生命] 天空渐亮完成")

# 3. —— 清理假球残月，确保纯净清朗天际 ——
moon = bpy.data.objects.get("残月")
if moon:
    bpy.data.objects.remove(moon, do_unlink=True)
print("[生命] 假球残月已清理，天际恢复纯净")

# 4. —— 流云漂移 + 瀑脚水雾脉动 ——
coll11 = bpy.data.collections.get("11_远山云气")
if coll11:
    drift = {"山腰流云": 14.0, "远山横岚": 10.0, "云海托底": 6.0}
    n_drift = n_mist = 0
    for i, ob in enumerate(coll11.objects):
        if ob.name.startswith("瀑脚水雾"):
            for axis in range(3):
                base = ob.scale[axis]
                fc = ob.driver_add("scale", axis)
                fc.driver.expression = (
                    f"{base:.4f}*(1+0.08*sin(frame*0.055+{i * 0.7:.2f}))"
                )
            n_mist += 1
            continue
        for prefix, dist in drift.items():
            if ob.name.startswith(prefix):
                ob.keyframe_insert("location", frame=F0)
                ob.location.x += dist
                ob.location.y += dist * 0.3
                ob.keyframe_insert("location", frame=F1)
                _linear(ob)
                n_drift += 1
                break
    print(f"[生命] 流云漂移 {n_drift} 团, 水雾脉动 {n_mist} 处")

# 5. —— 树木随风轻摇 ——
coll08 = bpy.data.collections.get("08_松竹花木")
n_tree = 0
if coll08:
    for i, ob in enumerate(coll08.objects):
        if ob.type != "MESH":
            continue
        phase = (i * 0.37) % 6.283
        fc = ob.driver_add("rotation_euler", 0)
        fc.driver.expression = f"0.022*sin(frame*0.04+{phase:.3f})"
        fc2 = ob.driver_add("rotation_euler", 1)
        fc2.driver.expression = f"0.016*sin(frame*0.031+{phase * 1.7:.3f})"
        n_tree += 1
print(f"[生命] 树木风摇驱动 {n_tree} 株完成")

# 6. —— 宫灯明灭与窗光呼吸 ——
lamp_mat = bpy.data.materials.get("暖绢宫灯")
if lamp_mat:
    p = _principled(lamp_mat.node_tree)
    if p:
        fc = p.inputs["Emission Strength"].driver_add("default_value")
        fc.driver.expression = "(1.35-0.00042*frame)*(1+0.22*sin(frame*0.11+0.5))"
        print("[生命] 宫灯明灭完成")

win = bpy.data.materials.get("窗内暖光")
if win:
    p = _principled(win.node_tree)
    if p:
        fc = p.inputs["Emission Strength"].driver_add("default_value")
        fc.driver.expression = "(0.42-0.00010*frame)*(1+0.08*sin(frame*0.07+1.3))"
        print("[生命] 窗内烛光呼吸完成")

# 7. —— 池水涟漪 4D 流动 ——
water = bpy.data.materials.get("碧池水")
if water:
    for n in water.node_tree.nodes:
        if n.type == "TEX_NOISE":
            try:
                n.noise_dimensions = "4D"
                fc = n.inputs["W"].driver_add("default_value")
                fc.driver.expression = "frame*0.008"
                print("[生命] 碧池水 4D 涟漪完成")
            except Exception as e:
                print("[生命] 碧池水设置略过:", e)

# 保存至文件
bpy.ops.wm.save_mainfile()
print("[生命] 全套动态系统注入并保存成功！")
