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
    print(
        "Querying Minneapolis Open Data REST API and applying 12-month filter..."
    )

    # Calculate cutoff date: exactly 12 months ago from today
    now = datetime.now(timezone.utc)
    try:
        cutoff_date = now.replace(year=now.year - 1)
    except ValueError:
        # Handle leap year edge case (Feb 29)
        cutoff_date = now.replace(year=now.year - 1, day=28)

    print(f"Filtering out permits issued before: {cutoff_date.strftime('%Y-%m-%d')}")

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

            skipped_old = 0
            skipped_nodate = 0

            for item in features:
                attrs = item.get("attributes", {})

                raw_issue = attrs.get("issueDate") or attrs.get("issuedDate")
                issue_str = format_arcgis_date(raw_issue)

                if not issue_str:
                    skipped_nodate += 1
                    continue

                # Parse issue date and check if it's within the past 12 months
                try:
                    issue_dt = datetime.strptime(
                        issue_str, "%Y-%m-%d"
                    ).replace(tzinfo=timezone.utc)
                    if issue_dt < cutoff_date:
                        skipped_old += 1
                        continue
                except Exception:
                    skipped_nodate += 1
                    continue

                raw_expire = attrs.get("expireDate") or attrs.get(
                    "expirationDate"
                )
                expire_str = format_arcgis_date(raw_expire) or "N/A"

                company_name = (
                    attrs.get("dbaName")
                    or attrs.get("applicantName")
                    or attrs.get("businessName")
                    or "Unknown Company"
                )
                rep_name = attrs.get("applicantName") or "N/A"

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

            print(f"Retained {len(records)} records from the past 12 months.")
            print(
                f"Filtered out {skipped_old} records older than 12 months and {skipped_nodate} records with missing dates."
            )

    except Exception as e:
        print(f"Endpoint query failed: {e}")

    return records


def main():
    records = fetch_minneapolis_live_licenses()
    output_path = os.path.join(os.path.dirname(__file__), "data.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    print(f"Successfully wrote {len(records)} filtered records to data.json.")


if __name__ == "__main__":
    main()