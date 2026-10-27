@echo off
title SentinelAI — Launcher
color 0A

echo.
echo  ============================================================
echo   SentinelAI — AI-Powered Network Intrusion Detection
echo  ============================================================
echo.

:: ── Check virtual environment exists ────────────────────────────────────────
if not exist "venv\Scripts\python.exe" (
    echo  [ERROR] Virtual environment not found.
    echo  Run this first:  python -m venv venv
    echo  Then run:        venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

echo  [1/6] Running Phase 1 - Data Loading...
venv\Scripts\python.exe scripts\load_data.py
if errorlevel 1 ( echo  [ERROR] Phase 1 failed. && pause && exit /b 1 )
echo  [OK] Phase 1 complete.
echo.

echo  [2/6] Running Phase 2 - Feature Engineering...
venv\Scripts\python.exe scripts\feature_engineering.py
if errorlevel 1 ( echo  [ERROR] Phase 2 failed. && pause && exit /b 1 )
echo  [OK] Phase 2 complete.
echo.

echo  [3/6] Running Phase 3 - Model Training...
venv\Scripts\python.exe scripts\train_models.py
if errorlevel 1 ( echo  [ERROR] Phase 3 failed. && pause && exit /b 1 )
echo  [OK] Phase 3 complete.
echo.

echo  [4/6] Running Phase 4 - Risk Scoring...
venv\Scripts\python.exe scripts\risk_scoring.py
if errorlevel 1 ( echo  [ERROR] Phase 4 failed. && pause && exit /b 1 )
echo  [OK] Phase 4 complete.
echo.

echo  [5/6] Running Phase 5 - AI Explanations...
venv\Scripts\python.exe scripts\ai_explanation.py
if errorlevel 1 ( echo  [ERROR] Phase 5 failed. && pause && exit /b 1 )
echo  [OK] Phase 5 complete.
echo.

echo  [6/6] Running Phase 6 - Database...
venv\Scripts\python.exe src\database.py
if errorlevel 1 ( echo  [ERROR] Phase 6 failed. && pause && exit /b 1 )
echo  [OK] Phase 6 complete.
echo.

echo  ============================================================
echo   All phases complete. Launching dashboard...
echo   Open your browser at: http://localhost:8501
echo   Press Ctrl+C in this window to stop the dashboard.
echo  ============================================================
echo.

venv\Scripts\streamlit.exe run dashboard\app.py
pause
