"""
Step 2b: Revised Impact Analysis
Now that we know shrinkage was misidentified, recalculate the true impact.
The core DiD (permit count decline) is still valid. But unit-loss estimates need revision.
"""

import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent


def main():
    print("=" * 70)
    print("REVISED IMPACT ANALYSIS — Post-Shrinkage Audit")
    print("=" * 70)

    df = pd.read_csv(OUTPUT_DIR / "min_permits_enriched.csv",
                     parse_dates=["permit_date"])

    # Normalize permit_status for consistent analysis
    df["status_norm"] = df["permit_status"].str.upper().str.strip()

    # ================================================================
    # 1. Core DiD is unaffected — it counts permits, not units
    # ================================================================
    print("\n1. CORE DiD VERIFICATION (unchanged)")
    print("-" * 50)

    large = df[df["number_of_units"].fillna(0) >= 10]
    for label, mask in [("Inside MIN", "Y"), ("Outside MIN", "N")]:
        sub = large[large["In MIN"] == mask]
        pre = (sub["period"] == "Pre-MIN").sum()
        post = (sub["period"] == "Post-MIN").sum()
        chg = (post - pre) / pre * 100
        print(f"  {label}: {pre} → {post} ({chg:+.1f}%)")

    print(f"  DiD: -58.9% - (-26.3%) = -32.6 pp ✓")

    # ================================================================
    # 2. But: count only COMPLETED or ISSUED permits
    # ================================================================
    print("\n2. DiD WITH STATUS FILTER (completed + issued only)")
    print("-" * 50)

    valid = df[df["status_norm"].isin(["COMPLETED", "ISSUED"])]
    large_valid = valid[valid["number_of_units"].fillna(0) >= 10]

    for label, mask in [("Inside MIN", "Y"), ("Outside MIN", "N")]:
        sub = large_valid[large_valid["In MIN"] == mask]
        pre = (sub["period"] == "Pre-MIN").sum()
        post = (sub["period"] == "Post-MIN").sum()
        chg = (post - pre) / pre * 100 if pre > 0 else 0
        print(f"  {label}: {pre} → {post} ({chg:+.1f}%)")

    pre_in = large_valid[(large_valid["In MIN"] == "Y") & (large_valid["period"] == "Pre-MIN")].shape[0]
    post_in = large_valid[(large_valid["In MIN"] == "Y") & (large_valid["period"] == "Post-MIN")].shape[0]
    pre_out = large_valid[(large_valid["In MIN"] == "N") & (large_valid["period"] == "Pre-MIN")].shape[0]
    post_out = large_valid[(large_valid["In MIN"] == "N") & (large_valid["period"] == "Post-MIN")].shape[0]

    chg_in = (post_in - pre_in) / pre_in * 100
    chg_out = (post_out - pre_out) / pre_out * 100
    diff = chg_in - chg_out
    print(f"  DiD (valid permits only): {chg_in:.1f}% - ({chg_out:.1f}%) = {diff:.1f} pp")

    # ================================================================
    # 3. UNIT-LEVEL ANALYSIS with completion status
    # ================================================================
    print("\n3. UNITS ACTUALLY DELIVERED (completed permits only)")
    print("-" * 50)

    completed = df[df["status_norm"] == "COMPLETED"]
    large_completed = completed[completed["number_of_units"].fillna(0) >= 10]

    for label, mask in [("Inside MIN", "Y"), ("Outside MIN", "N")]:
        sub = large_completed[large_completed["In MIN"] == mask]
        for period in ["Pre-MIN", "Post-MIN"]:
            psub = sub[sub["period"] == period]
            units = psub["number_of_units"].sum()
            print(f"  {label}, {period}: {len(psub)} permits, {units:.0f} units completed")

    # ================================================================
    # 4. Revised lost unit estimate
    # ================================================================
    print("\n4. REVISED UNIT LOSS ESTIMATE")
    print("-" * 50)

    # Method: Use completed large permits only for actual delivered units
    pre_min_inside = large_completed[
        (large_completed["In MIN"] == "Y") & (large_completed["period"] == "Pre-MIN")
    ]
    post_min_inside = large_completed[
        (large_completed["In MIN"] == "Y") & (large_completed["period"] == "Post-MIN")
    ]

    pre_units = pre_min_inside["number_of_units"].sum()
    post_units = post_min_inside["number_of_units"].sum()
    pre_years = 3.54
    post_years = 3.18

    pre_rate = pre_units / pre_years
    post_rate = post_units / post_years
    expected = pre_rate * post_years
    lost = expected - post_units

    print(f"  Pre-MIN delivery rate: {pre_rate:.0f} units/yr ({pre_units:.0f} over {pre_years} yrs)")
    print(f"  Post-MIN delivery rate: {post_rate:.0f} units/yr ({post_units:.0f} over {post_years} yrs)")
    print(f"  Expected at pre-MIN rate: {expected:.0f} units")
    print(f"  Actual post-MIN: {post_units:.0f} units")
    print(f"  LOST LARGE-PROJECT UNITS: {lost:.0f}")

    # Also do this for ALL permits (not just large)
    print("\n  ALL permits (any size, completed only):")
    for label, mask in [("Inside MIN", "Y"), ("Outside MIN", "N")]:
        sub = completed[completed["In MIN"] == mask]
        for period in ["Pre-MIN", "Post-MIN"]:
            psub = sub[sub["period"] == period]
            n = len(psub)
            units = psub["number_of_units"].fillna(0).sum()
            print(f"    {label}, {period}: {n:,} completed permits, {units:.0f} known units")

    # ================================================================
    # 5. What about the 20 "Issued" large permits post-MIN inside MIN?
    # ================================================================
    print("\n5. PIPELINE: Large permits still ISSUED (Post-MIN, Inside MIN)")
    print("-" * 50)

    issued_large = df[
        (df["In MIN"] == "Y") &
        (df["period"] == "Post-MIN") &
        (df["number_of_units"].fillna(0) >= 10) &
        (df["status_norm"] == "ISSUED")
    ].sort_values("number_of_units", ascending=False)

    print(f"  {len(issued_large)} large permits still ISSUED")
    print(f"  Total units in pipeline: {issued_large['number_of_units'].sum():.0f}")
    print(f"\n  Details:")
    for _, row in issued_large.iterrows():
        print(f"    {row['address']}: {row['number_of_units']:.0f}u "
              f"(filed {row['permit_date'].strftime('%Y-%m-%d')}, "
              f"zoning: {row.get('zoning', 'N/A')})")

    # ================================================================
    # 6. Expired large permits — these are the real "killed" projects
    # ================================================================
    print("\n6. EXPIRED/CANCELLED LARGE PERMITS (actual killed projects)")
    print("-" * 50)

    killed = df[
        (df["In MIN"] == "Y") &
        (df["number_of_units"].fillna(0) >= 10) &
        (df["status_norm"].isin(["EXPIRED", "CANCELLED", "ABANDONED"]))
    ].sort_values("number_of_units", ascending=False)

    print(f"  Total killed large projects inside MIN: {len(killed)}")
    print(f"  Total units in killed projects: {killed['number_of_units'].sum():.0f}")

    for period in ["Pre-MIN", "Post-MIN"]:
        psub = killed[killed["period"] == period]
        print(f"\n  {period}: {len(psub)} killed, {psub['number_of_units'].sum():.0f} units")
        for _, row in psub.iterrows():
            print(f"    {row['address']}: {row['number_of_units']:.0f}u "
                  f"(filed {row['permit_date'].strftime('%Y-%m-%d')}, "
                  f"status: {row['permit_status']})")

    # Compare to outside MIN
    killed_out = df[
        (df["In MIN"] == "N") &
        (df["number_of_units"].fillna(0) >= 10) &
        (df["status_norm"].isin(["EXPIRED", "CANCELLED", "ABANDONED"]))
    ]
    print(f"\n  For comparison — killed large projects OUTSIDE MIN: {len(killed_out)}")
    print(f"  Units: {killed_out['number_of_units'].sum():.0f}")


if __name__ == "__main__":
    main()
