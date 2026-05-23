@echo off
title Telecom Specification Extraction Tool
echo ========================================================
echo Starting Telecom Specification Extraction Tool...
echo ========================================================

:: Ensure Tesseract-OCR is in the PATH environment for Tesseract executions
echo Checking Tesseract-OCR PATH configuration...
set "PATH=C:\Program Files\Tesseract-OCR;%PATH%"

echo Running extraction script...
python extract_to_excel.py %*

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] The extraction script failed to execute.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ========================================================
echo Extraction Completed Successfully!
echo Output saved to: telecom_extracted_requirements.xlsx
echo ========================================================
pause
