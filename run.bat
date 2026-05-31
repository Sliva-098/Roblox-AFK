@echo off
title Roblox Anti-AFK Pro Launcher

rem Force the working directory to be the directory of this batch file
rem (Crucial when running "As Administrator" since it defaults to C:\Windows\System32)
cd /d "%~dp0"

cls

echo ===================================================
echo           Roblox Anti-AFK Pro Launcher
echo ===================================================
echo.

echo [INFO] Checking and installing required libraries...
python -m pip install --user pyautogui keyboard pygetwindow
echo.

echo [INFO] Launching Roblox Anti-AFK Pro...
echo.
python anti_afk.py

echo.
echo ===================================================
echo Launcher finished.
echo.
pause
