"""
Step 2: Shrinkage Audit
The prior analysis flagged addresses where a large-unit permit was followed by
a small-unit permit. But if the large permit was COMPLETED (building actually built),
that's not shrinkage — it's sequential development. We need to distinguish:

1. TRUE SHRINKAGE: Large permit expired/cancelled → small permit filed (developer gave up on large)
2. SEQUENTIAL DEVELOPMENT: Large permit completed → small permit filed (new project on same site)
3. SUPPLEMENTAL: Large and small permits overlap (additions, renovations, etc.)
"""

import pandas as pd
from pathlib import Path
from datetime import timedelta

OUTPUT_DIR = Path(__file__).parent


def main():
    print("=" * 70)
    print("STEP 2: SHRINKAGE AUDIT — Did the large projects actually get built?")
    print("=" * 70)

    df = pd.read_csv(OUTPUT_DIR / "min_permits_enriched.csv",
                     parse_dates=["permit_date"])

    # Focus on permits with known units inside MIN zones
    min_permits = df[(df["In MIN"] == "Y") & df["number_of_units"].notna()].copy()
    min_permits["units"] = min_permits["number_of_units"].astype(int)

    print(f"\nPermits inside MIN with known units: {len(min_permits):,}")

    # Group by address to find shrinkage candidates
    addr_groups = min_permits.groupby("address_clean")

    shrinkage_cases = []
    sequential_cases = []
    ambiguous_cases = []

    for addr, group in addr_groups:
        group = group.sort_values("permit_date")
        large = group[group["units"] >= 10]
        small = group[group["units"] < 10]

        if len(large) == 0 or len(small) == 0:
            continue

        # For each large permit, check if a smaller permit came after
        for _, lg in large.iterrows():
            later_small = small[small["permit_date"] > lg["permit_date"]]
            if len(later_small) == 0:
                continue

            first_small = later_small.iloc[0]
            lg_status = str(lg.get("permit_status", "")).upper()

            case = {
                "address": addr,
                "large_permit": lg["permit_number"],
                "large_units": lg["units"],
                "large_date": lg["permit_date"],
                "large_status": lg.get("permit_status", "Unknown"),
                "large_completed_date": lg.get("permitcompleteddate", ""),
                "small_permit": first_small["permit_number"],
                "small_units": first_small["units"],
                "small_date": first_small["permit_date"],
                "small_status": first_small.get("permit_status", "Unknown"),
                "large_period": lg["period"],
                "small_period": first_small["period"],
                "unit_drop": lg["units"] - first_small["units"],
                "zoning": lg.get("zoning", ""),
                "total_area": lg.get("total_area", ""),
                "owner_type": lg.get("owner_type", ""),
                "owner_1": lg.get("owner_1", ""),
            }

            if "COMPLETED" in lg_status:
                # Large project was built! This is sequential, not shrinkage
                sequential_cases.append(case)
            elif "EXPIRED" in lg_status or "CANCELLED" in lg_status or "ABANDONED" in lg_status:
                # Large project failed — this IS shrinkage
                shrinkage_cases.append(case)
            elif "ISSUED" in lg_status:
                # Still active — might still get built
                ambiguous_cases.append(case)
            else:
                ambiguous_cases.append(case)

    print(f"\n{'='*70}")
    print("SHRINKAGE CLASSIFICATION RESULTS")
    print(f"{'='*70}")
    print(f"\n  TRUE SHRINKAGE (large expired/cancelled → small filed):  {len(shrinkage_cases)}")
    print(f"  SEQUENTIAL DEV (large COMPLETED → small filed later):   {len(sequential_cases)}")
    print(f"  AMBIGUOUS (large still ISSUED):                         {len(ambiguous_cases)}")
    print(f"  TOTAL address-pairs examined:                           "
          f"{len(shrinkage_cases) + len(sequential_cases) + len(ambiguous_cases)}")

    # Detail on true shrinkage
    if shrinkage_cases:
        sdf = pd.DataFrame(shrinkage_cases)
        print(f"\n{'='*70}")
        print("TRUE SHRINKAGE CASES (large permit expired/cancelled)")
        print(f"{'='*70}")
        print(f"\n  Total true shrinkage cases: {len(sdf)}")
        print(f"  Total units lost (large - small): {sdf['unit_drop'].sum():,}")
        print(f"  Avg large project size: {sdf['large_units'].mean():.1f} units")
        print(f"  Avg small replacement size: {sdf['small_units'].mean():.1f} units")

        # By period
        pre_to_post = sdf[(sdf["large_period"] == "Pre-MIN") &
                          (sdf["small_period"] == "Post-MIN")]
        print(f"\n  Pre-MIN large → Post-MIN small (policy-induced): {len(pre_to_post)}")
        if len(pre_to_post) > 0:
            print(f"    Units lost in these cases: {pre_to_post['unit_drop'].sum():,}")

        # Zoning
        print(f"\n  Zoning distribution of true shrinkage parcels:")
        for z, c in sdf["zoning"].value_counts().head(10).items():
            print(f"    {z}: {c}")

        # Owner type
        print(f"\n  Owner type distribution:")
        for o, c in sdf["owner_type"].value_counts().items():
            print(f"    {o}: {c}")

        # Save
        sdf.to_csv(OUTPUT_DIR / "true_shrinkage_cases.csv", index=False)

    # Detail on sequential (FALSE shrinkage)
    if sequential_cases:
        seqdf = pd.DataFrame(sequential_cases)
        print(f"\n{'='*70}")
        print("SEQUENTIAL DEVELOPMENT (large permit COMPLETED — NOT shrinkage)")
        print(f"{'='*70}")
        print(f"\n  Total sequential cases: {len(seqdf)}")
        print(f"  These were INCORRECTLY counted as shrinkage in prior analysis")
        print(f"  Large projects that WERE built: {len(seqdf)}")
        print(f"  Units in those completed projects: {seqdf['large_units'].sum():,}")

        # Show some examples
        print(f"\n  Top 10 sequential cases (largest completed projects):")
        for _, row in seqdf.nlargest(10, "large_units").iterrows():
            print(f"    {row['address']}: {row['large_units']}u ({row['large_status']}) "
                  f"→ {row['small_units']}u ({row['small_status']})")

        seqdf.to_csv(OUTPUT_DIR / "sequential_development_cases.csv", index=False)

    # Detail on ambiguous
    if ambiguous_cases:
        ambdf = pd.DataFrame(ambiguous_cases)
        print(f"\n{'='*70}")
        print("AMBIGUOUS CASES (large permit still ISSUED)")
        print(f"{'='*70}")
        print(f"\n  Total ambiguous: {len(ambdf)}")
        print(f"  These large permits are still active/in-progress")

        ambdf.to_csv(OUTPUT_DIR / "ambiguous_shrinkage_cases.csv", index=False)

    # Now redo the shrinkage unit count with only TRUE shrinkage
    print(f"\n{'='*70}")
    print("REVISED SHRINKAGE ESTIMATE")
    print(f"{'='*70}")

    if shrinkage_cases:
        sdf = pd.DataFrame(shrinkage_cases)
        pre_post = sdf[(sdf["large_period"] == "Pre-MIN") &
                       (sdf["small_period"] == "Post-MIN")]
        print(f"\n  Policy-induced shrinkage (pre→post only): {len(pre_post)} cases")
        print(f"  Units in abandoned large projects: {pre_post['large_units'].sum():,}")
        print(f"  Units in replacement small projects: {pre_post['small_units'].sum():,}")
        print(f"  NET units lost to shrinkage: {pre_post['unit_drop'].sum():,}")
    else:
        print("\n  No true shrinkage cases found!")

    # Also check: did the PRIOR analysis count sequential development as shrinkage?
    # The prior analysis said 3,776 units lost to shrinkage and 58 large projects downsized
    prior_shrinkage_claim = 3776
    prior_projects_claim = 58

    total_identified = len(shrinkage_cases) + len(sequential_cases) + len(ambiguous_cases)
    true_shrinkage_units = sum(c["unit_drop"] for c in shrinkage_cases) if shrinkage_cases else 0

    print(f"\n  COMPARISON TO PRIOR ANALYSIS:")
    print(f"    Prior claim: {prior_projects_claim} projects, {prior_shrinkage_claim:,} units lost")
    print(f"    This audit found: {total_identified} address-pairs total")
    print(f"      - {len(shrinkage_cases)} TRUE shrinkage ({true_shrinkage_units:,} units lost)")
    print(f"      - {len(sequential_cases)} were actually COMPLETED (not shrinkage)")
    print(f"      - {len(ambiguous_cases)} still in progress")

    # Broader check: ALL large permits inside MIN and their outcomes
    print(f"\n{'='*70}")
    print("ALL LARGE PERMITS INSIDE MIN — OUTCOME SUMMARY")
    print(f"{'='*70}")

    all_large_min = df[(df["In MIN"] == "Y") & (df["number_of_units"].fillna(0) >= 10)]
    print(f"\n  Total large permits inside MIN: {len(all_large_min)}")

    for period in ["Pre-MIN", "Post-MIN"]:
        sub = all_large_min[all_large_min["period"] == period]
        print(f"\n  {period} (n={len(sub)}):")
        status_counts = sub["permit_status"].value_counts()
        for s, c in status_counts.items():
            pct = c / len(sub) * 100
            print(f"    {s:20s}: {c:>3} ({pct:.0f}%)")
        if sub["number_of_units"].notna().any():
            completed = sub[sub["permit_status"].str.upper().str.contains("COMPLETED", na=False)]
            print(f"    → Completed units: {completed['number_of_units'].sum():.0f}")
            expired = sub[sub["permit_status"].str.upper().str.contains("EXPIRED|CANCELLED|ABANDONED", na=False)]
            print(f"    → Expired/cancelled units: {expired['number_of_units'].sum():.0f}")


if __name__ == "__main__":
    main()
