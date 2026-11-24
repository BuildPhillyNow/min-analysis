"""
Reconstruct dated MIN overlay boundary vintages from the current consolidated
shapefile + the ordinance street text, for as-of-date applicability.

Only subarea (a) West Philadelphia changed geometry in the study window, via:
  - Bill 230007 (eff 4/25/2023): inserted the 54th->63rd St Market/El corridor.
  - Bill 250372 (eff ~6/2025): 49th & Woodland path swap.
The published GIS layer (our shapefile) lags the code: it reflects 230007 but
NOT 250372 (May-2025 and Nov-2025 extracts are byte-identical). So:

  vintage 'original'    7/18/2022 - 4/24/2023  = current MIN minus the 54th->63rd corridor
  vintage 'post230007'  4/25/2023 - (250372)   = current shapefile as-is
  vintage 'current'     250372 onward          = PENDING Planning's post-2025 shapefile

The 54th St cut line is fit from 781 OPA parcels addressed on 54th St (captures
the street's real tilt), so the reconstructed original edge follows 54th St, not
a longitude meridian.
"""
import json
import numpy as np, pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from pathlib import Path
HERE = Path(__file__).parent
MIN = pd.Timestamp("2022-07-18", tz="UTC"); B230007 = pd.Timestamp("2023-04-25", tz="UTC")

cur = gpd.read_file("/Users/jongeeting/Downloads/Zoning_Overlays/Zoning_Overlays.shp")
cur = unary_union(cur[cur.overlay_sy == "/MIN"].to_crs(4326).geometry.values)

# 54th St cut line (lng = A0*lat + A1), build a half-plane polygon WEST of it
A = np.load(HERE / "data" / "st54_fit.npy")
def lng54(lat): return A[0] * lat + A[1]
la0, la1 = 39.90, 40.00
west_halfplane = Polygon([(lng54(la0), la0), (lng54(la1), la1), (-75.32, la1), (-75.32, la0)])

corridor_230007 = cur.intersection(west_halfplane)     # the 54th->63rd El corridor (added Apr 2023)
min_original = cur.difference(west_halfplane)           # original 7/18/2022 boundary
print(f"current MIN acres:      {cur.area*0:.0f}", end="")  # placeholder
def acres(g): return gpd.GeoSeries([g], crs=4326).to_crs(2272).area.iloc[0] / 43560
print(f"\ncurrent (post-230007) MIN: {acres(cur):.0f} ac")
print(f"  230007 corridor (west of 54th): {acres(corridor_230007):.0f} ac")
print(f"  reconstructed original 2022:    {acres(min_original):.0f} ac")

# save vintages
def save(geom, name):
    gpd.GeoSeries([geom], crs=4326).to_file(HERE / "data" / f"{name}.geojson", driver="GeoJSON")
save(min_original, "min_boundary_2022_original")
save(cur, "min_boundary_post230007")
save(corridor_230007, "min_corridor_230007")

# ---- as-of-date applicability + re-validate against projects ----
def min_applies(lng, lat, date):
    """Is (lng,lat) inside the MIN boundary in effect on `date`? (pre-250372 only)"""
    pt = Point(lng, lat)
    if date < MIN: return False
    geom = min_original if date < B230007 else cur
    return geom.contains(pt)

p = pd.read_csv(HERE / "data" / "projects_enriched_6plus.csv", parse_dates=["ent_eff"])
ins = p[(p.in_min == "Y") & (p.units >= 10)].dropna(subset=["lng", "lat"]).drop_duplicates("opa").copy()
ins["pt"] = [Point(x, y) for x, y in zip(ins.lng, ins.lat)]
# The ONLY geometric delta is the 230007 corridor. It changes a project's MIN status
# ONLY if the project is in the corridor AND entitled in [7/18/2022, 4/25/2023) — before
# then MIN is temporally N/A; after, the corridor is in effect. (Boundary effect ≠ the
# temporal MIN rule; isolate it here so we don't conflate the two.)
ins["in_corridor"] = ins.pt.apply(corridor_230007.contains)
affected = ins[ins.in_corridor & (ins.ent_eff >= MIN) & (ins.ent_eff < B230007)]
print(f"\n230007 corridor contains {int(ins.in_corridor.sum())} inside-MIN large project(s).")
for _, r in ins[ins.in_corridor].iterrows():
    print(f"   {r.address:22.22s} {r.units:.0f}u entitled {str(r.ent_eff)[:10]}")
print(f">>> Projects whose MIN status the boundary vintage changes: {len(affected)}")

manifest = {
    "subarea_a_vintages": [
        {"name": "original", "effective": "2022-07-18", "until": "2023-04-24", "bill": "210633-A",
         "geometry": "min_boundary_2022_original.geojson", "note": "current minus 54th->63rd corridor"},
        {"name": "post230007", "effective": "2023-04-25", "until": "~2025-06 (250372)", "bill": "230007",
         "geometry": "min_boundary_post230007.geojson", "note": "= current published shapefile (GIS lags 250372)"},
        {"name": "current", "effective": "~2025-06", "until": None, "bill": "250372",
         "geometry": "PENDING Planning post-2025 shapefile", "note": "49th & Woodland change; not in published GIS yet"},
    ],
    "other_subareas": "b (TOD∩CD7), c (Kensington), d (Frankford), e (Feltonville): geometry static in study window (220418 Nov-2022 = technical corrections to c/d; 240333 = map cleanup).",
    "cut_line_54th_st": {"fit_lng_eq": f"{A[0]:.5f}*lat + {A[1]:.5f}", "source": "781 OPA parcels on 54th St"},
}
json.dump(manifest, open(HERE / "data" / "min_vintages_manifest.json", "w"), indent=2)
print("\nSaved vintages geojson + min_vintages_manifest.json")
