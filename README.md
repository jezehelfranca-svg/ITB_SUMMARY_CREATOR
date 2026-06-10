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
Create a project virtual environment and install all Python dependencies:
```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

On Windows, `make install` also checks for Tesseract OCR and installs it with
`winget` when needed.

### 3. Run The Local Web App
Start the extraction dashboard:
```bash
run.bat
```
Then open [http://localhost:5000](http://localhost:5000). The dashboard accepts
local PDFs and drag-and-drop uploads, streams extraction progress, previews
clauses, and downloads styled Excel or CSV output. Expand **Manual Filter
Rules** under Config Options to edit inclusion keywords and false-positive
exclusion patterns directly in the UI. Rules accept case-insensitive regular
expressions, are validated before saving, and apply to the next extraction.

### 4. Run Standalone Extraction
To generate the styled Excel spreadsheet (`telecom_extracted_requirements.xlsx`) and CSV file instantly using the pre-extracted, audited, and anonymized database cache, simply run:
```bash
.venv\Scripts\python extract_to_excel.py
```

If you want to force the tool to re-scan all PDF files in the directory page-by-page and extract requirements using the active OCR/processing pipeline, run:
```bash
python extract_to_excel.py --force-extract
```
The dynamic pipeline automatically filters out and anonymizes project/site references at runtime.

### 5. Run Tests
```bash
.venv\Scripts\python -m unittest discover -s tests -v
```

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

---

## 🏛️ Telecom Architecture & Block Diagram

A highly detailed, production-grade overall block diagram has been generated in [CTGU_Overall_Telecom_Architecture_Detailed.mmd](file:///g:/My%20Drive/Project/CTGU/CTGU-main/CTGU-main/CTGU_Overall_Telecom_Architecture_Detailed.mmd). It reflects all the technical specification requirements (CCTV, PAGA, Telephone, Time Synchronization, OT Networks, and UPS Power) mapped across Purdue levels and site boundaries.

### 📋 Architecture Completeness Checklist

| Subsystem / Area | Specification Requirement | Implementation in Block Diagram |
| :--- | :--- | :--- |
| **Site Boundaries** | Remote read-only process viewing monitoring at Site Beta (isolated). | Read-only OPC Link from Site Alpha (OPC Server) to Site Beta (OPC Client / Remote Historian) through isolated firewalls. |
| **CCTV Surveillance** | Min 20 cameras (12 PTZ, 8 Dome), STQC/MeitY certified, Ex d IP65, NVR RAID 60 days, Video Analytics Server. | `IPCAM_A` (1080p, Ex d, IR, STQC), `CCTV_SW_A` (Field switches), `CCTV_VMS_A` (NVR RAID min 60 days), `CCTV_ANA_A` (Analytics), `CCTV_CLIENT_A` linked to `LVS_A`. |
| **PAGA / Plant Comm** | Redundant Central Exchange, Master call station, Ex d field call stations, beacons/sirens, N+1 UPS amplifier racks. | `PAGA_EX_A` (Redundant Exchange), `PAGA_MCS_A` (Master Station), `PAGA_AMP_A` (N+1 amplifiers), `PAGA_FCS_EX_A` (Ex d), beacons, and sirens. |
| **Telephone System** | EPABX exchange (48V DC telephones), MDF-to-TJB demarcation, TDJB building distribution. | `TEL_EXCHANGE_A` (Owner EPABX), `MDF_A` (MDF Demarcation), `TJB_A` (Main JB), `TDJB_A` (Distribution JB), `RJ11_SOCKETS_A`. |
| **Time Synchronization** | Redundant GPS Master Clock, outdoor lightning protected antenna, NTP/PTP, IRIG-B, 1PPS/10MHz outputs. | `GPS_MASTER_A` (Redundant clocks), `GPS_ANT_A` (Weatherproof/lightning protected), `TIME_NET_A` distributing to Core switches, controllers, CCTV, PAGA, and slave clocks. |
| **OT Networks & Cyber** | IEC 62443 security zones, managed switches, HA pair firewalls, Jump Server (MFA/Recording), log retention for 180 days. | `FW_EXT_A`/`FW_INT_A` (HA Pairs), `DMZ_SW_A`, `Jump_A` (MFA/Session recording), `LogRelay_A`, `LogStore_A` (180 days retention). |
| **UPS Power Systems** | Redundant UPS (2x100% 10kVA) with Ni-Cd battery bank and ACDB, 3-hour backup time at Site Alpha, status monitoring to DCS. | `UPS_SYS_A` (Redundant UPS + Ni-Cd batteries + ACDB), `UPS_MON_A` (Monitoring card) connecting hardwired/Modbus alarms to `DCS_CTRL_A`. |

