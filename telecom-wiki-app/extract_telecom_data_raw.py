import os
import re
import csv
import json
import fitz  # PyMuPDF

# Define the PDF directory
pdf_dir = 'g:/My Drive/Project/ITB Project'

# Define output paths
output_csv = 'C:/Users/jezeh/.gemini/antigravity/brain/f214b7b2-f735-4f5a-84a2-666e18ac890f/telecom_extracted_requirements_raw.csv'
output_json = 'C:/Users/jezeh/.gemini/antigravity/brain/f214b7b2-f735-4f5a-84a2-666e18ac890f/telecom_extracted_requirements_raw.json'

# Keywords for telecom systems
KEYWORDS = [
    r"\bcctv\b", r"\bcamera[s]?\b", r"\bnvr\b", r"\bvms\b", r"\bsurveillance\b",
    r"\bpaga\b", r"\bpa/ga\b", r"\bpublic\s+address\b", r"\bgeneral\s+alarm\b", r"\bloudspeaker[s]?\b", r"\bacoustic\s+hood\b",
    r"\btelephone[s]?\b", r"\btelephony\b", r"\bintercom\b", r"\bpabx\b", r"\bhandset[s]?\b", r"\bhooter\b", r"\bflasher\b",
    r"\bfiber\s+optic[s]?\b", r"\bfoc\b", r"\boptical\s+fiber\b", r"\bstructured\s+cabling\b",
    r"\bcybersecurity\b", r"\bfirewall[s]?\b", r"\bnetwork\s+switch[es]?\b", r"\blan/wan\b", r"\bdmz\b", r"\biec\s+62443\b",
    r"\baccess\s+control\b", r"\bacs\b", r"\bcard\s+reader[s]?\b",
    r"\btelecom\b", r"\btelecommunication[s]?\b"
]
COMPILED_KWS = [re.compile(kw, re.IGNORECASE) for kw in KEYWORDS]

# Helper to check if text matches any telecom keyword
def is_telecom_match(text):
    for pat in COMPILED_KWS:
        if pat.search(text):
            return True
    return False

# Main script
def extract_data():
    files = sorted([f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')])
    print(f"Scanning {len(files)} PDF files...")
    
    extracted_records = []
    record_counter = 1
    
    # Regexes for document numbers and clauses
    doc_no_pat = re.compile(r'B773-[A-Z0-9-]+', re.IGNORECASE)
    spec_no_pat = re.compile(r'[67]-5[12]-\d{4}')
    clause_pat = re.compile(r'^\s*(?:\d+\.)+\d+\b|^\s*\d+\.0\b')
    
    for filename in files:
        filepath = os.path.join(pdf_dir, filename)
        print(f"Processing {filename}...")
        try:
            doc = fitz.open(filepath)
            
            # Document level states
            doc_level_doc_no = ""
            doc_level_spec_no = ""
            doc_level_spec_title = ""
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                blocks = page.get_text("blocks")
                
                # Sort blocks by y coordinate, then x coordinate to read top-to-bottom
                blocks = sorted(blocks, key=lambda b: (round(b[1], 1), round(b[0], 1)))
                
                # Check if this page updates document level state
                # Cover page checks:
                page_text = "\n".join([b[4] for b in blocks])
                
                # Search for spec numbers on page
                spec_matches = spec_no_pat.findall(page_text)
                if spec_matches:
                    doc_level_spec_no = spec_matches[0]
                    
                doc_matches = doc_no_pat.findall(page_text)
                if doc_matches:
                    doc_level_doc_no = doc_matches[0]
                    
                # If page contains standard specification header, update title
                if "STANDARD SPECIFICATION FOR" in page_text or "SPECIFICATION FOR" in page_text:
                    lines = [l.strip() for l in page_text.split('\n') if l.strip()]
                    title_parts = []
                    for line in lines[:15]:
                        if "SPECIFICATION FOR" in line.upper() or "STANDARD SPECIFICATION" in line.upper():
                            clean_line = line.replace("STANDARD SPECIFICATION FOR", "").replace("SPECIFICATION FOR", "").strip()
                            if clean_line:
                                title_parts.append(clean_line)
                    if title_parts:
                        doc_level_spec_title = " ".join(title_parts)
                
                # If page is not relevant, skip extraction
                if not is_telecom_match(page_text):
                    continue
                    
                # Track page-level section and clause
                page_section = ""
                last_clause_num = ""
                
                # Parse blocks
                for idx, block in enumerate(blocks):
                    text = block[4].strip()
                    if not text:
                        continue
                        
                    # Ignore header/footer standard blocks to avoid noise
                    if "Format No." in text or "Copyright EIL" in text:
                        continue
                    if "Page" in text and "of" in text and ("B773" in text or "6-5" in text):
                        footer_doc_match = doc_no_pat.search(text)
                        if footer_doc_match:
                            doc_level_doc_no = footer_doc_match.group(0)
                        continue
                        
                    # Check if the block is a section header (like 1.0 GENERAL or 2.0 DESIGN)
                    m_clause = clause_pat.match(text)
                    if m_clause:
                        parts = text.split('\n', 1)
                        clause_num = m_clause.group(0).strip()
                        clause_desc = parts[0].strip()
                        
                        # Is it a major section header? e.g. 1.0 or 2.0
                        if clause_num.endswith('.0'):
                            page_section = text.replace('\n', ' ').strip()
                        else:
                            last_clause_num = clause_num
                        
                        # If the block itself contains the description, we can continue to process it as a telecom match
                        # (since some blocks have both clause number and text)
                        if not is_telecom_match(text):
                            continue
                            
                    # Check if the current block matches telecom keywords
                    if is_telecom_match(text):
                        # Find the clause number for this block
                        clause_to_use = last_clause_num
                        
                        m_clause = clause_pat.match(text)
                        if m_clause:
                            clause_to_use = m_clause.group(0).strip()
                            desc_text = text[m_clause.end():].strip()
                        else:
                            # Check if the immediately preceding block was just a clause number
                            if idx > 0:
                                prev_block_text = blocks[idx-1][4].strip()
                                if clause_pat.match(prev_block_text) and len(prev_block_text.split('\n')) == 1:
                                    clause_to_use = prev_block_text
                            desc_text = text
                            
                        # Clean up formatting of the description text
                        desc_text = desc_text.replace('\n', ' ').replace('\t', ' ').strip()
                        desc_text = re.sub(r'\s+', ' ', desc_text)
                        
                        # Skip if too short (noise)
                        if len(desc_text) < 15:
                            continue
                            
                        # Determine ITB Document Number to output
                        itb_doc_no = doc_level_doc_no
                        if doc_level_spec_no:
                            if itb_doc_no:
                                itb_doc_no = f"{itb_doc_no} ({doc_level_spec_no})"
                            else:
                                itb_doc_no = doc_level_spec_no
                                
                        # Page number info
                        # Search for printed page number on the page (e.g. Page 4 of 20)
                        printed_page = ""
                        page_match = re.search(r'Page\s+(\d+)\s+of\s+(\d+)', page_text)
                        if page_match:
                            printed_page = f"Page {page_match.group(1)} of {page_match.group(2)}"
                        else:
                            printed_page = f"Page {page_num + 1}"
                            
                        # Determine section/clause reference
                        clause_ref = ""
                        if page_section:
                            clause_ref = page_section
                        if clause_to_use:
                            if clause_ref:
                                clause_ref = f"{clause_ref} / Clause {clause_to_use}"
                            else:
                                clause_ref = f"Clause {clause_to_use}"
                        if not clause_ref:
                            clause_ref = "General"
                            
                        extracted_records.append({
                            "Item": record_counter,
                            "Filename": filename,
                            "ITB Document number": itb_doc_no if itb_doc_no else "TBD",
                            "clause or section": clause_ref,
                            "page number": f"PDF Pg {page_num + 1} ({printed_page})" if printed_page else f"PDF Pg {page_num + 1}",
                            "the exact description verbatim": desc_text
                        })
                        record_counter += 1
                        
            doc.close()
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            
    print(f"Total records extracted: {len(extracted_records)}")
    
    # Save to CSV
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Item", "Filename", "ITB Document number", "clause or section", "page number", "the exact description verbatim"])
        for rec in extracted_records:
            writer.writerow([
                rec["Item"],
                rec["Filename"],
                rec["ITB Document number"],
                rec["clause or section"],
                rec["page number"],
                rec["the exact description verbatim"]
            ])
            
    # Save to JSON
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(extracted_records, f, indent=2, ensure_ascii=False)
        
    print(f"Saved outputs to:\n - CSV: {output_csv}\n - JSON: {output_json}")

if __name__ == '__main__':
    extract_data()
