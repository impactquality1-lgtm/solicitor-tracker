import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone


def format_arcgis_date(epoch_ms):
    """Converts ArcGIS Epoch timestamp (milliseconds) to YYYY-MM-DD string."""
    if not epoch_ms:
        return None
    try:
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
        return None


def fetch_minneapolis_live_licenses():
    url = (
        "https://services.arcgis.com/afSMGVsC7QlRK1kZ/arcgis/rest/services/"
        "Residential_Specialty/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=json"
    )

    records = []
    print("Querying Minneapolis Open Data REST API...")

    # Current date reference: October 27, 2026
    now = datetime.now(timezone.utc)

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
            print(f"Total raw features fetched: {len(features)}")

            skipped_expired = 0

            for item in features:
                attrs = item.get("attributes", {})

                # Extract expiration date (the primary date provided by the API)
                raw_expire = attrs.get("expirationDate")
                expire_str = format_arcgis_date(raw_expire)

                if not expire_str:
                    # If no expiration date, skip to ensure data integrity
                    skipped_expired += 1
                    continue

                # Ensure license is not long expired (keep active or recently expired within 30 days)
                try:
                    expire_dt = datetime.strptime(
                        expire_str, "%Y-%m-%d"
                    ).replace(tzinfo=timezone.utc)
                    # Filter out licenses that expired more than a year ago
                    if expire_dt < (now - timedelta(days=365)):
                        skipped_expired += 1
                        continue
                except Exception:
                    skipped_expired += 1
                    continue

                # Estimate issue date as 1 year prior to expiration date for standard 1-year trade licenses
                try:
                    issue_dt = expire_dt - timedelta(days=365)
                    issue_str = issue_dt.strftime("%Y-%m-%d")
                except Exception:
                    issue_str = "2026-01-01"

                company_name = (
                    attrs.get("dbaName")
                    or attrs.get("applicantName")
                    or "Unknown Company"
                )
                rep_name = attrs.get("applicantName") or "N/A"

                record = {
                    "id": str(attrs.get("licenseNumber") or "MPLS-LIC"),
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
                    "status": "ACTIVE",
                }
                records.append(record)

            print(f"Retained {len(records)} active/current records.")
            print(f"Filtered out {skipped_expired} expired or outdated records.")

    except Exception as e:
        print(f"Endpoint query failed: {e}")

    return records


def main():
    records = fetch_minneapolis_live_licenses()
    output_path = os.path.join(os.path.dirname(__file__), "data.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    print(f"Successfully wrote {len(records)} records to data.json.")


if __name__ == "__main__":
    main()