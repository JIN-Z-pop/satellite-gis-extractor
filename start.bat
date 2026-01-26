@echo off
chcp 65001 > nul
echo ============================================
echo Satellite GIS Extractor
echo ============================================

cd /d "%~dp0"

if not exist ".env" (
    echo [INFO] .env not found. Using default settings.
    echo [INFO] For Earth Engine, run: earthengine authenticate
)

echo.
echo Starting server...
echo.

cd backend
python server.py

pause
