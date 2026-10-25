@echo off
cd /d "%~dp0"
title Live Public Tunnel - Cloud File Deduplication
echo ====================================================================
echo   CREATING LIVE PUBLIC INTERNET LINK (LOCALTUNNEL)
echo   Target: http://localhost:5000
echo ====================================================================
echo.
echo Make sure your app is running (e.g. by running run_app.bat first).
echo Starting tunnel...
echo.
npx --yes localtunnel --port 5000
pause
