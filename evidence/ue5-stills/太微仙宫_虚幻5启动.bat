@echo off
chcp 65001 >nul
title 太微洞天世界 · 虚幻 5 渲染工程 (量身定制版)
cd /d "D:\Epic Games\UE_5.4\Engine\Binaries\Win64"

set PROJECT=D:\UnrealProjects\TaiWei_Cinema\TaiWei_Cinema.uproject

echo ====================================================================
echo  太微洞天世界 · 虚幻 5 渲染工程启动中...
echo  引擎版本：Unreal Engine 5.4.4 LTS
echo  硬件适配：MX450 (2GB VRAM) + 24GB 共享内存保护
echo  渲染管线：TSR 时间空间重构 + 离线切片渲染支持
echo ====================================================================
echo.

start "" "D:\Epic Games\UE_5.4\Engine\Binaries\Win64\UnrealEditor.exe" "%PROJECT%"
exit /b 0
