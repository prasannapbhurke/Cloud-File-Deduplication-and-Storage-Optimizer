@echo off
title Cloudflare Quick Tunnel - Cloud File Deduplication
echo ====================================================================
echo   LAUNCHING CLOUDFLARE QUICK TUNNEL (DIRECT HTTPS - NO PASSWORD)
echo   Targeting Local Web Server: http://localhost:5000
echo ====================================================================
echo.
echo Make sure your app is running (e.g. run 'run_app.bat' first).
echo.
echo Connecting to Cloudflare's Global Network...
echo.

set "CLOUDFLARED=C:\Program Files (x86)\cloudflared\cloudflared.exe"
if not exist "%CLOUDFLARED%" (
    set "CLOUDFLARED=cloudflared"
)

"%CLOUDFLARED%" tunnel --url http://localhost:5000
pause
