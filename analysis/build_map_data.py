"""
Build src/data/generated/min-map.json for the home page map.

Two things go on the map:

1. How the /MIN overlay has grown.
   - 2022: original boundary (analysis/data/min_boundary_2022_original.geojson,
     reconstructed in reconstruct_vintages.py).
   - 2023: the 54th-63rd Street corridor added by Bill 230007 (April 25, 2023)
     (analysis/data/min_corridor_230007.geojson).
   - 2026: Bill 260517 (June 12, 2026) widened the /TOC overlay to a quarter mile,
     and section 14-533(1)(b) puts every /TOC lot in the 7th Council District in
     MIN. The City's published /MIN layer has not been redrawn for this, so the
     area is derived here as (City /TOC layer in District 7) minus (City /MIN layer).
     It is approximate.
   Bill 250372 (2025, 49th and Woodland) is a small swap and is not drawn.

2. Housing projects of 10+ homes that received a development zoning permit on or
   after July 18, 2022, inside the overlay and around it, and how far each has gone:
   zoning permit only, building permit issued, or certificate of occupancy. Taken from
   analysis/data/zoning_cohort.csv (run zoning_conversion.py first). Inside MIN is
   tested against the boundary in force on the zoning permit date.

Run from the repo root:
  uv run --no-project --with shapely --with requests --with pandas python analysis/build_map_data.py \
      [path/to/major_streets.geojson]

The optional streets file (LineStrings with `stname` and `class`) only draws the
grey background streets; without it the map has none.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

import requests
from shapely.geometry import LineString, Point, box, mapping, shape
from shapely.ops import linemerge, unary_union

HERE = Path(__file__).parent
OUT = HERE.parent / "src" / "data" / "generated" / "min-map.json"
ARC = "https://services.arcgis.com/fLeGjb7u4uXqeF9q/arcgis/rest/services"
CARTO = "https://phl.carto.com/api/v2/sql"
MIN_DATE = "2022-07-18"
B230007 = "2023-04-25"
B260517 = "2026-06-12"
# Map window: both halves of the overlay with a little margin.
BBOX = (-75.262, 39.930, -75.050, 40.045)
ACRES_PER_DEG2 = 111.0 * 85.0 * 247.105  # close enough at 40 N for a label


def arc(layer, where):
    r = requests.get(
        f"{ARC}/{layer}/FeatureServer/0/query",
        params={"where": where, "outFields": "*", "outSR": 4326, "f": "geojson"},
        timeout=90,
    )
    r.raise_for_status()
    return [(f["properties"], shape(f["geometry"]).buffer(0)) for f in r.json()["features"]]


def carto(q):
    r = requests.post(CARTO, data={"q": q}, timeout=120)
    r.raise_for_status()
    return r.json()["rows"]


def local(name):
    return shape(json.load(open(HERE / "data" / name))["features"][0]["geometry"]).buffer(0)


def rings(geom, tol=0.00006):
    """Polygon/MultiPolygon -> list of polygons, each a list of rings of [lng, lat]."""
    geom = geom.simplify(tol, preserve_topology=True)
    polys = getattr(geom, "geoms", [geom])
    out = []
    for p in polys:
        if p.is_empty or p.geom_type != "Polygon":
            continue
        out.append(
            [[[round(x, 5), round(y, 5)] for x, y in ring.coords] for ring in [p.exterior, *p.interiors]]
        )
    return out


def acres(geom):
    return round(geom.area * ACRES_PER_DEG2)


UNIT_RE = re.compile(r"\(?\b(\d{1,4})\)?\s*(?:RESIDENTIAL\s+)?DWELLING\s+UNITS?", re.I)


def parse_units(text):
    found = [int(m) for m in UNIT_RE.findall(text or "")]
    return max(found) if found else None


def main():
    streets_path = sys.argv[1] if len(sys.argv) > 1 else None

    # ---- boundaries ----
    original = local("min_boundary_2022_original.geojson")
    corridor = local("min_corridor_230007.geojson")
    city_min = unary_union([g for _, g in arc("Zoning_Overlays", "overlay_symbol='/MIN'")])
    toc = unary_union([g for _, g in arc("Zoning_Overlays", "overlay_symbol LIKE '/TO%'")])
    districts = {str(p["district"]).strip(): g for p, g in arc("Council_Districts_2024", "1=1")}
    toc_d7 = toc.intersection(districts["7"]).difference(city_min.buffer(0.00003))
    toc_d7 = unary_union([g for g in getattr(toc_d7, "geoms", [toc_d7]) if g.area * ACRES_PER_DEG2 > 0.5])

    def boundary_on(day):
        g = original
        if day >= B230007:
            g = city_min
        if day >= B260517:
            g = unary_union([city_min, toc_d7])
        return g

    # ---- projects ----
    # Projects of 10+ homes with a development zoning permit on or after the effective
    # date, from analysis/data/zoning_cohort.csv (written by zoning_conversion.py; units
    # from BPN project groupings). Stage: zoning permit only, building permit, or
    # certificate of occupancy.
    import pandas as pd
    z = pd.read_csv(HERE / "data" / "zoning_cohort.csv", parse_dates=["zp_date", "bp_date"])
    z = z[(z.units >= 10) & (z.zp_date >= MIN_DATE)]
    x0, y0, x1, y1 = BBOX
    z = z[(z.lng > x0) & (z.lng < x1) & (z.lat > y0) & (z.lat < y1)]
    projects = []
    for r in z.itertuples():
        day = r.zp_date.date().isoformat()
        inside = bool(boundary_on(day).contains(Point(r.lng, r.lat)))
        co = bool(r.co) and not pd.isna(r.bp_date)
        stage = "complete" if co else "building" if not pd.isna(r.bp_date) else "zoning"
        projects.append({
            "address": str(r.address).title(), "lng": round(r.lng, 5), "lat": round(r.lat, 5),
            "units": int(r.units), "zp": day,
            "bp": None if pd.isna(r.bp_date) else r.bp_date.date().isoformat(),
            "stage": stage, "inside": inside,
        })
    projects.sort(key=lambda q: -q["units"])
    greater_cc = shape(json.load(open(HERE / "data" / "cc_greater_boundary.geojson"))["features"][0]["geometry"])

    # ---- background streets ----
    streets = []
    if streets_path:
        window = box(*BBOX)
        by_name = {}
        for f in json.load(open(streets_path))["features"]:
            if f["properties"].get("class") not in (2, 3):
                continue
            g = shape(f["geometry"])
            if g.intersects(window):
                by_name.setdefault(f["properties"].get("stname") or "", []).append(g.intersection(window))
        for name, parts in by_name.items():
            merged = linemerge(unary_union(parts)) if len(parts) > 1 else parts[0]
            for line in getattr(merged, "geoms", [merged]):
                if isinstance(line, LineString) and line.length > 0.002:
                    line = line.simplify(0.0001)
                    streets.append([[round(x, 4), round(y, 4)] for x, y in line.coords])

    out = {
        "pulled": date.today().isoformat(),
        "bbox": list(BBOX),
        "stages": [
            {"id": "2022", "date": MIN_DATE, "label": "July 2022", "bill": "210633-A",
             "note": "Original overlay", "acres": acres(original), "polygons": rings(original)},
            {"id": "2023", "date": B230007, "label": "April 2023", "bill": "230007",
             "note": "54th to 63rd Street corridor added", "acres": acres(corridor), "polygons": rings(corridor)},
            {"id": "2026", "date": B260517, "label": "June 2026", "bill": "260517",
             "note": "Transit overlay lots in District 7 (approximate)", "acres": acres(toc_d7),
             "polygons": rings(toc_d7)},
        ],
        "greaterCenterCity": rings(greater_cc, 0.0002),
        "labels": [
            {"name": "University City", "lng": -75.197, "lat": 39.9515},
            {"name": "Center City", "lng": -75.1655, "lat": 39.9500},
            {"name": "Fishtown", "lng": -75.1310, "lat": 39.9700},
            {"name": "Kensington", "lng": -75.1255, "lat": 39.9925},
            {"name": "Frankford", "lng": -75.0850, "lat": 40.0235},
            {"name": "West Philadelphia", "lng": -75.2285, "lat": 39.9585},
        ],
        "streets": streets,
        "projects": projects,
    }
    OUT.write_text(json.dumps(out, separators=(",", ":")))
    ins = [q for q in projects if q["inside"]]
    n = {k: sum(1 for q in ins if q["stage"] == k) for k in ("zoning", "building", "complete")}
    print(f"wrote {OUT} ({OUT.stat().st_size/1024:.0f} KB)")
    print("projects in window:", len(projects), "| inside MIN:", len(ins), n)
    print("acres:", [(s["id"], s["acres"]) for s in out["stages"]], "| streets:", len(streets))


if __name__ == "__main__":
    main()
