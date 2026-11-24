"""
Project starts inside /MIN versus comparable areas.

A "project" starts from BPN's grouping of City permits into one record per parcel or
permit job (see the BPN repo, pipeline/events/project_builder.py). One development can
have several such records: a zoning-stage record and a building-stage record, or one
record per building permit. That is more common before 2020, in the City's old permit
system. Records on the same parcel account or address that start within three years of
each other are therefore merged into one project (collapse(), GAP_YEARS). A project
"starts" on the date of its first permit event, usually the zoning permit. Units are BPN's
max_unit_count, taken from permit unit fields and permit text; coverage is steady at
76-82% of housing projects in every year since 2012, which City unit fields alone are not.

Cohort   Housing and mixed-use development projects with 10+ units (the size MIN
         regulates), started 2012-07-18 .. 2026-07-17.
Periods  baseline  2016-07-18 .. 2020-07-17  (four years before the abatement rush)
         rush      2020-07-18 .. 2022-07-17
         post      2022-07-18 .. 2026-07-17  (under MIN)
Treated  Project parcel inside the /MIN boundary in force when the project started.
Control  Outside /MIN, in census tracts whose 2016-2020 median sale price per sq ft is
         within the range of the tracts where inside-MIN projects sit.
Estimate gap = (control % change) - (inside % change), baseline to post, in projects and
         in units; 95% range from resampling census tracts.

Inputs
  analysis/data/bpn_parcel_project.csv   local export of BPN's parcel_project table
                                         (not in git). If absent, the committed
                                         analysis/data/project_starts_cohort.csv is used.
  analysis/data/tract_prices_pre_min.csv written by matched_control.py
  City OPA table (Carto) for parcel location, tract and zoning.

Run from the repo root:
  uv run --no-project --with shapely --with requests --with pandas --with numpy \
      python analysis/project_starts.py
"""
import json
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
T0 = pd.Timestamp("2012-07-18")
BASE0 = pd.Timestamp("2016-07-18")
RUSH0 = pd.Timestamp("2020-07-18")
PASSED = pd.Timestamp("2022-01-18")   # Bill 210633-A approved
MIN = pd.Timestamp("2022-07-18")      # effective
B230007 = pd.Timestamp("2023-04-25")
END = pd.Timestamp("2026-07-18")
RNG = np.random.default_rng(20261124)
FT_PER_DEG_LAT = 364_000.0
FT_PER_DEG_LNG = 279_000.0  # at 40 N
GAP_YEARS = 3  # repeat filings on one site within this many years are one development


def geom(name):
    return shape(json.load(open(DATA / name))["features"][0]["geometry"]).buffer(0)


def opa_attrs(keys):
    cache = DATA / "opa_attrs_projects.csv"
    have = pd.read_csv(cache, dtype={"parcel_number": str}) if cache.exists() else pd.DataFrame(columns=["parcel_number"])
    need = sorted(set(keys) - set(have.parcel_number))
    rows = []
    for i in range(0, len(need), 150):
        q = ("SELECT parcel_number, census_tract, zoning, ST_X(the_geom) AS lng, ST_Y(the_geom) AS lat "
             "FROM opa_properties_public WHERE parcel_number IN (%s)" % ",".join(f"'{k}'" for k in need[i:i + 150]))
        for a in range(5):
            r = requests.post(CARTO, data={"q": q}, timeout=120)
            if r.status_code == 200:
                break
            time.sleep(4 * (a + 1))
        r.raise_for_status()
        rows.append(pd.DataFrame(r.json()["rows"]))
    if rows:
        have = pd.concat([have, *rows], ignore_index=True)
        have.to_csv(cache, index=False)
    return have


def collapse(d, key, years):
    """One row per development: rows that share `key` (the parcel account, then the
    address) and start within `years` of the previous row are the same development
    filed more than once (a zoning-stage record and a building-stage record, or one
    record per building permit). Keep the earliest start and the largest unit count."""
    d = d.sort_values([key, "first_event_date"]).copy()
    gap = d.groupby(key).first_event_date.diff().dt.days
    d["_ep"] = (gap.isna() | (gap > years * 365.25)).cumsum()
    last = d.groupby("_ep").tail(1).set_index("_ep")
    g = d.groupby("_ep")
    out = g.head(1).set_index("_ep").copy()
    out["max_unit_count"] = g.max_unit_count.max()
    out["work_types"] = g.work_types.agg(lambda v: ", ".join(sorted({w.strip() for x in v.dropna() for w in x.split(",")})))
    out["stage"] = last.stage
    out["records"] = g.records.sum()
    return out.reset_index(drop=True)


def load(gap_years=GAP_YEARS):
    cohort = DATA / "project_starts_cohort.csv"
    src = DATA / "bpn_parcel_project.csv"
    if not src.exists():
        return pd.read_csv(cohort, parse_dates=["start"])
    d = pd.read_csv(src, low_memory=False, parse_dates=["first_event_date"])
    d = d[(d.category == "development") & d.track.isin(["housing", "mixed_use"]) & (d.max_unit_count >= 10)
          & (d.first_event_date >= T0) & (d.first_event_date < END)].copy()
    d["opa"] = d.opa_number.astype(str).str.zfill(9)
    d = d[d.opa.str.fullmatch(r"\d{9}")]
    d["records"] = 1
    if gap_years is not None:
        d = collapse(collapse(d, "opa", gap_years), "address", gap_years)
    o = opa_attrs(d.opa.unique())
    d = d.merge(o, left_on="opa", right_on="parcel_number", how="left").dropna(subset=["lng", "lat"])
    d["census_tract"] = pd.to_numeric(d.census_tract, errors="coerce")
    t = pd.read_csv(DATA / "tract_prices_pre_min.csv").rename(columns={"ppsf": "tract_ppsf"})
    t["census_tract"] = pd.to_numeric(t.census_tract, errors="coerce")
    d = d.merge(t[["census_tract", "tract_ppsf"]], on="census_tract", how="left")
    orig, cur, corr = geom("min_boundary_2022_original.geojson"), geom("min_boundary_post230007.geojson"), geom("min_corridor_230007.geojson")
    core, greater = geom("cc_core_boundary.geojson"), geom("cc_greater_boundary.geojson")
    po, pc, pk, pcore, pgr = prep(orig), prep(cur), prep(corr), prep(core), prep(greater)
    pucd = prep(geom("ucd_boundary.geojson"))
    pts = [Point(x, y) for x, y in zip(d.lng, d.lat)]
    d["in_min_current"] = [pc.contains(p) for p in pts]
    d["in_min_original"] = [po.contains(p) for p in pts]
    d["in_corridor_2023"] = [pk.contains(p) for p in pts]
    d["in_cc_core"] = [pcore.contains(p) for p in pts]
    d["in_cc_greater"] = [pgr.contains(p) for p in pts]
    d["in_ucd"] = [pucd.contains(p) for p in pts]
    # distance to the current MIN boundary, feet (scaled degrees; fine at this extent)
    from shapely.affinity import scale
    b = scale(cur.boundary, xfact=FT_PER_DEG_LNG, yfact=FT_PER_DEG_LAT, origin=(0, 0))
    d["dist_boundary_ft"] = [b.distance(Point(x * FT_PER_DEG_LNG, y * FT_PER_DEG_LAT)) for x, y in zip(d.lng, d.lat)]
    d["start"] = d.first_event_date
    d["units"] = d.max_unit_count.astype(int)
    d["new_res"] = d.work_types.fillna("").str.contains("New Residential")
    keep = ["project_id", "opa", "address", "start", "units", "stage", "origin_stage", "is_stalled", "work_types",
            "new_res", "council_district", "zoning", "lng", "lat", "census_tract", "tract_ppsf", "in_min_current",
            "in_min_original", "in_corridor_2023", "in_cc_core", "in_cc_greater", "in_ucd", "dist_boundary_ft", "records"]
    if gap_years == GAP_YEARS:
        d[keep].to_csv(cohort, index=False)
    return d[keep]


def period(s):
    return np.where(s < BASE0, "early", np.where(s < RUSH0, "baseline", np.where(s < MIN, "rush", "post")))


YEARS = {"baseline": 4.0, "rush": 2.0, "post": 4.0}


def summarize(df, w=None):
    w = np.ones(len(df)) if w is None else w
    per = period(df.start)
    out = {}
    for k in YEARS:
        m = per == k
        out[k] = (w[m].sum() / YEARS[k], (df.units.values * w)[m].sum() / YEARS[k])
    return out


def gap(ins, ctl, w=None):
    a, b = summarize(ins), summarize(ctl, w)
    if a["baseline"][0] == 0 or b["baseline"][0] == 0:
        return None
    r = {}
    for i, name in enumerate(["projects", "units"]):
        ichg, cchg = a["post"][i] / a["baseline"][i] - 1, b["post"][i] / b["baseline"][i] - 1
        r[name] = {"inside_base": a["baseline"][i], "inside_rush": a["rush"][i], "inside_post": a["post"][i],
                   "control_base": b["baseline"][i], "control_rush": b["rush"][i], "control_post": b["post"][i],
                   "inside_chg": ichg, "control_chg": cchg, "gap": cchg - ichg,
                   "shortfall": a["baseline"][i] * (cchg - ichg) * YEARS["post"]}
    return r


def control(ins, out, how):
    v = ins.tract_ppsf.dropna()
    if how == "all outside":
        return out, None
    lo, hi = {"band 0-100": (0, 1), "band 5-95": (.05, .95), "band 10-90": (.1, .9)}.get(how, (0, 1))
    c = out[(out.tract_ppsf >= v.quantile(lo)) & (out.tract_ppsf <= v.quantile(hi))]
    if how != "reweighted":
        return c, None
    edges = np.unique(v.quantile([0, .2, .4, .6, .8, 1]).values)
    base_i = ins[period(ins.start) == "baseline"]
    base_c = c[period(c.start) == "baseline"]
    ish = pd.cut(base_i.tract_ppsf, edges, include_lowest=True).value_counts(normalize=True)
    csh = pd.cut(base_c.tract_ppsf, edges, include_lowest=True).value_counts(normalize=True)
    cb = pd.cut(c.tract_ppsf, edges, include_lowest=True)
    w = cb.map(lambda k: ish.get(k, 0) / csh.get(k) if csh.get(k, 0) > 0 else 0).astype(float).values
    return c, w


def boot(ins, ctl, w, n=3000):
    c = ctl.assign(_w=1.0 if w is None else w)
    ig, cg = dict(tuple(ins.groupby("census_tract"))), dict(tuple(c.groupby("census_tract")))
    ik, ck = list(ig), list(cg)
    res = {"projects": [], "units": []}
    for _ in range(n):
        bi = pd.concat([ig[k] for k in RNG.choice(ik, len(ik))])
        bc = pd.concat([cg[k] for k in RNG.choice(ck, len(ck))])
        g = gap(bi, bc, bc._w.values)
        if g:
            for k in res:
                res[k].append((g[k]["gap"], g[k]["shortfall"]))
    out = {}
    for k, v in res.items():
        v = np.array(v)
        out[k] = {"gap_ci95": [round(float(np.percentile(v[:, 0], q)) * 100, 1) for q in (2.5, 97.5)],
                  "shortfall_ci95": [int(np.percentile(v[:, 1], q)) for q in (2.5, 97.5)],
                  "share_positive": round(float((v[:, 0] > 0).mean()), 3)}
    return out


def line(label, ins, ctl, w=None, do_boot=True):
    g = gap(ins, ctl, w)
    if not g:
        return {"label": label, "note": "empty baseline"}
    row = {"label": label, "n_inside": int(len(ins)), "n_control": int(len(ctl))}
    b = boot(ins, ctl, w) if do_boot else None
    for k in ("projects", "units"):
        x = g[k]
        f = lambda v: round(float(v), 1)
        row[k] = {"inside_per_yr": [f(x["inside_base"]), f(x["inside_rush"]), f(x["inside_post"])],
                  "control_per_yr": [f(x["control_base"]), f(x["control_rush"]), f(x["control_post"])],
                  "inside_chg_pct": f(x["inside_chg"] * 100), "control_chg_pct": f(x["control_chg"] * 100),
                  "gap_pp": f(x["gap"] * 100), "shortfall": int(round(x["shortfall"]))}
        if b:
            row[k].update(b[k])
    return row


def show(r):
    if "note" in r:
        print(f"{r['label']:58s} {r['note']}")
        return
    for k in ("projects", "units"):
        x = r[k]
        ci = f" CI {x.get('gap_ci95')} pos {x.get('share_positive')}" if "gap_ci95" in x else ""
        print(f"{r['label'][:58]:58s} {k:8s} inside {x['inside_per_yr']} ({x['inside_chg_pct']:+.0f}%)  control "
              f"{x['control_per_yr']} ({x['control_chg_pct']:+.0f}%)  gap {x['gap_pp']:+.0f}pp{ci}  shortfall {x['shortfall']}"
              + (f" {x.get('shortfall_ci95')}" if "shortfall_ci95" in x else ""))


def main():
    d = load()
    d["start"] = pd.to_datetime(d.start)
    d = d[d.tract_ppsf.notna()].copy()
    d["in_min"] = np.where(d.start >= B230007, d.in_min_current, d.in_min_original)
    ins_all, out_all = d[d.in_min], d[~d.in_min_current]
    print(f"projects: {len(d)} | inside MIN: {len(ins_all)} | outside: {len(out_all)}")
    results = {"pulled_from_bpn_build": "2026-11-23", "rows": []}

    def run(label, ins, out, how="band 5-95", do_boot=True):
        c, w = control(ins, out, how)
        r = line(label, ins, c, w, do_boot)
        results["rows"].append(r)
        show(r)

    print("\n== main comparison, by control definition")
    for how in ["all outside", "band 0-100", "band 5-95", "band 10-90", "reweighted"]:
        run(f"all 10+ unit projects | control: {how}", ins_all, out_all, how)

    print("\n== variants (control: band 5-95)")
    run("exclude starts Jul 18 - Oct 17, 2022 (likely filed before MIN)",
        ins_all[~((ins_all.start >= MIN) & (ins_all.start < MIN + pd.DateOffset(months=3)))],
        out_all[~((out_all.start >= MIN) & (out_all.start < MIN + pd.DateOffset(months=3)))])
    run("projects of 400 units or fewer", ins_all[ins_all.units <= 400], out_all[out_all.units <= 400])
    run("20+ units", ins_all[ins_all.units >= 20], out_all[out_all.units >= 20])
    run("50+ units", ins_all[ins_all.units >= 50], out_all[out_all.units >= 50])
    run("includes new residential construction", ins_all[ins_all.new_res], out_all[out_all.new_res])
    run("renovation / conversion only", ins_all[~ins_all.new_res], out_all[~out_all.new_res])
    run("District 3 inside MIN", ins_all[ins_all.council_district == 3], out_all)
    run("District 7 inside MIN", ins_all[ins_all.council_district == 7], out_all)

    if (DATA / "bpn_parcel_project.csv").exists():
        print("\n== how repeat filings for one development are merged (main comparison, control: band 5-95)")
        for lab, gy in [("not merged", None), ("merged within 2 years", 2), ("merged within 5 years", 5)]:
            e = load(gy)
            e["start"] = pd.to_datetime(e.start)
            e = e[e.tract_ppsf.notna()].copy()
            e["in_min"] = np.where(e.start >= B230007, e.in_min_current, e.in_min_original)
            run(f"repeat filings {lab}", e[e.in_min], e[~e.in_min_current])

    print("\n== named comparisons")
    # University City = the part of MIN inside the University City District's boundary
    # (analysis/data/ucd_boundary.geojson). The rest of MIN in District 3 (Mantua, Belmont,
    # blocks further west) is reported separately.
    uc = ins_all[ins_all.in_ucd]
    for lab, ins_, ctl in [("University City (MIN in UCD) vs Center City core", uc, out_all[out_all.in_cc_core]),
                           ("University City (MIN in UCD) vs greater Center City", uc, out_all[out_all.in_cc_greater]),
                           ("District 3 MIN outside UCD vs greater Center City",
                            ins_all[(ins_all.council_district == 3) & ~ins_all.in_ucd], out_all[out_all.in_cc_greater])]:
        r = line(lab, ins_, ctl)
        results["rows"].append(r); show(r)
    for lab, ctl in [("University City 50+ units vs greater Center City 50+", out_all[out_all.in_cc_greater & (out_all.units >= 50)])]:
        r = line(lab, uc[uc.units >= 50], ctl)
        results["rows"].append(r); show(r)

    print("\n== boundary: within 1,500 ft of the MIN line, inside vs outside")
    for ft in (1000, 1500, 2500):
        near_in = d[d.in_min_current & (d.dist_boundary_ft <= ft)]
        near_in = near_in[np.where(near_in.start >= B230007, near_in.in_min_current, near_in.in_min_original)]
        near_out = d[~d.in_min_current & (d.dist_boundary_ft <= ft)]
        r = line(f"within {ft} ft of boundary: inside vs outside", near_in, near_out)
        results["rows"].append(r); show(r)

    print("\n== placebo: pretend MIN took effect 2018-07-18 (baseline years only)")
    pre = d[(d.start >= BASE0) & (d.start < RUSH0)]
    fake = pd.Timestamp("2018-07-18")
    def chg(df, col=None):
        a, b = df[df.start < fake], df[df.start >= fake]
        return (b.units.sum() / a.units.sum() - 1, len(b) / len(a) - 1)
    pi = pre[pre.in_min_original]
    v = pi.tract_ppsf
    pc = pre[~pre.in_min_current & (pre.tract_ppsf >= v.quantile(.05)) & (pre.tract_ppsf <= v.quantile(.95))]
    ci, cc = chg(pi), chg(pc)
    results["placebo_2018"] = {"inside_units_chg": round(ci[0] * 100, 1), "control_units_chg": round(cc[0] * 100, 1),
                               "inside_projects_chg": round(ci[1] * 100, 1), "control_projects_chg": round(cc[1] * 100, 1)}
    print(results["placebo_2018"])

    print("\n== year by year (policy year 0 starts 2022-07-18): projects / units, inside vs control (band 5-95)")
    c, _ = control(ins_all, out_all, "band 5-95")
    yr = lambda s: np.floor((s - MIN).dt.days / 365.25).astype(int)
    ya = ins_all.groupby(yr(ins_all.start)).units.agg(["size", "sum"])
    yb = c.groupby(yr(c.start)).units.agg(["size", "sum"])
    yearly = {}
    for k in range(-10, 4):
        yearly[k] = [int(ya["size"].get(k, 0)), int(ya["sum"].get(k, 0)), int(yb["size"].get(k, 0)), int(yb["sum"].get(k, 0))]
        share = yearly[k][0] / (yearly[k][0] + yearly[k][2]) if yearly[k][0] + yearly[k][2] else float("nan")
        print(f"  year {k:+3d}: inside {yearly[k][0]:3d} / {yearly[k][1]:5d}   control {yearly[k][2]:3d} / {yearly[k][3]:5d}   inside share of projects {share:.0%}")
    results["yearly"] = yearly

    print("\n== race to the deadline: starts between approval (2022-01-18) and effect (2022-07-18) vs the same months a year earlier")
    def win(df, a, b):
        x = df[(df.start >= a) & (df.start < b)]
        return len(x), int(x.units.sum())
    race = {}
    for lab, df in [("inside", d[d.in_min_original]), ("control", c)]:
        race[lab] = {"2021-01-18..07-17": win(df, pd.Timestamp("2021-01-18"), pd.Timestamp("2021-07-18")),
                     "2021-07-18..2022-01-17": win(df, pd.Timestamp("2021-07-18"), PASSED),
                     "2022-01-18..07-17 (approval to effect)": win(df, PASSED, MIN),
                     "2022-07-18..2023-01-17": win(df, MIN, pd.Timestamp("2023-01-18"))}
        print(" ", lab, race[lab])
    results["deadline_race"] = race

    print("\n== 2023 expansion corridor (54th-63rd St), projects / units by period")
    k = d[d.in_corridor_2023]
    cor = {"2016-07..2022-07 (6 yrs, not in MIN)": win(k, BASE0, MIN), "2022-07..2023-04 (9 mo, not in MIN)": win(k, MIN, B230007),
           "2023-04..2026-07 (39 mo, in MIN)": win(k, B230007, END)}
    print(" ", cor)
    results["corridor_2023"] = cor

    print("\n== leave one out: main comparison (band 5-95), dropping each of the 8 largest projects")
    c, w = control(ins_all, out_all, "band 5-95")
    pool = pd.concat([ins_all.assign(_g="inside"), c.assign(_g="control")])
    pool = pool[period(pool.start) != "early"].sort_values("units", ascending=False).head(8)
    loo = []
    for _, row in pool.iterrows():
        g = gap(ins_all[ins_all.project_id != row.project_id], c[c.project_id != row.project_id])
        loo.append({"dropped": f"{row.address} ({row.units} units, {row._g}, {period(pd.Series([row.start]))[0]})",
                    "units_gap_pp": round(g["units"]["gap"] * 100, 1), "units_shortfall": int(g["units"]["shortfall"])})
        print("  ", loo[-1])
    results["leave_one_out"] = loo
    (HERE / "project_starts_results.json").write_text(json.dumps(results, indent=1, default=str))


if __name__ == "__main__":
    main()
