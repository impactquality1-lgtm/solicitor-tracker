import requests
from bs4 import BeautifulSoup
import json
import os

TARGET_KEYWORDS = ["roofing", "siding", "window", "exterior", "contractor", "restoration", "gutter", "remodeling"]

def scrape_minneapolis():
    url = "https://www.minneapolismn.gov/business-services/licenses-permits-inspections/business-licenses/door-secondhand/peddler-solicitor/solicitor/"
    records = []
    try:
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            rows = soup.find_all(['tr', 'li', 'p'])
            for idx, row in enumerate(rows):
                text = row.get_text().strip()
                text_lower = text.lower()
                matched_kw = next((kw for kw in TARGET_KEYWORDS if kw in text_lower), None)
                if matched_kw and 5 < len(text) < 120:
                    records.append({
                        "id": f"MPLS-{idx+100}",
                        "city": "Minneapolis (Solicitors)",
                        "company": text,
                        "solicitor": "Listed Applicant",
                        "matchedKeyword": matched_kw,
                        "status": "ACTIVE"
                    })
    except Exception as e:
        print(f"Error scraping Minneapolis: {e}")
    return records

def scrape_stpaul():
    url = "https://www.stpaul.gov/departments/safety-inspections/open-operate-expand-business/business-licenses-and-permits/peddler-license"
    records = []
    try:
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            rows = soup.find_all(['tr', 'li', 'div'])
            for idx, row in enumerate(rows):
                text = row.get_text().strip()
                text_lower = text.lower()
                matched_kw = next((kw for kw in TARGET_KEYWORDS if kw in text_lower), None)
                if matched_kw and 5 < len(text) < 120:
                    records.append({
                        "id": f"STP-{idx+100}",
                        "city": "Saint Paul (Solicitors)",
                        "company": text,
                        "solicitor": "Listed Applicant",
                        "matchedKeyword": matched_kw,
                        "status": "ACTIVE"
                    })
    except Exception as e:
        print(f"Error scraping Saint Paul: {e}")
    return records

def main():
    print("Executing municipal solicitor scraper...")
    records = []
    records.extend(scrape_minneapolis())
    records.extend(scrape_stpaul())

    output_path = os.path.join(os.path.dirname(__file__), 'data.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2)

    print(f"Scraper complete. Wrote {len(records)} records to data.json")

if __name__ == "__main__":
    main()
