import os
import re
import json
import tempfile
import sys
import threading
from flask import Flask, request, jsonify, render_template, send_file, Response
from werkzeug.utils import secure_filename

# Ensure project root is in Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.append(project_dir)

import extract_to_excel

app = Flask(__name__, template_folder=os.path.join(project_dir, 'templates'))
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB limit

# Global log buffer for UI streaming
ui_logs = []
logs_lock = threading.Lock()

class UILogRedirector:
    def __init__(self, original_stdout):
        self.original_stdout = original_stdout

    def write(self, message):
        self.original_stdout.write(message)
        clean_msg = message.strip()
        if clean_msg:
            with logs_lock:
                ui_logs.append(clean_msg)

    def flush(self):
        self.original_stdout.flush()

# Redirect stdout to capture logs for the web UI
sys.stdout = UILogRedirector(sys.stdout)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/list-pdfs', methods=['GET'])
def list_pdfs():
    try:
        files = sorted([f for f in os.listdir(project_dir) if f.lower().endswith('.pdf')])
        # Add basic info about whether they are in mapping
        mapping = extract_to_excel.page_mappings
        pdf_list = []
        for f in files:
            size_mb = os.path.getsize(os.path.join(project_dir, f)) / (1024 * 1024)
            has_mapping = f in mapping
            pdf_list.append({
                "name": f,
                "size_mb": round(size_mb, 2),
                "has_mapping": has_mapping
            })
        return jsonify({"success": True, "pdfs": pdf_list})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/logs', methods=['GET'])
def get_logs():
    clear = request.args.get('clear', 'false').lower() == 'true'
    with logs_lock:
        logs = list(ui_logs)
        if clear:
            ui_logs.clear()
    return jsonify({"success": True, "logs": logs})

@app.route('/api/extract', methods=['POST'])
def start_extraction():
    # Clear logs at start of extraction
    with logs_lock:
        ui_logs.clear()
        ui_logs.append("Initialization extraction runner...")

    data = request.form
    selected_files = request.form.getlist('files')
    force_extract = request.form.get('force_extract', 'false').lower() == 'true'
    
    # Check if there is an uploaded file
    uploaded_file = request.files.get('file')
    
    def run_async_extraction():
        try:
            target_files = []
            
            # Handle uploaded file
            if uploaded_file and uploaded_file.filename:
                sec_name = secure_filename(uploaded_file.filename)
                target_path = os.path.join(project_dir, sec_name)
                print(f"Saving uploaded file to {target_path}...")
                uploaded_file.save(target_path)
                target_files.append(sec_name)
            else:
                target_files = selected_files

            if not target_files:
                print("Error: No files selected for extraction.")
                return

            print(f"Target files to extract: {', '.join(target_files)}")

            # Load the reference database if exists
            db_records = []
            if os.path.exists(extract_to_excel.db_file):
                with open(extract_to_excel.db_file, "r", encoding="utf-8") as f:
                    db_records = json.load(f)

            all_records = []
            
            for fname in target_files:
                sheet_filename = fname.replace('.pdf', '')
                print(f"Starting extraction for {fname}...")
                
                # Check if we can pull from cache
                cached_items = [r for r in db_records if r.get('ITB File Name', '').replace('.pdf', '') == sheet_filename]
                
                if not force_extract and cached_items:
                    print(f"Found {len(cached_items)} cached records in database for {fname}. Loading instantly...")
                    all_records.extend(cached_items)
                else:
                    # Run dynamic page-by-page parser
                    filepath = os.path.join(project_dir, fname)
                    if not os.path.exists(filepath):
                        print(f"Error: PDF file not found at {filepath}")
                        continue
                    
                    import fitz
                    from hifi_extractor.page_classifier import classify_page, PageCategory
                    from hifi_extractor.text_extractor import extract_page
                    
                    doc = fitz.open(filepath)
                    total_pages = len(doc)
                    file_mapping = extract_to_excel.page_mappings.get(fname, {})
                    
                    print(f"Scanning {total_pages} pages of {fname} dynamically...")
                    
                    for p_idx in range(total_pages):
                        page_num = p_idx + 1
                        page = doc[p_idx]
                        
                        classification = classify_page(page, page_num)
                        if classification.category == PageCategory.EMPTY:
                            continue
                            
                        # Report progress
                        if page_num % 10 == 0 or page_num == total_pages:
                            print(f"[{fname}] Processing page {page_num}/{total_pages}...")
                            
                        page_result = extract_page(doc, p_idx, classification=classification)
                        text = page_result.text
                        
                        paragraphs = re.split(r'\n\s*\n|\n(?=\d+\.)', text)
                        for para in paragraphs:
                            para = para.strip().replace('\n', ' ')
                            para = re.sub(r'\s+', ' ', para)
                            
                            if len(para) > 15 and extract_to_excel.is_telecom_clause(para):
                                p_map = file_mapping.get(str(page_num), {})
                                doc_no = p_map.get("doc_no", "")
                                title = p_map.get("title", "")
                                
                                clause_or_drg = ""
                                if doc_no and title:
                                    clause_or_drg = f"{doc_no}, {title}"
                                elif doc_no:
                                    clause_or_drg = doc_no
                                elif title:
                                    clause_or_drg = title
                                else:
                                    clause_or_drg = f"Specification Section / Page {page_num}"
                                    
                                printed_page_match = re.search(r'Page\s+(\d+)\s+of\s+(\d+)', text)
                                printed_page = f"Page {printed_page_match.group(1)}" if printed_page_match else f"{page_num}"
                                
                                record = {
                                    "ITB File Name": fname.replace('.pdf', ''),
                                    "Clause or\nDrawing No.": clause_or_drg,
                                    "Page#": printed_page,
                                    "Item": extract_to_excel.get_item_label(para),
                                    "Requirement": para,
                                    "상세 내용": "Verbatim specification requirement extracted dynamically."
                                }
                                all_records.append(record)
                    doc.close()
                    print(f"Dynamic extraction finished for {fname}. Found {len(all_records)} clauses.")

            # Fully anonymize all collected records
            anonymized_records = []
            for r in all_records:
                clean_r = {}
                for k, v in r.items():
                    # Align key names to excel headers
                    excel_key = "Clause or\nDrawing No." if k in ["Clause or Drawing No.", "Clause or\nDrawing No."] else k
                    clean_r[excel_key] = extract_to_excel.anonymize(str(v))
                anonymized_records.append(clean_r)

            # Generate final Excel and CSV output files
            print("Compiling final styled spreadsheet...")
            extract_to_excel.generate_excel_table(anonymized_records, extract_to_excel.example_xlsx, extract_to_excel.output_xlsx)
            print("Finished writing output tables. Complete!")
            
        except Exception as e:
            print(f"Error in extraction process: {e}")

    # Launch extraction thread to avoid blocking Flask
    t = threading.Thread(target=run_async_extraction)
    t.start()
    return jsonify({"success": True, "message": "Extraction started in background."})

@app.route('/api/preview-data', methods=['GET'])
def preview_data():
    try:
        if not os.path.exists(extract_to_excel.output_xlsx):
            return jsonify({"success": False, "error": "No output spreadsheet generated yet."})
        
        # Read the generated spreadsheet rows
        wb = load_workbook(extract_to_excel.output_xlsx, data_only=True)
        ws = wb.active
        rows = []
        headers = ["ITB File Name", "Clause or\nDrawing No.", "Page#", "Item", "Requirement", "상세 내용"]
        
        # Row 1 is headers, Row 2 is blank spacer, Row 3+ is data
        for r_idx in range(3, ws.max_row + 1):
            row_vals = [ws.cell(r_idx, c_idx).value for c_idx in range(1, 7)]
            if any(row_vals): # Skip fully empty rows
                rows.append({
                    "ITB File Name": row_vals[0] or "",
                    "Clause or Drawing No.": row_vals[1] or "",
                    "Page#": row_vals[2] or "",
                    "Item": row_vals[3] or "",
                    "Requirement": row_vals[4] or "",
                    "상세 내용": row_vals[5] or ""
                })
        return jsonify({"success": True, "rows": rows, "count": len(rows)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/download', methods=['GET'])
def download_file():
    file_format = request.args.get('format', 'xlsx').lower()
    if file_format == 'csv':
        filepath = extract_to_excel.output_xlsx.replace('.xlsx', '.csv')
        mimetype = 'text/csv'
        download_name = 'telecom_extracted_requirements.csv'
    else:
        filepath = extract_to_excel.output_xlsx
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        download_name = 'telecom_extracted_requirements.xlsx'

    if not os.path.exists(filepath):
        return jsonify({"success": False, "error": "Requested file does not exist. Run extraction first."}), 404
        
    return send_file(filepath, mimetype=mimetype, as_attachment=True, download_name=download_name)

if __name__ == '__main__':
    print("Starting Flask web backend at http://localhost:5000...")
    app.run(host='127.0.0.1', port=5000, debug=False)
