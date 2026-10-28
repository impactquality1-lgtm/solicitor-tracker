import io
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
import pdfplumber

# Official list of 10 monitored Twin Cities municipalities with dynamic source types.
TARGET_CITIES = [
    {
        "city": "Minneapolis",
        "type": "arcgis",
        "url": "https://services.arcgis.com/afSMGVsC7QlRK1kZ/arcgis/rest/services/CCS_Permits/FeatureServer/0/query?where=1%3D1&outFields=*&resultRecordCount=1000&outSR=4326&f=json",
    },
    {
        "city": "St. Paul",
        "type": "arcgis",
        "url": "https://services1.arcgis.com/9meaaHE3uiba0zr8/arcgis/rest/services/Encroachment_Permits/FeatureServer/0/query?where=1%3D1&outFields=*&resultRecordCount=1000&outSR=4326&f=json",
    },
    {
        "city": "Coon Rapids",
        "type": "pdf",
        "url": "https://www.coonrapidsmn.gov/1165/Current-Solicitor-Peddler-Lists",
    },
    {
        "city": "Bloomington",
        "type": "pdf",
        "url": "https://www.bloomingtonmn.gov/lic/solicitors-bloomington",
    },
    {
        "city": "Minnetonka",
        "type": "pdf",
        "url": "https://www.minnetonkamn.gov/business/licenses",
    },
    {
        "city": "Edina",
        "type": "pdf",
        "url": "https://www.edinamn.gov/560/Business-Licensing",
    },
    {
        "city": "St. Louis Park",
        "type": "pdf",
        "url": "https://www.stlouisparkmn.gov/Services/Permits",
    },
    {
        "city": "Richfield",
        "type": "pdf",
        "url": "https://www.richfieldmn.gov/services/business-licensing",
    },
    {
        "city": "Brooklyn Park",
        "type": "pdf",
        "url": "https://www.brooklynpark.org/permits-and-licenses/",
    },
    {
        "city": "Eden Prairie",
        "type": "pdf",
        "url": "https://www.edenprairie.org/city-government/city-departments/city-clerk/business-licenses",
    },
]


def format_arcgis_date(val):
    if val is None:
        return None
    try:
        if isinstance(val, (int, float)):
            if val > 1e11:
                dt = datetime.fromtimestamp(val / 1000.0, tz=timezone.utc)
            elif val > 1e9:
                dt = datetime.fromtimestamp(val, tz=timezone.utc)
            else:
                return None
            return dt.strftime("%Y-%m-%d")

        if isinstance(val, str):
            if val.isdigit():
                num = float(val)
                if num > 1e11:
                    dt = datetime.fromtimestamp(num / 1000.0, tz=timezone.utc)
                elif num > 1e9:
                    dt = datetime.fromtimestamp(num, tz=timezone.utc)
                else:
                    return None
                return dt.strftime("%Y-%m-%d")
            return val[:10]
    except Exception:
        return None
    return None


def get_attr(attrs, *keys):
    """Case-insensitive attribute lookup for ArcGIS feature layers."""
    lower_map = {k.lower(): v for k, v in attrs.items()}
    for key in keys:
        val = lower_map.get(key.lower())
        if val is not None and val != "":
            return val
    return None


def fetch_pdf_permits(target):
    """Generic PDF scraper for municipalities publishing solicitor rosters as PDFs."""
    records = []
    city_name = target["city"]
    page_url = target["url"]

    if not page_url:
        print(f"Skipping {city_name} (PDF): No URL configured.")
        return records

    print(f"Querying solicitor PDF roster for {city_name}...")
    try:
        req = urllib.request.Request(
            page_url,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
        )
        with urllib.request.urlopen(req, timeout=20) as response:
            html_content = response.read().decode("utf-8")

        pdf_links = re.findall(r'href="([^"]+\.pdf[^"]*)"', html_content, re.IGNORECASE)
        doc_center_links = re.findall(r'href="(/DocumentCenter/View/[^"]+)"', html_content)
        
        parsed_uri = urllib.parse.urlparse(page_url)
        base_domain = f"{parsed_uri.scheme}://{parsed_uri.netloc}"
        
        all_candidates = pdf_links + [f"{base_domain}{l}" if l.startswith("/") else l for l in doc_center_links]
        
        target_pdf_url = None
        for link in all_candidates:
            if any(kw in link.lower() for kw in ["solicitor", "peddler", "license", "current", "list"]):
                if link.startswith("http"):
                    target_pdf_url = link
                elif link.startswith("/"):
                    target_pdf_url = f"{base_domain}{link}"
                break

        if not target_pdf_url and all_candidates:
            target_pdf_url = all_candidates[0] if all_candidates[0].startswith("http") else None

        if not target_pdf_url:
            print(f"Could not resolve active PDF link for {city_name}.")
            return records

        print(f"Downloading PDF for {city_name} from: {target_pdf_url}")
        pdf_req = urllib.request.Request(
            target_pdf_url,
            HEADERS = {
    	"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    	"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    	"Accept-Language": "en-US,en;q=0.9",
	}
        )
        with urllib.request.urlopen(pdf_req, timeout=30) as pdf_resp:
            pdf_bytes = pdf_resp.read()

        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                table = page.extract_table()
                if not table:
                    continue

                for row_idx, row in enumerate(table[1:]):  # Skip header
                    if not row or len(row) < 2:
                        continue

                    cleaned_row = [str(cell).strip() if cell else "" for cell in row]
                    company = cleaned_row[0] if len(cleaned_row) > 0 and cleaned_row[0] else "Unknown Company"
                    rep_name = cleaned_row[1] if len(cleaned_row) > 1 and cleaned_row[1] else "N/A"
                    expire_date = cleaned_row[2] if len(cleaned_row) > 2 and re.match(r'\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}', cleaned_row[2]) else "2027-01-01"

                    record = {
                        "id": f"{city_name[:3].upper()}-{page_idx}-{row_idx}-{hash(company) % 10000}",
                        "city": city_name,
                        "company": company,
                        "representative": rep_name,
                        "solicitor": rep_name,
                        "rep": rep_name,
                        "issueDate": "2026-01-01",
                        "expireDate": expire_date,
                        "expirationDate": expire_date,
                        "expires": expire_date,
                        "matchedKeyword": "solicitor-pdf",
                        "status": "ACTIVE",
                    }
                    records.append(record)

        print(f"Extracted {len(records)} valid records for {city_name} from PDF.")
    except Exception as e:
        print(f"Failed to process PDF for {city_name}: {e}")

    return records


def fetch_all_city_permits():
    records = []
    seen_permit_ids = set()
    now = datetime.now(timezone.utc)
    cutoff_date = now - timedelta(days=365)

    for target in TARGET_CITIES:
        city_name = target["city"]
        source_type = target.get("type", "arcgis")
        url = target.get("url")

        if not url:
            print(f"Skipping {city_name}: No endpoint configured.")
            continue

        if source_type == "pdf":
            pdf_recs = fetch_pdf_permits(target)
            for rec in pdf_recs:
                if rec["id"] not in seen_permit_ids:
                    seen_permit_ids.add(rec["id"])
                    records.append(rec)
        else:
            print(f"Querying active live permits for {city_name} (ArcGIS)...")
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"},
                )
                with urllib.request.urlopen(req, timeout=20) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                    features = payload.get("features", [])
                    print(f"Fetched {len(features)} raw features for {city_name}.")

                    city_retained = 0
                    for item in features:
                        attrs = item.get("attributes", {})

                        permit_id = str(
                            get_attr(attrs, "permitNumber", "permit_number", "folder_rsn", "objectid")
                            or f"{city_name}-PERMIT"
                        )
                        if permit_id in seen_permit_ids:
                            continue
                        seen_permit_ids.add(permit_id)

                        raw_issue = get_attr(attrs, "issueDate", "issuedate", "issue_date", "permit_date")
                        issue_str = format_arcgis_date(raw_issue)
                        if not issue_str:
                            continue

                        try:
                            issue_dt = datetime.strptime(issue_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                            if issue_dt < cutoff_date:
                                continue
                        except Exception:
                            continue

                        raw_expire = get_attr(attrs, "expirationDate", "expirationdate", "expiredate", "expire_date")
                        expire_str = format_arcgis_date(raw_expire) or "2027-01-01"

                        try:
                            expire_dt = datetime.strptime(expire_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                            status = "ACTIVE" if expire_dt >= now else "EXPIRED"
                        except Exception:
                            status = "ACTIVE"

                        company_name = str(
                            get_attr(attrs, "contractorName", "contractor_name", "applicantName", "applicant_name", "dbaname", "company_name")
                            or "Unknown Contractor"
                        )
                        rep_name = str(get_attr(attrs, "applicantName", "applicant_name", "representative", "contractorName") or "N/A")

                        record = {
                            "id": permit_id,
                            "city": city_name,
                            "company": company_name,
                            "representative": rep_name,
                            "solicitor": rep_name,
                            "rep": rep_name,
                            "issueDate": issue_str,
                            "expireDate": expire_str,
                            "expirationDate": expire_str,
                            "expires": expire_str,
                            "matchedKeyword": str(get_attr(attrs, "permitType", "permit_type", "folder_type") or "construction"),
                            "status": status,
                        }
                        records.append(record)
                        city_retained += 1

                    print(f"Retained {city_retained} valid records for {city_name}.")
            except Exception as e:
                print(f"Failed to query endpoint for {city_name}: {e}")

    return records


def main():
    records = fetch_all_city_permits()

    output_data = {
        "monitoredCitiesCount": len(TARGET_CITIES),
        "records": records,
    }

    output_path = os.path.join(os.path.dirname(__file__), "data.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print(
        f"\nSuccessfully wrote {len(records)} total records and {len(TARGET_CITIES)} monitored cities to data.json."
    )


if __name__ == "__main__":
    main()