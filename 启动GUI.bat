@echo off
chcp 65001 >nul 2>&1
title ok-ww GUI
cd /d "%~dp0"
echo Starting ok-ww GUI...
"D:\software\ok-ww\data\apps\ok-ww\python\python.exe" main.py
pause
