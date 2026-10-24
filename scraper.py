import requests
import json
import time
from bs4 import BeautifulSoup

BASE_URL = "https://place2lease.hdb.gov.sg/webservice-public/api/v1"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
}

SEARCH_URL = f"{BASE_URL}/tender-units/public/search-tender-units"
DETAIL_URL = f"{BASE_URL}/tender-units/public/view"


def fetch_all_unit_ids():
    """Fetch all tender unit IDs from the search listing API, paginating if needed."""
    page = 1
    page_size = 100
    unit_ids = []
    total = None

    while True:
        params = {
            "page": page,
            "pageSize": page_size,
            "order": "asc",
            "orderProperty": "lastPost.currentBidClosingDate",
            "startIndex": (page - 1) * page_size,
            "collectionSize": page_size,
        }
        resp = requests.get(SEARCH_URL, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if total is None:
            total = data["total"]
            print(f"Found {total} units in listing.")

        items = data["items"]
        if not items:
            break

        unit_ids.extend(item["tenderUnitId"] for item in items)

        if len(unit_ids) >= total:
            break
        page += 1

    return unit_ids


def fetch_unit_detail(unit_id):
    """Fetch the full detail JSON for a single unit."""
    resp = requests.get(f"{DETAIL_URL}/{unit_id}", headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()


def parse_conditions_html(html_str):
    """Use BeautifulSoup to parse the unitSpecificConditions HTML into clean text."""
    if not html_str:
        return ""
    soup = BeautifulSoup(html_str, "html.parser")
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        table_text_lines = []
        for row in rows:
            cells = [cell.get_text(strip=True) for cell in row.find_all(["td", "th"])]
            table_text_lines.append(" | ".join(cells))
        table.replace_with("\n".join(table_text_lines) + "\n")
    return soup.get_text(separator="\n", strip=True)


def extract_unit_data(detail):
    """Extract structured Unit Details and Important Unit Conditions from the API response."""
    unit_details = {
        "Unit ID": detail.get("tenderUnitId"),
        "HDB Ref No": detail.get("hdbRefNo"),
        "Address": detail.get("address"),
        "Block": detail.get("block"),
        "Street": detail.get("street"),
        "Level": detail.get("levelNo"),
        "Unit No": detail.get("unitNo"),
        "Postal Code": detail.get("postalCode"),
        "HDB Town": detail.get("hdbTownLabel"),
        "Property Type": detail.get("propertyTypeLabel"),
        "Usage Type": detail.get("usageTypeLabel"),
        "Floor Area (sqm)": detail.get("floorArea"),
        "Has Water Supply": detail.get("hasWater"),
        "Has Toilet": detail.get("hasToilet"),
        "Electrical Loading (Amps)": detail.get("electricalLoading"),
        "Electrical Type": detail.get("electricalTypeLabel"),
        "Service & Conservancy Charges": detail.get("scCharges"),
        "Exercise No": detail.get("exerciseNo"),
        "Tender Type": detail.get("tenderTypeLabel"),
        "Bid Opening Date": detail.get("bidOpeningDate"),
        "Bid Closing Date": detail.get("bidClosingDate"),
        "Tenure (months)": detail.get("tenure"),
        "Tenure Option (months)": detail.get("tenureOption"),
        "Rent-Free Months": detail.get("rentFreeMonth"),
        "Deposit Type": detail.get("depositTypeLabel"),
        "Allowed Trades": detail.get("specificTradesLabels", []),
        "Excluded Trades": detail.get("excludeTradesLabels", []),
    }

    conditions_html = detail.get("unitSpecificConditions", "")
    conditions_text = parse_conditions_html(conditions_html)

    return unit_details, conditions_text


def scrape_all_units():
    """Main scraping function: fetches all units and returns structured data."""
    unit_ids = fetch_all_unit_ids()
    all_units = []

    for i, uid in enumerate(unit_ids, start=1):
        print(f"  Fetching unit {i}/{len(unit_ids)}: ID {uid}...", end=" ")
        try:
            detail = fetch_unit_detail(uid)
            unit_details, conditions_text = extract_unit_data(detail)
            all_units.append({
                "unit_details": unit_details,
                "important_unit_conditions": conditions_text,
            })
            print("OK")
        except Exception as e:
            print(f"ERROR: {e}")
        time.sleep(0.3)

    print(f"\nScraped {len(all_units)} units successfully.")
    return all_units


def load_town_region(filepath="resources/town_region.txt"):
    mapping = {}
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if " - " in line:
                town, region = line.strip().rsplit(" - ", 1)
                mapping[town.strip()] = region.strip()
    return mapping


TOWN_REGION = load_town_region()


def build_corpus(all_units):
    """Convert scraped unit data into a text corpus suitable for RAG ingestion."""
    corpus_parts = []
    for unit in all_units:
        d = unit["unit_details"]
        region = TOWN_REGION.get(d.get("HDB Town", ""), "Unknown")
        lines = [
            f"=== UNIT: {d['Address']} ===",
            "",
            "--- Unit Details ---",
        ]
        for key, val in d.items():
            if isinstance(val, list):
                val = ", ".join(val) if val else "N/A"
            elif isinstance(val, bool):
                val = "Yes" if val else "No"
            elif val is None:
                val = "N/A"
            lines.append(f"{key}: {val}")
        lines.append(f"Region: {region}")

        lines.append("")
        lines.append("--- Important Unit Conditions ---")
        lines.append(unit["important_unit_conditions"] or "No specific conditions listed.")
        lines.append("")

        corpus_parts.append("\n".join(lines))

    return "\n\n".join(corpus_parts)


if __name__ == "__main__":
    print("\n\n\n\nScraping Place2Lease listings...\n")
    all_units = scrape_all_units()

    with open("resources/place2lease_units.json", "w", encoding="utf-8") as f:
        json.dump(all_units, f, indent=2, ensure_ascii=False)
    print("Saved JSON to resources/place2lease_units.json")

    corpus = build_corpus(all_units)
    with open("resources/place2lease_corpus.txt", "w", encoding="utf-8") as f:
        f.write(corpus)
    print(f"Saved corpus to resources/place2lease_corpus.txt ({len(corpus)} chars)")
