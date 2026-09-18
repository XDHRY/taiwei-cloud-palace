@echo off
setlocal EnableExtensions

for %%I in ("%~dp0..\..") do set "ROOT=%%~fI"
if not defined BLENDER set "BLENDER=D:\blender-portable\blender.exe"

set "GEN=%ROOT%\blender\src\taiwei_cloud_palace_generator.py"
set "AUDIT=%ROOT%\blender\scripts-rebuild\audit_float.py"
set "SHOTS=%ROOT%\blender\scripts-rebuild\render_defect_shots.py"
if not defined REBUILD set "REBUILD=%ROOT%\build\TaiWei_WukongRebuild"

if not exist "%BLENDER%" (
  echo [ERROR] missing Blender: %BLENDER%
  echo Set BLENDER to your blender.exe path and rerun.
  exit /b 2
)
if not exist "%GEN%" (
  echo [ERROR] missing generator: %GEN%
  exit /b 3
)
if not exist "%AUDIT%" (
  echo [ERROR] missing audit script: %AUDIT%
  exit /b 4
)
if not exist "%SHOTS%" (
  echo [ERROR] missing render script: %SHOTS%
  exit /b 5
)

if not exist "%REBUILD%" mkdir "%REBUILD%"

set "TAIWEI_QUALITY=HIGH"
set "TAIWEI_CLEAR=1"
set "TAIWEI_SAVE=1"
set "TAIWEI_OUTPUT_DIRECTORY=%REBUILD%"
set "TAIWEI_PROJECT_FILENAME=TaiWei_Wukong_HIGH.blend"
set "TAIWEI_TEXTURE_DIR=%ROOT%\assets\textures_wukong"
set "TAIWEI_SHOT_DIR=%REBUILD%\shots_high"

"%BLENDER%" --background --python "%GEN%" --python "%AUDIT%" --python "%SHOTS%" > "%REBUILD%\rebuild_v2.log" 2>&1
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" echo [ERROR] rebuild failed; see %REBUILD%\rebuild_v2.log
exit /b %RC%
