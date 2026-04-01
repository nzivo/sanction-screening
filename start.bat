@echo off
REM Sanctions Screening System Startup Script for Windows

echo ==========================================
echo   Sanctions Screening System
echo ==========================================
echo.

REM Check if we're in the project root
if not exist "backend" (
    echo Error: backend folder not found
    exit /b 1
)
if not exist "frontend" (
    echo Error: frontend folder not found
    exit /b 1
)

echo Starting services...
echo.

REM Start Backend
echo Starting Backend Server...
cd backend
start "Sanctions Backend" cmd /k "..\\venv\\Scripts\\activate && python main.py"
cd ..
timeout /t 3 /nobreak > nul

REM Start Frontend
echo Starting Frontend Server...
cd frontend
if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
)
start "Sanctions Frontend" cmd /k "npm run dev"
cd ..

echo.
echo ==========================================
echo   Startup Complete!
echo ==========================================
echo.
echo Backend API:  http://localhost:8001
echo API Docs:     http://localhost:8001/docs
echo Frontend:     http://localhost:3001
echo.
echo Press any key to exit (servers will keep running)...
pause > nul
