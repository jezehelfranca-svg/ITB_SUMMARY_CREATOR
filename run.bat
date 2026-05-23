@echo off
title Telecom Specification Extraction Dashboard
echo ========================================================
echo Starting Telecom Specification Extraction Dashboard...
echo ========================================================

:: Ensure Tesseract-OCR is in the PATH environment for Tesseract executions
echo Checking Tesseract-OCR PATH configuration...
set "PATH=C:\Program Files\Tesseract-OCR;%PATH%"

:: Navigate to the web app directory and start the Flask server
cd telecom-wiki-app
echo Launching default web browser at http://localhost:5000...
start "" "http://localhost:5000"

echo Starting Flask server...
python app.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Flask server failed to start or crashed.
    pause
)
