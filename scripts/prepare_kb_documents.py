import os
import sys
import zipfile
import csv
import xml.etree.ElementTree as ET

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DOCS_DIR = os.path.join(BASE_DIR, "docs")
KB_DOCS_DIR = os.path.join(BASE_DIR, "knowledge_base_docs")
os.makedirs(KB_DOCS_DIR, exist_ok=True)

def extract_docx_text(docx_path: str) -> str:
    """Extract clean text from a .docx file without third-party dependencies."""
    if not os.path.exists(docx_path):
        return ""
    try:
        with zipfile.ZipFile(docx_path, 'r') as z:
            xml_content = z.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            # Find all paragraph tags
            paragraphs = []
            for p in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
                texts = [node.text for node in p.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if node.text]
                if texts:
                    paragraphs.append(''.join(texts))
            return '\n\n'.join(paragraphs)
    except Exception as e:
        print(f"Error reading docx {docx_path}: {e}")
        return ""

print("=== 1. Extracting Global_Context_DATA_DICTIONARY.md.docx ===")
dict_path = os.path.join(DATA_DIR, "Global_Context_DATA_DICTIONARY.md.docx")
dict_text = extract_docx_text(dict_path)
if dict_text:
    out_file = os.path.join(KB_DOCS_DIR, "indiamart_data_dictionary.md")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("# IndiaMART Global Context & Data Dictionary\n\n")
        f.write(dict_text)
    print(f"[OK] Wrote {out_file} ({len(dict_text)} chars)")

print("=== 2. Extracting Sarvam Prompt - Buyer Side VANI.docx ===")
prompt_path = os.path.join(DATA_DIR, "Sarvam Prompt - Buyer Side VANI.docx")
prompt_text = extract_docx_text(prompt_path)
if prompt_text:
    out_file = os.path.join(KB_DOCS_DIR, "indiamart_buyer_side_prompt_spec.md")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("# IndiaMART Buyer-Side VANI Voice Bot Specification\n\n")
        f.write(prompt_text)
    print(f"[OK] Wrote {out_file} ({len(prompt_text)} chars)")

print("=== 3. Copying Comprehensive Empirical Dataset Analysis ===")
comp_path = os.path.join(DOCS_DIR, "comprehensive_dataset_analysis.md")
if os.path.exists(comp_path):
    with open(comp_path, "r", encoding="utf-8") as f:
        content = f.read()
    out_file = os.path.join(KB_DOCS_DIR, "indiamart_12k_calls_empirical_analysis.md")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[OK] Wrote {out_file} ({len(content)} chars)")

print("=== 4. Copying Call Quality Definitions ===")
cq_path = os.path.join(DOCS_DIR, "call_quality.md")
if os.path.exists(cq_path):
    with open(cq_path, "r", encoding="utf-8") as f:
        content = f.read()
    out_file = os.path.join(KB_DOCS_DIR, "indiamart_call_quality_metrics.md")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[OK] Wrote {out_file} ({len(content)} chars)")

print("=== 5. Extracting Sample Call Logs & Dispositions ===")
call_logs_path = os.path.join(DATA_DIR, "Call_Logs_Hackathon.csv")
if os.path.exists(call_logs_path):
    disposition_counts = {}
    with open(call_logs_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            d = row.get("call_disposition_reason") or "Unknown"
            disposition_counts[d] = disposition_counts.get(d, 0) + 1
    
    out_file = os.path.join(KB_DOCS_DIR, "indiamart_historical_call_dispositions.md")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("# IndiaMART Historical Call Log Dispositions & Outcomes\n\n")
        f.write("## Overview\nAnalysis of disposition distributions from historical VANI bot call attempts:\n\n")
        f.write("| Disposition Reason | Count |\n|---|---|\n")
        for k, v in sorted(disposition_counts.items(), key=lambda x: x[1], reverse=True)[:25]:
            f.write(f"| {k} | {v:,} |\n")
        f.write("\n## Key Protocol:\n")
        f.write("Calls tagged with 'do_not_call' or 'frustrated_dnc' must instantly trigger `end_interaction` with an apology without further sales attempts.\n")
    print(f"[OK] Wrote {out_file}")

print("\nPreparation complete! Ready for Knowledge Base upload.")
