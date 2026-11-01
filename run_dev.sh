#!/bin/bash
# ==============================================================================
# Campus Grievance Addressal System (CGAS) - Unified Local Runner (Linux / macOS)
# Course: CS1207 Object Oriented Programming Lab | Group II-8
# ==============================================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "=================================================================="
echo " Starting Campus Grievance Addressal System (CGAS) v1.0"
echo " CS1207 OOP Lab Group II-8"
echo "=================================================================="

# 1. Verify Python 3
PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo "[ERROR] Python 3 is required but neither 'python3' nor 'python' was found in PATH."
    exit 1
fi

PY_VER=$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "[OK] Found Python $PY_VER ($PYTHON_BIN)"

# 2. Verify Node.js and npm
if ! command -v npm >/dev/null 2>&1; then
    echo "[ERROR] Node.js / npm is required for the frontend but was not found in PATH."
    echo "        Please install Node.js (v18+) from https://nodejs.org/"
    exit 1
fi
NPM_VER=$(npm --version)
echo "[OK] Found npm v$NPM_VER"

# 3. Initialize or verify Python virtualenv
if [ ! -d "backend/venv" ]; then
    echo ""
    echo "[SETUP] Creating Python virtual environment in backend/venv..."
    "$PYTHON_BIN" -m venv backend/venv
    ./backend/venv/bin/pip install --upgrade pip
    ./backend/venv/bin/pip install -r backend/requirements.txt
fi

# 4. Initialize database with seed data if needed
echo ""
echo "[SETUP] Ensuring MongoDB connection and initial demo accounts..."
./backend/venv/bin/python backend/app/seed.py || {
    echo "[WARNING] Could not connect to MongoDB on default port (27017)."
    echo "          Please ensure MongoDB is running ('mongod', 'systemctl start mongod', or set MONGODB_URL)."
}

# 5. Check frontend dependencies
if [ ! -d "frontend/node_modules" ]; then
    echo ""
    echo "[SETUP] Installing frontend npm dependencies..."
    (cd frontend && npm install)
fi

# 6. Process cleanup on exit
cleanup() {
    trap - SIGINT SIGTERM EXIT
    echo ""
    echo "=================================================================="
    echo " Shutting down CGAS development servers..."
    kill $(jobs -p) 2>/dev/null || true
    echo " Servers stopped."
    echo "=================================================================="
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# 7. Start FastAPI Backend on port 8000
echo ""
echo "[START] Launching FastAPI backend on http://localhost:8000..."
./backend/venv/bin/uvicorn app.main:app --reload --port 8000 --app-dir backend &

# 8. Start Vite Frontend on port 5173
echo "[START] Launching Vite React frontend on http://localhost:5173..."
(cd frontend && npm run dev) &

# 9. Startup summary
echo ""
echo "=================================================================="
echo "  Campus Grievance Addressal System (CGAS) is running!"
echo ""
echo "  Web Application:   http://localhost:5173"
echo "  Backend API:       http://localhost:8000"
echo "  Interactive Docs:  http://localhost:8000/docs"
echo "  Health Check:      http://localhost:8000/api/health"
echo ""
echo "  Demo Credentials:"
echo "    - Student:  25CSB0A22  /  Student@123  (Soham S. Roy)"
echo "    - Admin:    admin01    /  Admin@123    (Chief Admin)"
echo "=================================================================="
echo "Press Ctrl+C to terminate both servers."
echo ""

wait
