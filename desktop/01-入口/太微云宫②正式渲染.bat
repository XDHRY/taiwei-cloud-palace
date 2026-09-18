@echo off
chcp 65001 >nul
title 太微云宫 · 正式渲染 720 帧
cd /d E:\UserData\xdrhh\.openclaw\workspace

set BLENDER=D:\blender-portable\blender.exe
set FFMPEG=C:\Users\xdrhh\bin\ffmpeg.exe
set DESKTOP=E:\zhuomian
set BLEND=taiwei_video\TaiWei_Video.blend
set LOG=taiwei_video\render.log

echo ============================================================
echo  太微云宫 · 正式渲染
echo  720 帧，1920x1080，24fps，30 秒
echo  运镜：迎仙石阶 - 山门前庭 - 荷塘虹桥 - 廊庑 - 正殿 - 云外远山
echo  预计 5 - 6 小时（建议过夜跑）
echo.
echo  中途关了窗口/断电都没关系：
echo  重新双击本脚本即可接着渲，已完成的帧会自动跳过。
echo ============================================================
echo.

echo [%date% %time%] ==== 渲染开始 ==== >> %LOG%
for %%C in ("1 120" "121 240" "241 360" "361 480" "481 600" "601 720") do (
  for /f "tokens=1,2" %%a in (%%C) do (
    echo ----- 第 %%a 至 %%b 帧 -----
    echo [%date% %time%] chunk %%a-%%b start >> %LOG%
    %BLENDER% -b %BLEND% -s %%a -e %%b -a >> %LOG% 2>&1
    echo [%date% %time%] chunk %%a-%%b done >> %LOG%
  )
)
echo [%date% %time%] ==== 帧渲染完成 ==== >> %LOG%

echo.
echo ----- 合成 H.265 主片 -----
%FFMPEG% -y -framerate 24 -i taiwei_video\frames\f_%%04d.png -vf "fade=t=in:st=0:d=1.0,fade=t=out:st=28.6:d=1.4" -c:v libx265 -preset slow -crf 16 -pix_fmt yuv420p -tag:v hvc1 "%DESKTOP%\TaiWei_CloudPalace_1080p24_h265.mp4"
if errorlevel 1 goto fail

echo ----- 合成 H.264 兼容版 -----
%FFMPEG% -y -framerate 24 -i taiwei_video\frames\f_%%04d.png -vf "fade=t=in:st=0:d=1.0,fade=t=out:st=28.6:d=1.4" -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -movflags +faststart "%DESKTOP%\TaiWei_CloudPalace_1080p24_h264.mp4"
if errorlevel 1 goto fail

echo [%date% %time%] ==== 全部完成 ==== >> %LOG%
echo.
echo ============================================================
echo  完成，成片已放到桌面：
echo    %DESKTOP%\TaiWei_CloudPalace_1080p24_h265.mp4   （主片）
echo    %DESKTOP%\TaiWei_CloudPalace_1080p24_h264.mp4   （兼容版）
echo ============================================================
start "" "%DESKTOP%\TaiWei_CloudPalace_1080p24_h264.mp4"
pause
exit /b 0

:fail
echo.
echo [错误] 上一步失败，请把窗口内容截图发给素。
pause
exit /b 1
