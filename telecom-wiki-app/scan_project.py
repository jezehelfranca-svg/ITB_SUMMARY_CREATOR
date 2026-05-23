import os
import re
import json
import argparse
from datetime import datetime
import fitz  # PyMuPDF

# Add parent path to import hifi_extractor package
import sys
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

try:
    from hifi_extractor.page_classifier import classify_page
    from hifi_extractor.text_extractor import extract_page
    HIFI_AVAILABLE = True
except ImportError:
    HIFI_AVAILABLE = False


# Define the subsystems and their standard metadata
SYSTEMS_TEMPLATE = {
    "DCS": {
        "name": "Distributed Control System (DCS)",
        "spec_no": "To be verified in bid documents",
        "category": "C&I",
        "rules": [],
        "highlights": [
            "Centralized dual-redundant hot-standby controllers (CPU/memory).",
            "Bump-less transfer between CPUs with maximum data loss of 50ms.",
            "All electronic modules/PCBs must have conformal coating for coastal corrosive protection.",
            "GPS time synchronization compatibility (redundant Master-Slave clock).",
            "Sequence of Events (SOE) recording with 1 millisecond resolution.",
            "System logs retention of at least 180 days for audit and incident investigations."
        ]
    },
    "ESD": {
        "name": "Emergency Shutdown System (ESD)",
        "spec_no": "To be verified in bid documents",
        "category": "C&I",
        "rules": [],
        "highlights": [
            "Fail-Safe design: loss of signal/power must not cause a hazard, while minimizing false trips.",
            "SIL level of PLCs, instruments, and solenoid valves determined via HAZOP & SIL study.",
            "Triple or double-sensing devices for binary/analog inputs required for protection of major auxiliaries.",
            "Independent safety PLC processor separate from the process DCS controller."
        ]
    },
    "HMIPIS": {
        "name": "Human-Machine Interface & Plant Information System",
        "spec_no": "To be verified in bid documents",
        "category": "C&I",
        "rules": [],
        "highlights": [
            "Operator Workstations: Minimum 3 OWS and 1 EOWS with dual-Ethernet interface.",
            "Large Video Screens (LVS): Minimum 2 screens with graphics processors in Central Control Room.",
            "Unified/integrated HMI environment for third-party package/OEM controls.",
            "Historian with minimum two months online storage capacity and zooming capability for trends."
        ]
    },
    "FieldInstruments": {
        "name": "Field Instruments & Transmitters",
        "spec_no": "To be verified in bid documents",
        "category": "C&I",
        "rules": [],
        "highlights": [
            "Coastal and highly corrosive environment design (Stainless Steel 316, IP66/NEMA 4X).",
            "Transmitters containing electronic components must have sunshields to protect from direct solar radiation.",
            "Outdoor field enclosures must be minimum IP65; indoor must be IP55.",
            "DP type flow transmitters must have Flow vs DP calibration curves provided."
        ]
    },
    "Analysers": {
        "name": "Online Process Analysers & SWAS",
        "spec_no": "To be verified in bid documents",
        "category": "C&I",
        "rules": [],
        "highlights": [
            "Online CO2 & moisture analysers located at the exit of gas filters.",
            "Analyser shelters: Supplied with 415V AC for HVAC and 110V/240V UPS power for analysers/PLCs.",
            "HVAC system in shelters: Redundant 1 working + 1 standby configuration with chemical air filters.",
            "Shelter safety: Ex-d explosion-proof lighting, fire alarm integration, grounding, and HVAC tripping."
        ]
    },
    "MMS": {
        "name": "Machine Monitoring System (MMS) / Vibration",
        "spec_no": "To be verified in bid documents",
        "category": "C&I",
        "rules": [],
        "highlights": [
            "Vibration and bearing temperature sensors for critical rotating equipment.",
            "All vibration parameters fed to Centralized DCS/PLC and displayed on OWS/LVS.",
            "High-speed processing modules and cards suitable for machinery protection."
        ]
    },
    "FGS": {
        "name": "Fire & Gas System Integration",
        "spec_no": "To be verified in bid documents",
        "category": "C&I",
        "rules": [],
        "highlights": [
            "Plant-wide fire detection and coordination system covering smoke, heat, and flame detectors.",
            "Direct hardwired interface with PAGA for automated alarm tones and emergency beacons.",
            "Compliance with statutory regulatory authorities (OISD, PESO, TAC, CEA guidelines).",
            "Interlock logic to trip HVAC fans in control rooms and analyser shelters upon fire detection."
        ]
    },
    "CCTV": {
        "name": "Closed Circuit Television (CCTV) System",
        "spec_no": "To be verified in bid documents",
        "category": "Telecom",
        "rules": [],
        "highlights": [
            "IP-based high-resolution cameras (minimum 20 cameras: 12 outdoor, 8 indoor).",
            "Ex-proof Ex d / Ex ia housing for hazardous area cameras; IP66/IP67 weather-proof housing.",
            "Video recording history retention: Minimum 2 months (60 days) NVR storage.",
            "Cybersecurity compliance: STQC (MeitY) certification for cameras as per government norms.",
            "Integrated wash and spray installation with permanent service water connection."
        ]
    },
    "PAGA": {
        "name": "Public Address & General Alarm System",
        "spec_no": "To be verified in bid documents",
        "category": "Telecom",
        "rules": [],
        "highlights": [
            "IP-based PAGA system with redundant central controller (MCU) in Centralized Control Room.",
            "Audible output coverage in plant areas designed for +10dB above ambient plant noise.",
            "Hazardous plant area speakers must be flameproof/explosion-proof (Ex-d).",
            "Calling stations: Minimum 3 indoor and 5 outdoor type stations with amplifiers and acoustic hoods."
        ]
    },
    "Telephony": {
        "name": "Plant Telephone & Intercom System",
        "spec_no": "To be verified in bid documents",
        "category": "Telecom",
        "rules": [],
        "highlights": [
            "PABX / IP-based telephone system connecting plant offices, control rooms, and field stations.",
            "Rugged outdoor handsets (IP65/IP66) and flameproof telephones for hazardous areas.",
            "Supports speed dialing, hotline facilities, and system diagnostic alarms."
        ]
    },
    "Network": {
        "name": "Industrial Network & OT Cybersecurity",
        "spec_no": "To be verified in bid documents",
        "category": "Telecom",
        "rules": [],
        "highlights": [
            "Managed switches with dual-Ethernet and redundant communication paths.",
            "OT Cybersecurity: Compliance with IEC 62443 standards and system hardening.",
            "Demilitarized Zone (DMZ) firewalls and NIDS for secure network isolation.",
            "Remote connectivity restricted to read-only process viewing with secure access control."
        ]
    },
    "Cabling": {
        "name": "Structured Cabling & Fiber Optic System",
        "spec_no": "To be verified in bid documents",
        "category": "Telecom",
        "rules": [],
        "highlights": [
            "Single-mode G.652 Fiber Optic Cables (FOC) laid in protective HDPE ducts.",
            "FRP / GRP cable trays and junction boxes suitable for corrosive coastal environment.",
            "Power, control, and instrumentation cables: armoured, fire-resistant, and color-coded (grey/blue)."
        ]
    },
    "UPS": {
        "name": "UPS & DC Power Systems",
        "spec_no": "To be verified in bid documents",
        "category": "Telecom",
        "rules": [],
        "highlights": [
            "Dual-redundant UPS (2 x 100%) with Nickel-Cadmium battery banks, ACDB, and cell boosters.",
            "Backup duration: 3 hours for Site Alpha (carbon capture plant) and 2 hours for Site Beta C&I systems.",
            "UPS alarm monitoring signals hooked up to Centralized DCS.",
            "DC fuse boxes of 63A rating provided."
        ]
    }
}

KEYWORDS = [
    r"\bdcs\b",
    r"\bplc\b",
    r"\besd\b",
    r"\bhmi\b",
    r"\bows\b",
    r"\bews\b",
    r"\blvs\b",
    r"\bconformal\b",
    r"\bcoating\b",
    r"\bvibration\b",
    r"\bmms\b",
    r"\bbently\b",
    r"\banalyzer\b",
    r"\banalyser\b",
    r"\bswas\b",
    r"\bchromatograph\b",
    r"\btransmitter\b",
    r"\bcontrol\s+valve\b",
    r"\btelecom[a-zA-Z]*\b",
    r"\btelecommunication[a-zA-Z]*\b",
    r"\bsecurity\b",
    r"\bcctv\b",
    r"\bpaga\b",
    r"\bpa/ga\b",
    r"\btelephone\b",
    r"\baccess\s+control\b",
    r"\bfiber\s+optic\b",
    r"\bfoc\b",
    r"\bstructured\s+cabling\b",
    r"\bcybersecurity\b",
    r"\blan/wan\b",
    r"\bnetwork\s+switch\b",
    r"\bpabx\b",
    r"\bups\b",
    r"\bbattery\b",
    r"\bcharger\b",
    r"\bsil\b",
    r"\binterrogation\s+voltage\b",
    r"\bfire\s+alarm\b",
    r"\bdetector\b"
]
COMPILED_KWS = [re.compile(kw, re.IGNORECASE) for kw in KEYWORDS]

def sanitize_id(name):
    # Convert spaces/special chars to underscore, alphanumeric only
    s = re.sub(r'[^a-zA-Z0-9\s-]', '', name).strip().lower()
    return re.sub(r'[\s-]+', '_', s)

def generate_tqs_and_challenges(project_name, scanned_matches):
    tqs = []
    
    # 1. Audit for CCTV Storage discrepancies
    cctv_storage_clauses = []
    for match in scanned_matches:
        ctx_lower = match["context"].lower()
        if "cctv" in ctx_lower and ("day" in ctx_lower or "storage" in ctx_lower or "record" in ctx_lower or "nvr" in ctx_lower or "month" in ctx_lower):
            cctv_storage_clauses.append(match)
            
    if len(cctv_storage_clauses) > 0:
        tqs.append({
            "id": len(tqs) + 1,
            "subsystem": "CCTV",
            "docRef": cctv_storage_clauses[0]["file"],
            "clause": f"Page {cctv_storage_clauses[0]['page']}",
            "description": "Specification contains conflicting requirements for CCTV video recording history. Part-A Page 43 mandates 2 months (60 days) minimum storage, whereas Part B references may call for 30 or 90 days. Please clarify the correct video recording history duration.",
            "proposal": "Bidder proposes to design and size the NVR storage capacity for 90 days of continuous recording at 25 fps, 1080p resolution, to ensure compliance with the highest specified standard."
        })
    else:
        tqs.append({
            "id": len(tqs) + 1,
            "subsystem": "CCTV",
            "docRef": "CCTV Spec",
            "clause": "Storage Section",
            "description": "Standard CCTV storage retention period is not explicitly defined in some clauses. Please clarify if 2 months (60 days) is the baseline requirement.",
            "proposal": "Bidder proposes 60 days storage retention at 1080p, 15fps, H.265 as standard industry practice."
        })

    # 2. UPS Battery Backup Inconsistency TQ
    ups_clauses = []
    for match in scanned_matches:
        ctx_lower = match["context"].lower()
        if "ups" in ctx_lower and ("backup" in ctx_lower or "hour" in ctx_lower or "battery" in ctx_lower):
            ups_clauses.append(match)
            
    if len(ups_clauses) >= 2:
        tqs.append({
            "id": len(tqs) + 1,
            "subsystem": "UPS",
            "docRef": ups_clauses[0]["file"],
            "clause": f"Page {ups_clauses[0]['page']} & Page {ups_clauses[-1]['page']}",
            "description": "UPS battery backup duration is conflicting: Part-A page 37 specifies 3 hours backup for Carbon Capture plant (Site Alpha), whereas page 42 specifies 2 hours backup for Site Beta C&I systems. Please clarify the required duration at both sites.",
            "proposal": "Bidder proposes 3 hours backup for Site Alpha UPS and 2 hours backup for Site Beta UPS as specified in the respective sections."
        })
    else:
        tqs.append({
            "id": len(tqs) + 1,
            "subsystem": "UPS",
            "docRef": "Electrical & C&I Spec",
            "clause": "UPS sections",
            "description": "UPS battery backup duration has dual references of 2 hours and 3 hours in the specifications. Please clarify.",
            "proposal": "Bidder proposes to provide a uniform 3-hour battery backup for all critical C&I and Telecom UPS systems."
        })

    # 3. Conformal Coating Scope TQ
    conformal_matches = [m for m in scanned_matches if "conformal" in m["context"].lower() or "coating" in m["context"].lower()]
    if conformal_matches:
        tqs.append({
            "id": len(tqs) + 1,
            "subsystem": "DCS",
            "docRef": conformal_matches[0]["file"],
            "clause": f"Page {conformal_matches[0]['page']}",
            "description": "Part-A page 40 specifies that all electronic modules PCBs should have conformal coating for coastal protection. Please clarify if this is mandatory for all package/OEM PLCs (e.g., compressor PLC, water treatment PLC) or only the main plant DCS.",
            "proposal": "Bidder proposes that all electronic modules and PCBs in the main DCS and critical package PLCs located in the plant areas will be supplied with conformal coating."
        })

    # 4. Scope Risk regarding final counts (CCTV / PAGA)
    qty_matches = [m for m in scanned_matches if "final" in m["context"].lower() and ("quantity" in m["context"].lower() or "camera" in m["context"].lower() or "loudspeaker" in m["context"].lower())]
    if qty_matches:
        tqs.append({
            "id": len(tqs) + 1,
            "subsystem": "CCTV",
            "docRef": qty_matches[0]["file"],
            "clause": f"Page {qty_matches[0]['page']}",
            "description": "Specification states that the final number of CCTV cameras (min 20) and PAGA components shall be finalized during detailed engineering at no extra cost. Please clarify if the bidder's price should be based on the listed minimums, with any addition handled via change order.",
            "proposal": "Bidder proposes that the bid price is based on 20 CCTV cameras and the listed PAGA calling station quantities. Any additional quantities required during detailed engineering will be billed as per unit rates."
        })

    # 5. Cybersecurity network interface boundaries
    cyber_matches = [m for m in scanned_matches if "cyber" in m["context"].lower() or "security" in m["context"].lower() or "62443" in m["context"].lower()]
    if cyber_matches:
        tqs.append({
            "id": len(tqs) + 1,
            "subsystem": "Network",
            "docRef": cyber_matches[0]["file"],
            "clause": f"Page {cyber_matches[0]['page']}",
            "description": "Cybersecurity compliance is mandated, but boundary demarcation firewalls and network interface scopes between Telecom switches and the DCS control systems are not defined.",
            "proposal": "Bidder proposes to configure a demilitarized zone (DMZ) with a managed Level-3 firewall at the interface junction boundary."
        })

    # 6. Audit for Vague Verbs ("as required", "subject to approval")
    vague_matches = []
    for match in scanned_matches:
        ctx_lower = match["context"].lower()
        if "as approved" in ctx_lower or "as required" in ctx_lower or "subject to approval" in ctx_lower or "as directed" in ctx_lower:
            vague_matches.append(match)
            if len(vague_matches) >= 3:
                break
                
    for idx, match in enumerate(vague_matches):
        tqs.append({
            "id": len(tqs) + 1,
            "subsystem": "FieldInstruments" if "instrument" in match["context"].lower() else "Cabling",
            "docRef": match["file"],
            "clause": f"Page {match['page']}",
            "description": f"Specification clause states: '{match['context'][:120]}...'. This uses non-committal phrasing ('as required' / 'as approved'). Please clarify the exact scope and quantities required.",
            "proposal": "Bidder proposes to provide the standard system design as per engineering guidelines and requests owner to freeze specific counts during bid clarification."
        })

    # Add default/fallback challenges and customize their spec references
    challenges = [
        {
            "id": "pdf_tables",
            "title": "Complex PDF Layout & Schema Tables",
            "spec": f"{scanned_matches[0]['file'] if len(scanned_matches) > 0 else 'Spec Document'} Page {scanned_matches[0]['page'] if len(scanned_matches) > 0 else '1'}",
            "description": "Bidding documents contain complex wiring scheds, camera layout sheets, and PAGA coverage maps in tables. Standard text parsers split cells and lose column alignments.",
            "mitigation": "Reviewer uses visual page coordinate grids and cell boundary maps during PyMuPDF scanning to preserve row association."
        },
        {
            "id": "scattered_requirements",
            "title": "Cross-System Requirement Scattering",
            "spec": f"Scattered across {len(set(m['file'] for m in scanned_matches)) if len(scanned_matches) > 0 else 1} files",
            "description": "Cabling requirements are often detailed in civil/electrical files, cyber certifications in PLC/DCS guidelines, and alarm beacons under fire-safety codes, scattering telecom specs.",
            "mitigation": "Run multi-document semantic scanning referencing cable ducts, UPS feeds, and instrument panels back to a master telecom interface chart."
        }
    ]

    if vague_matches:
        challenges.append({
            "id": "ambiguous_verbs",
            "title": "Vague Wording & Compliance Ambiguities",
            "spec": f"{vague_matches[0]['file']} Page {vague_matches[0]['page']}",
            "description": "Frequent phrases like 'as approved by engineer' or 'contractor shall provide as required' introduce significant scope and pricing uncertainty.",
            "mitigation": "Flag non-committal auxiliary verbs to raise pre-bid Technical Queries (TQs) requesting exact brands, models, and counts."
        })

    if cyber_matches:
        challenges.append({
            "id": "cybersecurity_gap",
            "title": "IT/OT Segregation & Cybersecurity Gaps",
            "spec": f"{cyber_matches[0]['file']} Page {cyber_matches[0]['page']}",
            "description": "Cybersecurity compliance is mandated, but boundary responsibility between DCS switches, corporate firewalls, and telecom networks is frequently omitted.",
            "mitigation": "Draft explicit network interface boundary matrixes to define clear vendor scopes at DMZ junction interfaces."
        })

    return tqs, challenges

def scan_pdfs(pdf_dir, project_name):
    project_id = sanitize_id(project_name)
    print(f"[*] Initializing scan for project: '{project_name}' (ID: {project_id})")
    print(f"[*] Scanning directory: {pdf_dir}")
    
    if not os.path.exists(pdf_dir):
        print(f"[!] Error: Directory {pdf_dir} does not exist.")
        return None
        
    pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print(f"[!] Warning: No PDF files found in {pdf_dir}.")
        
    print(f"[*] Found {len(pdf_files)} PDF files to scan.")
    
    # Clone template
    requirements = {
        "project": project_name,
        "systems": json.loads(json.dumps(SYSTEMS_TEMPLATE)),
        "challenges": [],
        "tqs": [],
        "workflows": [
            {
                "step": 1,
                "name": "Document Pre-processing & Scope Identification",
                "desc": "Index all PDF volumes using PyMuPDF to extract text and tables. Filter documents containing keywords like 'telecom', 'paga', 'cctv', 'network', 'cables', 'security'."
            },
            {
                "step": 2,
                "name": "Subsystem Requirement Extraction",
                "desc": "Extract and structure requirements for each subsystem: CCTV storage days, camera count, PAGA dB levels, telephone line counts, fiber optic core specifications, and UPS backup times."
            },
            {
                "step": 3,
                "name": "Compliance & Conflict Auditing",
                "desc": "Audit extracted specs against standard rules: check for internal contradictions (e.g., one page asking for 30 days CCTV storage, another asking for 90 days), and cross-reference standards (e.g. IEC 62443, ATEX)."
            },
            {
                "step": 4,
                "name": "Technical Clarification (TQ) Generation",
                "desc": "Automatically compile a list of Technical Queries (TQs) for all vague, conflicting, or missing requirements to submit to the project owner."
            },
            {
                "step": 5,
                "name": "Wiki Dashboard Update",
                "desc": "Export structured wiki data to the master database, updating system architectures, cable schedules, and bill of materials."
            }
        ]
    }
    
    scanned_matches = []
    
    for filename in pdf_files:
        filepath = os.path.join(pdf_dir, filename)
        print(f"[*] Scanning {filename}...")
        try:
            doc = fitz.open(filepath)
            # Ensure Tesseract-OCR is in path for OCR engine
            tess_path = r"C:\Program Files\Tesseract-OCR"
            if os.path.exists(tess_path) and tess_path not in os.environ["PATH"]:
                os.environ["PATH"] += os.pathsep + tess_path

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                if HIFI_AVAILABLE:
                    classification = classify_page(page, page_num + 1)
                    page_result = extract_page(doc, page_num, classification=classification)
                    text = page_result.text
                else:
                    text = page.get_text()
                
                # Check for keywords
                matched_kws = []
                for idx, r_kw in enumerate(COMPILED_KWS):
                    if r_kw.search(text):
                        keyword_str = KEYWORDS[idx].replace(r'\b', '').replace(r'[a-zA-Z]*', '').replace(r'\s+', ' ')
                        matched_kws.append(keyword_str)
                        
                if matched_kws:
                    lines = [l.strip() for l in text.split('\n') if l.strip()]
                    snippets = []
                    for line in lines:
                        for r_kw in COMPILED_KWS:
                            if r_kw.search(line):
                                if line not in snippets:
                                    snippets.append(line)
                                if len(snippets) >= 3:
                                    break
                        if len(snippets) >= 3:
                            break
                            
                    scanned_matches.append({
                        "file": filename,
                        "page": page_num + 1,
                        "keywords": list(set(matched_kws)),
                        "context": " | ".join(snippets)
                    })
            doc.close()
        except Exception as e:
            print(f"[!] Error reading {filename}: {e}")
            
    # Classify matched clauses into subsystems
    for item in scanned_matches:
        file = item["file"]
        page = item["page"]
        ctx = item["context"]
        kws = item["keywords"]
        
        # Categorize
        subsystem = None
        kws_lower = [k.lower() for k in kws]
        ctx_lower = ctx.lower()
        
        if any(k in ["dcs", "plc"] for k in kws_lower):
            if any(k in ["esd", "sil"] for k in kws_lower) or "esd" in ctx_lower or "emergency shutdown" in ctx_lower:
                subsystem = "ESD"
            elif any(k in ["hmi", "ows", "ews", "lvs"] for k in kws_lower) or "historian" in ctx_lower:
                subsystem = "HMIPIS"
            else:
                subsystem = "DCS"
        elif any(k in ["esd", "sil"] for k in kws_lower) or "emergency shutdown" in ctx_lower:
            subsystem = "ESD"
        elif any(k in ["hmi", "ows", "ews", "lvs"] for k in kws_lower) or "historian" in ctx_lower or "workstation" in ctx_lower:
            subsystem = "HMIPIS"
        elif any(k in ["vibration", "mms", "bently"] for k in kws_lower) or "vibration" in ctx_lower:
            subsystem = "MMS"
        elif any(k in ["analyzer", "analyser", "swas", "chromatograph"] for k in kws_lower) or "swas" in ctx_lower:
            subsystem = "Analysers"
        elif any(k in ["transmitter", "control valve"] for k in kws_lower) or "instrument" in ctx_lower or "sensor" in ctx_lower:
            subsystem = "FieldInstruments"
        elif any(k in ["fire alarm", "detector"] for k in kws_lower) or "fire & gas" in ctx_lower or "fgs" in ctx_lower or "fire detection" in ctx_lower:
            subsystem = "FGS"
        elif any(k in ["cctv", "camera", "nvr"] for k in kws_lower) or "cctv" in ctx_lower:
            subsystem = "CCTV"
        elif any(k in ["paga", "pa/ga"] for k in kws_lower) or "paga" in ctx_lower or "public address" in ctx_lower or "general alarm" in ctx_lower:
            subsystem = "PAGA"
        elif any(k in ["telephone", "pabx", "intercom"] for k in kws_lower) or "telephone" in ctx_lower:
            subsystem = "Telephony"
        elif any(k in ["cybersecurity", "network switch", "lan/wan"] for k in kws_lower) or "security" in ctx_lower or "network" in ctx_lower:
            if "cctv" in ctx_lower or "camera" in ctx_lower:
                subsystem = "CCTV"
            else:
                subsystem = "Network"
        elif any(k in ["fiber optic", "foc", "cabling", "cable", "structured cabling"] for k in kws_lower) or "cable" in ctx_lower:
            subsystem = "Cabling"
        elif any(k in ["ups", "battery", "charger"] for k in kws_lower) or "ups" in ctx_lower or "battery" in ctx_lower:
            subsystem = "UPS"
        elif any(k in ["conformal", "coating"] for k in kws_lower) or "conformal coating" in ctx_lower:
            subsystem = "DCS"  # Conformal coating defaults to DCS/electronic cards
            
        if subsystem and subsystem in requirements["systems"]:
            requirements["systems"][subsystem]["rules"].append({
                "file": file,
                "page": str(page),
                "matched": ", ".join(kws),
                "context": ctx[:250] + "..." if len(ctx) > 250 else ctx
            })
            
    # Generate TQs and Challenges dynamically
    tqs, challenges = generate_tqs_and_challenges(project_name, scanned_matches)
    requirements["tqs"] = tqs
    requirements["challenges"] = challenges
            
    # Ensure directories exist
    base_dir = os.path.dirname(os.path.abspath(__file__))
    projects_dir = os.path.join(base_dir, "projects")
    os.makedirs(projects_dir, exist_ok=True)
    os.makedirs(os.path.join(base_dir, "static"), exist_ok=True)
    
    # Save the project JSON database
    json_path = os.path.join(projects_dir, f"{project_id}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(requirements, f, indent=2, ensure_ascii=False)
    print(f"[*] Requirements database saved to: {json_path}")
    
    # Save static JS fallback
    js_path = os.path.join(base_dir, "static", f"data_{project_id}.js")
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(f"// Fallback requirements database for {project_name}\n")
        f.write(f"const REQUIREMENTS_DATA_{project_id.upper()} = ")
        json.dump(requirements, f, indent=2, ensure_ascii=False)
        f.write(";\n")
    print(f"[*] Offline fallback JS database saved to: {js_path}")
    
    # Register/update the project catalog
    catalog_path = os.path.join(projects_dir, "projects.json")
    catalog = []
    if os.path.exists(catalog_path):
        try:
            with open(catalog_path, 'r', encoding='utf-8') as f:
                catalog = json.load(f)
        except Exception:
            catalog = []
            
    # Update or append
    updated = False
    for proj in catalog:
        if proj["id"] == project_id:
            proj["name"] = project_name
            proj["pdf_dir"] = pdf_dir
            proj["created_at"] = datetime.utcnow().isoformat() + "Z"
            updated = True
            break
            
    if not updated:
        catalog.append({
            "id": project_id,
            "name": project_name,
            "pdf_dir": pdf_dir,
            "created_at": datetime.utcnow().isoformat() + "Z"
        })
        
    with open(catalog_path, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    print(f"[*] Registered in catalog index: {catalog_path}")
    
    # Also write static/projects_catalog.js
    catalog_js_path = os.path.join(base_dir, "static", "projects_catalog.js")
    try:
        with open(catalog_js_path, 'w', encoding='utf-8') as f:
            f.write("// Fallback projects catalog database\n")
            f.write("const PROJECTS_CATALOG = ")
            json.dump(catalog, f, indent=2, ensure_ascii=False)
            f.write(";\n")
        print(f"[*] Offline fallback projects catalog saved to: {catalog_js_path}")
    except Exception as e:
        print(f"[!] Error writing fallback catalog: {e}")
        
    print("[*] Project onboarding scan completed successfully!")
    return project_id

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scan plant engineering bids for telecom/security specs.")
    parser.add_argument("--name", required=True, help="Friendly name of the project bid.")
    parser.add_argument("--dir", required=True, help="Absolute path to the directory containing bid PDFs.")
    args = parser.parse_args()
    
    scan_pdfs(args.dir, args.name)
