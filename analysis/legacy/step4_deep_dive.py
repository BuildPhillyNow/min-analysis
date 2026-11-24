"""
Step 4: Deep Dive Analyses
- 9-unit threshold gaming
- CD3 vs CD7 district breakdowns
- Hot submarket differentials
- LIHTC/subsidized project identification
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
import requests
import time

OUTPUT_DIR = Path(__file__).parent
CARTO_URL = "https://phl.carto.com/api/v2/sql"


def load_data():
    df = pd.read_csv(OUTPUT_DIR / "min_permits_enriched.csv",
                     parse_dates=["permit_date"])
    df["status_norm"] = df["permit_status"].str.upper().str.strip()
    df["units"] = df["number_of_units"].fillna(0).astype(int)
    df["quarter"] = df["permit_date"].dt.to_period("Q")
    return df


def threshold_gaming(df):
    """Are developers building exactly 9 units to duck MIN?"""
    print("=" * 70)
    print("9-UNIT THRESHOLD ANALYSIS")
    print("=" * 70)

    # Focus on permits with known units
    has_units = df[df["number_of_units"].notna()].copy()
    has_units["units"] = has_units["number_of_units"].astype(int)

    # Unit count distribution 1-15
    print("\nUnit count distribution (1-20 units), Inside MIN:")
    for period in ["Pre-MIN", "Post-MIN"]:
        sub = has_units[(has_units["In MIN"] == "Y") & (has_units["period"] == period)]
        print(f"\n  {period}:")
        dist = sub["units"].value_counts().sort_index()
        for u in range(1, 21):
            count = dist.get(u, 0)
            bar = "#" * min(count, 80)
            marker = " <<<" if u == 9 else (" --- THRESHOLD" if u == 10 else "")
            print(f"    {u:>2}u: {count:>4} {bar}{marker}")

    # Same for outside MIN (control)
    print("\n\nUnit count distribution (1-20 units), Outside MIN:")
    for period in ["Pre-MIN", "Post-MIN"]:
        sub = has_units[(has_units["In MIN"] == "N") & (has_units["period"] == period)]
        print(f"\n  {period}:")
        dist = sub["units"].value_counts().sort_index()
        for u in range(1, 21):
            count = dist.get(u, 0)
            bar = "#" * min(count, 80)
            marker = " <<<" if u == 9 else (" --- THRESHOLD" if u == 10 else "")
            print(f"    {u:>2}u: {count:>4} {bar}{marker}")

    # Key metric: 7-9 unit projects (just under threshold) vs 10-12 (just over)
    print("\n\nJUST-UNDER vs JUST-OVER THRESHOLD:")
    for min_s, label in [("Y", "Inside MIN"), ("N", "Outside MIN")]:
        sub = has_units[has_units["In MIN"] == min_s]
        for period in ["Pre-MIN", "Post-MIN"]:
            psub = sub[sub["period"] == period]
            under = psub[(psub["units"] >= 7) & (psub["units"] <= 9)].shape[0]
            over = psub[(psub["units"] >= 10) & (psub["units"] <= 12)].shape[0]
            ratio = under / over if over > 0 else float("inf")
            print(f"  {label} {period}: 7-9u={under}, 10-12u={over}, ratio={ratio:.2f}")

    # Completed 9-unit projects post-MIN inside MIN
    print("\n\n9-UNIT PROJECTS POST-MIN INSIDE MIN (completed or issued):")
    nine_unit = has_units[
        (has_units["units"] == 9) &
        (has_units["In MIN"] == "Y") &
        (has_units["period"] == "Post-MIN") &
        (has_units["status_norm"].isin(["COMPLETED", "ISSUED"]))
    ].sort_values("permit_date")

    print(f"  Count: {len(nine_unit)}")
    for _, row in nine_unit.iterrows():
        print(f"    {row['address']}: 9u ({row['permit_status']}, "
              f"{row['permit_date'].strftime('%Y-%m-%d')}, "
              f"zoning: {row.get('zoning', 'N/A')}, "
              f"owner: {str(row.get('owner_1', 'N/A'))[:40]})")

    # Compare: 8-unit projects too
    print(f"\n8-UNIT PROJECTS POST-MIN INSIDE MIN:")
    eight_unit = has_units[
        (has_units["units"] == 8) &
        (has_units["In MIN"] == "Y") &
        (has_units["period"] == "Post-MIN") &
        (has_units["status_norm"].isin(["COMPLETED", "ISSUED"]))
    ]
    print(f"  Count: {len(eight_unit)}")


def district_analysis(df):
    """CD3 vs CD7 breakdown with charts."""
    print("\n\n" + "=" * 70)
    print("DISTRICT-BY-DISTRICT ANALYSIS")
    print("=" * 70)

    for cd in [3, 7]:
        print(f"\n{'='*50}")
        print(f"COUNCIL DISTRICT {cd}")
        print(f"{'='*50}")

        cd_df = df[df["council_district"] == cd]

        # Overall permit counts
        for min_s, label in [("Y", "Inside MIN"), ("N", "Outside MIN")]:
            sub = cd_df[cd_df["In MIN"] == min_s]
            pre = (sub["period"] == "Pre-MIN").sum()
            post = (sub["period"] == "Post-MIN").sum()
            chg = (post - pre) / pre * 100 if pre > 0 else 0
            print(f"  {label} all permits: {pre:,} → {post:,} ({chg:+.1f}%)")

        # Large project analysis
        large = cd_df[cd_df["number_of_units"].fillna(0) >= 10]
        print(f"\n  Large projects (10+ units):")
        for min_s, label in [("Y", "Inside MIN"), ("N", "Outside MIN")]:
            sub = large[large["In MIN"] == min_s]
            pre = (sub["period"] == "Pre-MIN").sum()
            post = (sub["period"] == "Post-MIN").sum()
            chg = (post - pre) / pre * 100 if pre > 0 else 0
            print(f"    {label}: {pre} → {post} ({chg:+.1f}%)")

        # Completed units
        completed = cd_df[cd_df["status_norm"] == "COMPLETED"]
        large_completed = completed[completed["number_of_units"].fillna(0) >= 10]
        print(f"\n  Completed large-project units:")
        for min_s, label in [("Y", "Inside MIN"), ("N", "Outside MIN")]:
            sub = large_completed[large_completed["In MIN"] == min_s]
            for period in ["Pre-MIN", "Post-MIN"]:
                psub = sub[sub["period"] == period]
                units = psub["number_of_units"].sum()
                print(f"    {label} {period}: {len(psub)} permits, {units:.0f} units")

        # Owner type
        print(f"\n  Entity/Developer activity:")
        devs = cd_df[cd_df["owner_type"] == "Entity/Developer"]
        for min_s, label in [("Y", "Inside"), ("N", "Outside")]:
            sub = devs[devs["In MIN"] == min_s]
            pre = (sub["period"] == "Pre-MIN").sum()
            post = (sub["period"] == "Post-MIN").sum()
            chg = (post - pre) / pre * 100 if pre > 0 else 0
            print(f"    {label} MIN: {pre:,} → {post:,} ({chg:+.1f}%)")

    # Generate charts
    _generate_district_charts(df)


def _generate_district_charts(df):
    """Generate quarterly trend charts for CD3 and CD7."""

    # Set up the style
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "font.size": 10,
        "axes.titlesize": 13,
        "axes.labelsize": 11,
    })

    min_date = pd.Timestamp("2022-07-18")

    for scope, scope_label in [(None, "Combined CD3+CD7"), (3, "Council District 3"), (7, "Council District 7")]:
        sub = df if scope is None else df[df["council_district"] == scope]

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(f"MIN Policy Impact — {scope_label}", fontsize=15, fontweight="bold", y=0.98)

        # Chart 1: All permits quarterly
        ax = axes[0, 0]
        for min_s, label, color in [("Y", "Inside MIN", "#C2714F"), ("N", "Outside MIN", "#5B8DB8")]:
            s = sub[sub["In MIN"] == min_s].copy()
            quarterly = s.groupby(s["permit_date"].dt.to_period("Q")).size()
            quarterly.index = quarterly.index.to_timestamp()
            ax.plot(quarterly.index, quarterly.values, color=color, label=label, linewidth=1.5)
        ax.axvline(min_date, color="red", linestyle="--", alpha=0.7, label="MIN effective")
        ax.set_title("All Permits (Quarterly)")
        ax.legend(fontsize=8)
        ax.set_ylabel("Permits")

        # Chart 2: Large projects quarterly
        ax = axes[0, 1]
        large = sub[sub["number_of_units"].fillna(0) >= 10]
        for min_s, label, color in [("Y", "Inside MIN", "#C2714F"), ("N", "Outside MIN", "#5B8DB8")]:
            s = large[large["In MIN"] == min_s].copy()
            quarterly = s.groupby(s["permit_date"].dt.to_period("Q")).size()
            quarterly.index = quarterly.index.to_timestamp()
            ax.plot(quarterly.index, quarterly.values, color=color, label=label, linewidth=1.5)
        ax.axvline(min_date, color="red", linestyle="--", alpha=0.7, label="MIN effective")
        ax.set_title("Large Projects (10+ units, Quarterly)")
        ax.legend(fontsize=8)
        ax.set_ylabel("Permits")

        # Chart 3: Completed units (cumulative)
        ax = axes[1, 0]
        completed = sub[sub["status_norm"] == "COMPLETED"]
        for min_s, label, color in [("Y", "Inside MIN", "#C2714F"), ("N", "Outside MIN", "#5B8DB8")]:
            s = completed[completed["In MIN"] == min_s].copy()
            s = s.sort_values("permit_date")
            s["cum_units"] = s["number_of_units"].fillna(0).cumsum()
            ax.plot(s["permit_date"], s["cum_units"], color=color, label=label, linewidth=1.5)
        ax.axvline(min_date, color="red", linestyle="--", alpha=0.7, label="MIN effective")
        ax.set_title("Cumulative Completed Units")
        ax.legend(fontsize=8)
        ax.set_ylabel("Units")

        # Chart 4: Unit size distribution shift
        ax = axes[1, 1]
        has_units = sub[sub["number_of_units"].notna()].copy()
        has_units["units"] = has_units["number_of_units"].astype(int)
        inside = has_units[has_units["In MIN"] == "Y"]

        bins = list(range(1, 16)) + [20, 50, 100, 500]
        bin_labels = [str(b) for b in bins[:-1]]

        for period, color, alpha in [("Pre-MIN", "#5B8DB8", 0.6), ("Post-MIN", "#C2714F", 0.6)]:
            psub = inside[inside["period"] == period]
            counts = psub["units"].clip(upper=499).value_counts().sort_index()
            # Bin into groups
            grouped = {}
            for u in range(1, 10):
                grouped[str(u)] = counts.get(u, 0)
            grouped["10-14"] = sum(counts.get(u, 0) for u in range(10, 15))
            grouped["15-49"] = sum(counts.get(u, 0) for u in range(15, 50))
            grouped["50+"] = sum(counts.get(u, 0) for u in range(50, 500))

            x = range(len(grouped))
            width = 0.35
            offset = -width/2 if period == "Pre-MIN" else width/2
            ax.bar([i + offset for i in x], grouped.values(),
                   width=width, label=period, color=color, alpha=alpha)

        ax.set_xticks(range(len(grouped)))
        ax.set_xticklabels(grouped.keys(), rotation=45, fontsize=8)
        ax.set_title("Unit Size Distribution (Inside MIN)")
        ax.legend(fontsize=8)
        ax.set_ylabel("Permits")
        ax.axvline(8.5, color="red", linestyle=":", alpha=0.5)  # 9→10 threshold line
        ax.text(8.7, ax.get_ylim()[1] * 0.9, "10-unit\nthreshold", fontsize=7, color="red")

        plt.tight_layout(rect=[0, 0, 1, 0.95])
        fname = f"min_impact_{'combined' if scope is None else f'cd{scope}'}.png"
        fig.savefig(OUTPUT_DIR / fname, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"  Saved: {fname}")


def hot_submarket_analysis(df):
    """Hot submarket differential — areas right outside MIN that absorbed development."""
    print("\n\n" + "=" * 70)
    print("HOT SUBMARKET ANALYSIS")
    print("=" * 70)

    # Define "hot" as addresses with 3+ permits total
    addr_counts = df.groupby("address_clean").size()
    hot_addrs = addr_counts[addr_counts >= 3].index

    hot = df[df["address_clean"].isin(hot_addrs)]
    not_hot = df[~df["address_clean"].isin(hot_addrs)]

    print(f"\n  Hot addresses (3+ permits): {len(hot_addrs):,}")
    print(f"  Hot permits: {len(hot):,}")
    print(f"  Non-hot permits: {len(not_hot):,}")

    print(f"\n  Hot Submarket DiD:")
    for min_s, label in [("Y", "Inside MIN"), ("N", "Outside MIN")]:
        sub = hot[hot["In MIN"] == min_s]
        pre = (sub["period"] == "Pre-MIN").sum()
        post = (sub["period"] == "Post-MIN").sum()
        chg = (post - pre) / pre * 100 if pre > 0 else 0
        print(f"    {label}: {pre:,} → {post:,} ({chg:+.1f}%)")

    # By district
    for cd in [3, 7]:
        print(f"\n  CD{cd} Hot Submarket:")
        cd_hot = hot[hot["council_district"] == cd]
        for min_s, label in [("Y", "Inside MIN"), ("N", "Outside MIN")]:
            sub = cd_hot[cd_hot["In MIN"] == min_s]
            pre = (sub["period"] == "Pre-MIN").sum()
            post = (sub["period"] == "Post-MIN").sum()
            chg = (post - pre) / pre * 100 if pre > 0 else 0
            print(f"      {label}: {pre:,} → {post:,} ({chg:+.1f}%)")

    # Neighborhoods just outside MIN — where did development shift?
    print(f"\n  Neighborhoods OUTSIDE MIN with most post-MIN growth:")
    outside_post = df[(df["In MIN"] == "N") & (df["period"] == "Post-MIN")]
    outside_pre = df[(df["In MIN"] == "N") & (df["period"] == "Pre-MIN")]

    post_nh = outside_post.groupby("census_tract").size()
    pre_nh = outside_pre.groupby("census_tract").size()

    growth = (post_nh - pre_nh.reindex(post_nh.index, fill_value=0)).sort_values(ascending=False)
    print(f"  Top 10 census tracts by permit growth (outside MIN):")
    for tract, g in growth.head(10).items():
        pre_c = pre_nh.get(tract, 0)
        post_c = post_nh.get(tract, 0)
        print(f"    Tract {tract}: {pre_c} → {post_c} (+{g})")


def lihtc_analysis(df):
    """Identify LIHTC/subsidized projects among completed permits."""
    print("\n\n" + "=" * 70)
    print("LIHTC / SUBSIDIZED PROJECT IDENTIFICATION")
    print("=" * 70)

    # Load the affordable housing reference data we have
    aff_path = Path.home() / "Projects/Housing-Transit/Affordable_Housing.csv"
    if aff_path.exists():
        aff = pd.read_csv(aff_path)
        print(f"\n  Loaded {len(aff)} affordable housing records from local file")
        print(f"  Columns: {list(aff.columns)}")
        # Try to match by address
        if "address" in [c.lower() for c in aff.columns]:
            addr_col = [c for c in aff.columns if c.lower() == "address"][0]
            aff["address_clean"] = aff[addr_col].str.strip().str.upper()
            matched = df[df["address_clean"].isin(aff["address_clean"])]
            print(f"  Matched to permits by address: {len(matched)}")

    # Also query OpenDataPhilly for affordable housing data
    print(f"\n  Querying CARTO for affordable housing projects...")
    try:
        # Check what affordable housing tables exist
        q = "SELECT * FROM affordable_housing LIMIT 1"
        resp = requests.get(CARTO_URL, params={"q": q}, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            fields = list(data.get("fields", {}).keys())
            print(f"  affordable_housing table fields: {fields}")

            # Get all affordable housing in CD3 and CD7
            q2 = ("SELECT project_name, address, program, total_units, "
                  "total_affordable_units, developer, fiscal_year_complete, "
                  "ST_X(the_geom) as lng, ST_Y(the_geom) as lat "
                  "FROM affordable_housing "
                  "WHERE fiscal_year_complete >= '2019' "
                  "ORDER BY fiscal_year_complete")
            resp2 = requests.get(CARTO_URL, params={"q": q2}, timeout=30)
            if resp2.status_code == 200:
                aff_data = resp2.json()
                aff_df = pd.DataFrame(aff_data["rows"])
                print(f"  Affordable housing projects since 2019: {len(aff_df)}")

                if len(aff_df) > 0:
                    aff_df["address_clean"] = aff_df["address"].str.strip().str.upper()

                    # Match to our permits
                    matched_permits = df.merge(
                        aff_df[["address_clean", "project_name", "program",
                                "total_units", "total_affordable_units", "developer"]],
                        on="address_clean", how="inner", suffixes=("", "_aff")
                    ).drop_duplicates(subset=["permit_number"])

                    print(f"\n  Matched affordable projects to permits: {len(matched_permits)}")

                    if len(matched_permits) > 0:
                        print(f"\n  Affordable projects INSIDE MIN:")
                        aff_inside = matched_permits[matched_permits["In MIN"] == "Y"]
                        for period in ["Pre-MIN", "Post-MIN"]:
                            psub = aff_inside[aff_inside["period"] == period]
                            large = psub[psub["number_of_units"].fillna(0) >= 10]
                            print(f"    {period}: {len(psub)} permits, {len(large)} large")
                            for _, row in large.iterrows():
                                print(f"      {row['address']}: {row['number_of_units']:.0f}u "
                                      f"({row.get('program', 'N/A')}, "
                                      f"{row['permit_status']}, "
                                      f"{row.get('project_name', 'N/A')})")

                        print(f"\n  Affordable projects OUTSIDE MIN:")
                        aff_outside = matched_permits[matched_permits["In MIN"] == "N"]
                        for period in ["Pre-MIN", "Post-MIN"]:
                            psub = aff_outside[aff_outside["period"] == period]
                            large = psub[psub["number_of_units"].fillna(0) >= 10]
                            print(f"    {period}: {len(psub)} permits, {len(large)} large")
                            for _, row in large.iterrows():
                                print(f"      {row['address']}: {row['number_of_units']:.0f}u "
                                      f"({row.get('program', 'N/A')}, "
                                      f"{row['permit_status']})")

                    # Save
                    matched_permits.to_csv(OUTPUT_DIR / "affordable_permits_matched.csv", index=False)

                    # DiD excluding affordable projects
                    print(f"\n\n  DiD EXCLUDING AFFORDABLE/SUBSIDIZED PROJECTS:")
                    aff_permit_nums = set(matched_permits["permit_number"])
                    market_rate = df[~df["permit_number"].isin(aff_permit_nums)]

                    large_mr = market_rate[market_rate["number_of_units"].fillna(0) >= 10]
                    for min_s, label in [("Y", "Inside MIN"), ("N", "Outside MIN")]:
                        sub = large_mr[large_mr["In MIN"] == min_s]
                        pre = (sub["period"] == "Pre-MIN").sum()
                        post = (sub["period"] == "Post-MIN").sum()
                        chg = (post - pre) / pre * 100 if pre > 0 else 0
                        print(f"    {label}: {pre} → {post} ({chg:+.1f}%)")

                    # Completed units market-rate only
                    mr_completed = market_rate[market_rate["status_norm"] == "COMPLETED"]
                    large_mr_completed = mr_completed[mr_completed["number_of_units"].fillna(0) >= 10]
                    print(f"\n  Market-rate completed large-project units:")
                    for min_s, label in [("Y", "Inside MIN"), ("N", "Outside MIN")]:
                        sub = large_mr_completed[large_mr_completed["In MIN"] == min_s]
                        for period in ["Pre-MIN", "Post-MIN"]:
                            psub = sub[sub["period"] == period]
                            units = psub["number_of_units"].sum()
                            print(f"    {label} {period}: {len(psub)} permits, {units:.0f} units")

        else:
            print(f"  CARTO error: {resp.status_code}")
            # Try alternate approach
            _lihtc_by_owner_heuristic(df)
    except Exception as e:
        print(f"  Error querying CARTO: {e}")
        _lihtc_by_owner_heuristic(df)


def _lihtc_by_owner_heuristic(df):
    """Fallback: identify likely subsidized projects by owner name."""
    print(f"\n  Fallback: Identifying likely subsidized projects by owner name...")

    subsidized_keywords = [
        "HOUSING AUTH", "PHA ", "HABITAT", "AFFORDABLE",
        "CDC", "COMMUNITY DEV", "HOUSING TRUST",
        "LIHTC", "TAX CREDIT", "PENNROSE", "WODA",
        "CONIFER", "JONATHAN ROSE", "MICHAELS ORG",
        "NATIONAL CHURCH", "PRESBY", "INGERMAN",
        "JOURNEY HOME", "PHILA HOUSING",
    ]

    large = df[df["number_of_units"].fillna(0) >= 10].copy()
    large["owner_upper"] = large["owner_1"].fillna("").str.upper()
    large["likely_subsidized"] = large["owner_upper"].apply(
        lambda o: any(kw in o for kw in subsidized_keywords)
    )

    print(f"\n  Likely subsidized large projects (by owner name heuristic):")
    sub_projects = large[large["likely_subsidized"]]
    print(f"    Total: {len(sub_projects)}")
    for min_s, label in [("Y", "Inside MIN"), ("N", "Outside MIN")]:
        s = sub_projects[sub_projects["In MIN"] == min_s]
        for period in ["Pre-MIN", "Post-MIN"]:
            ps = s[s["period"] == period]
            print(f"    {label} {period}: {len(ps)} permits")
            for _, row in ps.iterrows():
                print(f"      {row['address']}: {row['number_of_units']:.0f}u "
                      f"(owner: {str(row['owner_1'])[:50]}, {row['permit_status']})")


def main():
    df = load_data()
    threshold_gaming(df)
    district_analysis(df)
    hot_submarket_analysis(df)
    lihtc_analysis(df)


if __name__ == "__main__":
    main()
