"""
Collect the figures the site shows into src/data/generated/min-evidence.json, so no
number on the site is typed by hand. Reads the outputs of project_starts.py,
zoning_conversion.py and parcel_odds.py, plus the project cohort.

Run from the repo root, after those scripts:
  uv run --no-project --with pandas --with numpy python analysis/export_site_data.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
OUT = HERE.parent / "src" / "data" / "generated" / "min-evidence.json"
MIN = pd.Timestamp("2022-07-18")


def row(rows, label):
    return next(r for r in rows if r["label"].startswith(label))


def pack(r):
    def side(k):
        x = r[k]
        return {"insideBase": x["inside_per_yr"][0], "insidePost": x["inside_per_yr"][2],
                "controlBase": x["control_per_yr"][0], "controlPost": x["control_per_yr"][2],
                "insideChg": round(x["inside_chg_pct"]), "controlChg": round(x["control_chg_pct"]),
                "gap": round(x["gap_pp"]), "gapLow": round(x["gap_ci95"][0]), "gapHigh": round(x["gap_ci95"][1]),
                "shortfall": int(round(x["shortfall"], -2)) if abs(x["shortfall"]) >= 1000 else int(x["shortfall"]),
                "shortfallLow": int(round(x["shortfall_ci95"][0], -2)) if abs(x["shortfall_ci95"][0]) >= 1000 else int(x["shortfall_ci95"][0]),
                "shortfallHigh": int(round(x["shortfall_ci95"][1], -2)) if abs(x["shortfall_ci95"][1]) >= 1000 else int(x["shortfall_ci95"][1]),
                "sharePositive": x["share_positive"]}
    return {"nInside": r["n_inside"], "nControl": r["n_control"], "projects": side("projects"), "units": side("units")}


def main():
    ps = json.load(open(HERE / "project_starts_results.json"))
    zc = json.load(open(HERE / "zoning_conversion_results.json"))
    po = json.load(open(HERE / "parcel_odds_results.json"))
    rows = ps["rows"]

    main_ = pack(row(rows, "all 10+ unit projects | control: band 5-95"))
    alts = [pack(r) for r in rows if r["label"].startswith("all 10+ unit projects | control:")]
    c = pd.read_csv(HERE / "data" / "project_starts_cohort.csv", parse_dates=["start"])
    c = c[c.tract_ppsf.notna()]
    c["py"] = np.floor((c.start - MIN).dt.days / 365.25).astype(int)
    uc = c[c.in_min_original & c.in_ucd]
    gr = c[~c.in_min_current & c.in_cc_greater]
    core = c[~c.in_min_current & c.in_cc_core]

    def share(lo, hi):
        a, g = uc[(uc.py >= lo) & (uc.py < hi)], gr[(gr.py >= lo) & (gr.py < hi)]
        return {"uc": int(len(a)), "cc": int(len(g)), "share": round(100 * len(a) / (len(a) + len(g)))}

    uc_years = []
    for k in range(-10, 4):
        s = share(k, k + 1)
        uc_years.append({"label": f"{2022 + k}–{(23 + k) % 100:02d}", "underMin": k >= 0, **s,
                         "core": int((core.py == k).sum())})
    def size(df, lo, hi):
        x = df[(df.py >= lo) & (df.py < hi)]
        return {"projects": int(len(x)), "homes": int(x.units.sum()), "big": int((x.units >= 100).sum()),
                "largest": int(x.units.max()) if len(x) else 0}
    uc_size = {k: {"before": size(df, -6, -2), "underMin": size(df, 0, 4)}
               for k, df in (("uc", uc), ("core", core), ("greater", gr))}
    uc_post = uc[uc.py >= 0]
    uc_size["ucUnderMinEastOf40th"] = int((uc_post.lng > -75.2025).sum())
    uc_size["ucBeforeEastOf40th"] = int((uc[(uc.py >= -6) & (uc.py < -2)].lng > -75.2025).sum())
    uc_size["ucUnderMinNewConstruction"] = int(uc_post.new_res.sum())
    cc_post = int((gr.py >= 0).sum())
    usual = share(-6, 0)["share"] / 100
    yearly = [{"label": f"{2022 + int(k)}–{(23 + int(k)) % 100:02d}", "underMin": int(k) >= 0, "inside": v[0], "control": v[2],
               "share": round(100 * v[0] / (v[0] + v[2])) if v[0] + v[2] else None}
              for k, v in sorted(ps["yearly"].items(), key=lambda kv: int(kv[0]))]

    conv = {(t["size"], t["group"], t["cohort"]): t for t in zc["tables"]}
    def cv(group, cohort):
        t = conv[("10+ units", group, cohort)]
        return {"projects": t["projects"], "units": t["units"], "ever": round(t["ever_bp"] * 100),
                "m12": round(t["bp_12m"] * 100), "m18": round(t["bp_18m"] * 100), "m24": round(t["bp_24m"] * 100)}

    models = {m["sample"]: m for m in po["models"]}
    def odds(name, spec="no controls"):
        x = models[name][spec]
        return {"or": x["odds_ratio"], "low": x["ci95"][0], "high": x["ci95"][1]}

    out = {
        "asOf": "November 2026",
        "baseline": "July 2016 to July 2020",
        "post": "July 2022 to July 2026",
        "cohortProjects": int(len(c)),
        "main": main_,
        "gapRangeAcrossControls": {
            "projects": [min(a["projects"]["gap"] for a in alts), max(a["projects"]["gap"] for a in alts)],
            "units": [min(a["units"]["gap"] for a in alts), max(a["units"]["gap"] for a in alts)]},
        "excludeFirstThreeMonths": pack(row(rows, "exclude starts")),
        "newResidential": pack(row(rows, "includes new residential")),
        "district3": pack(row(rows, "District 3 inside MIN")),
        "district7": pack(row(rows, "District 7 inside MIN")),
        "ucVsCore": pack(row(rows, "University City (MIN in UCD) vs Center City core")),
        "ucVsGreater": pack(row(rows, "University City (MIN in UCD) vs greater Center City")),
        "boundary1500": pack(row(rows, "within 1500 ft")),
        "allOutside": pack(row(rows, "all 10+ unit projects | control: all outside")),
        "reweighted": pack(row(rows, "all 10+ unit projects | control: reweighted")),
        "repeatFilings": {"notMerged": pack(row(rows, "repeat filings not merged")),
                          "within2": pack(row(rows, "repeat filings merged within 2 years")),
                          "within5": pack(row(rows, "repeat filings merged within 5 years"))},
        "d3OutsideUc": pack(row(rows, "District 3 MIN outside UCD")),
        "uc50": pack(row(rows, "University City 50+ units")),
        "ucSize": uc_size,
        "yearlyShare": yearly,
        "ucShare": {"p2012_16": share(-10, -6), "p2016_20": share(-6, -2), "p2020_22": share(-2, 0), "underMin": share(0, 4),
                    "years": uc_years, "ccProjectsUnderMin": cc_post,
                    "expectedAtUsualShare": int(round(cc_post * usual / (1 - usual))), "usualShare": round(usual * 100)},
        "conversion": {"insideUnderMin": cv("inside MIN", "2022-26 (under MIN)"),
                       "controlUnderMin": cv("matched control", "2022-26 (under MIN)"),
                       "insideBefore": cv("inside MIN", "2020-22 (before MIN)"),
                       "controlBefore": cv("matched control", "2020-22 (before MIN)")},
        "parcelOdds": {"sites": po["sites_with_10plus_capacity"], "sitesInside": po["sites_inside_min"],
                       "citywide": odds("citywide"), "citywideControls": odds("citywide", "with controls"),
                       "matched": odds("price-matched tracts (5-95 band)"),
                       "near2500": odds("within 2,500 ft of the MIN boundary"),
                       "near1500": odds("within 1,500 ft of the MIN boundary")},
    }
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ("main", "ucShare", "conversion", "parcelOdds", "gapRangeAcrossControls")}, indent=1)[:3500])


if __name__ == "__main__":
    main()
