@echo off
rem Lance le watcher qui relance le worker en boucle
cd /d %~dp0
cd ..
if not exist logs mkdir logs
:loop
echo Starting worker %DATE% %TIME% >> logs\worker.log
venv\Scripts\python.exe scripts\worker.py >> logs\worker.log 2>&1
echo Worker exited %DATE% %TIME% >> logs\worker.log
timeout /t 5 /nobreak >nul
goto loop
