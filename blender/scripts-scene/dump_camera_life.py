"""只读审计：导出 TaiWei_Video.blend 的相机动画与生命系统驱动，供新场景迁移。"""
import bpy
import json

out = {"cameras": [], "animated_objects": [], "drivers": [], "frame_range": None}

scene = bpy.context.scene
out["frame_range"] = [scene.frame_start, scene.frame_end]
out["render_engine"] = scene.render.engine
out["resolution"] = [scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.resolution_percentage]

for obj in bpy.data.objects:
    ad = obj.animation_data
    if not ad:
        continue
    info = {"name": obj.name, "type": obj.type, "actions": [], "drivers": []}
    if ad.action:
        for fc in ad.action.fcurves:
            keys = [[round(k.co[0], 2), round(k.co[1], 5)] for k in fc.keyframe_points]
            info["actions"].append({
                "data_path": fc.data_path,
                "array_index": fc.array_index,
                "keys": keys,
            })
    for drv in ad.drivers:
        info["drivers"].append({
            "data_path": drv.data_path,
            "array_index": drv.array_index,
            "expression": drv.driver.expression,
        })
    if obj.type == "CAMERA":
        out["cameras"].append(info)
    elif info["actions"] or info["drivers"]:
        out["animated_objects"].append(info)

# 相机约束（跟随路径等）
constraints = []
for obj in bpy.data.objects:
    if obj.type == "CAMERA" and obj.constraints:
        for c in obj.constraints:
            constraints.append({
                "camera": obj.name, "type": c.type,
                "target": c.target.name if getattr(c, "target", None) else None,
            })
out["camera_constraints"] = constraints

# 曲线对象（可能的运镜路径）
out["curves"] = [
    {"name": o.name, "points": len(o.data.splines[0].bezier_points)
     if o.data.splines and o.data.splines[0].bezier_points else
     len(o.data.splines[0].points) if o.data.splines else 0}
    for o in bpy.data.objects if o.type == "CURVE"
]

path = "E:/UserData/xdrhh/.openclaw/workspace/taiwei_video/diag/camera_life_dump.json"
with open(path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("DUMPED", path, "cameras=", len(out["cameras"]),
      "animated=", len(out["animated_objects"]),
      "curves=", len(out["curves"]))
