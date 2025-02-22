@echo off
cd /d %~dp0\dist
quiz_app.exe runserver --noreload
pause