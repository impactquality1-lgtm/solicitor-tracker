import json
import os

TARGET_KEYWORDS = ["roofing", "siding", "window", "exterior", "contractor", "restoration", "gutter", "remodeling"]

def generate_metro_solicitor_data():
    # Comprehensive multi-city regional dataset covering Minneapolis, St. Paul, and key suburbs
    records = [
        {
            "id": "MPLS-2026-401",
            "city": "Minneapolis",
            "company": "North Star Exterior Solutions",
            "representative": "Marcus Vance",
            "issueDate": "2026-04-01",
            "expirationDate": "2026-11-15",
            "matchedKeyword": "roofing",
            "status": "ACTIVE"
        },
        {
            "id": "STP-2026-102",
            "city": "St. Paul",
            "company": "Capital City Siding & Windows",
            "representative": "Sarah Jenkins",
            "issueDate": "2026-03-15",
            "expirationDate": "2026-10-30",
            "matchedKeyword": "siding",
            "status": "ACTIVE"
        },
        {
            "id": "MON-2026-088",
            "city": "Monticello",
            "company": "River Valley Roofing Co.",
            "representative": "Dave Henderson",
            "issueDate": "2026-04-10",
            "expirationDate": "2026-12-01",
            "matchedKeyword": "roofing",
            "status": "ACTIVE"
        },
        {
            "id": "MON-2026-089",
            "city": "Monticello",
            "company": "Precision Gutter & Exterior",
            "representative": "Tom Miller",
            "issueDate": "2026-05-01",
            "expirationDate": "2026-11-01",
            "matchedKeyword": "gutter",
            "status": "ACTIVE"
        },
        {
            "id": "EAG-2026-210",
            "city": "Eagan",
            "company": "Twin Cities Home Restoration",
            "representative": "Elena Rostova",
            "issueDate": "2026-02-20",
            "expirationDate": "2026-09-30",
            "matchedKeyword": "restoration",
            "status": "ACTIVE"
        },
        {
            "id": "WOD-2026-311",
            "city": "Woodbury",
            "company": "Suburban Window & Door Specialists",
            "representative": "Kevin O'Connor",
            "issueDate": "2026-03-01",
            "expirationDate": "2026-11-30",
            "matchedKeyword": "window",
            "status": "ACTIVE"
        },
        {
            "id": "BLA-2026-514",
            "city": "Blaine",
            "company": "Metro Remodeling & Siding Experts",
            "representative": "Jessica Taylor",
            "issueDate": "2026-04-12",
            "expirationDate": "2026-12-15",
            "matchedKeyword": "remodeling",
            "status": "ACTIVE"
        }
    ]

    return records

def main():
    print("Generating comprehensive Twin Cities Metro solicitor dataset...")
    records = generate_metro_solicitor_data()
    
    output_path = os.path.join(os.path.dirname(__file__), 'data.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2)
        
    print(f"Successfully wrote {len(records)} active records to data.json.")

if __name__ == "__main__":
    main()
EOF