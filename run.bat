@echo off
title Telecom Specification Extraction Engine
echo ========================================================
echo Starting Standalone Telecom Specification Extractor...
echo ========================================================

:: Ensure Tesseract-OCR is in the PATH environment
echo Checking Tesseract-OCR PATH configuration...
set "PATH=C:\Program Files\Tesseract-OCR;%PATH%"

echo Launching default web browser at http://localhost:5000...
start "" "http://localhost:5000"

echo Starting local web server...
python app.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Flask server failed to start or crashed.
    pause
    exit /b %ERRORLEVEL%
)
