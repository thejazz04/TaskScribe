@echo off
echo ========================================
echo Starting Meeting Summarizer Backend
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate
echo.

REM Check if dependencies are installed
echo Checking dependencies...
python -c "import torch" 2>nul
if errorlevel 1 (
    echo.
    echo WARNING: AI dependencies not found!
    echo Please run: install_dependencies.bat
    echo.
    pause
    exit /b 1
)
echo Dependencies OK!
echo.

REM Check if .env exists
if not exist ".env" (
    echo Creating .env file from .env.example...
    copy .env.example .env
    echo.
    echo Please configure your .env file with MongoDB URI
    echo.
)

REM Create uploads directory
if not exist "uploads\" (
    echo Creating uploads directory...
    mkdir uploads
    echo.
)

REM Start Flask server
echo Starting Flask server on http://localhost:5000
echo.
python server.py

pause
