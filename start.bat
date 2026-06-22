@echo off
echo Starting TDPortal-OS...

:: Redis (Docker)
docker start tdportal-redis 2>nul || docker run -d --name tdportal-redis -p 6379:6379 redis:7-alpine
echo [1/4] Redis OK

:: Backend + Worker via PowerShell (no cmd windows)
powershell -NoProfile -WindowStyle Hidden -Command ^
  "$env:PYTHONPATH='f:\search_engine\backend';" ^
  "Start-Process python -ArgumentList '-m','uvicorn','app.main:app','--host','0.0.0.0','--port','8000' -WorkingDirectory 'f:\search_engine\backend' -WindowStyle Hidden -RedirectStandardOutput 'C:\tmp\tdportal\backend.log' -RedirectStandardError 'C:\tmp\tdportal\backend.err';" ^
  "Start-Sleep 7;" ^
  "Start-Process python -ArgumentList '-m','celery','-A','app.workers.celery_app','worker','--loglevel=info','--pool=solo' -WorkingDirectory 'f:\search_engine\backend' -WindowStyle Hidden -RedirectStandardOutput 'C:\tmp\tdportal\worker.log' -RedirectStandardError 'C:\tmp\tdportal\worker.err'"

echo [2/4] Backend starting (port 8000)
echo [3/4] Celery worker starting

:: Frontend (Vite) — also no persistent cmd window
powershell -NoProfile -WindowStyle Hidden -Command ^
  "Start-Process node -ArgumentList 'node_modules\vite\bin\vite.js' -WorkingDirectory 'f:\search_engine\frontend' -WindowStyle Hidden -RedirectStandardOutput 'C:\tmp\tdportal\frontend.log' -RedirectStandardError 'C:\tmp\tdportal\frontend.err'"

echo [4/4] Frontend starting (port 5173)
echo.
echo TDPortal-OS running at http://localhost:5173  (no background windows)
echo.
