@echo off
title Cloud File Deduplication - Complete Live Launcher
echo ====================================================================
echo   LAUNCHING APP ^& CLOUDFLARE LIVE TUNNEL
echo ====================================================================
echo.
echo Starting Flask App Server...
start "Cloud File Deduplication - Flask Server" cmd /k "run_app.bat"

echo Waiting 3 seconds for server initialization...
timeout /t 3 /nobreak >nul

echo Starting Cloudflare Quick Tunnel...
start "Cloudflare Quick Tunnel" cmd /k "run_cloudflare_tunnel.bat"

echo.
echo ====================================================================
echo Both services are now running!
echo Look at the 'Cloudflare Quick Tunnel' window to see your live HTTPS URL.
echo Anyone worldwide can open that link directly without any password!
echo ====================================================================
echo.
pause
