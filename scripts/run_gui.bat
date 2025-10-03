@echo off
REM Windows batch script to run Prompt Manager GUI

echo ====================================================
echo            Prompt Manager GUI Launcher
echo ====================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Change to script directory
cd /d "%~dp0\.."

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Warning: No virtual environment found
    echo Running with system Python...
)

REM Install GUI requirements if needed
echo Checking GUI requirements...
pip install -q -r requirements-gui.txt
if errorlevel 1 (
    echo Warning: Failed to install some GUI requirements
)

REM Run the GUI
echo Starting Prompt Manager GUI...
echo.
python run_gui.py

REM Deactivate virtual environment if it was activated
if exist "venv\Scripts\activate.bat" (
    deactivate
)

echo.
echo GUI session ended.
pause

