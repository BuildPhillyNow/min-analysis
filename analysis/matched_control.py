"""
Matched-control estimate of MIN's effect on large-project housing permits.
Reproducible from public City data; nothing here depends on files outside the repo.

Question: after July 18, 2022, did permitted units in 10+ unit projects fall more
inside the /MIN overlay than in comparable strong-market areas elsewhere in the city?

Design
  Universe   Building permits (permittype Building / Residential Building) with
             10+ units, citywide, 2016-07-18 .. 2026-07-17. MIN covers any
             development of ten or more dwelling units (section 14-533(2)), so
             conversions count alongside new construction.
  Periods    Baseline 2016-07-18 .. 2020-07-17 (four years before the rush);
             rush 2020-07-18 .. 2022-07-17 (the 10-year abatement was due to change
             at the end of 2020, then at the end of 2021, and permits bunched ahead
             of both deadlines); post 2022-07-18 .. 2026-07-17.
             The specification grid uses the symmetric window 2018-07-18 .. 2026-07-17.
  Systems    The City changed permit systems in March 2020. Before then, new
             construction is recorded as permittype BP_NEWCNST; both are pulled.
             The old system almost never recorded unit counts on alterations, so
             conversions before 2020 are undercounted and any before/after
             comparison of conversions that reaches back past 2020 is unreliable.
  Unit       One project per parcel (OPA account): the largest-unit permit.
  Treated    Permit point inside the /MIN boundary in force on the permit date
             (original 2022 boundary; plus the 54th-63rd St corridor from 2023-04-25).
  Market     PRE-MIN market strength of the project's census tract: median sale
             price per sq ft of residential sales recorded 2016-07-18 .. 2020-07-17
             (OPA last-sale records), before both MIN and the abatement rush. Measured before treatment and at tract level,
             so a parcel's own redevelopment cannot move it.
  Control    Non-MIN projects in tracts whose pre-MIN price falls in the range of
             the tracts where inside-MIN projects sit (several band widths), plus a
             reweighted version that matches the inside distribution bin by bin.
  Estimate   Difference-in-differences on units:
               DiD = (inside % change) - (control % change)
               deterred units = inside pre-period units x DiD

Every specification is run and written out; nothing is selected.

Run from the repo root:
  uv run --no-project --with shapely --with requests --with pandas --with numpy \
      python analysis/matched_control.py [--refresh]
Writes analysis/data/matched_projects.csv, analysis/data/tract_prices_pre_min.csv and
analysis/matched_control_results.json.
"""
import io
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from shapely.geometry import Point, shape
from shapely.ops import unary_union
from shapely.prepared import prep

HERE = Path(__file__).parent
DATA = HERE / "data"
CARTO = "https://phl.carto.com/api/v2/sql"
ARC = "https://services.arcgis.com/fLeGjb7u4uXqeF9q/arcgis/rest/services"
MIN = pd.Timestamp("2022-07-18", tz="UTC")
W0 = pd.Timestamp("2016-07-18", tz="UTC")      # pull start: six years before
GRID0 = pd.Timestamp("2018-07-18", tz="UTC")   # symmetric four-year window used by the grid
RUSH0 = pd.Timestamp("2020-07-18", tz="UTC")   # start of the two tax-abatement deadline years
W1 = pd.Timestamp("2026-07-18", tz="UTC")
B230007 = pd.Timestamp("2023-04-25", tz="UTC")
RNG = np.random.default_rng(20261124)

SUBSIDIZED = ["HOUSING AUTH", "HABITAT", "PENNROSE", "WODA", "INGERMAN", "CONIFER", "JONATHAN ROSE", "MICHAELS",
              "HACE", "PROJECT HOME", "NEWCOURTLAND", "NEW COURTLAND", "IMPACT SERV", "MISSION FIRST", "AFFORDABLE",
              "SENIOR HOUSING", "LAND TRUST", "COMMUNITY JUSTICE", "INTERCULTURAL", "CDC", "COMMUNITY DEV",
              "HOUSING TRUST", "REDEVELOPMENT", "TURNER COURT", "PEOPLE'S EMERGENCY", "EMERGENCY CENTER", "ESPERANZA",
              "GAUDENZIA", "LIBERTY RESOURCES", "STONEWATER", "MOUNT VERNON MANOR", "BEECH", "DIGNITY", "ELDERS PLACE",
              "WOMEN'S COMMUNITY", "CATCH", "SUSQUEHANNA NET", "OPPORTUNITIES SERV", "TRIANGLE SENIOR",
              "VOLUNTEERS OF AMERICA", "NORRIS SQUARE", "NUEVA"]
INSTITUTION = ["TRUSTEES OF", "UNIVERSITY OF PENN", "DREXEL UNIV", "TEMPLE UNIV", "THOMAS JEFFERSON UNIV",
               "UNIVERSITY CITY SCIENCE"]


def carto_csv(sql):
    r = requests.post(CARTO, data={"q": sql, "format": "csv"}, timeout=300)
    r.raise_for_status()
    return pd.read_csv(io.StringIO(r.text))


def pull_projects():
    sql = f"""
      SELECT p.permitnumber, p.address, p.permittype, p.typeofwork, p.status, p.permitissuedate,
             p.certificateofoccupancydate, p.numberofunits, p.opa_account_num, p.council_district,
             ST_X(p.the_geom) AS lng, ST_Y(p.the_geom) AS lat,
             o.census_tract, o.zoning, o.owner_1
      FROM permits p
      LEFT JOIN opa_properties_public o ON o.parcel_number = p.opa_account_num
      WHERE p.permittype IN ('Building','Residential Building','BP_NEWCNST','BP_ADDITON','BP_ALTER')
        AND p.numberofunits >= 10
        AND p.permitissuedate >= '{W0.date()}' AND p.permitissuedate < '{W1.date()}'"""
    d = carto_csv(sql)
    d["permitissuedate"] = pd.to_datetime(d.permitissuedate, utc=True)
    d = d.dropna(subset=["lng", "lat", "opa_account_num"])
    d["units"] = d.numberofunits.astype(int)
    # one project per parcel: the largest-unit building permit
    d = d.sort_values(["units", "permitissuedate"], ascending=[False, True]).drop_duplicates("opa_account_num")
    d["nc"] = d.typeofwork.fillna("").str.contains("New Construction", case=False) | (d.permittype == "BP_NEWCNST")
    o = " " + d.owner_1.fillna("").str.upper() + " "
    d["cls"] = np.where(o.apply(lambda s: any(k in s for k in INSTITUTION)), "institutional",
                        np.where(o.apply(lambda s: any(k in s for k in SUBSIDIZED)), "subsidized", "market-rate"))
    return d


def pull_tract_prices():
    sql = f"""
      SELECT census_tract,
             percentile_cont(0.5) WITHIN GROUP (ORDER BY sale_price / total_livable_area) AS ppsf,
             count(*) AS n
      FROM opa_properties_public
      WHERE sale_date >= '{W0.date()}' AND sale_date < '{RUSH0.date()}'
        AND sale_price BETWEEN 20000 AND 5000000
        AND total_livable_area > 300
        AND category_code_description IN ('SINGLE FAMILY','MULTI FAMILY','MIXED USE')
      GROUP BY 1"""
    return carto_csv(sql)


def min_boundaries():
    def local(name):
        return shape(json.load(open(DATA / name))["features"][0]["geometry"]).buffer(0)
    r = requests.get(f"{ARC}/Zoning_Overlays/FeatureServer/0/query",
                     params={"where": "overlay_symbol='/MIN'", "outFields": "overlay_symbol", "outSR": 4326,
                             "f": "geojson"}, timeout=120)
    r.raise_for_status()
    city = unary_union([shape(f["geometry"]).buffer(0) for f in r.json()["features"]])
    return prep(local("min_boundary_2022_original.geojson")), prep(city)


def build(refresh=False):
    pj, tp = DATA / "matched_projects.csv", DATA / "tract_prices_pre_min.csv"
    if pj.exists() and tp.exists() and not refresh:
        return pd.read_csv(pj, parse_dates=["permitissuedate"]), pd.read_csv(tp)
    d, t = pull_projects(), pull_tract_prices()
    orig, cur = min_boundaries()
    d["in_min_current"] = [cur.contains(Point(x, y)) for x, y in zip(d.lng, d.lat)]
    d["in_min"] = [(cur if when >= B230007 else orig).contains(Point(x, y))
                   for x, y, when in zip(d.lng, d.lat, d.permitissuedate)]
    # pre-period projects are "inside" if the parcel is in the overlay as first enacted
    t = t[t.n >= 10]
    d = d.merge(t.rename(columns={"ppsf": "tract_ppsf", "n": "tract_sales"}), on="census_tract", how="left")
    d.to_csv(pj, index=False)
    t.to_csv(tp, index=False)
    return d, t


# ---------- estimation ----------

def did(ins, ctl, w=None):
    """Units DiD. w = optional weights for control rows."""
    w = np.ones(len(ctl)) if w is None else w
    ip = ins.loc[ins.permitissuedate < MIN, "units"].sum()
    io = ins.loc[ins.permitissuedate >= MIN, "units"].sum()
    cpre = (ctl.permitissuedate < MIN).values
    cp = (ctl.units.values * w)[cpre].sum()
    co = (ctl.units.values * w)[~cpre].sum()
    if ip == 0 or cp == 0:
        return None
    ichg, cchg = io / ip - 1, co / cp - 1
    return {"inside_pre": int(ip), "inside_post": int(io), "inside_chg": round(ichg * 100, 1),
            "control_pre": int(round(cp)), "control_post": int(round(co)), "control_chg": round(cchg * 100, 1),
            "did_pp": round((cchg - ichg) * 100, 1), "deterred": int(round(ip * (cchg - ichg))),
            "n_inside": [int((ins.permitissuedate < MIN).sum()), int((ins.permitissuedate >= MIN).sum())],
            "n_control": [int(cpre.sum()), int((~cpre).sum())]}


def control_for(ins, out, match):
    """Return (control rows, weights)."""
    v = ins.tract_ppsf.dropna()
    if match == "none":
        return out, None
    if match.startswith("band"):
        lo, hi = {"band_full": (0, 1), "band_5_95": (.05, .95), "band_10_90": (.1, .9), "band_25_75": (.25, .75)}[match]
        c = out[(out.tract_ppsf >= v.quantile(lo)) & (out.tract_ppsf <= v.quantile(hi))]
        return c, None
    if match == "reweight_quintile":
        # bins = quintiles of the inside projects' tract price; weight control so each
        # bin carries the same share of pre-period projects as inside MIN
        edges = np.unique(v.quantile([0, .2, .4, .6, .8, 1]).values)
        c = out[(out.tract_ppsf >= edges[0]) & (out.tract_ppsf <= edges[-1])].copy()
        ib = pd.cut(ins.tract_ppsf, edges, include_lowest=True)
        cb = pd.cut(c.tract_ppsf, edges, include_lowest=True)
        ish = ib[ins.permitissuedate < MIN].value_counts(normalize=True)
        csh = cb[c.permitissuedate < MIN].value_counts(normalize=True)
        w = cb.map(lambda b: ish.get(b, 0) / csh.get(b, np.nan) if csh.get(b, 0) > 0 else 0).astype(float).values
        return c, w
    raise ValueError(match)


def subset(d, kind, lo, trim, cls):
    x = d[d.units >= lo]
    if kind == "new_construction":
        x = x[x.nc]
    if trim:
        x = x[x.units <= trim]
    if cls == "market_rate":
        x = x[x.cls == "market-rate"]
    return x[x.tract_ppsf.notna()]


def run_grid(d):
    rows = []
    for kind, lo, trim, cls, match in itertools.product(
            ["new_construction", "all_types"], [10, 20, 50], [None, 400, 250, 150], ["all", "market_rate"],
            ["none", "band_full", "band_5_95", "band_10_90", "band_25_75", "reweight_quintile"]):
        x = subset(d, kind, lo, trim, cls)
        ins, out = x[x.in_min], x[~x.in_min_current]
        c, w = control_for(ins, out, match)
        r = did(ins, c, w)
        if r:
            rows.append({"type": kind, "min_units": lo, "trim": trim, "cls": cls, "match": match, **r})
    return pd.DataFrame(rows)


def tract_bootstrap(d, kind, lo, trim, cls, match, n=2000):
    x = subset(d, kind, lo, trim, cls)
    ins, out = x[x.in_min], x[~x.in_min_current]
    c, w = control_for(ins, out, match)
    c = c.assign(_w=1.0 if w is None else w)
    it, ct = list(ins.census_tract.unique()), list(c.census_tract.unique())
    ig, cg = dict(tuple(ins.groupby("census_tract"))), dict(tuple(c.groupby("census_tract")))
    est = []
    for _ in range(n):
        bi = pd.concat([ig[t] for t in RNG.choice(it, len(it))])
        bc = pd.concat([cg[t] for t in RNG.choice(ct, len(ct))])
        r = did(bi, bc, bc._w.values)
        if r:
            est.append((r["did_pp"], r["deterred"]))
    e = np.array(est)
    return {"did_pp_ci": [round(float(np.percentile(e[:, 0], q)), 1) for q in (2.5, 50, 97.5)],
            "deterred_ci": [int(np.percentile(e[:, 1], q)) for q in (2.5, 50, 97.5)],
            "share_positive": round(float((e[:, 0] > 0).mean()), 3)}


def yearly(d, kind, lo, trim, cls, match):
    """Units by policy year (year 0 starts 2022-07-18), inside vs matched control."""
    x = subset(d, kind, lo, trim, cls)
    ins, out = x[x.in_min], x[~x.in_min_current]
    c, w = control_for(ins, out, match)
    yr = lambda s: np.floor((s - MIN).dt.days / 365.25).astype(int)
    a = ins.groupby(yr(ins.permitissuedate)).units.sum()
    cw = c.units.values * (1 if w is None else w)
    b = pd.Series(cw, index=yr(c.permitissuedate).values).groupby(level=0).sum()
    return {int(k): [int(a.get(k, 0)), int(round(b.get(k, 0)))] for k in range(-4, 4)}


def placebo(d, kind, lo, trim, cls, match):
    """Fake effective date 2020-07-18 using pre-MIN data only (two 2-year windows)."""
    x = subset(d, kind, lo, trim, cls)
    x = x[x.permitissuedate < MIN]
    fake = pd.Timestamp("2020-07-18", tz="UTC")
    ins, out = x[x.in_min_current], x[~x.in_min_current]
    c, w = control_for(ins.assign(permitissuedate=ins.permitissuedate), out, match)
    def chg(df, wt=None):
        u = df.units.values * (1 if wt is None else wt)
        pre = (df.permitissuedate < fake).values
        return u[~pre].sum() / u[pre].sum() - 1
    return round((chg(c, w) - chg(ins)) * 100, 1)


def leave_one_out(d, kind, lo, trim, cls, match, k=6):
    x = subset(d, kind, lo, trim, cls)
    out = []
    for _, row in x.sort_values("units", ascending=False).head(k).iterrows():
        y = x[x.opa_account_num != row.opa_account_num]
        ins, o = y[y.in_min], y[~y.in_min_current]
        c, w = control_for(ins, o, match)
        r = did(ins, c, w)
        out.append({"dropped": f"{row.address} ({row.units} units, {'inside' if row.in_min_current else 'control'}, "
                               f"{'post' if row.permitissuedate >= MIN else 'pre'})",
                    "did_pp": r["did_pp"], "deterred": r["deterred"]})
    return out


def periods_table(d, n_boot=2000):
    """Annualized units by period, inside MIN vs matched control, by project type.
    Gap = control change minus inside change, baseline -> post. CI by tract bootstrap."""
    def per(s):
        return np.where(s < RUSH0, "baseline", np.where(s < MIN, "rush", "post"))
    years = {"baseline": 4.0, "rush": 2.0, "post": 4.0}

    def rates(df, w=None):
        u = df.units.values * (1.0 if w is None else w)
        g = pd.Series(u, index=per(df.permitissuedate)).groupby(level=0).sum()
        return {k: g.get(k, 0.0) / years[k] for k in years}

    def gap(ins, c, w):
        a, b = rates(ins), rates(c, w)
        if a["baseline"] == 0 or b["baseline"] == 0:
            return None
        ichg, cchg = a["post"] / a["baseline"] - 1, b["post"] / b["baseline"] - 1
        return a, b, ichg, cchg, (cchg - ichg), a["baseline"] * (cchg - ichg) * years["post"]

    out = []
    for kind, mask in [("new_construction", d.nc), ("conversion", ~d.nc), ("all_types", d.nc | ~d.nc)]:
        for trim in [None, 400]:
            for match in ["none", "band_5_95", "band_10_90", "reweight_quintile"]:
                x = d[mask & d.tract_ppsf.notna()]
                if trim:
                    x = x[x.units <= trim]
                ins, o = x[x.in_min], x[~x.in_min_current]
                c, w = control_for(ins, o, match)
                r = gap(ins, c, w)
                if not r:
                    continue
                a, b, ichg, cchg, g, det = r
                c2 = c.assign(_w=1.0 if w is None else w)
                it, ct = list(ins.census_tract.unique()), list(c2.census_tract.unique())
                ig, cg = dict(tuple(ins.groupby("census_tract"))), dict(tuple(c2.groupby("census_tract")))
                bs = []
                for _ in range(n_boot):
                    bi = pd.concat([ig[t] for t in RNG.choice(it, len(it))])
                    bc = pd.concat([cg[t] for t in RNG.choice(ct, len(ct))])
                    rr = gap(bi, bc, bc._w.values)
                    if rr:
                        bs.append((rr[4], rr[5]))
                bs = np.array(bs)
                out.append({
                    "type": kind, "trim": trim, "match": match,
                    "inside_per_yr": {k: int(round(v)) for k, v in a.items()},
                    "control_per_yr": {k: int(round(v)) for k, v in b.items()},
                    "inside_chg_pct": round(ichg * 100, 1), "control_chg_pct": round(cchg * 100, 1),
                    "gap_pp": round(g * 100, 1), "deterred_units": int(round(det)),
                    "gap_pp_ci95": [round(float(np.percentile(bs[:, 0], q)) * 100, 1) for q in (2.5, 97.5)],
                    "deterred_ci95": [int(np.percentile(bs[:, 1], q)) for q in (2.5, 97.5)],
                    "share_boot_positive": round(float((bs[:, 0] > 0).mean()), 3),
                    "n_inside": int(len(ins)), "n_control": int(len(c)),
                })
    return out


def main():
    full, t = build("--refresh" in sys.argv)
    full["permitissuedate"] = pd.to_datetime(full.permitissuedate, utc=True)
    periods = periods_table(full)
    d = full[full.permitissuedate >= GRID0].copy()
    print(f"projects: {len(d)} | inside MIN: {int(d.in_min_current.sum())} | no tract price: {int(d.tract_ppsf.isna().sum())}")
    print("inside by district:", d[d.in_min_current].council_district.value_counts().to_dict())
    g = run_grid(d)
    g.to_csv(DATA / "matched_control_grid.csv", index=False)
    matched = g[g.match != "none"]
    summary = {}
    for kind in ["new_construction", "all_types"]:
        m = matched[matched.type == kind]
        summary[kind] = {
            "specs": int(len(m)),
            "did_pp": {q: round(float(m.did_pp.quantile(p)), 1) for q, p in
                       [("min", 0), ("p25", .25), ("median", .5), ("p75", .75), ("max", 1)]},
            "deterred": {q: int(m.deterred.quantile(p)) for q, p in
                         [("min", 0), ("p25", .25), ("median", .5), ("p75", .75), ("max", 1)]},
            "share_positive": round(float((m.did_pp > 0).mean()), 3),
            "untrimmed_only": {"did_pp": [float(m[m.trim.isna()].did_pp.min()), float(m[m.trim.isna()].did_pp.median()),
                                          float(m[m.trim.isna()].did_pp.max())],
                               "deterred": [int(m[m.trim.isna()].deterred.min()), int(m[m.trim.isna()].deterred.median()),
                                            int(m[m.trim.isna()].deterred.max())]},
        }
    base = dict(lo=10, trim=None, cls="all", match="band_5_95")
    detail = {}
    for kind in ["new_construction", "all_types"]:
        x = subset(d, kind, base["lo"], base["trim"], base["cls"])
        c, w = control_for(x[x.in_min], x[~x.in_min_current], base["match"])
        detail[kind] = {
            "base_spec": base,
            "estimate": did(x[x.in_min], c, w),
            "bootstrap": tract_bootstrap(d, kind, **base),
            "yearly_units_inside_vs_control": yearly(d, kind, **base),
            "placebo_2020_did_pp": placebo(d, kind, **base),
            "leave_one_out": leave_one_out(d, kind, **base),
        }
    out = {"pulled": pd.Timestamp.now().date().isoformat(), "projects": int(len(d)),
           "window": [str(W0.date()), str(W1.date())], "periods_baseline_2016_2020": periods,
           "summary_matched_specs_2018_2026": summary, "base_2018_2026": detail}
    (HERE / "matched_control_results.json").write_text(json.dumps(out, indent=1, default=str))
    for r in periods:
        print(f"{r['type']:17s} trim={str(r['trim']):5s} {r['match']:18s} inside {r['inside_per_yr']} ({r['inside_chg_pct']:+.0f}%) "
              f"control {r['control_per_yr']} ({r['control_chg_pct']:+.0f}%) gap {r['gap_pp']:+.0f}pp {r['gap_pp_ci95']} "
              f"deterred {r['deterred_units']} {r['deterred_ci95']} pos {r['share_boot_positive']}")


if __name__ == "__main__":
    main()
