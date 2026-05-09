@echo off
cd /d "%~dp0"
echo Starting GH-emails-mxf agent...
python main.py
if errorlevel 1 (
    echo Agent exited with an error. Check logs\agent.log for details.
    pause
)
