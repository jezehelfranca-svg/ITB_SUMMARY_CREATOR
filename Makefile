# Makefile for HiFi PDF Extraction Pipeline

PYTHON = python
PDF_DIR = .
OUTPUT_DIR = output_chunks

.PHONY: help install diagnose extract test batch run-extract run-ui

help:
	@echo "HiFi PDF Extraction Pipeline Automation"
	@echo "========================================"
	@echo "Available commands:"
	@echo "  make install        - Install python requirements and system packages"
	@echo "  make run-extract    - Run standalone extraction on all PDFs and export to Excel"
	@echo "  make diagnose PDF=x - Diagnose page classification on a specific PDF"
	@echo "  make extract PDF=x  - Extract a specific PDF to Markdown"
	@echo "  make test           - Run full verification suite on Part_A sample"
	@echo "  make batch          - Batch process all PDFs in the current directory"

install:
	$(PYTHON) -m pip install -r hifi_extractor/requirements.txt
	$(PYTHON) -m pip install markitdown docling
	@echo "Checking Tesseract OCR..."
	@where tesseract >nul 2>&1 || (echo "Tesseract not found. Installing via winget..." && winget install --id UB-Mannheim.TesseractOCR --silent --accept-package-agreements --accept-source-agreements)

diagnose:
	@if not defined PDF (echo Error: Please specify PDF=filename.pdf && exit /b 1)
	$(PYTHON) -m hifi_extractor diagnose "$(PDF)"

extract:
	@if not defined PDF (echo Error: Please specify PDF=filename.pdf && exit /b 1)
	@set /p OUT="Enter output filename (e.g. out.md): "
	$(PYTHON) -m hifi_extractor extract "$(PDF)" -o "%OUT%"

test:
	$(PYTHON) -m hifi_extractor diagnose "Part_A_Technical_Specification_150_TPD_CO2_To_Urea.pdf" --pages 38-44
	$(PYTHON) -m hifi_extractor extract "Part_A_Technical_Specification_150_TPD_CO2_To_Urea.pdf" --pages 38-44 -o test_output_part_a_38_44.md

batch:
	$(PYTHON) -m hifi_extractor batch "*.pdf" -o "$(OUTPUT_DIR)"

run-extract:
	$(PYTHON) extract_to_excel.py

run-ui:
	$(PYTHON) app.py

