# ITB Project Telecom Specification Extraction Pipeline & Wiki

This project is a high-fidelity local-first pipeline designed to ingest complex, scanned, or corrupted engineering specification PDFs (Invitation to Bid/ITB documents), extract verbatim telecom-related clauses layout-aware, and catalog them into a searchable web dashboard for review, validation, and Technical Query (TQ) generation.

---

## 📂 Project Architecture

The project consists of three main components:

1.  **[hifi_extractor/](file:///g:/My%20Drive/Project/ITB Project/hifi_extractor/)**: A modular Python package implementing a tiered text extraction pipeline:
    *   *Direct Parsing*: Uses PyMuPDF for fast digital text rendering.
    *   *OpenCV Image Processing*: Denoises, binarizes, and deskews scanned documents.
    *   *Tesseract OCR*: Extracts text from image-only pages or pages with garbled font encodings.
    *   *DBSCAN Margin Suppression*: Strips repetitive headers, footers, and page numbers.
    *   *Token Chunking*: Creates clean, semantic markdown boundaries for LLM ingestion.
2.  **[telecom-wiki-app/](file:///g:/My%20Drive/Project/ITB Project/telecom-wiki-app/)**: A dynamic local plant engineering dashboard:
    *   *Flask Backend*: Handles project database onboarding, cataloging, and local API requests.
    *   *Static Dashboard*: A dark glassmorphic UI showcasing technical summaries, cables schedules, compliance statuses, and Technical Queries (TQs).
3.  **[Makefile](file:///g:/My%20Drive/Project/ITB Project/Makefile)**: Automation script to setup requirements, run diagnoses, execute tests, and batch extract files.

---

## 🚀 Quick Start

### 1. Prerequisites
*   Python 3.10+ installed.
*   **Tesseract OCR** (automated installation via `make install` using Windows Package Manager, or install manually and add `C:\Program Files\Tesseract-OCR` to your User PATH environment variable).

### 2. Setup
Clone the repository and install all dependencies:
```bash
make install
```

### 3. Verification
Verify that Tesseract OCR, PyMuPDF, and libraries are functioning properly by running extraction on the Part_A sample range (pages 38–44):
```bash
make test
```
This will print classifications and output a verified markdown file `test_output_part_a_38_44.md`.

---

## 🔄 Extraction & Onboarding Workflow

### Step 1: Diagnose PDF Pages
Determine if your PDF pages are clean text, image-only scans, or contain corrupt font layers:
```bash
make diagnose PDF="Part_B1_Technical_Specification_CO2_Urea_1_500.pdf"
```

### Step 2: Extract to Markdown / Chunking
Extract specific page ranges to structured Markdown files:
```bash
python -m hifi_extractor extract "Part_B1_Technical_Specification_CO2_Urea_1_500.pdf" --pages 2-10 -o output.md
```
To chunk documents with a maximum token size for LLM ingestion:
```bash
python -m hifi_extractor extract "Part_B1_Technical_Specification_CO2_Urea_1_500.pdf" -o output.md --chunk-size 512
```

### Step 3: Run Onboarding Scanner
Scan your PDF folder, automatically run OCR where necessary, and compile the subsystem requirements database:
```bash
python telecom-wiki-app/scan_project.py --name "Urea Synthesis Plant" --dir "g:\My Drive\Project\ITB Project"
```
This registers the project, creates static JS data fallbacks, and writes JSON files inside `telecom-wiki-app/projects/`.

### Step 4: Launch Web Dashboard
Start the local server:
```bash
cd telecom-wiki-app
python app.py
```
Open your browser and navigate to `http://localhost:5000` to interact with your dashboard, review cable schedules, and export Technical Queries.
