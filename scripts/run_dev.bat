@echo off
setlocal

REM Get the project root directory (one level up from this script)
set "ROOT_DIR=%~dp0.."
cd /d "%ROOT_DIR%"

REM --- Configuration ---
set API_PORT=3000
set VITE_PORT=3030

REM --- Environment Variables for Processes ---
set "VITE_API_URL=http://localhost:%API_PORT%"
set "VITE_PORT=%VITE_PORT%"
set "SERVER_PORT=%API_PORT%"

echo [run_dev.bat] Starting Python backend on port %API_PORT%...
START "Backend" uvicorn src.backend.main:app --host 127.0.0.1 --port %API_PORT% --reload

echo [run_dev.bat] Starting React frontend on port %VITE_PORT%...
START "Frontend" npm run dev

endlocal
