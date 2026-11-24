"""
Step 1: Build Enriched Permit-Parcel Dataset
Loads 8,924 L&I permits and enriches each with OPA parcel data via CARTO API.
"""

import pandas as pd
import requests
import time
import re
import json
from pathlib import Path
from urllib.parse import quote

PERMITS_PATH = Path.home() / "Projects/Housing-Transit/cd3_cd7_permits_with_MIN_status.xlsx"
OUTPUT_DIR = Path(__file__).parent
CARTO_URL = "https://phl.carto.com/api/v2/sql"

OPA_FIELDS = [
    "parcel_number", "location", "owner_1", "owner_2",
    "zoning", "market_value", "sale_price", "sale_date",
    "total_area", "total_livable_area", "frontage", "depth",
    "year_built", "number_stories", "category_code_description",
    "census_tract", "building_code_description", "taxable_land",
    "taxable_building", "number_of_bedrooms", "number_of_bathrooms",
]

# ST_X/ST_Y on the_geom gives us WGS84 coords for transit analysis later
GEO_FIELDS = "ST_X(the_geom) as lng, ST_Y(the_geom) as lat"


def classify_owner(owner_name: str) -> str:
    """Classify owner into Entity/Developer, Public, Nonprofit, or Individual."""
    if not owner_name or pd.isna(owner_name):
        return "Unknown"
    name = owner_name.upper().strip()

    # Public entities
    public_keywords = [
        "CITY OF PHILA", "PHILADELPHIA HOUSING AUTH", "PHA ",
        "REDEVELOPMENT AUTH", "SCHOOL DIST", "SEPTA",
        "COMMONWEALTH", "DEPT OF", "DEPARTMENT OF",
        "WATER DEPT", "FAIRMOUNT PARK", "FREE LIBRARY",
        "PARKING AUTH", "LAND BANK", "PHILA LAND BANK",
    ]
    if any(kw in name for kw in public_keywords):
        return "Public"

    # Nonprofits
    nonprofit_keywords = [
        "HABITAT FOR HUMANITY", "CDC", "COMMUNITY DEV",
        "HOUSING TRUST", "AFFORDABLE", "ASSOC", "ASSOCIATION",
        "FOUNDATION", "CHURCH", "TEMPLE", "MOSQUE",
        "CONGREGATION", "MINISTRY", "MISSIONARY",
        "UNIVERSITY", "COLLEGE", "HOSPITAL",
        "PRESERVATION", "CONSERV",
    ]
    if any(kw in name for kw in nonprofit_keywords):
        return "Nonprofit"

    # Entity/Developer (LLC, LP, Corp, Inc, etc.)
    entity_patterns = [
        r'\bLLC\b', r'\bLP\b', r'\bL\.P\.', r'\bINC\b',
        r'\bCORP\b', r'\bLTD\b', r'\bL\.L\.C',
        r'\bPARTNERS\b', r'\bPARTNERSHIP\b',
        r'\bGROUP\b', r'\bHOLDINGS?\b', r'\bENTERPRISE',
        r'\bINVEST', r'\bDEVELOP', r'\bPROPERT',
        r'\bREALTY\b', r'\bREAL ESTATE\b', r'\bBUILDERS?\b',
        r'\bCONSTRUCT', r'\bTRUST\b', r'\bESTATE OF\b',
    ]
    if any(re.search(pat, name) for pat in entity_patterns):
        return "Entity/Developer"

    return "Individual"


def batch_query_carto(addresses: list[str], batch_size: int = 40) -> dict:
    """Query CARTO for OPA data, batching addresses with IN clauses."""
    results = {}
    fields_str = ", ".join(OPA_FIELDS) + ", " + GEO_FIELDS
    total_batches = (len(addresses) + batch_size - 1) // batch_size

    for i in range(0, len(addresses), batch_size):
        batch = addresses[i:i + batch_size]
        batch_num = i // batch_size + 1

        # Escape single quotes in addresses
        escaped = [addr.replace("'", "''") for addr in batch]
        in_clause = ", ".join(f"'{a}'" for a in escaped)

        query = f"SELECT {fields_str} FROM opa_properties_public WHERE location IN ({in_clause})"

        try:
            resp = requests.get(CARTO_URL, params={"q": query}, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            for row in data.get("rows", []):
                loc = row.get("location", "").strip()
                if loc:
                    results[loc] = row

            if batch_num % 10 == 0 or batch_num == total_batches:
                print(f"  CARTO batch {batch_num}/{total_batches}: "
                      f"{len(results)} addresses matched so far")

        except Exception as e:
            print(f"  Batch {batch_num} error: {e}")

        # Rate limit: ~2 requests/sec is conservative
        time.sleep(0.5)

    return results


def main():
    print("=" * 60)
    print("STEP 1: Building Enriched Permit-Parcel Dataset")
    print("=" * 60)

    # Load permits
    print("\nLoading permits...")
    df = pd.read_excel(PERMITS_PATH)
    print(f"  Loaded {len(df):,} permits")
    print(f"  Columns: {list(df.columns)}")
    print(f"  Date range: {df['permit_date'].min()} to {df['permit_date'].max()}")
    print(f"  Inside MIN: {(df['In MIN'] == 'Y').sum():,}")
    print(f"  Outside MIN: {(df['In MIN'] == 'N').sum():,}")

    # Normalize addresses
    df["address_clean"] = df["address"].str.strip().str.upper()
    unique_addresses = df["address_clean"].dropna().unique().tolist()
    print(f"\n  Unique addresses: {len(unique_addresses):,}")

    # Query CARTO
    print(f"\nQuerying CARTO for OPA parcel data...")
    opa_data = batch_query_carto(unique_addresses)
    print(f"\n  Matched {len(opa_data):,} / {len(unique_addresses):,} addresses "
          f"({len(opa_data)/len(unique_addresses)*100:.1f}%)")

    # Try fuzzy matching for unmatched addresses
    unmatched = [a for a in unique_addresses if a not in opa_data]
    print(f"  Unmatched: {len(unmatched):,}")

    # Some L&I addresses may have unit numbers (e.g., "123 MAIN ST UNIT A")
    # Try stripping unit suffixes
    unit_pattern = re.compile(r'\s+(UNIT|APT|STE|#|FL|FLOOR)\s*\S*$', re.IGNORECASE)
    retry_addresses = []
    retry_map = {}  # cleaned -> original
    for addr in unmatched:
        cleaned = unit_pattern.sub('', addr).strip()
        if cleaned != addr and cleaned not in opa_data:
            retry_addresses.append(cleaned)
            retry_map[cleaned] = addr

    if retry_addresses:
        print(f"\n  Retrying {len(retry_addresses)} addresses with unit suffixes stripped...")
        retry_results = batch_query_carto(retry_addresses)
        for cleaned_addr, row in retry_results.items():
            original = retry_map.get(cleaned_addr, cleaned_addr)
            opa_data[original] = row
        print(f"  After retry: {len(opa_data):,} total matches "
              f"({len(opa_data)/len(unique_addresses)*100:.1f}%)")

    # Merge OPA data onto permits
    print("\nMerging parcel data onto permits...")
    opa_df = pd.DataFrame.from_dict(opa_data, orient="index")
    opa_df.index.name = "address_clean"
    opa_df = opa_df.reset_index()

    enriched = df.merge(opa_df, on="address_clean", how="left", suffixes=("", "_opa"))

    # Classify owners
    print("Classifying owner types...")
    enriched["owner_type"] = enriched["owner_1"].apply(classify_owner)
    owner_counts = enriched["owner_type"].value_counts()
    print(f"  Owner type distribution:")
    for otype, count in owner_counts.items():
        print(f"    {otype}: {count:,} ({count/len(enriched)*100:.1f}%)")

    # Add derived fields
    enriched["has_opa_match"] = enriched["parcel_number"].notna()
    enriched["period"] = enriched["permit_date"].apply(
        lambda d: "Pre-MIN" if d < pd.Timestamp("2022-07-18") else "Post-MIN"
    )
    enriched["is_large"] = enriched["number_of_units"].fillna(0) >= 10
    enriched["has_units"] = enriched["number_of_units"].notna()

    # Summary stats
    match_rate = enriched["has_opa_match"].mean()
    print(f"\n  Overall match rate: {match_rate*100:.1f}%")
    print(f"  Match rate inside MIN: "
          f"{enriched.loc[enriched['In MIN']=='Y', 'has_opa_match'].mean()*100:.1f}%")
    print(f"  Match rate outside MIN: "
          f"{enriched.loc[enriched['In MIN']=='N', 'has_opa_match'].mean()*100:.1f}%")

    # Save
    out_path = OUTPUT_DIR / "min_permits_enriched.csv"
    enriched.to_csv(out_path, index=False)
    print(f"\nSaved enriched dataset: {out_path}")
    print(f"  {len(enriched):,} rows, {len(enriched.columns)} columns")
    print(f"  Columns: {list(enriched.columns)}")

    # Quick verification: reproduce the original DiD
    print("\n" + "=" * 60)
    print("VERIFICATION: Reproducing original DiD finding")
    print("=" * 60)

    large = enriched[enriched["is_large"]]
    for label, mask in [("Inside MIN", enriched["In MIN"] == "Y"),
                        ("Outside MIN", enriched["In MIN"] == "N")]:
        sub = large[mask]
        pre = (sub["period"] == "Pre-MIN").sum()
        post = (sub["period"] == "Post-MIN").sum()
        change = (post - pre) / pre * 100 if pre > 0 else 0
        print(f"  {label}: {pre} pre → {post} post ({change:+.1f}%)")

    pre_in = large[(enriched["In MIN"] == "Y") & (large["period"] == "Pre-MIN")].shape[0]
    post_in = large[(enriched["In MIN"] == "Y") & (large["period"] == "Post-MIN")].shape[0]
    pre_out = large[(enriched["In MIN"] == "N") & (large["period"] == "Pre-MIN")].shape[0]
    post_out = large[(enriched["In MIN"] == "N") & (large["period"] == "Post-MIN")].shape[0]

    chg_in = (post_in - pre_in) / pre_in * 100
    chg_out = (post_out - pre_out) / pre_out * 100
    diff = chg_in - chg_out
    print(f"\n  DiD differential: {chg_in:.1f}% - ({chg_out:.1f}%) = {diff:.1f} pp")
    print(f"  Expected: ~-33 pp")

    return enriched


if __name__ == "__main__":
    main()
