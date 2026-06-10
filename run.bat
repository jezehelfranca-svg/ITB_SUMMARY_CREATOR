@echo off
setlocal
title Telecom Specification Extraction Engine
echo ========================================================
echo Starting Standalone Telecom Specification Extractor...
echo ========================================================

set "PYTHON=python"
if exist "%~dp0.venv\Scripts\python.exe" set "PYTHON=%~dp0.venv\Scripts\python.exe"

echo Checking Python dependencies...
"%PYTHON%" -c "import cv2, fitz, flask, openpyxl, requests, sklearn" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Required Python dependencies are missing.
    echo Run: "%PYTHON%" -m pip install -r "%~dp0requirements.txt"
    pause
    exit /b 1
)

:: Ensure Tesseract-OCR is in the PATH environment
echo Checking Tesseract-OCR PATH configuration...
set "PATH=C:\Program Files\Tesseract-OCR;%PATH%"

echo Launching default web browser at http://localhost:5000...
start "" "http://localhost:5000"

echo Starting local web server...
"%PYTHON%" "%~dp0app.py"

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Flask server failed to start or crashed.
    pause
    exit /b %ERRORLEVEL%
)
