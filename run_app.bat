@echo off
REM Quick launcher for Meeting Summarizer Streamlit App

echo ========================================
echo Meeting Summarizer - Starting App
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "llm_env\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please create it first:
    echo   python -m venv llm_env
    echo   .\llm_env\Scripts\activate
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call llm_env\Scripts\activate.bat

REM Check if streamlit is installed
python -c "import streamlit" 2>nul
if errorlevel 1 (
    echo.
    echo Streamlit not found. Installing dependencies...
    pip install -r requirements.txt
    echo.
)

REM Check if FFmpeg is available
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo.
    echo WARNING: FFmpeg not found in PATH!
    echo The app requires FFmpeg to process video files.
    echo Please install FFmpeg from https://ffmpeg.org
    echo.
    pause
)

echo.
echo Starting Streamlit app...
echo The app will open in your browser automatically.
echo.
echo To stop the app, press Ctrl+C in this window.
echo.

streamlit run app_meeting.py

pause



