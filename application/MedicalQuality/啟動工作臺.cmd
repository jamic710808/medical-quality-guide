@echo off
cd /d "%~dp0"
set PYTHONUTF8=1
py -3.13 scripts\manage.py start
if errorlevel 1 pause
start "" http://127.0.0.1:8180
