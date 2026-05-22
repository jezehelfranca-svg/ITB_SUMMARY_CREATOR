import os
import json
import csv
import io
from flask import Flask, send_from_directory, jsonify, request, Response
from scan_project import scan_pdfs, sanitize_id

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
        
        # Hard fallback to ctgu
        fallback_path = os.path.join(PROJECTS_DIR, "ctgu.json")
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

if __name__ == '__main__':
    print("Starting ITB Wiki Server on http://localhost:5000/")
    app.run(debug=True, port=5000)
