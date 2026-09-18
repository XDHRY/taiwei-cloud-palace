@echo off
chcp 65001 >nul
title 太微云宫 · 快速预览 180 帧
cd /d E:\UserData\xdrhh\.openclaw\workspace

set BLENDER=D:\blender-portable\blender.exe
set FFMPEG=C:\Users\xdrhh\bin\ffmpeg.exe
set DESKTOP=E:\zhuomian
set BLEND=taiwei_video\TaiWei_Video.blend

echo ============================================================
echo  太微云宫 · 快速预览
echo  沿正式巡航路径每 4 帧取 1 帧，共 180 帧，半分辨率
echo  运镜：迎仙石阶 - 山门前庭 - 荷塘虹桥 - 廊庑 - 正殿 - 云外远山
echo  预计 20 分钟
echo ============================================================
echo.

%BLENDER% -b %BLEND% -P taiwei_preview.py
if errorlevel 1 goto fail

echo.
echo ----- 合成 7 秒速览（180 帧 @24fps，动作顺滑）-----
%FFMPEG% -y -framerate 24 -i taiwei_video\preview\p_%%04d.png -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -movflags +faststart "%DESKTOP%\太微云宫_样片_7秒速览.mp4"
if errorlevel 1 goto fail

echo ----- 合成 30 秒原速节奏参考（同样 180 帧 @6fps，会顿）-----
%FFMPEG% -y -framerate 6 -i taiwei_video\preview\p_%%04d.png -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -movflags +faststart "%DESKTOP%\太微云宫_样片_30秒节奏参考.mp4"

echo.
echo ============================================================
echo  完成，样片已放到桌面，正在打开：
echo    %DESKTOP%\太微云宫_样片_7秒速览.mp4
echo    %DESKTOP%\太微云宫_样片_30秒节奏参考.mp4
echo ============================================================
start "" "%DESKTOP%\太微云宫_样片_7秒速览.mp4"
pause
exit /b 0

:fail
echo.
echo [错误] 上一步失败，请把窗口内容截图发给素。
pause
exit /b 1
