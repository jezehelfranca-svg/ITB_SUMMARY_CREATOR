import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECTS_DIR = os.path.join(BASE_DIR, "projects")
STATIC_DIR = os.path.join(BASE_DIR, "static")

def sync_projects():
    print("[*] Synchronizing JSON database changes to offline Javascript files...")
    
    if not os.path.exists(PROJECTS_DIR):
        print(f"[!] Error: Projects directory {PROJECTS_DIR} not found.")
        return

    # Get all JSON files in projects/ folder except projects.json itself
    json_files = [f for f in os.listdir(PROJECTS_DIR) if f.endswith('.json') and f != 'projects.json']
    
    for f_name in json_files:
        project_id = f_name.replace('.json', '')
        json_path = os.path.join(PROJECTS_DIR, f_name)
        js_path = os.path.join(STATIC_DIR, f"data_{project_id}.js")
        
        try:
            # Read updated JSON content
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Write to offline JS fallback
            with open(js_path, 'w', encoding='utf-8') as js_file:
                js_file.write(f"// Fallback requirements database for {data.get('project', project_id)}\n")
                js_file.write(f"const REQUIREMENTS_DATA_{project_id.upper()} = ")
                json.dump(data, js_file, indent=2, ensure_ascii=False)
                js_file.write(";\n")
            
            # If it's the primary project_co2_urea project, update data.js (which is the default offline load)
            if project_id == 'project_co2_urea':
                default_js_path = os.path.join(STATIC_DIR, "data.js")
                with open(default_js_path, 'w', encoding='utf-8') as default_js_file:
                    default_js_file.write("// Default requirements database fallback\n")
                    default_js_file.write("const REQUIREMENTS_DATA = ")
                    json.dump(data, default_js_file, indent=2, ensure_ascii=False)
                    default_js_file.write(";\n")
                print(f"[*] Updated default offline data: static/data.js")
                
            print(f"[+] Synchronized: projects/{f_name} -> static/data_{project_id}.js")
            
        except Exception as e:
            print(f"[!] Error syncing {f_name}: {e}")
            
    # Synchronize the project catalog
    catalog_json_path = os.path.join(PROJECTS_DIR, "projects.json")
    if os.path.exists(catalog_json_path):
        catalog_js_path = os.path.join(STATIC_DIR, "projects_catalog.js")
        try:
            with open(catalog_json_path, 'r', encoding='utf-8') as f:
                catalog_data = json.load(f)
            with open(catalog_js_path, 'w', encoding='utf-8') as f:
                f.write("// Fallback projects catalog database\n")
                f.write("const PROJECTS_CATALOG = ")
                json.dump(catalog_data, f, indent=2, ensure_ascii=False)
                f.write(";\n")
            print(f"[+] Synchronized catalog: {catalog_json_path} -> {catalog_js_path}")
        except Exception as e:
            print(f"[!] Error syncing catalog: {e}")
            
    print("[*] Synchronization completed successfully!")

if __name__ == "__main__":
    sync_projects()
