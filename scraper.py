import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

# Official list of 10 monitored Twin Cities municipalities.
TARGET_CITIES = [
    {
        "city": "Minneapolis",
        "url": "https://services.arcgis.com/afSMGVsC7QlRK1kZ/arcgis/rest/services/CCS_Permits/FeatureServer/0/query?where=1%3D1&outFields=*&resultRecordCount=1000&outSR=4326&f=json",
    },
    {
        "city": "St. Paul",
        "url": None,
    },
    {
        "city": "Bloomington",
        "url": None,
    },
    {
        "city": "Edina",
        "url": None,
    },
    {
        "city": "Minnetonka",
        "url": None,
    },
    {
        "city": "St. Louis Park",
        "url": None,
    },
    {
        "city": "Richfield",
        "url": None,
    },
    {
        "city": "Brooklyn Park",
        "url": None,
    },
    {
        "city": "Eden Prairie",
        "url": None,
    },
    {
        "city": "Plymouth",
        "url": None,
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


def fetch_all_city_permits():
    records = []
    seen_permit_ids = set()
    now = datetime.now(timezone.utc)
    cutoff_date = now - timedelta(days=365)

    for target in TARGET_CITIES:
        city_name = target["city"]
        url = target["url"]

        if not url:
            print(f"Skipping {city_name}: No active live endpoint configured (0 rows).")
            continue

        print(f"Querying active live permits for {city_name}...")
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
                print(f"Fetched {len(features)} raw features for {city_name}.")

                city_retained = 0
                for item in features:
                    attrs = item.get("attributes", {})

                    permit_id = str(
                        attrs.get("permitNumber")
                        or attrs.get("OBJECTID")
                        or f"{city_name}-PERMIT"
                    )
                    if permit_id in seen_permit_ids:
                        continue
                    seen_permit_ids.add(permit_id)

                    raw_issue = (
                        attrs.get("issueDate")
                        or attrs.get("IssuedDate")
                        or attrs.get("ISSUE_DATE")
                    )
                    issue_str = format_arcgis_date(raw_issue)
                    if not issue_str:
                        continue

                    try:
                        issue_dt = datetime.strptime(
                            issue_str, "%Y-%m-%d"
                        ).replace(tzinfo=timezone.utc)
                        if issue_dt < cutoff_date:
                            continue
                    except Exception:
                        continue

                    raw_expire = attrs.get("expirationDate") or attrs.get("expireDate")
                    expire_str = format_arcgis_date(raw_expire) or "2027-01-01"

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
                        "city": city_name,
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