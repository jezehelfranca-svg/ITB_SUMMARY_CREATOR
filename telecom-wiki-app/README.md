# Telecom & Security ITB Requirements Wiki

A dynamic, multi-project plant engineering wiki and automated scanner designed to ingest large Invitation to Bid (ITB) documents, parse specifications for Telecom and Security subsystems, audit for discrepancies and regulatory certification gaps, and compile Technical Queries (TQs) for bidder clarification.

The application works in two modes:
1. **Flask Server Mode**: Provides dynamic project loading, a CLI parser, and interactive TQ management.
2. **Offline Standalone Mode**: Simply double-click `static/index.html` to run the dashboard offline on site with no network or server dependencies.

---

## 🚀 Getting Started

### Prerequisites
Make sure you have Python 3.8+ installed on your system. Install the required PDF processing and web dependencies:
```bash
pip install PyMuPDF Flask
```

### Running the Local Web App
To start the backend server and launch the wiki dashboard locally:
1. Open terminal and navigate to the project directory:
   ```bash
   cd "g:/My Drive/Project/ITB Project/telecom-wiki-app"
   ```
2. Run the Flask application:
   ```bash
   python app.py
   ```
3. Open your web browser and navigate to:
   ```
   http://localhost:5000/
   ```

---

## 📦 GitHub Repository Setup

To upload this repository to your GitHub account:

1. **Create a new repository on GitHub**:
   - Go to [GitHub](https://github.com) and click **New** repository.
   - Name it (e.g., `telecom-itb-wiki-app`).
   - Leave it **empty** (do NOT initialize with a README, gitignore, or license, as they are already included here).
   - Click **Create repository**.

2. **Link this local repository to GitHub and push**:
   Open your terminal in `g:/My Drive/Project/ITB Project/telecom-wiki-app` and execute:
   ```bash
   # Add your GitHub remote URL (replace the URL below with your actual repo link)
   git remote add origin https://github.com/YOUR_USERNAME/telecom-itb-wiki-app.git

   # Rename branch to main
   git branch -M main

   # Push to GitHub
   git push -u origin main
   ```

---

## 🔄 Workflow: Onboarding Next Projects

When a new project bid package arrives, follow this standardized workflow to onboard the new technical specifications into the wiki database.

### Method A: Scanning via the Web UI (Recommended)
1. Ensure the Flask server is running (`python app.py`).
2. Navigate to the **Reviewer Workflow** tab on the web dashboard.
3. In **Step 1: Document Ingestion**, enter the **Project Name** and the **Local PDF Folder Path** containing the bid's specification documents.
4. Click **Trigger PDF Extraction Scan**.
5. The backend will parse the documents, classify them by subsystem, register the project, and automatically refresh the dashboard.

### Method B: Scanning via CLI
You can onboard a project directly from your command line:
```bash
python scan_project.py --name "Project Name" --dir "C:/path/to/project/pdfs"
```
*Example:*
```bash
python scan_project.py --name "Urea Synthesis Plant" --dir "g:\My Drive\Project\ITB Project"
```
This script:
- Automatically routes pages through the **HiFi Extraction Pipeline (`hifi_extractor`)** if installed. This will classify each page and selectively run Tesseract OCR on scanned images (e.g. Part_B1) or force-OCR on corrupt font encodings (e.g. Part_B3) while keeping direct text parsing for clean native-text pages.
- Parses the PDF folder for telecom keywords.
- Compiles the requirements database into `projects/<project_id>.json`.
- Registers the project inside the master catalog `projects/projects.json`.
- Generates a static fallback database file under `static/data_<project_id>.js` so the project can be loaded in offline standalone mode.


### Method C: Automated Scanning on GitHub (CI/CD Workflow)
A pre-configured GitHub Action workflow is included in `.github/workflows/scan-new-bid.yml`.
When you push new PDF files or run the workflow manually via GitHub Actions:
1. It spins up a runner, installs Python, and runs the scanner.
2. It processes PDFs from the `input_pdfs/` folder.
3. It automatically commits the generated JSON requirements database and offline JS fallbacks back into your repository.
4. To run it: Go to your GitHub repository -> **Actions** -> select **Scan New Project Bid** -> click **Run workflow**.

---

## 📂 Project Architecture

```
telecom-wiki-app/
├── .github/workflows/
│   └── scan-new-bid.yml   # CI/CD action for automated PDF scans on Git push
├── projects/
│   ├── projects.json      # Master index catalog of all onboarded projects
│   ├── project_co2_urea.json          # Extracted requirements database for ITB Project project
│   └── *.json             # Requirements databases for future projects
├── static/
│   ├── index.html         # Main wiki frontend interface
│   ├── style.css          # Styling (custom dark glassmorphism)
│   ├── app.js             # Core frontend controller (manages UI, TQs, and tabs)
│   ├── data.js            # Default global data fallback for offline mode
│   ├── data_project_co2_urea.js       # Offline ITB Project project database fallback
│   └── data_*.js          # Offline database fallbacks for future projects
├── .gitignore             # Screen out heavy PDF documents and caches from Git
├── app.py                 # Flask server backend
├── scan_project.py        # Python PyMuPDF specification parser and CLI onboarder
└── README.md              # Project documentation and workflows
```

---

## 🛠️ Offline Standalone Mode
If you are on-site or in a restricted network area without internet or server access:
1. Double-click the file `static/index.html` to open the app directly in any browser.
2. The page loads using standard offline paths.
3. The project selector allows switching between projects (e.g., `project_co2_urea`, `project_urea`). The frontend will automatically inject the corresponding `static/data_<project_id>.js` fallback file to load the respective specifications database locally.
