@echo off
echo ========================================
echo Installing Backend Dependencies
echo ========================================
echo.
echo This will install all required packages.
echo NOTE: This may take 10-15 minutes and download ~5GB
echo.
pause

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate
) else (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate
)

echo.
echo ========================================
echo Step 1: Upgrading pip
echo ========================================
python -m pip install --upgrade pip

echo.
echo ========================================
echo Step 2: Installing Flask dependencies
echo ========================================
pip install Flask flask-cors flask-pymongo pymongo python-dotenv werkzeug

echo.
echo ========================================
echo Step 3: Installing PyTorch (LARGE!)
echo ========================================
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

echo.
echo ========================================
echo Step 4: Installing AI dependencies
echo ========================================
pip install transformers accelerate
pip install openai-whisper
pip install sentencepiece

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo You can now run: python server.py
echo.
pause
