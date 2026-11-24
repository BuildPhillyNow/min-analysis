# MIN overlay analysis

Source for [min-analysis.netlify.app](https://min-analysis.netlify.app), Build Philly Now's analysis of
Philadelphia's Mixed-Income Neighborhoods (/MIN) overlay, and the scripts behind every figure on it.

We publish the code and data so others can check the numbers. If you find an error, open an issue or write
to jon@buildphillynow.org.

## What the analysis asks

After MIN took effect on July 18, 2022, did housing projects of 10 or more homes become scarcer inside the
overlay than in comparable parts of the city?

| Script (`analysis/`) | Question |
|---|---|
| `project_starts.py` | Did project starts fall more inside MIN than in comparable areas? Includes District 3 and 7, University City against Center City, the boundary test, a placebo and leave-one-out checks. |
| `parcel_odds.py` | Site by site, did parcels zoned for 10+ homes become less likely to get a project inside MIN? |
| `zoning_conversion.py` | Do zoning permits issued under MIN reach a building permit as often as elsewhere? |
| `matched_control.py` | The same comparison from City building permits alone, by period and project type. |
| `export_site_data.py` | Collects the results into `src/data/generated/min-evidence.json`. No figure on the site is typed by hand. |
| `build_map_data.py` | Builds the map of MIN's boundary over time and the projects zoned under it. |

Each script states its method at the top. `analysis/METHODOLOGY.md` has the current status, the corrections
made so far and the known weak points.

## Results that cut against the headline

They are on the site and in `analysis/*_results.json`:

- For the overlay as a whole, the gap in project starts has a 95% range that includes zero.
- Within 1,500 feet of the MIN boundary there is no difference between inside and outside.
- Projects that get zoning permits under MIN reach building permits at the same rate as elsewhere.
- The District 7 gap could be chance.
- Counting only projects with new residential construction, the gap is smaller and less certain.

## Data

Public City of Philadelphia sources: the permits and property tables on the City's Carto SQL API, and the
zoning overlay, council district and improvement district layers on its ArcGIS services.

Two inputs are Build Philly Now's own and are not in this repository:

- `analysis/data/bpn_parcel_project.csv`, BPN's grouping of City permits into projects. The derived cohort
  the analysis uses is committed (`analysis/data/project_starts_cohort.csv`), and `project_starts.py` runs
  from it when the full export is absent.
- BPN's parcel file with zoning capacity, needed only by `parcel_odds.py`. Its results are committed.

## Run it

```bash
uv run --no-project --with shapely --with requests --with pandas --with numpy python analysis/project_starts.py
```

```bash
uv run --no-project --with pandas --with numpy python analysis/export_site_data.py
```

```bash
bun install && bun run build
```

The site is a static Next.js export.
