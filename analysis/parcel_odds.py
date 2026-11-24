"""
Parcel-level test: is a site that can hold 10+ units less likely to get a 10+ unit
project under MIN than a similar site outside it?

Unit      A parcel whose base zoning allows 10 or more homes by right
          (BPN zoning engine: zoning_max_units_base >= 10), privately owned.
Outcome   Whether a 10+ unit housing project (analysis/data/project_starts_cohort.csv)
          started on the parcel in the period. Projects are placed on parcels by
          location, not account number, because redeveloped lots get new accounts.
Periods   baseline 2016-07-18 .. 2020-07-17; post 2022-07-18 .. 2026-07-17 (four years each).
Treated   Parcel inside the original 2022 /MIN boundary. Parcels in the 54th-63rd
          Street corridor (added April 2023) are left out.
Model     Logit on the stacked two-period panel:
            start ~ MIN x post + zoning group x post + log lot area + log allowed units
                    + log tract sale price x post + near rail + Center City
          Standard errors clustered by census tract. The MIN x post odds ratio is the
          estimate: below 1 means MIN sites became less likely to be developed than
          similar sites elsewhere.
          Run citywide, in the price-matched tracts, and within 1,500 / 2,500 ft of
          the MIN boundary.

Inputs    BPN parcel cache (path as argument; not public), project_starts_cohort.csv,
          tract_prices_pre_min.csv. Only the model results are written to the repo;
          parcel-level zoning capacity is BPN's and is not copied here.

Run from the repo root:
  uv run --no-project --with pyarrow --with pandas --with numpy --with shapely --with statsmodels \
      python analysis/parcel_odds.py /path/to/phila_pwd_parcels.parquet
"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import shapely
import statsmodels.formula.api as smf
from shapely.affinity import scale
from shapely.geometry import shape

HERE = Path(__file__).parent
DATA = HERE / "data"
BASE0, RUSH0 = pd.Timestamp("2016-07-18"), pd.Timestamp("2020-07-18")
MIN, END = pd.Timestamp("2022-07-18"), pd.Timestamp("2026-07-18")
FT_LAT, FT_LNG = 364_000.0, 279_000.0
warnings.filterwarnings("ignore")


def geom(name):
    return shape(json.load(open(DATA / name))["features"][0]["geometry"]).buffer(0)


def zgroup(z):
    z = (z or "").upper().replace("-", "")
    if z in ("CMX4", "CMX5"):
        return "CMX-4/5"
    if z == "CMX3":
        return "CMX-3"
    if z in ("CMX1", "CMX2", "CMX2.5"):
        return "CMX-1/2/2.5"
    if z == "RM1":
        return "RM-1"
    if z.startswith("RM"):
        return "RM-2+/RMX"
    if z in ("IRMX", "ICMX"):
        return "IRMX/ICMX"
    return "other"


def main():
    parcels_path = sys.argv[1]
    cols = ["geometry", "parcel_number", "zoning_base_district", "total_area", "zoning_max_units_base", "census_tract",
            "council_district", "publicly_owned", "tod_rail", "in_core_cc", "in_greater_cc"]
    p = pd.read_parquet(parcels_path, columns=cols)
    n_all = len(p)
    p = p[(p.zoning_max_units_base >= 10) & (p.publicly_owned != "Yes") & (p.total_area > 0)].copy()
    g = shapely.from_wkb(p.geometry.values)
    p["geom"] = g
    cen = shapely.centroid(g)
    p["lng"], p["lat"] = shapely.get_x(cen), shapely.get_y(cen)
    orig, cur, corr = geom("min_boundary_2022_original.geojson"), geom("min_boundary_post230007.geojson"), geom("min_corridor_230007.geojson")
    shapely.prepare(orig); shapely.prepare(cur); shapely.prepare(corr)
    p["in_min"] = shapely.contains(orig, cen)
    p["in_cur"] = shapely.contains(cur, cen)
    p = p[~(shapely.contains(corr, cen))].copy()
    b = scale(cur.boundary, xfact=FT_LNG, yfact=FT_LAT, origin=(0, 0))
    p["dist_ft"] = shapely.distance(b, shapely.points(p.lng.values * FT_LNG, p.lat.values * FT_LAT))
    t = pd.read_csv(DATA / "tract_prices_pre_min.csv").rename(columns={"ppsf": "tract_ppsf"})
    t["census_tract"] = pd.to_numeric(t.census_tract, errors="coerce")
    p["census_tract"] = pd.to_numeric(p.census_tract, errors="coerce")
    p = p.merge(t[["census_tract", "tract_ppsf"]], on="census_tract", how="left").dropna(subset=["tract_ppsf", "census_tract"])
    p["zg"] = p.zoning_base_district.map(zgroup)
    p["rail"] = (p.tod_rail == "Yes").astype(int)
    p["cc"] = (p.in_greater_cc.astype(str).str.lower().isin(["true", "yes", "1", "1.0"])).astype(int)
    p["l_area"], p["l_units"], p["l_price"] = np.log(p.total_area), np.log(p.zoning_max_units_base), np.log(p.tract_ppsf)
    p = p.reset_index(drop=True)

    # place project starts on parcels by location
    c = pd.read_csv(DATA / "project_starts_cohort.csv", parse_dates=["start"])
    c = c[((c.start >= BASE0) & (c.start < RUSH0)) | ((c.start >= MIN) & (c.start < END))].copy()
    c["post"] = (c.start >= MIN).astype(int)
    tree = shapely.STRtree(p.geom.values)
    pts = shapely.points(c.lng.values, c.lat.values)
    idx = tree.query(pts, predicate="within")
    hit = pd.DataFrame({"proj": idx[0], "parcel": idx[1]}).drop_duplicates("proj")
    c = c.reset_index(drop=True)
    c["parcel"] = hit.set_index("proj").parcel.reindex(c.index)
    placed = c.parcel.notna()
    cap = {"projects_in_periods": int(len(c)), "on_a_10plus_capacity_private_parcel": int(placed.sum()),
           "inside_min_share_placed": round(float(c[c.in_min_original].parcel.notna().mean()), 3),
           "outside_share_placed": round(float(c[~c.in_min_current].parcel.notna().mean()), 3),
           "placed_by_period_inside": c[c.in_min_original].groupby("post").parcel.apply(lambda s: round(float(s.notna().mean()), 3)).to_dict(),
           "placed_by_period_outside": c[~c.in_min_current].groupby("post").parcel.apply(lambda s: round(float(s.notna().mean()), 3)).to_dict()}

    rows = []
    for post in (0, 1):
        y = np.zeros(len(p), dtype=int)
        y[c[placed & (c.post == post)].parcel.astype(int).values] = 1
        rows.append(p[["census_tract", "in_min", "in_cur", "zg", "rail", "cc", "l_area", "l_units", "l_price", "dist_ft", "tract_ppsf"]]
                    .assign(post=post, y=y))
    d = pd.concat(rows, ignore_index=True)
    d["min"] = d.in_min.astype(int)
    d = d[d.in_min | ~d.in_cur]

    v = p[p.in_min].tract_ppsf
    samples = {
        "citywide": d,
        "price-matched tracts (5-95 band)": d[(d.tract_ppsf >= v.quantile(.05)) & (d.tract_ppsf <= v.quantile(.95))],
        "within 2,500 ft of the MIN boundary": d[d.dist_ft <= 2500],
        "within 1,500 ft of the MIN boundary": d[d.dist_ft <= 1500],
    }
    out = {"parcels_citywide": int(n_all), "sites_with_10plus_capacity": int(len(p)), "sites_inside_min": int(p.in_min.sum()),
           "project_placement": cap, "models": []}
    print(json.dumps({k: out[k] for k in ("sites_with_10plus_capacity", "sites_inside_min", "project_placement")}, indent=1))
    for name, s in samples.items():
        raw = s.groupby(["min", "post"]).y.agg(["sum", "size"])
        rate = (raw["sum"] / raw["size"] * 1000).round(2)
        row = {"sample": name, "sites": int(len(s) / 2), "sites_inside": int(s[(s.post == 0)]["min"].sum()),
               "starts": {f"min{m}_post{q}": int(raw["sum"].get((m, q), 0)) for m in (0, 1) for q in (0, 1)},
               "starts_per_1000_sites": {f"min{m}_post{q}": float(rate.get((m, q), np.nan)) for m in (0, 1) for q in (0, 1)}}
        for label, f in [("no controls", "y ~ min * post"),
                         ("with controls", "y ~ min * post + C(zg) * post + l_area + l_units + l_price * post + rail + cc")]:
            try:
                m = smf.logit(f, s).fit(disp=0, maxiter=200, cov_type="cluster", cov_kwds={"groups": s.census_tract.values})
                b_, se = m.params["min:post"], m.bse["min:post"]
                row[label] = {"odds_ratio": round(float(np.exp(b_)), 2),
                              "ci95": [round(float(np.exp(b_ - 1.96 * se)), 2), round(float(np.exp(b_ + 1.96 * se)), 2)],
                              "p": round(float(m.pvalues["min:post"]), 3),
                              "post_odds_ratio_outside": round(float(np.exp(m.params["post"])), 2)}
            except Exception as e:  # separation in a thin sample
                row[label] = {"error": str(e)[:80]}
        out["models"].append(row)
        print(json.dumps(row))
    (HERE / "parcel_odds_results.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
