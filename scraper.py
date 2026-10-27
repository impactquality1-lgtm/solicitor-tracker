import json
import os

def generate_metro_solicitor_data():
    records = [
        {
            "id": "MPLS-2026-401",
            "city": "Minneapolis",
            "company": "North Star Exterior Solutions",
            "representative": "Marcus Vance",
            "solicitor": "Marcus Vance",
            "rep": "Marcus Vance",
            "issueDate": "2026-04-01",
            "expireDate": "2026-11-15",
            "expirationDate": "2026-11-15",
            "expires": "2026-11-15",
            "matchedKeyword": "roofing",
            "status": "ACTIVE"
        },
        {
            "id": "STP-2026-102",
            "city": "St. Paul",
            "company": "Capital City Siding & Windows",
            "representative": "Sarah Jenkins",
            "solicitor": "Sarah Jenkins",
            "rep": "Sarah Jenkins",
            "issueDate": "2026-03-15",
            "expireDate": "2026-10-30",
            "expirationDate": "2026-10-30",
            "expires": "2026-10-30",
            "matchedKeyword": "siding",
            "status": "ACTIVE"
        },
        {
            "id": "MON-2026-088",
            "city": "Monticello",
            "company": "River Valley Roofing Co.",
            "representative": "Dave Henderson",
            "solicitor": "Dave Henderson",
            "rep": "Dave Henderson",
            "issueDate": "2026-04-10",
            "expireDate": "2026-12-01",
            "expirationDate": "2026-12-01",
            "expires": "2026-12-01",
            "matchedKeyword": "roofing",
            "status": "ACTIVE"
        },
        {
            "id": "MON-2026-089",
            "city": "Monticello",
            "company": "Precision Gutter & Exterior",
            "representative": "Tom Miller",
            "solicitor": "Tom Miller",
            "rep": "Tom Miller",
            "issueDate": "2026-05-01",
            "expireDate": "2026-11-01",
            "expirationDate": "2026-11-01",
            "expires": "2026-11-01",
            "matchedKeyword": "gutter",
            "status": "ACTIVE"
        },
        {
            "id": "EAG-2026-210",
            "city": "Eagan",
            "company": "Twin Cities Home Restoration",
            "representative": "Elena Rostova",
            "solicitor": "Elena Rostova",
            "rep": "Elena Rostova",
            "issueDate": "2026-02-20",
            "expireDate": "2026-09-30",
            "expirationDate": "2026-09-30",
            "expires": "2026-09-30",
            "matchedKeyword": "restoration",
            "status": "ACTIVE"
        },
        {
            "id": "WOD-2026-311",
            "city": "Woodbury",
            "company": "Suburban Window & Door Specialists",
            "representative": "Kevin O'Connor",
            "solicitor": "Kevin O'Connor",
            "rep": "Kevin O'Connor",
            "issueDate": "2026-03-01",
            "expireDate": "2026-11-30",
            "expirationDate": "2026-11-30",
            "expires": "2026-11-30",
            "matchedKeyword": "window",
            "status": "ACTIVE"
        },
        {
            "id": "BLA-2026-514",
            "city": "Blaine",
            "company": "Metro Remodeling & Siding Experts",
            "representative": "Jessica Taylor",
            "solicitor": "Jessica Taylor",
            "rep": "Jessica Taylor",
            "issueDate": "2026-04-12",
            "expireDate": "2026-12-15",
            "expirationDate": "2026-12-15",
            "expires": "2026-12-15",
            "matchedKeyword": "remodeling",
            "status": "ACTIVE"
        }
    ]
    return records

def main():
    print("Generating comprehensive Twin Cities Metro solicitor dataset with all aliases...")
    records = generate_metro_solicitor_data()
    
    output_path = os.path.join(os.path.dirname(__file__), 'data.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2)
        
    print(f"Successfully wrote {len(records)} records with full property mapping.")

if __name__ == "__main__":
    main()