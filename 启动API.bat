@echo off
chcp 65001 >nul 2>&1
title ok-ww API Server
cd /d "%~dp0"
echo Starting ok-ww API server...
echo http://127.0.0.1:8270
echo.
"D:\software\ok-ww\data\apps\ok-ww\python\python.exe" server.py
pause
