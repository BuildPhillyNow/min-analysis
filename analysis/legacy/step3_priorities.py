"""
Steps 3-6: Priority Analyses
P1: Parcel-level characteristics of development collapse
P2: Dead parcel analysis (frozen parcels)
P3: Transit-oriented analysis
P4: Owner type patterns
P5: Zoning inconsistency check
"""

import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path
import requests
import json

OUTPUT_DIR = Path(__file__).parent

# Zoning FAR lookup (Philadelphia Zoning Code §14-701)
# Conservative estimates for residential use
ZONING_FAR = {
    "RSA1": 0.5, "RSA2": 0.5, "RSA3": 0.9, "RSA4": 1.0, "RSA5": 2.0,
    "RSD1": 0.5, "RSD2": 0.5, "RSD3": 0.7,
    "RM1": 2.5, "RM2": 2.5, "RM3": 3.0, "RM4": 3.5,
    "RTA1": 2.0,
    "CMX1": 1.5, "CMX2": 2.0, "CMX2.5": 3.0, "CMX3": 3.5, "CMX4": 5.0, "CMX5": 12.0,
    "IRMX": 3.0, "ICMX": 3.0,
    "CA1": 5.0, "CA2": 12.0,
    "I1": 1.0, "I2": 2.0, "I3": 3.0,
    "SP-PO-A": 5.0, "SP-INS": 3.0,
}

# Conservative: 800 sqft per unit
SQFT_PER_UNIT = 800


def normalize_zoning(z):
    """Normalize zoning codes for FAR lookup."""
    if pd.isna(z):
        return None
    z = str(z).upper().strip().replace("-", "").replace(" ", "")
    # Handle CMX-2.5 variant
    if "CMX25" in z:
        return "CMX2.5"
    # Re-add hyphens for standard codes
    for prefix in ["RSA", "RSD", "CMX", "RM", "RTA", "CA", "SP"]:
        if z.startswith(prefix) and len(z) > len(prefix):
            return prefix + z[len(prefix):]
    return z


def estimate_max_units(total_area, zoning):
    """Estimate max units from lot area and zoning FAR."""
    if pd.isna(total_area) or pd.isna(zoning) or total_area <= 0:
        return None
    z_norm = normalize_zoning(zoning)
    far = ZONING_FAR.get(z_norm)
    if far is None:
        return None
    max_sqft = total_area * far
    return int(max_sqft / SQFT_PER_UNIT)


def priority1_parcel_characteristics():
    """P1: What do the parcels look like where development collapsed?"""
    print("\n" + "=" * 70)
    print("PRIORITY 1: PARCEL CHARACTERISTICS OF DEVELOPMENT COLLAPSE")
    print("=" * 70)

    df = pd.read_csv(OUTPUT_DIR / "min_permits_enriched.csv",
                     parse_dates=["permit_date"])

    # Compare characteristics of parcels with large permits pre-MIN vs post-MIN
    large = df[df["number_of_units"].fillna(0) >= 10].copy()

    print("\nParcel characteristics of large-project sites:")
    for period in ["Pre-MIN", "Post-MIN"]:
        for min_s in ["Y", "N"]:
            sub = large[(large["period"] == period) & (large["In MIN"] == min_s)]
            label = f"{period}, {'Inside' if min_s == 'Y' else 'Outside'} MIN"
            if len(sub) == 0:
                continue

            # Deduplicate by address for parcel-level stats
            parcels = sub.drop_duplicates(subset="address_clean")
            print(f"\n  {label} ({len(parcels)} unique parcels):")
            print(f"    Median lot size: {parcels['total_area'].median():,.0f} sqft")
            print(f"    Mean lot size:   {parcels['total_area'].mean():,.0f} sqft")
            print(f"    Median market value: ${parcels['market_value'].median():,.0f}")
            print(f"    Mean market value:   ${parcels['market_value'].mean():,.0f}")

            # Zoning
            print(f"    Top zoning codes:")
            for z, c in parcels["zoning"].value_counts().head(5).items():
                print(f"      {z}: {c} ({c/len(parcels)*100:.0f}%)")

            # Owner type
            print(f"    Owner types:")
            for o, c in parcels["owner_type"].value_counts().items():
                print(f"      {o}: {c} ({c/len(parcels)*100:.0f}%)")

    # Compare: which zoning codes STOPPED producing large projects?
    print("\n\n  Zoning codes that STOPPED producing large projects inside MIN:")
    pre_zones = large[(large["period"] == "Pre-MIN") & (large["In MIN"] == "Y")]["zoning"].value_counts()
    post_zones = large[(large["period"] == "Post-MIN") & (large["In MIN"] == "Y")]["zoning"].value_counts()

    all_zones = set(pre_zones.index) | set(post_zones.index)
    zone_comparison = []
    for z in all_zones:
        pre_c = pre_zones.get(z, 0)
        post_c = post_zones.get(z, 0)
        zone_comparison.append({"zoning": z, "pre": pre_c, "post": post_c,
                                "change": post_c - pre_c})

    zdf = pd.DataFrame(zone_comparison).sort_values("change")
    print(f"    {'Zoning':<10} {'Pre':>5} {'Post':>5} {'Change':>7}")
    for _, row in zdf.iterrows():
        print(f"    {row['zoning']:<10} {row['pre']:>5} {row['post']:>5} {row['change']:>+7}")


def priority2_dead_parcels():
    """P2: Parcels with pre-MIN activity but zero post-MIN activity."""
    print("\n" + "=" * 70)
    print("PRIORITY 2: DEAD PARCEL ANALYSIS (Frozen Development Sites)")
    print("=" * 70)

    df = pd.read_csv(OUTPUT_DIR / "min_permits_enriched.csv",
                     parse_dates=["permit_date"])

    # Find addresses with pre-MIN permits but no post-MIN permits
    pre = df[df["period"] == "Pre-MIN"].groupby(["address_clean", "In MIN"]).size().reset_index(name="pre_count")
    post = df[df["period"] == "Post-MIN"].groupby(["address_clean", "In MIN"]).size().reset_index(name="post_count")

    merged = pre.merge(post, on=["address_clean", "In MIN"], how="left")
    merged["post_count"] = merged["post_count"].fillna(0).astype(int)
    frozen = merged[merged["post_count"] == 0]

    for min_s, label in [("Y", "Inside MIN"), ("N", "Outside MIN")]:
        sub = frozen[frozen["In MIN"] == min_s]
        active = pre[pre["In MIN"] == min_s]
        rate = len(sub) / len(active) * 100

        print(f"\n  {label}:")
        print(f"    Pre-MIN active addresses: {len(active):,}")
        print(f"    Frozen (no post-MIN activity): {len(sub):,} ({rate:.1f}%)")

    # Characterize frozen parcels inside MIN
    frozen_inside = frozen[frozen["In MIN"] == "Y"]["address_clean"].tolist()

    # Get parcel data for frozen addresses
    parcel_data = df[
        (df["address_clean"].isin(frozen_inside)) &
        (df["period"] == "Pre-MIN")
    ].drop_duplicates(subset="address_clean")

    print(f"\n  Frozen parcel characteristics (inside MIN, n={len(parcel_data)}):")
    print(f"    Median lot size: {parcel_data['total_area'].median():,.0f} sqft")
    print(f"    Mean market value: ${parcel_data['market_value'].mean():,.0f}")

    # Estimate theoretical capacity
    parcel_data["max_units"] = parcel_data.apply(
        lambda r: estimate_max_units(r["total_area"], r["zoning"]), axis=1
    )
    has_capacity = parcel_data[parcel_data["max_units"].notna()]
    total_capacity = has_capacity["max_units"].sum()

    print(f"    Parcels with calculable zoning capacity: {len(has_capacity)}")
    print(f"    TOTAL THEORETICAL CAPACITY (frozen parcels): {total_capacity:,} units")

    # Zoning distribution
    print(f"\n    Zoning distribution of frozen parcels:")
    for z, c in parcel_data["zoning"].value_counts().head(10).items():
        print(f"      {z}: {c}")

    # How many had large projects?
    frozen_large = df[
        (df["address_clean"].isin(frozen_inside)) &
        (df["period"] == "Pre-MIN") &
        (df["number_of_units"].fillna(0) >= 10)
    ].drop_duplicates(subset="address_clean")

    print(f"\n    Frozen parcels that had large (10+u) pre-MIN permits: {len(frozen_large)}")
    if len(frozen_large) > 0:
        print(f"    Units in those pre-MIN large projects: {frozen_large['number_of_units'].sum():.0f}")

    # Save frozen parcels
    parcel_data.to_csv(OUTPUT_DIR / "frozen_parcels_inside_min.csv", index=False)


def priority3_transit():
    """P3: Transit-oriented analysis using geocoded parcels."""
    print("\n" + "=" * 70)
    print("PRIORITY 3: TRANSIT-ORIENTED ANALYSIS")
    print("=" * 70)

    df = pd.read_csv(OUTPUT_DIR / "min_permits_enriched.csv",
                     parse_dates=["permit_date"])

    # Filter to permits with coordinates
    has_coords = df[df["lat"].notna() & df["lng"].notna()].copy()
    print(f"  Permits with coordinates: {len(has_coords):,} / {len(df):,}")

    # Get SEPTA stations from OpenDataPhilly
    print("  Fetching SEPTA station data...")
    septa_url = "https://phl.carto.com/api/v2/sql"

    # BSL + MFL + trolley stations
    stations = []
    for table, label in [
        ("septa_rail_stations", "Regional Rail"),
        ("septa_trolley_stops", "Trolley"),
    ]:
        try:
            q = f"SELECT stop_name, ST_X(the_geom) as lng, ST_Y(the_geom) as lat FROM {table}"
            resp = requests.get(septa_url, params={"q": q}, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                for row in data.get("rows", []):
                    if row.get("lat") and row.get("lng"):
                        stations.append({
                            "name": row["stop_name"],
                            "lat": row["lat"],
                            "lng": row["lng"],
                            "type": label
                        })
                print(f"    {label}: {len(data.get('rows', []))} stations")
        except Exception as e:
            print(f"    {label} error: {e}")

    # Also try SEPTA high frequency bus stops or subway
    for table_name in ["septa_bus_stops"]:
        try:
            q = f"SELECT stop_name, ST_X(the_geom) as lng, ST_Y(the_geom) as lat FROM {table_name} LIMIT 1"
            resp = requests.get(septa_url, params={"q": q}, timeout=10)
            if resp.status_code == 200:
                print(f"    {table_name}: available")
        except:
            pass

    if not stations:
        print("  Could not fetch SEPTA stations. Using hardcoded BSL/MFL stations.")
        # Hardcode BSL + MFL stations in CD3 and CD7 areas
        stations = [
            # BSL stations in/near CD3 and CD7
            {"name": "City Hall", "lat": 39.9526, "lng": -75.1632, "type": "Subway"},
            {"name": "Walnut-Locust", "lat": 39.9478, "lng": -75.1636, "type": "Subway"},
            {"name": "Lombard-South", "lat": 39.9424, "lng": -75.1636, "type": "Subway"},
            {"name": "Ellsworth-Federal", "lat": 39.9291, "lng": -75.1653, "type": "Subway"},
            {"name": "Tasker-Morris", "lat": 39.9243, "lng": -75.1653, "type": "Subway"},
            {"name": "Snyder", "lat": 39.9206, "lng": -75.1653, "type": "Subway"},
            {"name": "Oregon", "lat": 39.9155, "lng": -75.1653, "type": "Subway"},
            # MFL stations
            {"name": "30th Street", "lat": 39.9566, "lng": -75.1820, "type": "Subway"},
            {"name": "34th Street", "lat": 39.9566, "lng": -75.1905, "type": "Subway"},
            {"name": "40th Street", "lat": 39.9564, "lng": -75.2013, "type": "Subway"},
            {"name": "46th Street", "lat": 39.9565, "lng": -75.2142, "type": "Subway"},
            {"name": "52nd Street", "lat": 39.9564, "lng": -75.2235, "type": "Subway"},
            {"name": "56th Street", "lat": 39.9564, "lng": -75.2310, "type": "Subway"},
            {"name": "60th Street", "lat": 39.9564, "lng": -75.2373, "type": "Subway"},
            {"name": "63rd Street", "lat": 39.9564, "lng": -75.2467, "type": "Subway"},
            {"name": "Girard", "lat": 39.9742, "lng": -75.1541, "type": "Subway"},
            {"name": "Berks", "lat": 39.9795, "lng": -75.1485, "type": "Subway"},
            {"name": "York-Dauphin", "lat": 39.9880, "lng": -75.1425, "type": "Subway"},
            {"name": "Huntingdon", "lat": 39.9938, "lng": -75.1382, "type": "Subway"},
            {"name": "Somerset", "lat": 39.9997, "lng": -75.1340, "type": "Subway"},
            {"name": "Allegheny", "lat": 40.0038, "lng": -75.1308, "type": "Subway"},
        ]

    stations_df = pd.DataFrame(stations)
    print(f"  Total stations for analysis: {len(stations_df)}")

    # Compute distance to nearest station for each permit
    def nearest_station_dist(lat, lng):
        """Distance in miles to nearest station (haversine approximation)."""
        if pd.isna(lat) or pd.isna(lng):
            return None
        # Simple euclidean in degree-space, convert to miles
        # At Philadelphia's latitude: 1 degree lat ≈ 69 miles, 1 degree lng ≈ 54 miles
        dlat = (stations_df["lat"] - lat) * 69
        dlng = (stations_df["lng"] - lng) * 54
        dists = np.sqrt(dlat**2 + dlng**2)
        return dists.min()

    has_coords["dist_to_station"] = has_coords.apply(
        lambda r: nearest_station_dist(r["lat"], r["lng"]), axis=1
    )

    has_coords["near_transit"] = has_coords["dist_to_station"] <= 0.25
    has_coords["transit_band"] = pd.cut(
        has_coords["dist_to_station"],
        bins=[0, 0.25, 0.5, 1.0, float("inf")],
        labels=["<0.25mi", "0.25-0.5mi", "0.5-1mi", ">1mi"]
    )

    print(f"\n  Transit proximity distribution:")
    print(has_coords["transit_band"].value_counts().sort_index().to_string())

    # DiD by transit proximity
    print(f"\n  DiD by Transit Proximity (large projects, 10+ units):")
    large = has_coords[has_coords["number_of_units"].fillna(0) >= 10]

    for band in ["<0.25mi", "0.25-0.5mi", "0.5-1mi", ">1mi"]:
        band_data = large[large["transit_band"] == band]
        for min_s, label in [("Y", "Inside"), ("N", "Outside")]:
            sub = band_data[band_data["In MIN"] == min_s]
            pre = (sub["period"] == "Pre-MIN").sum()
            post = (sub["period"] == "Post-MIN").sum()
            if pre > 0:
                chg = (post - pre) / pre * 100
                print(f"    {band:12s} {label:8s} MIN: {pre:>3} → {post:>3} ({chg:+.0f}%)")
            else:
                print(f"    {band:12s} {label:8s} MIN: {pre:>3} → {post:>3}")

    # Overall near-transit vs not
    print(f"\n  Summary: Near Transit (<0.25mi) vs Far (>0.25mi)")
    for near, near_label in [(True, "Near Transit"), (False, "Far from Transit")]:
        sub_large = large[large["near_transit"] == near]
        for min_s, label in [("Y", "Inside MIN"), ("N", "Outside MIN")]:
            sub = sub_large[sub_large["In MIN"] == min_s]
            pre = (sub["period"] == "Pre-MIN").sum()
            post = (sub["period"] == "Post-MIN").sum()
            if pre > 0:
                chg = (post - pre) / pre * 100
                print(f"    {near_label:20s} {label:12s}: {pre:>3} → {post:>3} ({chg:+.0f}%)")

    # ALL permits near transit
    print(f"\n  All permits (any size) near transit (<0.25mi):")
    near_all = has_coords[has_coords["near_transit"]]
    for min_s, label in [("Y", "Inside MIN"), ("N", "Outside MIN")]:
        sub = near_all[near_all["In MIN"] == min_s]
        pre = (sub["period"] == "Pre-MIN").sum()
        post = (sub["period"] == "Post-MIN").sum()
        if pre > 0:
            chg = (post - pre) / pre * 100
            print(f"    {label}: {pre:,} → {post:,} ({chg:+.1f}%)")


def priority4_owner_types():
    """P4: How did different owner types respond to MIN?"""
    print("\n" + "=" * 70)
    print("PRIORITY 4: OWNER TYPE PATTERNS")
    print("=" * 70)

    df = pd.read_csv(OUTPUT_DIR / "min_permits_enriched.csv",
                     parse_dates=["permit_date"])

    # DiD by owner type
    print("\n  DiD by Owner Type (all permits):")
    for otype in ["Entity/Developer", "Individual", "Nonprofit", "Public"]:
        sub = df[df["owner_type"] == otype]
        for min_s, label in [("Y", "Inside"), ("N", "Outside")]:
            s = sub[sub["In MIN"] == min_s]
            pre = (s["period"] == "Pre-MIN").sum()
            post = (s["period"] == "Post-MIN").sum()
            if pre > 0:
                chg = (post - pre) / pre * 100
                print(f"    {otype:20s} {label:8s} MIN: {pre:>5,} → {post:>5,} ({chg:+.1f}%)")

    # Large projects by owner type
    print(f"\n  Large Projects (10+ units) by Owner Type:")
    large = df[df["number_of_units"].fillna(0) >= 10]
    for otype in ["Entity/Developer", "Individual", "Nonprofit", "Public"]:
        sub = large[large["owner_type"] == otype]
        for min_s, label in [("Y", "Inside"), ("N", "Outside")]:
            s = sub[sub["In MIN"] == min_s]
            pre = (s["period"] == "Pre-MIN").sum()
            post = (s["period"] == "Post-MIN").sum()
            if pre > 0:
                chg = (post - pre) / pre * 100
                print(f"    {otype:20s} {label:8s} MIN: {pre:>3} → {post:>3} ({chg:+.0f}%)")
            elif post > 0:
                print(f"    {otype:20s} {label:8s} MIN: {pre:>3} → {post:>3} (new)")

    # Developer flight: LLC/entity activity shift
    print(f"\n  Developer Flight Analysis (Entity/Developer permits):")
    devs = df[df["owner_type"] == "Entity/Developer"]
    for period in ["Pre-MIN", "Post-MIN"]:
        sub = devs[devs["period"] == period]
        inside = (sub["In MIN"] == "Y").sum()
        outside = (sub["In MIN"] == "N").sum()
        total = inside + outside
        pct_inside = inside / total * 100 if total > 0 else 0
        print(f"    {period}: {inside:,} inside ({pct_inside:.1f}%) | "
              f"{outside:,} outside ({100-pct_inside:.1f}%)")

    # Check: same owner names appearing outside MIN post-policy
    print(f"\n  Owner Migration Check:")
    dev_permits = df[df["owner_type"] == "Entity/Developer"].copy()
    dev_permits["owner_clean"] = dev_permits["owner_1"].str.upper().str.strip()

    # Owners who had permits inside MIN pre-policy
    pre_inside_owners = set(dev_permits[
        (dev_permits["period"] == "Pre-MIN") & (dev_permits["In MIN"] == "Y")
    ]["owner_clean"].dropna().unique())

    # Of those, how many appear outside MIN post-policy?
    post_outside = dev_permits[
        (dev_permits["period"] == "Post-MIN") & (dev_permits["In MIN"] == "N")
    ]
    migrated = post_outside[post_outside["owner_clean"].isin(pre_inside_owners)]
    migrated_owners = migrated["owner_clean"].nunique()

    print(f"    Developers active inside MIN pre-policy: {len(pre_inside_owners)}")
    print(f"    Of those, active OUTSIDE MIN post-policy: {migrated_owners}")
    print(f"    Migration rate: {migrated_owners/len(pre_inside_owners)*100:.1f}%")

    if migrated_owners > 0:
        print(f"\n    Top migrated developers (by post-MIN outside permits):")
        top_migrated = migrated.groupby("owner_clean").size().nlargest(10)
        for owner, count in top_migrated.items():
            pre_count = len(dev_permits[
                (dev_permits["owner_clean"] == owner) &
                (dev_permits["period"] == "Pre-MIN") &
                (dev_permits["In MIN"] == "Y")
            ])
            print(f"      {owner[:50]}: {pre_count} inside pre → {count} outside post")


def priority5_zoning_inconsistency():
    """P5: High-density zoned parcels inside MIN that stopped producing."""
    print("\n" + "=" * 70)
    print("PRIORITY 5: ZONING INCONSISTENCY CHECK")
    print("=" * 70)

    df = pd.read_csv(OUTPUT_DIR / "min_permits_enriched.csv",
                     parse_dates=["permit_date"])

    # High-density zoning codes that should encourage large residential
    high_density_codes = ["CMX-3", "CMX-4", "CMX-5", "RM-3", "RM-4", "IRMX", "ICMX",
                          "CMX3", "CMX4", "CMX5", "RM3", "RM4", "CA-1", "CA-2", "CA1", "CA2"]

    inside_min = df[df["In MIN"] == "Y"].copy()
    inside_min["zoning_clean"] = inside_min["zoning"].str.upper().str.strip().str.replace("-", "")

    # Normalize comparison
    hd_norm = set(z.replace("-", "").upper() for z in high_density_codes)
    inside_min["is_high_density"] = inside_min["zoning_clean"].isin(hd_norm)

    hd = inside_min[inside_min["is_high_density"]]
    print(f"\n  High-density zoned parcels inside MIN: {hd['address_clean'].nunique():,} unique addresses")
    print(f"  Total permits on these parcels: {len(hd):,}")

    # Pre/post activity on high-density parcels
    print(f"\n  Activity on high-density parcels inside MIN:")
    for period in ["Pre-MIN", "Post-MIN"]:
        sub = hd[hd["period"] == period]
        large = sub[sub["number_of_units"].fillna(0) >= 10]
        print(f"    {period}: {len(sub):,} permits, {len(large)} large (10+u)")
        if sub["number_of_units"].notna().any():
            print(f"      Total known units: {sub['number_of_units'].sum():.0f}")

    # Calculate wasted capacity
    hd_parcels = hd.drop_duplicates(subset="address_clean")
    hd_parcels["max_units"] = hd_parcels.apply(
        lambda r: estimate_max_units(r["total_area"], r["zoning"]), axis=1
    )
    has_capacity = hd_parcels[hd_parcels["max_units"].notna()]

    print(f"\n  Zoning capacity on high-density MIN parcels:")
    print(f"    Parcels with calculable capacity: {len(has_capacity):,}")
    print(f"    Total theoretical capacity: {has_capacity['max_units'].sum():,} units")
    print(f"    Median per-parcel capacity: {has_capacity['max_units'].median():.0f} units")

    # Which high-density parcels went dead?
    pre_addrs = set(hd[hd["period"] == "Pre-MIN"]["address_clean"])
    post_addrs = set(hd[hd["period"] == "Post-MIN"]["address_clean"])
    dead_hd = pre_addrs - post_addrs

    dead_parcels = hd_parcels[hd_parcels["address_clean"].isin(dead_hd)]
    dead_parcels["max_units"] = dead_parcels.apply(
        lambda r: estimate_max_units(r["total_area"], r["zoning"]), axis=1
    )
    dead_has_cap = dead_parcels[dead_parcels["max_units"].notna()]

    print(f"\n  High-density parcels that went DEAD (pre-MIN activity, no post-MIN):")
    print(f"    Count: {len(dead_hd)}")
    if len(dead_has_cap) > 0:
        print(f"    Wasted zoning capacity: {dead_has_cap['max_units'].sum():,} units")

    # Show the irony: city upzoned for density, MIN blocked it
    print(f"\n  THE IRONY:")
    for z in ["CMX3", "CMX4", "RM1", "IRMX"]:
        z_sub = inside_min[inside_min["zoning_clean"] == z]
        pre = (z_sub["period"] == "Pre-MIN").sum()
        post = (z_sub["period"] == "Post-MIN").sum()
        large_pre = z_sub[(z_sub["period"] == "Pre-MIN") & (z_sub["number_of_units"].fillna(0) >= 10)].shape[0]
        large_post = z_sub[(z_sub["period"] == "Post-MIN") & (z_sub["number_of_units"].fillna(0) >= 10)].shape[0]
        if pre > 0:
            print(f"    {z}: {pre} → {post} permits ({(post-pre)/pre*100:+.0f}%), "
                  f"large: {large_pre} → {large_post}")


def main():
    priority1_parcel_characteristics()
    priority2_dead_parcels()
    priority3_transit()
    priority4_owner_types()
    priority5_zoning_inconsistency()


if __name__ == "__main__":
    main()
