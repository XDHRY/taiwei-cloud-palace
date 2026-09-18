@echo off
setlocal
chcp 65001 >nul
title 太微云宫 · 30秒巡航视频渲染管线

set BLENDER=D:\blender-portable\blender.exe
set BLEND_FILE=E:\UserData\xdrhh\.openclaw\workspace\taiwei_video\TaiWei_WukongRebuild\TaiWei_Wukong_HIGH.blend
set OUT_DIR=E:\zhuomian\太微云宫3D\05-样片成片\30秒巡航_1080P

if not exist "%BLENDER%" (
    echo [错误] 未找到 Blender: %BLENDER%
    pause
    exit /b 1
)

if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"

echo ========================================================
echo   太微云宫 · 30秒殿宇仙卷影视级漫游视频渲染
echo   引擎: Blender 4.5 EEVEE Next
echo   画幅: 1920x1080 (1080P @ 24fps)
echo   总帧数: 720 帧 (30 秒)
echo   相机: 巡航相机 (平滑贝塞尔三维飞行轨迹)
echo   输出目录: %OUT_DIR%
echo ========================================================
echo.

"%BLENDER%" --background "%BLEND_FILE%" --python-expr "import bpy; s=bpy.context.scene; s.camera=bpy.data.objects['巡航相机']; s.frame_start=1; s.frame_end=720; s.render.image_settings.file_format='FFMPEG'; s.render.ffmpeg.format='MPEG4'; s.render.ffmpeg.codec='H264'; s.render.ffmpeg.constant_rate_factor='PERC_LOSSLESS'; s.render.filepath=r'%OUT_DIR%\TaiWei_Palace_Tour_30s.mp4'; print('Rendering 30s tour video to:', s.render.filepath); bpy.ops.render.render(animation=True)"

echo.
echo ========================================================
echo   渲染完成！视频已保存至:
echo   %OUT_DIR%\TaiWei_Palace_Tour_30s.mp4
echo ========================================================
pause
