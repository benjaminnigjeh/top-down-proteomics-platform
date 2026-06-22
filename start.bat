@echo off
echo Starting TDPortal-OS services...

:: Redis (Docker)
docker start tdportal-redis 2>nul || docker run -d --name tdportal-redis -p 6379:6379 redis:7-alpine
echo [1/4] Redis started

:: Backend (uvicorn)
set PYTHONPATH=f:\search_engine\backend
start "TDPortal-Backend" /MIN cmd /c "cd /d f:\search_engine\backend && set PYTHONPATH=f:\search_engine\backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 >> C:\tmp\tdportal\backend.log 2>&1"
echo [2/4] Backend starting on port 8000...

:: Wait for backend
timeout /t 6 /nobreak >nul

:: Celery worker
start "TDPortal-Worker" /MIN cmd /c "cd /d f:\search_engine\backend && set PYTHONPATH=f:\search_engine\backend && python -m celery -A app.workers.celery_app worker --loglevel=info --pool=solo >> C:\tmp\tdportal\worker.log 2>&1"
echo [3/4] Celery worker started

:: Frontend (Vite)
start "TDPortal-Frontend" /MIN cmd /c "cd /d f:\search_engine\frontend && npm run dev >> C:\tmp\tdportal\frontend.log 2>&1"
echo [4/4] Frontend starting on port 5173...

timeout /t 4 /nobreak >nul
echo.
echo TDPortal-OS is running at http://localhost:5173
echo.
