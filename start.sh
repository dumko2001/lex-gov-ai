#!/bin/bash
set -e

echo "=========================================="
echo "  Lex-Gov AI - Hackathon Startup Script"
echo "=========================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found. Please install Python 3.10+"
    exit 1
fi

# Prefer 3.12/3.11/3.10 when available; fallback to python3.
PYTHON_BIN="python3"
if command -v python3.12 &> /dev/null; then
    PYTHON_BIN="python3.12"
elif command -v python3.11 &> /dev/null; then
    PYTHON_BIN="python3.11"
elif command -v python3.10 &> /dev/null; then
    PYTHON_BIN="python3.10"
fi

# Check Node
if ! command -v node &> /dev/null; then
    echo "Error: node not found. Please install Node.js 18+"
    exit 1
fi

cd "$(dirname "$0")"

# Force runtime, temp, and package/model caches onto the external drive.
EXTERNAL_ROOT="$(pwd)"
EXTERNAL_CACHE_ROOT="$EXTERNAL_ROOT/.external-cache"
EXTERNAL_TMP="$EXTERNAL_ROOT/.external-tmp"
mkdir -p "$EXTERNAL_CACHE_ROOT" "$EXTERNAL_TMP"
mkdir -p \
  "$EXTERNAL_CACHE_ROOT/pip" \
  "$EXTERNAL_CACHE_ROOT/npm" \
  "$EXTERNAL_CACHE_ROOT/pycache" \
  "$EXTERNAL_CACHE_ROOT/huggingface" \
  "$EXTERNAL_CACHE_ROOT/torch" \
  "$EXTERNAL_CACHE_ROOT/matplotlib" \
  "$EXTERNAL_CACHE_ROOT/xdg"

export TMPDIR="$EXTERNAL_TMP"
export PIP_CACHE_DIR="$EXTERNAL_CACHE_ROOT/pip"
export npm_config_cache="$EXTERNAL_CACHE_ROOT/npm"
export PYTHONPYCACHEPREFIX="$EXTERNAL_CACHE_ROOT/pycache"
export HF_HOME="$EXTERNAL_CACHE_ROOT/huggingface"
export TRANSFORMERS_CACHE="$EXTERNAL_CACHE_ROOT/huggingface/transformers"
export TORCH_HOME="$EXTERNAL_CACHE_ROOT/torch"
export MPLCONFIGDIR="$EXTERNAL_CACHE_ROOT/matplotlib"
export XDG_CACHE_HOME="$EXTERNAL_CACHE_ROOT/xdg"

echo "Using external cache root: $EXTERNAL_CACHE_ROOT"
echo "Using external temp dir:   $EXTERNAL_TMP"

# Backend setup
echo "[1/4] Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "  Creating Python virtual environment..."
    "$PYTHON_BIN" -m venv venv
fi

# Recreate venv if existing interpreter is below 3.10.
if [ -x "venv/bin/python" ]; then
    PY_VER="$(venv/bin/python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    case "$PY_VER" in
        3.10|3.11|3.12|3.13) ;;
        *)
            echo "  Rebuilding venv with $PYTHON_BIN (found old Python $PY_VER)..."
            rm -rf venv
            "$PYTHON_BIN" -m venv venv
            ;;
    esac
fi

echo "  Installing Python dependencies..."
source venv/bin/activate
pip install -q -r requirements.txt

echo "  Creating database tables..."
venv/bin/python -c "from app.main import app; from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"

echo "  Seeding demo data..."
venv/bin/python -c "
from app.core.database import SessionLocal
from app.models.all import User
from app.core.security import get_password_hash
db = SessionLocal()
if not db.query(User).first():
    users = [
        User(email='admin@lexgov.ai', full_name='System Admin', employee_id='ADM001', department='Admin', role='ADMIN', hashed_password=get_password_hash('admin123')),
        User(email='nodal@revenue.gov', full_name='Revenue Officer', employee_id='REV001', department='Revenue', role='NODAL_OFFICER', hashed_password=get_password_hash('nodal123')),
        User(email='nodal@law.gov', full_name='Law Officer', employee_id='LAW001', department='Law', role='NODAL_OFFICER', hashed_password=get_password_hash('nodal123')),
        User(email='dept@revenue.gov', full_name='Revenue Dept User', employee_id='REV002', department='Revenue', role='DEPT_HEAD', hashed_password=get_password_hash('dept123')),
    ]
    db.add_all(users)
    db.commit()
    print('  Created 4 demo users')
else:
    print('  Users already exist')
db.close()
"

echo "  Starting backend server..."
venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Frontend setup
echo ""
echo "[2/4] Setting up frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "  Installing Node dependencies..."
    npm install
fi

echo "  Starting frontend server..."
npm run dev -- --host 0.0.0.0 &
FRONTEND_PID=$!
cd ..

echo ""
echo "=========================================="
echo "  Lex-Gov AI is running!"
echo "=========================================="
echo ""
echo "  Frontend: http://localhost:5173"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "  Demo Login:"
echo "    admin@lexgov.ai / admin123"
echo "    nodal@revenue.gov / nodal123"
echo ""
echo "  Press Ctrl+C to stop both servers"
echo ""

# Wait for interrupt
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" TERM
wait
