import os
import json
import csv
import io
import sys
from flask import Flask, send_from_directory, jsonify, request, Response
from scan_project import scan_pdfs, sanitize_id

# Add parent path to import hifi_extractor package
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

app = Flask(__name__, static_folder='static')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECTS_DIR = os.path.join(BASE_DIR, "projects")
os.makedirs(PROJECTS_DIR, exist_ok=True)
CATALOG_PATH = os.path.join(PROJECTS_DIR, "projects.json")

# Ensure catalog exists
if not os.path.exists(CATALOG_PATH):
    with open(CATALOG_PATH, 'w', encoding='utf-8') as f:
        json.dump([], f)

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/api/projects', methods=['GET'])
def get_projects():
    try:
        if os.path.exists(CATALOG_PATH):
            with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
                projects = json.load(f)
            return jsonify(projects)
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/requirements', methods=['GET'])
def get_default_requirements():
    try:
        if os.path.exists(CATALOG_PATH):
            with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
                projects = json.load(f)
            if projects:
                default_id = projects[0]["id"]
                req_path = os.path.join(PROJECTS_DIR, f"{default_id}.json")
                if os.path.exists(req_path):
                    with open(req_path, 'r', encoding='utf-8') as f_req:
                        return jsonify(json.load(f_req))
        
        # Hard fallback to project_co2_urea
        fallback_path = os.path.join(PROJECTS_DIR, "project_co2_urea.json")
        if os.path.exists(fallback_path):
            with open(fallback_path, 'r', encoding='utf-8') as f_req:
                return jsonify(json.load(f_req))
                
        return jsonify({"error": "No requirements databases found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/requirements/<project_id>', methods=['GET'])
def get_project_requirements(project_id):
    try:
        req_path = os.path.join(PROJECTS_DIR, f"{project_id}.json")
        if not os.path.exists(req_path):
            return jsonify({"error": f"Requirements for project '{project_id}' not found"}), 404
            
        with open(req_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scan', methods=['POST'])
def run_project_scan():
    try:
        data = request.json or {}
        name = data.get('name')
        pdf_dir = data.get('dir')
        
        if not name or not pdf_dir:
            return jsonify({"error": "Missing 'name' or 'dir' in scan request"}), 400
            
        project_id = scan_pdfs(pdf_dir, name)
        if not project_id:
            return jsonify({"error": "Scanning failed"}), 500
            
        return jsonify({
            "status": "success",
            "message": f"Successfully scanned and onboarded project '{name}'",
            "project_id": project_id
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tq/export', methods=['POST'])
def export_tqs():
    try:
        tqs = request.json.get('tqs', [])
        
        def generate():
            data = io.StringIO()
            writer = csv.writer(data)
            writer.writerow(['TQ Item', 'Subsystem', 'Document Ref', 'Clause/Page Ref', 'Description of Ambiguity / Contradiction', 'Bidder Proposal / Clarification Request', 'Owner Reply'])
            for tq in tqs:
                writer.writerow([
                    tq.get('id', ''),
                    tq.get('subsystem', ''),
                    tq.get('docRef', ''),
                    tq.get('clause', ''),
                    tq.get('description', ''),
                    tq.get('proposal', ''),
                    '' # blank for owner reply
                ])
                yield data.getvalue()
                data.seek(0)
                data.truncate(0)
                
        return Response(
            generate(),
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=telecom_security_tqs.csv"}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/pdf-files', methods=['GET'])
def list_pdf_files():
    try:
        pdf_dir = "g:\\My Drive\\Project\\CTGU"
        files = sorted([f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')])
        return jsonify(files)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/extract', methods=['POST'])
def run_hifi_extract():
    try:
        data = request.json or {}
        filename = data.get('filename')
        pages = data.get('pages', '')
        ocr_lang = data.get('ocr_lang', 'eng')
        dpi = int(data.get('dpi', 300))
        suppress_margins = bool(data.get('suppress_margins', True))
        margin_method = data.get('margin_method', 'static_zone')
        header_zone = float(data.get('header_zone', 5.0))
        footer_zone = float(data.get('footer_zone', 5.0))
        chunk_size = int(data.get('chunk_size', 0))
        overlap = int(data.get('overlap', 50))
        
        if not filename:
            return jsonify({"error": "Missing 'filename' in request"}), 400
            
        pdf_dir = "g:\\My Drive\\Project\\CTGU"
        full_path = os.path.join(pdf_dir, filename)
        if not os.path.exists(full_path):
            return jsonify({"error": f"PDF file not found: {filename}"}), 404
            
        page_range = None
        if pages:
            if '-' in pages:
                parts = pages.split('-')
                page_range = (int(parts[0].strip()), int(parts[1].strip()))
            else:
                page = int(pages.strip())
                page_range = (page, page)
                
        from hifi_extractor.pipeline import run_pipeline, PipelineConfig
        
        config = PipelineConfig(
            ocr_language=ocr_lang,
            dpi=dpi,
            suppress_margins=suppress_margins,
            margin_method=margin_method,
            header_zone_pct=header_zone / 100.0,
            footer_zone_pct=footer_zone / 100.0,
            format_markdown=True,
            enable_chunking=chunk_size > 0,
            max_tokens=chunk_size if chunk_size > 0 else 512,
            overlap_tokens=overlap,
            include_page_numbers=True
        )
        
        # Ensure Tesseract OCR is in the path
        tess_path = r"C:\Program Files\Tesseract-OCR"
        if os.path.exists(tess_path) and tess_path not in os.environ["PATH"]:
            os.environ["PATH"] += os.pathsep + tess_path
            
        result = run_pipeline(
            pdf_path=full_path,
            config=config,
            page_range=page_range
        )
        
        return jsonify({
            "status": "success",
            "summary": result.summary(),
            "markdown": result.markdown,
            "details": result.to_dict()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting ITB Wiki Server on http://localhost:5000/")
    app.run(debug=True, port=5000)
