@echo off
echo Stopping Satellite GIS Extractor servers...

REM Stop Python process on port 5001
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5001 ^| findstr LISTENING') do taskkill /F /PID %%a 2>nul

echo Servers stopped.
