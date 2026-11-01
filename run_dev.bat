@echo off
REM ==============================================================================
REM Campus Grievance Addressal System (CGAS) - Unified Local Runner (Windows)
REM Course: CS1207 Object Oriented Programming Lab | Group II-8
REM ==============================================================================

echo ==================================================================
echo  Starting Campus Grievance Addressal System (CGAS) v1.0
echo  CS1207 OOP Lab Group II-8
echo ==================================================================

cd %~dp0

REM 1. Verify Python availability
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python was not found in your system PATH.
    echo         Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

REM 2. Verify Node.js and npm
npm --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] npm was not found in your system PATH.
    echo         Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

REM 3. Virtual environment setup
IF NOT EXIST "backend\venv" (
    echo [SETUP] Creating Python virtual environment in backend\venv...
    python -m venv backend\venv
    call backend\venv\Scripts\pip.exe install --upgrade pip
    call backend\venv\Scripts\pip.exe install -r backend\requirements.txt
)

REM 4. Database initialization and seeding
echo [SETUP] Ensuring MongoDB connection and initial demo accounts...
call backend\venv\Scripts\python.exe backend\app\seed.py

REM 5. Frontend node_modules check
IF NOT EXIST "frontend\node_modules" (
    echo [SETUP] Installing frontend npm packages...
    cd frontend && npm install && cd ..
)

echo.
echo [START] Launching FastAPI Backend on http://localhost:8000...
start "CGAS Backend (FastAPI)" cmd /k "backend\venv\Scripts\uvicorn.exe app.main:app --reload --port 8000 --app-dir backend"

echo [START] Launching Vite Frontend on http://localhost:5173...
start "CGAS Frontend (Vite)" cmd /k "cd frontend && npm run dev"

echo.
echo ==================================================================
echo   Campus Grievance Addressal System (CGAS) is running!
echo.
echo   Web Application:   http://localhost:5173
echo   Backend API:       http://localhost:8000
echo   Interactive Docs:  http://localhost:8000/docs
echo   Health Check:      http://localhost:8000/api/health
echo.
echo   Demo Credentials:
echo     - Student:  25CSB0A22  /  Student@123  (Soham S. Roy)
echo     - Admin:    admin01    /  Admin@123    (Chief Admin)
echo ==================================================================
echo Both servers are running in separate terminal windows.
echo Close those windows or press any key here when finished.
pause
