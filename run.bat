@echo off
echo ===================================================
echo   Starting MindScribe Backend on Port 8000...
echo ===================================================
echo.
echo Please open your browser and navigate to: 
echo.
echo      http://localhost:8000
echo.
echo (Using port 8000 fixes the Firebase login error once and for all!)
echo.
cd backend
uvicorn app.main:app --reload --host localhost --port 8000
