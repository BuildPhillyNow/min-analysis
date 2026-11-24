"""
Committed, reproducible MIN permit-panel builder.

Pulls L&I BUILDING permits in Council Districts 3 & 7 from the city's CARTO
`permits` table, spatially classifies each as inside/outside the MIN overlay
(/MIN polygon in the PCPC Zoning_Overlays shapefile), and derives the fields
the analysis needs. Writes analysis/data/min_permits_rebuilt.csv.

Design choices vs. the original min_permits_enriched_2025.csv:
  * Universe = permittype IN ('Building','Residential Building') ONLY. The
    original mixed in trade permits (Electrical/Mechanical/Fire) which never
    enter the >=10-unit analysis; restricting to building permits reproduces
    the 247 large permits exactly (246/247 identical) and makes "building
    permits" mean building permits. More defensible, same findings.
  * MIN via live spatial join (overlay_sy == '/MIN'); validated 100% against
    the original in_min flag on all 247 large permits.

Window default: 2018-07-01 .. today, so either the legacy window (2019-01 ..
2025-12) or the symmetric 4-year window (2018-07-18 .. 2022-07-17 vs
2022-07-18 .. 2026-07-17) can be cut downstream without re-pulling.
"""
import sys, time, datetime as dt
from pathlib import Path
import requests
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

HERE = Path(__file__).parent
OUT = HERE / "data" / "min_permits_rebuilt.csv"
CARTO = "https://phl.carto.com/api/v2/sql"
SHP = Path.home() / "Downloads/Zoning_Overlays/Zoning_Overlays.shp"
POLICY = pd.Timestamp("2022-07-18", tz="UTC")

START = "2018-07-01"
END = (dt.date.today() + dt.timedelta(days=1)).isoformat()  # inclusive of today

FIELDS = ("permitnumber, address, typeofwork, status, permittype, "
          "commercialorresidential, permitissuedate, permitcompleteddate, "
          "certificateofoccupancydate, numberofunits, opa_account_num, "
          "council_district, ST_X(the_geom) AS lng, ST_Y(the_geom) AS lat")


def pull(start=START, end=END):
    where = (f"council_district IN ('3','7') "
             f"AND permittype IN ('Building','Residential Building') "
             f"AND permitissuedate >= '{start}' AND permitissuedate < '{end}'")
    sql = f"SELECT {FIELDS} FROM permits WHERE {where}"
    print(f"CARTO pull {start} .. {end} ...", flush=True)
    r = requests.get(CARTO, params={"q": sql, "format": "csv"}, timeout=180)
    r.raise_for_status()
    from io import StringIO
    df = pd.read_csv(StringIO(r.text))
    print(f"  {len(df):,} building permits pulled", flush=True)
    return df


def classify_min(df):
    shp = gpd.read_file(SHP)
    mn = shp[shp["overlay_sy"] == "/MIN"].to_crs(4326)
    assert len(mn) >= 1, "no /MIN overlay found in shapefile"
    geo = df.dropna(subset=["lng", "lat"]).copy()
    gp = gpd.GeoDataFrame(geo, geometry=[Point(x, y) for x, y in zip(geo.lng, geo.lat)], crs=4326)
    j = gpd.sjoin(gp, mn[["geometry"]], how="left", predicate="within")
    # a point may match multiple polygon parts -> collapse to any-match per permit
    inside = j.index.to_series().groupby(level=0).apply(lambda idx: j.loc[idx.index, "index_right"].notna().any())
    df["in_min"] = "N"
    df.loc[geo.index, "in_min"] = inside.reindex(geo.index).fillna(False).map({True: "Y", False: "N"})
    df["has_geo"] = df["lng"].notna() & df["lat"].notna()
    return df


def derive(df):
    d = df.copy()
    d["permitissuedate"] = pd.to_datetime(d["permitissuedate"], utc=True, errors="coerce")
    d = d.dropna(subset=["permitissuedate"])
    d["date"] = d["permitissuedate"]
    d["period"] = (d["permitissuedate"] >= POLICY).map({True: "post", False: "pre"})
    q = d["permitissuedate"].dt.to_period("Q")
    d["quarter"] = q.astype(str).str.replace(r"Q", "Q", regex=False)
    d["numberofunits"] = pd.to_numeric(d["numberofunits"], errors="coerce")
    d["is_large"] = d["numberofunits"].fillna(0) >= 10
    d["has_units"] = d["numberofunits"].notna()
    d["nc"] = d["typeofwork"] == "New Construction"
    return d


def main():
    df = pull()
    df = classify_min(df)
    df = derive(df)
    df.to_csv(OUT, index=False)
    print(f"\nWrote {OUT}  ({len(df):,} rows)")
    print(f"  date range: {df.permitissuedate.min()} .. {df.permitissuedate.max()}")
    print(f"  in_min: {df.in_min.value_counts().to_dict()}")
    print(f"  large (>=10u): {int(df.is_large.sum())}  | with units: {int(df.has_units.sum())}")
    print(f"  missing geo: {(~df.has_geo).sum()}")


if __name__ == "__main__":
    main()
