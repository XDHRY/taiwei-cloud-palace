@echo off
setlocal
set BLENDER=D:\blender-portable\blender.exe
set BLEND=E:\UserData\xdrhh\.openclaw\workspace\taiwei_video\TaiWei_WukongRebuild\TaiWei_Wukong_HIGH.blend
set SCRIPT=E:\UserData\xdrhh\.openclaw\workspace\tools\render_full_720_pipeline.py

"%BLENDER%" --background "%BLEND%" --python "%SCRIPT%"
