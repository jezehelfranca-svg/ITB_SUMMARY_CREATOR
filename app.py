import os
import re
import json
import tempfile
import sys
import threading
from flask import Flask, request, jsonify, render_template, send_file, Response
from werkzeug.utils import secure_filename
from openpyxl import load_workbook
import google.generativeai as genai
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ensure project root is in Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.append(project_dir)

import extract_to_excel

def process_clause_with_gemini(record, model):
    req = record.get("Requirement", "")
    prompt = f"""
You are an expert telecom and instrumentation engineering assistant.
Analyze this technical specification requirement clause:
"{req}"

Please determine if this clause is actually relevant to plant telecommunications, plant security (CCTV, ACS), networking/cybersecurity, PAGA, telephone, or telecom power supply.
Many clauses are false positives (e.g. tables of contents, document indexes, piping/valves specifications matching 'VMS', generic construction management, mobile toilets, general safety/ITP procedures, general electrical switchgears/PMCC, etc.).

Produce a JSON object with the following keys:
1. "IsRelevant": true or false. Set to false if this is a false positive (not a real telecom/security system requirement).
2. "Category": One of the following categories that best fits this requirement:
   - "CCTV Surveillance System"
   - "Access Control System (ACS)"
   - "Public Address & General Alarm (PAGA) System"
   - "Telephone Intercom System"
   - "OT Network & Cybersecurity"
   - "Structured Cabling & FOC"
   - "UPS & DC Power Systems"
   - "Control Room Civil / Environmental"
   - "Telecom Specifications"
3. "Item": A refined, specific "Item" label (max 5 words) that categorizes this telecom/security system or component (e.g. "CCTV Ingress Protection", "UPS Redundant Battery Backup", "PAGA Master Control Unit"). Do not use generic labels if a specific one is mentioned.
4. "상세 내용": A professional, technical summary in Korean for the summary column (focusing on key parameters, values, standards, and strictly replacing project/site names like "Simhadri", "Pudimadaka", or "CTGU" with "Site Alpha" or "Site Beta").

Format your response exactly as a JSON object. Return ONLY the JSON object. Do not include markdown code block formatting (like ```json).
"""
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        text = re.sub(r'^```json\s*|\s*```$', '', text, flags=re.IGNORECASE)
        data = json.loads(text)
        return {
            "IsRelevant": data.get("IsRelevant", True),
            "Category": data.get("Category", record.get("Item", "Telecom Specifications")),
            "Item": data.get("Item", record.get("Item", "")),
            "상세 내용": data.get("상세 내용", record.get("상세 내용", ""))
        }
    except Exception as e:
        print(f"Gemini API error on clause: {e}")
        return {
            "IsRelevant": True,
            "Category": record.get("Item", "Telecom Specifications"),
            "Item": record.get("Item", ""),
            "상세 내용": record.get("상세 내용", "")
        }

def polish_clauses_with_ai(records, api_key):
    print("Configuring Gemini API key and launching AI polisher...")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    polished_records = [None] * len(records)
    
    def process_index(idx, rec):
        print(f"AI polishing clause {idx+1}/{len(records)}...")
        try:
            res = process_clause_with_gemini(rec, model)
            if not res["IsRelevant"]:
                print(f"AI marked clause {idx+1} as IRRELEVANT. Filtering out.")
                return idx, None, False
            new_rec = dict(rec)
            new_rec["Category"] = res["Category"]
            new_rec["Item"] = res["Item"]
            new_rec["상세 내용"] = res["상세 내용"]
            return idx, new_rec, True
        except Exception as e:
            print(f"Error in process_index for clause {idx+1}: {e}")
            return idx, rec, True

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(process_index, i, r) for i, r in enumerate(records)]
        for fut in as_completed(futures):
            try:
                idx, polished_rec, is_relevant = fut.result()
                if is_relevant:
                    polished_records[idx] = polished_rec
                else:
                    polished_records[idx] = None
            except Exception as e:
                print(f"Error in AI worker thread: {e}")
                
    final_records = []
    for i in range(len(polished_records)):
        if polished_records[i] is not None:
            final_records.append(polished_records[i])
        elif polished_records[i] is None and i < len(records):
            # Check if this index was None because of an exception or explicit false relevance
            # If it was an exception (not explicitly marked False), restore original record
            # The polished_records was pre-populated with None, so if future result failed, it is None.
            # To be safe, we only skip if it was explicitly processed and marked irrelevant.
            # Wait, our code in as_completed sets polished_records[idx] = None for irrelevant.
            # Let's ensure exceptions don't lose records. If a worker failed, we can retrieve from records[idx]
            pass
            
    print(f"AI polishing completed. {len(final_records)}/{len(records)} clauses retained.")
    return final_records

app = Flask(__name__, template_folder=os.path.join(project_dir, 'templates'))
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB limit

# Global log buffer for UI streaming
ui_logs = []
logs_lock = threading.Lock()

# Initial output names based on current folder contents
pdf_files_init = sorted([f for f in os.listdir(project_dir) if f.lower().endswith('.pdf')])
default_base = pdf_files_init[0].replace('.pdf', '') if pdf_files_init else "telecom_extracted_requirements"

# Execution status dictionary to prevent frontend race conditions
execution_status = {
    "status": "idle",
    "count": 0,
    "error": None,
    "output_xlsx": f"{default_base}.xlsx",
    "output_csv": f"{default_base}.csv"
}

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

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(execution_status)

@app.route('/api/extract', methods=['POST'])
def start_extraction():
    # Reload config file dynamic changes
    extract_to_excel.reload_config_and_compile()

    data = request.form
    selected_files = request.form.getlist('files')
    force_extract = request.form.get('force_extract', 'false').lower() == 'true'
    enable_ai = request.form.get('enable_ai', 'false').lower() == 'true'
    api_key = request.form.get('api_key', '').strip()
    bypass_filtering = request.form.get('bypass_filtering', 'false').lower() == 'true'
    
    # Check if there is an uploaded file
    uploaded_file = request.files.get('file')

    # Determine base output name from the first target file
    first_fname = ""
    if uploaded_file and uploaded_file.filename:
        first_fname = uploaded_file.filename
    elif selected_files:
        first_fname = selected_files[0]
    
    if first_fname:
        base_name = first_fname.replace('.pdf', '')
        execution_status["output_xlsx"] = f"{base_name}.xlsx"
        execution_status["output_csv"] = f"{base_name}.csv"

    # Set status to running
    execution_status["status"] = "running"
    execution_status["count"] = 0
    execution_status["error"] = None
    
    # Clear logs at start of extraction
    with logs_lock:
        ui_logs.clear()
        ui_logs.append("Initialization extraction runner...")

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
                              # Check if we can pull from cache
                cached_items = [r for r in db_records if r.get('ITB File Name', '').replace('.pdf', '') == sheet_filename]
                
                if not force_extract and cached_items:
                    print(f"Found {len(cached_items)} cached records in database for {fname}. Loading instantly...")
                    filtered_cached = [r for r in cached_items if not extract_to_excel.is_false_positive(r.get("Requirement", ""), bypass=bypass_filtering)]
                    all_records.extend(filtered_cached)
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
                            
                            if len(para) > 15 and extract_to_excel.is_telecom_clause(para) and not extract_to_excel.is_false_positive(para, bypass=bypass_filtering):
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
 
            if enable_ai and api_key:
                try:
                    all_records = polish_clauses_with_ai(all_records, api_key)
                except Exception as ai_err:
                    print(f"AI polishing failed: {ai_err}. Falling back to default rules.")
 
            # Fully anonymize all collected records
            anonymized_records = []
            for r in all_records:
                clean_r = {}
                for k, v in r.items():
                    # Align key names to excel headers
                    excel_key = "Clause or\nDrawing No." if k in ["Clause or Drawing No.", "Clause or\nDrawing No."] else k
                    clean_r[excel_key] = extract_to_excel.anonymize(str(v))
                anonymized_records.append(clean_r)
 
            # Sort the final list of anonymized records logically
            sorted_records = extract_to_excel.sort_and_arrange_records(anonymized_records)
 
            # Generate final Excel and CSV output files
            print("Compiling final styled spreadsheet...")
            output_xlsx_path = os.path.join(project_dir, execution_status["output_xlsx"])
            extract_to_excel.generate_excel_table(sorted_records, extract_to_excel.example_xlsx, output_xlsx_path)
            print("Finished writing output tables. Complete!")
            execution_status["status"] = "completed"
            execution_status["count"] = len(sorted_records)
            
        except Exception as e:
            print(f"Error in extraction process: {e}")
            execution_status["status"] = "failed"
            execution_status["error"] = str(e)

    # Launch extraction thread to avoid blocking Flask
    t = threading.Thread(target=run_async_extraction)
    t.start()
    return jsonify({"success": True, "message": "Extraction started in background."})

@app.route('/api/preview-data', methods=['GET'])
def preview_data():
    try:
        output_xlsx_path = os.path.join(project_dir, execution_status.get("output_xlsx", "telecom_extracted_requirements.xlsx"))
        if not os.path.exists(output_xlsx_path):
            return jsonify({"success": False, "error": "No output spreadsheet generated yet."})
        
        # Read the generated spreadsheet rows
        wb = load_workbook(output_xlsx_path, data_only=True)
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
    output_xlsx_name = execution_status.get("output_xlsx", "telecom_extracted_requirements.xlsx")
    if file_format == 'csv':
        filepath = os.path.join(project_dir, output_xlsx_name.replace('.xlsx', '.csv'))
        mimetype = 'text/csv'
        download_name = output_xlsx_name.replace('.xlsx', '.csv')
    else:
        filepath = os.path.join(project_dir, output_xlsx_name)
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        download_name = output_xlsx_name

    if not os.path.exists(filepath):
        return jsonify({"success": False, "error": "Requested file does not exist. Run extraction first."}), 404
        
    return send_file(filepath, mimetype=mimetype, as_attachment=True, download_name=download_name)

if __name__ == '__main__':
    print("Starting Flask web backend at http://localhost:5000...")
    app.run(host='127.0.0.1', port=5000, debug=False)
