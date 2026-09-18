@echo off
setlocal
set BLENDER=D:\blender-portable\blender.exe
set GEN=E:\UserData\xdrhh\.openclaw\workspace\taiwei_cloud_palace_generator.py
set REBUILD=E:\UserData\xdrhh\.openclaw\workspace\taiwei_video\TaiWei_WukongRebuild
if not exist "%BLENDER%" (
  echo missing blender
  exit /b 2
)
set TAIWEI_QUALITY=HIGH
set TAIWEI_CLEAR=1
set TAIWEI_SAVE=1
set TAIWEI_OUTPUT_DIRECTORY=%REBUILD%
set TAIWEI_PROJECT_FILENAME=TaiWei_Wukong_HIGH.blend
set TAIWEI_SHOT_DIR=%REBUILD%\shots_high
"%BLENDER%" --background --python "%GEN%" --python "%REBUILD%\audit_float.py" --python "%REBUILD%\render_defect_shots.py" > "%REBUILD%\rebuild_v2.log" 2>&1
exit /b %ERRORLEVEL%
