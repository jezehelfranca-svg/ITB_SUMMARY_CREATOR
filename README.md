# Standalone Telecom Specification Extraction Tool

This tool is a high-fidelity local-first pipeline designed to ingest engineering specification PDFs, extract telecom-related clauses (such as CCTV, PAGA, Telephone, structured cabling, cybersecurity, UPS systems), and catalog them into a styled Excel table matching strict engineering templates.

---

## 📂 Project Architecture

The project consists of the following components:

1.  **[hifi_extractor/](file:///g:/My%20Drive/Project/CTGU/hifi_extractor/)**: A modular Python package implementing a layout-aware tiered text extraction pipeline:
    *   *Direct Parsing*: Uses PyMuPDF for fast digital text rendering.
    *   *OpenCV Image Processing*: Denoises, binarizes, and deskews scanned documents.
    *   *Tesseract OCR*: Extracts text from image-only pages or pages with garbled font encodings.
    *   *DBSCAN/Static Zone Margin Suppression*: Strips repetitive headers, footers, and page numbers.
2.  **[extract_to_excel.py](file:///g:/My%20Drive/Project/CTGU/extract_to_excel.py)**: The main standalone script that compiles the final, styled Excel table (`telecom_extracted_requirements.xlsx`) using cell styles, column widths, and gridline setups copied directly from `ITB_SUMMARY_EXAMPLE.xlsx`.
3.  **[telecom_extracted_requirements_db.json](file:///g:/My%20Drive/Project/CTGU/telecom_extracted_requirements_db.json)**: A local database containing the 40 audited and fully anonymized requirements (replacing specific site/project names with `Site Alpha` and `Site Beta`).
4.  **[run.bat](file:///g:/My%20Drive/Project/CTGU/run.bat)**: Windows batch script wrapper to execute the standalone extraction utility.
5.  **[Makefile](file:///g:/My%20Drive/Project/CTGU/Makefile)**: Automation script to setup requirements, run diagnoses, execute tests, and run the Excel extraction.

---

## 🚀 Quick Start

### 1. Prerequisites
*   Python 3.10+ installed.
*   **Tesseract OCR** (automated installation via `make install` using Windows Package Manager, or installed manually at `C:\Program Files\Tesseract-OCR`).

### 2. Setup
Install all python dependencies:
```bash
make install
```

### 3. Run Standalone Extraction
To generate the styled Excel spreadsheet (`telecom_extracted_requirements.xlsx`) and CSV file instantly using the pre-extracted, audited, and anonymized database cache, simply run:
```bash
run.bat
```
or:
```bash
make run-extract
```

If you want to force the tool to re-scan all PDF files in the directory page-by-page and extract requirements using the active OCR/processing pipeline, run:
```bash
python extract_to_excel.py --force-extract
```
The dynamic pipeline automatically filters out and anonymizes project/site references at runtime.

---

## 🔄 Customizing & Verification

### Diagnose PDF Pages
To check if a specific PDF document's pages contain native digital text, garbled text, or scanned images:
```bash
make diagnose PDF="Part_B1_Technical_Specification_CO2_Urea_1_500.pdf"
```

### Extract PDF Range to Markdown
To extract a page range from a specific document for inspection or verification:
```bash
python -m hifi_extractor extract "Part_A_Technical_Specification_150_TPD_CO2_To_Urea.pdf" --pages 38-44 -o output.md
```
