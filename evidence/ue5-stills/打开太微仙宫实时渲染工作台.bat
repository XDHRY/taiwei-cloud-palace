@echo off
chcp 65001 >nul
title 虚幻5太微仙宫工程与Unity对照监视器
cd /d "D:\Epic Games\UE_5.4\Engine\Binaries\Win64"

set PROJECT=D:\UnrealProjects\TaiWei_Cinema\TaiWei_Cinema.uproject

echo ====================================================================
echo  太微仙宫 · 双引擎协同渲染工作台
echo  正在启动虚幻5图形编辑器 (窗口化对齐与组件实时监视)...
echo  项目文件：%PROJECT%
echo ====================================================================

start "" "UnrealEditor.exe" "%PROJECT%" /Game/TaiWei_Assets/TaiWei_MainScene -windowed -ResX=1600 -ResY=900
exit /b 0
