@echo off
REM ====================================================================
REM Prompt Manager - EXE Builder Script
REM ====================================================================
REM This script builds a standalone executable using PyInstaller
REM ====================================================================

echo.
echo ========================================
echo Prompt Manager - EXE Builder
echo ========================================
echo.

REM Change to project root directory
cd /d "%~dp0.."

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or later
    pause
    exit /b 1
)

echo [1/5] Checking Python installation...
python --version
echo.

REM Check/Install PyInstaller
echo [2/5] Checking PyInstaller installation...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller
        pause
        exit /b 1
    )
) else (
    echo PyInstaller is already installed
)
echo.

REM Clean previous builds
echo [3/5] Cleaning previous build artifacts...
if exist "build" (
    echo Removing build directory...
    rmdir /s /q build
)
if exist "dist\PromptManager.exe" (
    echo Removing previous executable...
    del /f /q dist\PromptManager.exe
)
echo Build artifacts cleaned
echo.

REM Build the executable
echo [4/5] Building executable with PyInstaller...
echo This may take several minutes...
echo.
pyinstaller --clean prompt_manager.spec

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    echo Please check the error messages above
    pause
    exit /b 1
)

echo.
echo [5/5] Verifying build...
if exist "dist\PromptManager.exe" (
    echo.
    echo ========================================
    echo BUILD SUCCESSFUL!
    echo ========================================
    echo.
    echo Executable location: dist\PromptManager.exe
    echo.
    for %%A in ("dist\PromptManager.exe") do (
        echo File size: %%~zA bytes
    )
    echo.
    echo You can now distribute the PromptManager.exe file.
    echo The application will store its data in:
    echo   %APPDATA%\PromptManager\
    echo.
    echo ========================================
    echo.
    
    REM Ask if user wants to run the executable
    set /p run_exe="Do you want to run the executable now? (Y/N): "
    if /i "%run_exe%"=="Y" (
        echo.
        echo Starting PromptManager...
        start "" "dist\PromptManager.exe"
    )
) else (
    echo.
    echo [ERROR] Build completed but executable not found!
    echo Expected location: dist\PromptManager.exe
    pause
    exit /b 1
)

echo.
pause
