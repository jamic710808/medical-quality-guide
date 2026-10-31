@echo off
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "MQ_ENABLE_LOCAL_MODEL=0"
py -3.13 scripts\manage.py start
if errorlevel 1 exit /b 1
start "" "http://127.0.0.1:8180/"
