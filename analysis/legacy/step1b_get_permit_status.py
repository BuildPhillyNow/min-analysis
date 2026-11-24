"""
Step 1b: Fetch permit status/outcome data from L&I CARTO table.
Adds status, permitcompleteddate, certificateofoccupancydate to enriched dataset.
"""

import pandas as pd
import requests
import time
from pathlib import Path

ENRICHED_PATH = Path(__file__).parent / "min_permits_enriched.csv"
CARTO_URL = "https://phl.carto.com/api/v2/sql"


def batch_query_status(permit_numbers: list[str], batch_size: int = 50) -> dict:
    """Query L&I CARTO for permit status by permit number."""
    results = {}
    total_batches = (len(permit_numbers) + batch_size - 1) // batch_size

    for i in range(0, len(permit_numbers), batch_size):
        batch = permit_numbers[i:i + batch_size]
        batch_num = i // batch_size + 1

        in_clause = ", ".join(f"'{p}'" for p in batch)
        query = (
            f"SELECT permitnumber, status, permitcompleteddate, "
            f"certificateofoccupancydate, typeofwork, numberofunits, "
            f"opa_account_num "
            f"FROM permits "
            f"WHERE permitnumber IN ({in_clause})"
        )

        try:
            resp = requests.get(CARTO_URL, params={"q": query}, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            for row in data.get("rows", []):
                pn = str(row.get("permitnumber", "")).strip()
                if pn:
                    results[pn] = row

            if batch_num % 10 == 0 or batch_num == total_batches:
                print(f"  Batch {batch_num}/{total_batches}: {len(results)} permits matched")

        except Exception as e:
            print(f"  Batch {batch_num} error: {e}")

        time.sleep(0.5)

    return results


def main():
    print("=" * 60)
    print("STEP 1b: Fetching Permit Status Data from L&I")
    print("=" * 60)

    df = pd.read_csv(ENRICHED_PATH)
    print(f"Loaded {len(df):,} enriched permits")

    permit_nums = df["permit_number"].astype(str).tolist()
    print(f"Querying L&I for {len(permit_nums):,} permit numbers...")

    status_data = batch_query_status(permit_nums)
    print(f"\nMatched {len(status_data):,} / {len(permit_nums):,} "
          f"({len(status_data)/len(permit_nums)*100:.1f}%)")

    # Merge status data
    status_df = pd.DataFrame.from_dict(status_data, orient="index")
    status_df.index.name = "permit_number_str"
    status_df = status_df.reset_index()

    df["permit_number_str"] = df["permit_number"].astype(str)
    df = df.merge(
        status_df[["permit_number_str", "status", "permitcompleteddate",
                    "certificateofoccupancydate", "typeofwork",
                    "numberofunits", "opa_account_num"]].rename(
            columns={
                "numberofunits": "li_units",
                "status": "permit_status",
                "typeofwork": "type_of_work",
            }
        ),
        on="permit_number_str",
        how="left"
    )
    df.drop(columns=["permit_number_str"], inplace=True)

    # Status distribution
    print("\nPermit status distribution:")
    status_counts = df["permit_status"].value_counts(dropna=False)
    for s, c in status_counts.items():
        print(f"  {str(s):20s}: {c:>6,} ({c/len(df)*100:.1f}%)")

    # Key question: status by period and MIN
    print("\nStatus by Period and MIN zone:")
    for period in ["Pre-MIN", "Post-MIN"]:
        for min_status in ["Y", "N"]:
            sub = df[(df["period"] == period) & (df["In MIN"] == min_status)]
            label = f"{period}, {'Inside' if min_status == 'Y' else 'Outside'} MIN"
            print(f"\n  {label} (n={len(sub):,}):")
            sc = sub["permit_status"].value_counts(dropna=False)
            for s, c in sc.items():
                print(f"    {str(s):20s}: {c:>5,} ({c/len(sub)*100:.1f}%)")

    # Critical check: large projects and their status
    print("\n" + "=" * 60)
    print("CRITICAL: Large project (10+ unit) status")
    print("=" * 60)
    large = df[df["is_large"]]
    print(f"\nTotal large projects: {len(large)}")
    for period in ["Pre-MIN", "Post-MIN"]:
        for min_status in ["Y", "N"]:
            sub = large[(large["period"] == period) & (large["In MIN"] == min_status)]
            label = f"{period}, {'Inside' if min_status == 'Y' else 'Outside'} MIN"
            print(f"\n  {label} (n={len(sub)}):")
            sc = sub["permit_status"].value_counts(dropna=False)
            for s, c in sc.items():
                print(f"    {str(s):15s}: {c:>3}")

    # Check: L&I unit counts vs our xlsx unit counts
    df["li_units_num"] = pd.to_numeric(df["li_units"], errors="coerce")
    has_both = df[df["number_of_units"].notna() & df["li_units_num"].notna()]
    if len(has_both) > 0:
        matches = (has_both["number_of_units"] == has_both["li_units_num"]).sum()
        print(f"\nUnit count validation: {matches:,}/{len(has_both):,} "
              f"({matches/len(has_both)*100:.1f}%) match between xlsx and L&I")

    # Save
    out_path = Path(__file__).parent / "min_permits_enriched.csv"
    df.to_csv(out_path, index=False)
    print(f"\nUpdated enriched dataset with status: {out_path}")
    print(f"  {len(df):,} rows, {len(df.columns)} columns")


if __name__ == "__main__":
    main()
