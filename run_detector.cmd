@echo off

REM Navigate to the directory where the Python script is located
cd /d "%~dp0"

REM Run the Python script
python object_detector.py

pause
