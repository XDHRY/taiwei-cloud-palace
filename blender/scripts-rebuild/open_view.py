import bpy

# 打开后自动进入：04 中轴礼序相机 + EEVEE 实时渲染视图
scene = bpy.context.scene
cam = bpy.data.objects.get("04_中轴礼序")
if cam is not None and cam.type == "CAMERA":
    scene.camera = cam

for window in bpy.context.window_manager.windows:
    for area in window.screen.areas:
        if area.type == "VIEW_3D":
            for space in area.spaces:
                if space.type == "VIEW_3D":
                    space.shading.type = "RENDERED"
                    region = space.region_3d
                    if region is not None:
                        region.view_perspective = "CAMERA"

print("太微云宫 HIGH 已就绪：渲染视图 + 04 中轴礼序相机")
