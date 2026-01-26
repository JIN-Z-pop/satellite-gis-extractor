@echo off
echo Stopping Satellite GIS Extractor servers...

REM Stop Python processes on port 5000 and 8081
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8081 ^| findstr LISTENING') do taskkill /F /PID %%a 2>nul

echo Servers stopped.
