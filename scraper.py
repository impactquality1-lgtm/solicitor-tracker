import requests
from bs4 import BeautifulSoup
import json
import os
import re
import io
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

TARGET_KEYWORDS = ["roofing", "siding", "window", "exterior", "contractor", "restoration", "gutter", "remodeling"]

# --- SCENARIO 1: Static HTML Scraping (Suburbs like Monticello, Cottage Grove) ---
def scrape_static_html_sources():
    records = []
    sources = [
        {
            "city": "Monticello",
            "url": "https://www.monticellomn.gov/659/Active-Peddler-Permits-Solicitor-Registr",
            "id_prefix": "MON"
        }
    ]
    
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
    
    for src in sources:
        try:
            resp = requests.get(src["url"], headers=headers, timeout=15)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                items = soup.find_all(['li', 'tr', 'p'])
                for idx, item in enumerate(items):
                    text = item.get_text().strip()
                    text_lower = text.lower()
                    matched_kw = next((kw for kw in TARGET_KEYWORDS if kw in text_lower), None)
                    if matched_kw and 5 < len(text) < 120:
                        records.append({
                            "id": f"{src['id_prefix']}-2026-{idx+100}",
                            "city": src["city"],
                            "company": text,
                            "solicitor": "Registered Applicant",
                            "matchedKeyword": matched_kw,
                            "status": "ACTIVE"
                        })
        except Exception as e:
            print(f"Error scraping static source {src['city']}: {e}")
            
    return records

# --- SCENARIO 2: PDF Roster Parsing (Suburbs publishing monthly PDFs) ---
def scrape_pdf_sources():
    records = []
    if not pdfplumber:
        print("pdfplumber not installed; skipping PDF sources.")
        return records

    pdf_sources = [
        {
            "city": "Eagan",
            "url": "https://www.cityofeagan.com/images/Police/Solicitor_Peddler_Licenses.pdf",
            "id_prefix": "EAG"
        }
    ]

    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}

    for src in pdf_sources:
        try:
            resp = requests.get(src["url"], headers=headers, timeout=20)
            if resp.status_code == 200:
                with pdfplumber.open(io.BytesIO(resp.content)) as pdf:
                    for page_idx, page in enumerate(pdf.pages):
                        text = page.extract_text()
                        if not text:
                            continue
                        for line_idx, line in enumerate(text.split('\n')):
                            line_lower = line.lower()
                            matched_kw = next((kw for kw in TARGET_KEYWORDS if kw in line_lower), None)
                            if matched_kw and len(line.strip()) > 5:
                                records.append({
                                    "id": f"{src['id_prefix']}-PDF-{page_idx+1}-{line_idx+1}",
                                    "city": src["city"],
                                    "company": line.strip(),
                                    "solicitor": "PDF Record",
                                    "matchedKeyword": matched_kw,
                                    "status": "ACTIVE"
                                })
        except Exception as e:
            print(f"Error parsing PDF for {src['city']}: {e}")

    return records

# --- SCENARIO 3: Open Data / API Fallback (Minneapolis & St. Paul) ---
def scrape_open_data_apis():
    records = []
    # Minneapolis Business Licensing Open Data API endpoint
    mpls_api = "https://services2.arcgis.com/POS2e333333/arcgis/rest/services/Business_Licenses/FeatureServer/0/query?where=1%3D1&outFields=*&f=json"
    
    try:
        resp = requests.get(mpls_api, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            features = data.get("features", [])
            for idx, feat in enumerate(features):
                attrs = feat.get("attributes", {})
                comp_name = attrs.get("BusinessName") or attrs.get("ApplicantName") or ""
                lic_type = attrs.get("LicenseType") or ""
                combined = f"{comp_name} {lic_type}".lower()
                matched_kw = next((kw for kw in TARGET_KEYWORDS if kw in combined), None)
                if matched_kw and comp_name:
                    records.append({
                        "id": f"MPLS-API-{idx+1000}",
                        "city": "Minneapolis",
                        "company": comp_name,
                        "solicitor": lic_type or "Solicitor/Peddler",
                        "matchedKeyword": matched_kw,
                        "status": "ACTIVE"
                    })
    except Exception as e:
        print(f"Open Data API fetch skipped or updated: {e}")

    return records

def main():
    print("Executing Hybrid Municipal Solicitor Scraper Engine...")
    all_records = []
    
    # Run all 3 scenario handlers
    all_records.extend(scrape_static_html_sources())
    all_records.extend(scrape_pdf_sources())
    all_records.extend(scrape_open_data_apis())

    print(f"Extraction finished. Total valid records found: {len(all_records)}")

    output_path = os.path.join(os.path.dirname(__file__), 'data.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_records, f, indent=2)

    print(f"Successfully wrote {len(all_records)} records to data.json")

if __name__ == "__main__":
    main()
