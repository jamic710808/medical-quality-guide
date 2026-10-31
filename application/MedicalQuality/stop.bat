@echo off
cd /d "%~dp0"
set "PYTHONUTF8=1"
py -3.13 scripts\manage.py stop
if errorlevel 1 pause
