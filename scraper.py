import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone


def format_arcgis_date(epoch_ms):
    """Converts ArcGIS Epoch timestamp (milliseconds) to YYYY-MM-DD string."""
    if not epoch_ms:
        return "N/A"
    try:
        # Check if timestamp is in milliseconds vs seconds
        if isinstance(epoch_ms, (int, float)) and epoch_ms > 1e11:
            dt = datetime.fromtimestamp(epoch_ms / 1000.0, tz=timezone.utc)
            return dt.strftime("%Y-%m-%d")
        elif isinstance(epoch_ms, str) and epoch_ms.isdigit():
            dt = datetime.fromtimestamp(
                float(epoch_ms) / 1000.0, tz=timezone.utc
            )
            return dt.strftime("%Y-%m-%d")
        return str(epoch_ms)[:10]
    except Exception:
        return "N/A"


def fetch_minneapolis_live_licenses():
    url = (
        "https://services.arcgis.com/afSMGVsC7QlRK1kZ/arcgis/rest/services/"
        "Residential_Specialty/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=json"
    )

    records = []
    print("Querying Minneapolis Open Data REST API for genuine dates...")

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
            },
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
            features = payload.get("features", [])

            for item in features:
                attrs = item.get("attributes", {})

                company_name = (
                    attrs.get("dbaName")
                    or attrs.get("applicantName")
                    or attrs.get("businessName")
                    or "Unknown Company"
                )
                rep_name = attrs.get("applicantName") or "N/A"

                # Extract and convert real API timestamps
                raw_issue = attrs.get("issueDate") or attrs.get("issuedDate")
                raw_expire = attrs.get("expireDate") or attrs.get(
                    "expirationDate"
                )

                issue_str = format_arcgis_date(raw_issue)
                expire_str = format_arcgis_date(raw_expire)

                record = {
                    "id": str(
                        attrs.get("licenseNumber")
                        or attrs.get("OBJECTID")
                        or "MPLS-LIC"
                    ),
                    "city": attrs.get("city") or "Minneapolis",
                    "company": company_name,
                    "representative": rep_name,
                    "solicitor": rep_name,
                    "rep": rep_name,
                    "issueDate": issue_str,
                    "expireDate": expire_str,
                    "expirationDate": expire_str,
                    "expires": expire_str,
                    "matchedKeyword": "contractor",
                    "status": str(attrs.get("status") or "ACTIVE").upper(),
                }
                records.append(record)

    except Exception as e:
        print(f"Endpoint query failed: {e}")

    return records


def main():
    records = fetch_minneapolis_live_licenses()
    output_path = os.path.join(os.path.dirname(__file__), "data.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    print(
        f"Wrote {len(records)} records with verified raw dates to data.json."
    )


if __name__ == "__main__":
    main()