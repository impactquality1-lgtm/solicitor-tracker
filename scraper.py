import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone


def format_arcgis_date(val):
    """Robustly converts ArcGIS date fields (epoch ms, epoch sec, or string) to YYYY-MM-DD."""
    if val is None:
        return None
    try:
        if isinstance(val, (int, float)):
            if val > 1e11:  # Milliseconds
                dt = datetime.fromtimestamp(val / 1000.0, tz=timezone.utc)
            elif val > 1e9:  # Seconds
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


def fetch_minneapolis_live_permits():
    url = (
        "https://services.arcgis.com/afSMGVsC7QlRK1kZ/arcgis/rest/services/"
        "CCS_Permits/FeatureServer/0/query?where=1%3D1&outFields=*&resultRecordCount=1000&outSR=4326&f=json"
    )

    records = []
    seen_permit_ids = set()  # Track unique IDs to eliminate duplicate rows
    print("Querying active Minneapolis CCS_Permits REST API...")

    now = datetime.now(timezone.utc)
    cutoff_date = now - timedelta(days=365)  # Strict rolling 12-month window

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
            },
        )
        with urllib.request.urlopen(req, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
            features = payload.get("features", [])
            print(f"Total raw permits fetched from CCS_Permits: {len(features)}")

            skipped_old = 0
            skipped_nodate = 0
            skipped_duplicate = 0

            for item in features:
                attrs = item.get("attributes", {})

                # Unique ID check for deduplication
                permit_id = str(
                    attrs.get("permitNumber")
                    or attrs.get("OBJECTID")
                    or "MPLS-PERMIT"
                )
                if permit_id in seen_permit_ids:
                    skipped_duplicate += 1
                    continue
                seen_permit_ids.add(permit_id)

                # Extract issue date
                raw_issue = (
                    attrs.get("issueDate")
                    or attrs.get("IssuedDate")
                    or attrs.get("ISSUE_DATE")
                    or attrs.get("issued_date")
                )
                issue_str = format_arcgis_date(raw_issue)

                if not issue_str:
                    skipped_nodate += 1
                    continue

                # Enforce rolling 12-month filter
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

                raw_expire = attrs.get("expirationDate") or attrs.get("expireDate")
                expire_str = format_arcgis_date(raw_expire) or "2027-01-01"

                # Dynamically calculate status based on expiration date vs today
                try:
                    expire_dt = datetime.strptime(
                        expire_str, "%Y-%m-%d"
                    ).replace(tzinfo=timezone.utc)
                    status = "ACTIVE" if expire_dt >= now else "EXPIRED"
                except Exception:
                    status = "ACTIVE"

                company_name = (
                    attrs.get("contractorName")
                    or attrs.get("applicantName")
                    or attrs.get("dbaName")
                    or "Unknown Contractor"
                )
                rep_name = attrs.get("applicantName") or "N/A"

                record = {
                    "id": permit_id,
                    "city": attrs.get("city") or "Minneapolis",
                    "company": company_name,
                    "representative": rep_name,
                    "solicitor": rep_name,
                    "rep": rep_name,
                    "issueDate": issue_str,
                    "expireDate": expire_str,
                    "expirationDate": expire_str,
                    "expires": expire_str,
                    "matchedKeyword": str(attrs.get("permitType") or "construction"),
                    "status": status,
                }
                records.append(record)

            print(f"Retained {len(records)} unique active permits.")
            print(
                f"Filtered out: {skipped_old} older than 12 months, {skipped_duplicate} duplicates, {skipped_nodate} missing dates."
            )

    except Exception as e:
        print(f"Endpoint query failed: {e}")

    return records


def main():
    records = fetch_all_city_permits()

    output_data = {
        # Dynamically derived from the length of TARGET_CITIES array
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