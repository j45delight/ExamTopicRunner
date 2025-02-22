@echo off
cd /d %~dp0\dist
ExamTopicRunner.exe runserver --noreload
pause