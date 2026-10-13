@echo off
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python 3.10 or newer is required. Install Python and select Add Python to PATH.
  pause
  exit /b 1
)
python -m pip install -r requirements.txt
if errorlevel 1 pause & exit /b 1
start "Vortex Arena User Panel" http://127.0.0.1:8082
python Vortex_Arena_User.py
pause
