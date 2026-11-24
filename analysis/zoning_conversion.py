"""
Do housing projects that get a zoning permit go on to get a building permit?
Inside /MIN versus comparable areas, before and after July 18, 2022.

Cohort   One row per parcel: the first zoning permit for new construction, an
         addition, or a combined lot relocation and new development, issued on or
         after 2020-03-16 (the City's current permit system; earlier zoning permits
         are in a different format and are left out).
Units    Zoning permits carry no unit count. Units come from, in order:
           1. BPN's project groupings for the parcel (analysis/data/bpn_parcel_project.csv,
              a local export; max_unit_count of the parcel's housing projects), if present;
           2. the largest "(N) DWELLING UNITS" style count in the zoning permit's
              approved scope of work.
         Parcels with neither are kept as "units unknown" and reported separately.
Outcome  A building permit (Building / Residential Building; new construction or
         addition/alteration) on the same parcel issued on or after the zoning permit.
         Reported as the share reaching a building permit within 12, 18 and 24 months,
         among zoning permits old enough to be observed that long.
Treated  Zoning permit point inside the /MIN boundary in force on its date.
Control  Outside /MIN, in tracts whose pre-rush sale price is within the 5th-95th
         percentile of the tracts where inside-MIN cohort projects sit
         (analysis/data/tract_prices_pre_min.csv, written by matched_control.py).

Run from the repo root:
  uv run --no-project --with shapely --with requests --with pandas --with numpy \
      python analysis/zoning_conversion.py [--refresh]
"""
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from shapely.geometry import Point, shape
from shapely.prepared import prep

HERE = Path(__file__).parent
DATA = HERE / "data"
CARTO = "https://phl.carto.com/api/v2/sql"
START = pd.Timestamp("2020-03-16", tz="UTC")
MIN = pd.Timestamp("2022-07-18", tz="UTC")
B230007 = pd.Timestamp("2023-04-25", tz="UTC")
RNG = np.random.default_rng(20261124)

WORDS = ("ONE TWO THREE FOUR FIVE SIX SEVEN EIGHT NINE TEN ELEVEN TWELVE THIRTEEN FOURTEEN FIFTEEN SIXTEEN "
         "SEVENTEEN EIGHTEEN NINETEEN TWENTY").split()
UNIT_RES = [
    re.compile(r"\(?\b(\d{1,4})\)?\s*(?:RESIDENTIAL\s+|NEW\s+)?(?:DWELLING|RESIDENTIAL|APARTMENT)\s+UNITS?", re.I),
    re.compile(r"\(?\b(\d{1,4})\)?\s*(?:DWELLINGS|APARTMENTS)\b", re.I),
    re.compile(r"\(?\b(\d{1,4})\)?\s*UNITS?\b(?!\s*(?:OF\s+)?(?:PARKING|BICYCLE|BIKE))", re.I),
    re.compile(r"\(?\b(\d{1,4})\)?\s*(?:-|\s)?FAMILY\b", re.I),
]


def parse_units(text):
    t = text.upper() if isinstance(text, str) else ""
    found = []
    for rx in UNIT_RES[:2]:
        found += [int(m) for m in rx.findall(t)]
    if not found and ("MULTI-FAMILY" in t or "MULTIFAMILY" in t or "MULTI FAMILY" in t or "HOUSEHOLD LIVING" in t):
        for rx in UNIT_RES[2:]:
            found += [int(m) for m in rx.findall(t)]
    found = [n for n in found if 0 < n < 3000]
    return max(found) if found else None


def carto(sql, tries=5):
    for a in range(tries):
        r = requests.post(CARTO, data={"q": sql}, timeout=180)
        if r.status_code == 200:
            return pd.DataFrame(r.json()["rows"])
        time.sleep(5 * (a + 1))
    r.raise_for_status()


def pull():
    zp, bp = [], []
    for y in range(2020, pd.Timestamp.now().year + 1):
        zp.append(carto(f"""
          SELECT p.permitnumber, p.address, p.opa_account_num, p.permitissuedate, p.status, p.typeofwork,
                 p.approvedscopeofwork, ST_X(p.the_geom) AS lng, ST_Y(p.the_geom) AS lat, o.census_tract, o.zoning
          FROM permits p LEFT JOIN opa_properties_public o ON o.parcel_number = p.opa_account_num
          WHERE p.permittype = 'Zoning'
            AND p.typeofwork IN ('New construction, addition, GFA change',
                                 'Combined Lot Line Relocation and New Development')
            AND p.permitissuedate >= '{y}-01-01' AND p.permitissuedate < '{y + 1}-01-01'"""))
        bp.append(carto(f"""
          SELECT opa_account_num, permitissuedate, typeofwork, numberofunits, certificateofoccupancydate
          FROM permits
          WHERE permittype IN ('Building','Residential Building')
            AND (typeofwork ILIKE '%new construction%' OR typeofwork ILIKE '%addition%')
            AND permitissuedate >= '{y}-01-01' AND permitissuedate < '{y + 1}-01-01'"""))
    return pd.concat(zp), pd.concat(bp)


def build(refresh=False):
    out = DATA / "zoning_cohort.csv"
    if out.exists() and not refresh:
        return pd.read_csv(out, parse_dates=["zp_date", "bp_date", "pulled"])
    zp, bp = pull()
    pulled = pd.Timestamp.now(tz="UTC")
    zp["zp_date"] = pd.to_datetime(zp.permitissuedate, utc=True)
    zp = zp[(zp.zp_date >= START) & zp.opa_account_num.notna() & zp.lng.notna()].copy()
    zp["opa"] = zp.opa_account_num.astype(str).str.split(".").str[0].str.zfill(9)
    zp["text_units"] = zp.approvedscopeofwork.map(parse_units)
    # one row per parcel: earliest zoning permit dates the project; unit count = largest parsed on any of them
    tu = zp.groupby("opa").text_units.max()
    zp = zp.sort_values("zp_date").drop_duplicates("opa").drop(columns="text_units").merge(tu, on="opa", how="left")

    bpn_path = DATA / "bpn_parcel_project.csv"
    if bpn_path.exists():
        b = pd.read_csv(bpn_path, usecols=["opa_number", "max_unit_count", "category", "track"], low_memory=False)
        b = b[(b.category == "development") & b.track.isin(["housing", "mixed_use"])]
        b["opa"] = b.opa_number.astype(str).str.zfill(9)
        zp = zp.merge(b.groupby("opa").max_unit_count.max().rename("bpn_units"), on="opa", how="left")
    else:
        zp["bpn_units"] = np.nan
    zp["units"] = zp.bpn_units.where(zp.bpn_units.notna(), zp.text_units)
    zp["units_source"] = np.where(zp.bpn_units.notna(), "bpn", np.where(zp.text_units.notna(), "zoning text", "unknown"))

    bp["bp_date"] = pd.to_datetime(bp.permitissuedate, utc=True)
    bp = bp[bp.opa_account_num.notna()].copy()
    bp["opa"] = bp.opa_account_num.astype(str).str.split(".").str[0].str.zfill(9)
    m = zp[["opa", "zp_date"]].merge(bp[["opa", "bp_date", "certificateofoccupancydate"]], on="opa")
    m = m[m.bp_date >= m.zp_date]
    first = m.groupby("opa").agg(bp_date=("bp_date", "min"),
                                 co=("certificateofoccupancydate", lambda s: s.notna().any()))
    zp = zp.merge(first, on="opa", how="left")
    zp["co"] = zp.co.fillna(False)

    orig = prep(shape(json.load(open(DATA / "min_boundary_2022_original.geojson"))["features"][0]["geometry"]).buffer(0))
    cur = prep(shape(json.load(open(DATA / "min_boundary_post230007.geojson"))["features"][0]["geometry"]).buffer(0))
    pts = [Point(x, y) for x, y in zip(zp.lng, zp.lat)]
    zp["in_min_current"] = [cur.contains(p) for p in pts]
    zp["in_min"] = [(cur if d >= B230007 else orig).contains(p) for p, d in zip(pts, zp.zp_date)]
    t = pd.read_csv(DATA / "tract_prices_pre_min.csv").rename(columns={"ppsf": "tract_ppsf"})
    zp["census_tract"] = pd.to_numeric(zp.census_tract, errors="coerce")
    t["census_tract"] = pd.to_numeric(t.census_tract, errors="coerce")
    zp = zp.merge(t[["census_tract", "tract_ppsf"]], on="census_tract", how="left")
    zp["pulled"] = pulled
    keep = ["permitnumber", "address", "opa", "zp_date", "status", "typeofwork", "lng", "lat", "census_tract", "zoning",
            "text_units", "bpn_units", "units", "units_source", "bp_date", "co", "in_min_current", "in_min",
            "tract_ppsf", "pulled"]
    zp[keep].to_csv(out, index=False)
    return pd.read_csv(out, parse_dates=["zp_date", "bp_date", "pulled"])


def rate_table(d, label, months=(12, 18, 24)):
    pulled = d.pulled.iloc[0]
    rows = []
    for cohort, lo, hi in [("2020-22 (before MIN)", START, MIN), ("2022-26 (under MIN)", MIN, pulled)]:
        c = d[(d.zp_date >= lo) & (d.zp_date < hi)]
        r = {"group": label, "cohort": cohort, "projects": len(c), "units": int(c.units.sum()),
             "ever_bp": round(c.bp_date.notna().mean(), 3) if len(c) else None,
             "ever_bp_units": round((c.units * c.bp_date.notna()).sum() / c.units.sum(), 3) if c.units.sum() else None}
        for mth in months:
            old = c[c.zp_date <= pulled - pd.DateOffset(months=mth)]
            hit = (old.bp_date - old.zp_date) <= pd.Timedelta(days=30.44 * mth)
            r[f"bp_{mth}m"] = round(hit.mean(), 3) if len(old) else None
            r[f"n_{mth}m"] = len(old)
        rows.append(r)
    return rows


def boot_gap(ins, ctl, mth=18, n=2000):
    """Tract bootstrap of (control - inside) share reaching a building permit within mth months, post-MIN cohort."""
    pulled = ins.pulled.iloc[0]
    def prep_(d):
        d = d[(d.zp_date >= MIN) & (d.zp_date <= pulled - pd.DateOffset(months=mth))].copy()
        d["hit"] = (d.bp_date - d.zp_date) <= pd.Timedelta(days=30.44 * mth)
        return d
    a, b = prep_(ins), prep_(ctl)
    ag, bg = dict(tuple(a.groupby("census_tract"))), dict(tuple(b.groupby("census_tract")))
    ak, bk = list(ag), list(bg)
    g = []
    for _ in range(n):
        x = pd.concat([ag[k] for k in RNG.choice(ak, len(ak))]).hit.mean()
        y = pd.concat([bg[k] for k in RNG.choice(bk, len(bk))]).hit.mean()
        g.append(y - x)
    return {"inside": round(a.hit.mean(), 3), "control": round(b.hit.mean(), 3), "n_inside": len(a), "n_control": len(b),
            "gap_ci95": [round(float(np.percentile(g, q)), 3) for q in (2.5, 97.5)]}


def main():
    d = build("--refresh" in sys.argv)
    print(f"parcels with a development zoning permit since {START.date()}: {len(d)}")
    print("unit source:", d.units_source.value_counts().to_dict())
    big = d[d.units >= 10]
    print("10+ units:", len(big), "| inside MIN:", int(big.in_min.sum()),
          "| unit source among 10+:", big.units_source.value_counts().to_dict())
    v = big[big.in_min].tract_ppsf.dropna()
    lo, hi = v.quantile(.05), v.quantile(.95)
    out = {"pulled": str(d.pulled.iloc[0]), "tables": [], "bootstrap_18m_under_MIN": {}}
    for name, df in [("10+ units", big), ("50+ units", d[d.units >= 50]), ("units unknown", d[d.units.isna()])]:
        ins = df[df.in_min]
        ctl = df[~df.in_min_current & (df.tract_ppsf >= lo) & (df.tract_ppsf <= hi)]
        for lab, g in [("inside MIN", ins), ("matched control", ctl), ("all outside MIN", df[~df.in_min_current])]:
            out["tables"] += [{"size": name, **r} for r in rate_table(g, lab)]
        if len(ins[ins.zp_date >= MIN]) >= 5:
            out["bootstrap_18m_under_MIN"][name] = boot_gap(ins, ctl)
    t = pd.DataFrame(out["tables"])
    pd.set_option("display.width", 250)
    print(t.to_string(index=False))
    print(json.dumps(out["bootstrap_18m_under_MIN"], indent=1))
    p = big[big.in_min & (big.zp_date >= MIN)].sort_values("zp_date")
    p = p.assign(months_since=((p.pulled - p.zp_date).dt.days / 30.44).round(0),
                 months_to_bp=((p.bp_date - p.zp_date).dt.days / 30.44).round(0))
    print(p[["address", "zp_date", "units", "units_source", "status", "months_since", "months_to_bp", "co"]]
          .assign(zp_date=p.zp_date.dt.date).to_string(index=False))
    (HERE / "zoning_conversion_results.json").write_text(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
