"""
Compute the core MIN DiD figures from a rebuilt permit panel for a given
pre/post window. Prints a comparison-friendly summary and (optionally) writes
JSON. Used both to VALIDATE against the legacy window and to generate the
symmetric 4-year numbers.

Usage:
  python compute_stats.py legacy      # 2019-01-01 .. 2025-12-31 (validation)
  python compute_stats.py symmetric   # 2018-07-18 .. 2026-07-17 (4yr/4yr)
"""
import sys, json
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).parent
CSV = HERE / "data" / "min_permits_rebuilt.csv"
POLICY = pd.Timestamp("2022-07-18", tz="UTC")

WINDOWS = {
    # name: (pre_start, pre_end/post_start=policy, post_end)
    "legacy":    ("2019-01-01", "2025-12-31"),
    "symmetric": ("2018-07-18", "2026-07-17"),
}


def yrs(a, b):
    return (pd.Timestamp(b, tz="UTC") - pd.Timestamp(a, tz="UTC")).days / 365.25


def rate_block(d, mask, pre_y, post_y):
    sub = d[mask]
    pre = int((sub.period == "pre").sum()); post = int((sub.period == "post").sum())
    pr, po = pre / pre_y, post / post_y
    dec = (pr - po) / pr * 100 if pr else float("nan")
    return dict(pre=pre, post=post, pre_rate=round(pr, 1), post_rate=round(po, 1), decline_pct=round(dec, 1))


def main(win="legacy", write=False):
    start, end = WINDOWS[win]
    pre_y = yrs(start, "2022-07-18"); post_y = yrs("2022-07-18", end)
    d = pd.read_csv(CSV, parse_dates=["permitissuedate"])
    d = d[(d.permitissuedate >= pd.Timestamp(start, tz="UTC")) &
          (d.permitissuedate <= pd.Timestamp(end, tz="UTC"))].copy()
    d["period"] = np.where(d.permitissuedate >= POLICY, "post", "pre")
    d["is_large"] = d.numberofunits.fillna(0) >= 10
    d["nc"] = d.typeofwork == "New Construction"
    Y = d[d.in_min == "Y"]; N = d[d.in_min == "N"]

    print(f"\n===== WINDOW: {win}  ({start} .. {end}) | pre {pre_y:.2f}y / post {post_y:.2f}y =====")
    print(f"total building permits: {len(d):,} | inside {len(Y):,} / outside {len(N):,} | large {int(d.is_large.sum())}")

    large = d.is_large
    nc_large = d.is_large & d.nc
    print("\nNEW CONSTRUCTION >=10u   [legacy target: in 27.7->8.7 (-68.6), out 6.8->4.6 (-31.6)]")
    inc = rate_block(d, nc_large & (d.in_min == "Y"), pre_y, post_y)
    outc = rate_block(d, nc_large & (d.in_min == "N"), pre_y, post_y)
    print(f"  inside : {inc}")
    print(f"  outside: {outc}")
    did_nc = round(inc["decline_pct"] - outc["decline_pct"], 1)
    print(f"  DiD (decline diff) = {did_nc} pp")

    print("\nALL TYPES >=10u          [legacy target: in 35.3->16.8 (-52.4), out 10.5->7.8 (-25.1)]")
    ina = rate_block(d, large & (d.in_min == "Y"), pre_y, post_y)
    outa = rate_block(d, large & (d.in_min == "N"), pre_y, post_y)
    print(f"  inside : {ina}")
    print(f"  outside: {outa}")
    did_all = round(ina["decline_pct"] - outa["decline_pct"], 1)
    print(f"  DiD (decline diff) = {did_all} pp")

    # lost permits (flat 0% counterfactual, all-types large inside)
    exp = ina["pre"] / pre_y * post_y
    flat_lost = exp - ina["post"]
    print(f"\nLOST PERMITS (flat 0% counterfactual, inside all-types large):")
    print(f"  pre={ina['pre']} post={ina['post']} expected={exp:.0f} lost={flat_lost:.0f}   [legacy target: 122/58/64]")

    # unit-size estimators from PRE-MIN inside large distribution
    pu = Y[large & (Y.period == "pre") & Y.numberofunits.notna()].numberofunits
    lo, hi = np.percentile(pu, [5, 95]); tm = pu[(pu >= lo) & (pu <= hi)].mean()
    est = dict(n=int(len(pu)), mean=round(pu.mean(), 1), trimmed=round(tm, 1), median=round(pu.median(), 1))
    print(f"\nUNIT-SIZE ESTIMATORS (pre inside large): {est}   [legacy target: mean 60.4 / trim 46.6 / med 30.0]")
    print(f"  Flat-counterfactual deterred UNITS: mean {flat_lost*pu.mean():.0f} / trimmed {flat_lost*tm:.0f} / median {flat_lost*pu.median():.0f}")

    # DiD-adjusted lost (control-differenced)
    ctl_factor = outa["post_rate"] / outa["pre_rate"] if outa["pre_rate"] else float("nan")
    did_lost = ina["pre_rate"] * ctl_factor * post_y - ina["post"]
    print(f"  DiD-adjusted (control-differenced) deterred units: trimmed {did_lost*tm:.0f} (permits {did_lost:.0f})")

    out = dict(window=win, span=[start, end], pre_years=round(pre_y, 2), post_years=round(post_y, 2),
               total=len(d), inside=len(Y), outside=len(N), large=int(d.is_large.sum()),
               new_construction={"inside": inc, "outside": outc, "did_pp": did_nc},
               all_types={"inside": ina, "outside": outa, "did_pp": did_all},
               lost_permits_flat=round(flat_lost), unit_estimators=est,
               units_flat={"mean": round(flat_lost*pu.mean()), "trimmed": round(flat_lost*tm), "median": round(flat_lost*pu.median())},
               units_did_adjusted={"trimmed": round(did_lost*tm), "permits": round(did_lost, 1)})
    if write:
        p = HERE / "data" / f"stats_{win}.json"
        p.write_text(json.dumps(out, indent=2))
        print(f"\nWrote {p}")
    return out


if __name__ == "__main__":
    win = sys.argv[1] if len(sys.argv) > 1 else "legacy"
    main(win, write="--write" in sys.argv)
