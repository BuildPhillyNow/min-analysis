> **Status, November 2026: sections 2 and 3 below are superseded.**
> The matched-control estimate described in section 2 (about 400 to 500 new-construction units; 1,000 to 1,400 with
> conversions) could not be reproduced. The script that produced it was never saved, the two stored citywide files
> disagree with each other, and the result changes sign with the outlier trim. City unit counts on alterations are
> also missing before the March 2020 permit-system change, so conversion comparisons that reach back past 2020 are unreliable.
>
> The current analysis is in four scripts, each of which states its method at the top and writes every result:
>
> | Script | Question | Headline |
> |---|---|---|
> | `project_starts.py` | Did 10+ unit project starts fall more inside MIN than in comparable areas? | Overlay-wide: −61% vs −47% in projects (gap 14 points, 95% range −5 to 35); −72% vs −46% in homes (gap 27, range −4 to 53). District 3: gap 31 (12 to 56). University City vs Center City core: −67% vs −18% (gap 48, range 15 to 94) |
> | `zoning_conversion.py` | Do zoning permits under MIN convert to building permits less often? | No: 49% vs 51% within 24 months |
> | `parcel_odds.py` | Site by site, did MIN parcels become less likely to be developed? | Odds ratio 0.48 in price-matched tracts (0.24 to 0.93); 0.42 citywide (0.22 to 0.81); 0.92 within 1,500 ft of the boundary (0.38 to 2.22) |
> | `matched_control.py` | The building-permit version, by period and project type | New construction −40% vs −21% from a 2016–2020 baseline; range includes zero |
>
> `export_site_data.py` collects the figures the site shows into `src/data/generated/min-evidence.json`.
> `project_starts.py` uses BPN project groupings (a derived cohort file is committed); `parcel_odds.py` needs the BPN parcel cache.
>
> Two corrections made on November 24, 2026:
>
> 1. **Repeat records merged.** BPN's groupings can hold several records for one development (a zoning-stage record and a
>    building-stage record, or one per building permit), mostly before 2020 and more often inside MIN. Counting each as a
>    project inflated the "before" rate inside MIN. Records on the same parcel or address that start within three years of
>    each other are now one project. Unmerged, the overlay-wide gap was 24 points (4 to 48) and the homes shortfall about
>    1,900; merged, 14 points (−5 to 35) and about 900 (none to 2,200). Two-year and five-year rules give 13 and 11 points.
>    `parcel_odds.py` and `zoning_conversion.py` count parcels, not records, and were not affected.
> 2. **University City redrawn.** "University City" is now the part of MIN inside the University City District boundary
>    (`data/ucd_boundary.geojson`, City BIDs layer), not all of MIN in District 3. Mantua, Belmont and the blocks further
>    west are reported separately.
>
> Known weak points, all shown on the site: the overlay-wide gap in project starts could be chance; near the MIN boundary
> the gap disappears; pre-2020 trends were not parallel; the District 7 range includes zero; projects that include new
> construction alone give a smaller, less certain gap; renovations of existing apartment buildings count as projects.

# MIN Overlay Impact Analysis — Methodology & Robustness

**Build Philly Now — draft for internal review. Numbers are provisional (symmetric-window rebuild, data through early July 2026); finalized at the July 18 anniversary re-pull and reconciled against the city's 2025 Inclusionary Housing Programs report.**

This document records how the analysis was built, every way we stress-tested it, and — just as important — where the evidence is strong and where it is not. It is written so that a hostile, competent analyst could re-run our steps and reach our conclusions, and so that our public claims never outrun what the data supports. Where a number is contestable, we say so and give the range.

**Sourcing standard.** Every figure falls into one of two buckets, and we never blur them. (1) **Our own analysis** of the L&I permit, OPA parcel, and PCPC zoning-overlay records — units, completions, entitlement timing, classification, the deterrent, the funnel. (2) **Official city program reports** (the Mixed Income Housing / MIR reports) — used only for figures that do not exist in permit data: affordable-unit counts and Housing Trust Fund revenue. These are always attributed ("per the city's own report"). We do **not** use numbers we cannot independently reproduce or trace to an official published source — in particular the "673 permitted / 191 affordable" figure quoted from a Council office via a news article is excluded.

---

## 1. Data and design

**Universe.** All L&I building permits (`permittype IN ('Building','Residential Building')`) in Council Districts 3 and 7, pulled from the city's CARTO `permits` table. Restricting to building permits (not the trade permits — electrical, plumbing, mechanical — that the original file mixed in) is both cleaner and lossless: the ≥10-unit projects that MIN regulates are essentially all `Building` permits, and this filter reproduces the original analysis's 247 large permits exactly (246/247 identical). Script: `build_permits.py`.

**Treatment vs. control.** *Inside MIN* = permit point falls within the `/MIN` overlay polygon (exact point-in-polygon against the PCPC `Zoning_Overlays` shapefile). *Control* = permits outside MIN but within the same two council districts. This within-district difference-in-differences (DiD) design absorbs anything that hit CD3/CD7 as a whole — neighborhood trends, interest rates, construction costs, the tax-abatement phase-out. The spatial classification was validated at **100%** against the original analysis's flag on all 247 large permits.

**Study window (symmetric 4-year).** Pre-MIN: Jul 18 2018 – Jul 17 2022. Post-MIN: Jul 18 2022 – Jul 17 2026. Equal 4.0-year periods anchored exactly on the policy's effective date and its fourth anniversary. This replaces the original's asymmetric Jan 2019–Dec 2025 window and removes the arbitrary start date.

**Dating: when did MIN actually apply?** The city's own rule (§14-533, confirmed in the 2024 MIR report) is that MIN attaches to projects whose **zoning-permit application was filed after July 18, 2022** — an *entitlement-date* trigger, not a building-permit date. We therefore date each project two ways and report both: by **building-permit date** (when construction was permitted) and by **entitlement date** (earliest development zoning permit at the parcel — the city's legal trigger). This distinction turns out to matter a great deal (§2).

**Boundary vintages.** MIN's boundary was amended five times (Bills 210633-A, 220418, 230007, 240333, 250372). We reconstructed dated boundary vintages (`reconstruct_vintages.py`) and verified that **no amendment misclassifies a single project in the analysis** — the one substantive geometry change (Bill 230007's 54th→63rd El-corridor extension) contains one large project, entitled in 2020, i.e. pre-MIN regardless. Details in the boundary appendix.

**Reproduction gate.** Before changing anything, we confirmed the rebuilt pipeline reproduces the published legacy-window figures to the decimal: new-construction ≥10u DiD 27.7→8.7 inside / 6.8→4.6 outside; 64 lost permits (122 expected − 58 actual); per-project size estimators mean 60.4 / trimmed 46.6 / median 30.0. The machinery is faithful; what follows is about *interpretation*, not arithmetic.

---

## 2. The deterrent, measured in units against a matched control

Housing supply is counted in *units*, not permits — a permit is one row whether it holds one home or four hundred. So we measure units, and — decisively — against a control matched on **market strength**, not just geography.

**Why the control is everything here.** MIN blankets the strong-market submarkets of Districts 3 and 7 (University City above all); it was expanded repeatedly, with no market studies, to cover any area with workable development economics. The parcels left *outside* MIN within those districts are therefore, by construction, the weaker-market leftovers. A naive within-district DiD compares a strong market to weak ones and books the entire strong-vs-weak gap as "MIN." That inflates the estimate: the within-district figure is ~1,000–2,200 deterred units, but it is an **upper bound contaminated by control selection**, not a defensible number.

**The matched control.** We pulled every ≥10-unit building permit citywide (2018–2026, `citywide_large_alltypes.csv`), spatially classified inside/outside MIN, and restricted the non-MIN control to parcels whose OPA land value per square foot falls inside the inside-MIN band — comparing MIN parcels to genuinely comparable strong-market parcels citywide (Center City, Fishtown, Graduate Hospital, etc.) instead of weak West Philly. Zoning-stratified cross-checks (CMX-2/3/4/5, RM-1, IRMX).

**Result: a real but modest deterrent of ~400–500 new-construction units.** The new-construction unit DiD is **+16 to +23 pp and stable** across the 10/20/50-unit cutoffs and across outlier-trimming. The direction is positive in every specification we ran.

| New construction ≥10u, matched control | DiD | Deterred units |
|---|---|---|
| Build permits (outlier-trimmed) | +16 to +23 pp | **~400–500** |
| Delivered / completed (trimmed) | +3 to +6 pp | ~60–130 |

Two honest limits on the magnitude:

- **Conversions are too spiky to anchor a number.** MIN also regulates conversions (10+ unit additions/alterations), and non-MIN strong markets did more adaptive-reuse when ground-up stalled. Including conversions raises the raw estimate to ~1,000–1,400 units — but that is dominated by one or two mega-conversions (a single 1,017-unit project); trimming the two largest halves it. We report the stable new-construction figure and treat the conversion channel as directionally-consistent but **not reliably quantifiable** — development is spiky, and a handful of mega-projects swing any count.
- **Permitting vs. delivery.** The ~400–500 is deterred *permitting*. The incremental effect on *completed* housing against a matched control is small (~60–130 units) — most deterred projects would have struggled to complete in this rate environment regardless.

**A finding we tested and discarded — stated so no one resurrects it.** An earlier within-district cut showed inside-MIN projects completing at 59% vs. 92% outside, and we briefly treated it as a clean feasibility signal. **It does not survive a matched control:** against comparable strong-market parcels, inside-MIN projects complete at ~82% vs. the control's ~75% — no worse. The 59-vs-92 gap was an artifact of the weak within-district control (small West Philly projects finish reliably; large projects stall everywhere). **We make no completion-rate claim.**

**Threshold gaming: none.** No bunching just under the 10-unit trigger (the inside 7–9u vs 10–12u ratio actually *fell* post-MIN — developers stopped building rather than downsizing).

**Bottom line for the deterrent.** Real, positive across every rigorous specification, and ~400–500 deterred new-construction units against a market-matched control. This is a supporting fact, not the headline — the headline is production (§4–6).

---

## 3. Independent R cross-check

To make sure the effect wasn't an artifact of how we sliced inside/outside, we rebuilt the DiD from a completely different construction — a spatial grid-cell × quarter panel — with formal inference the original lacked. Scripts: `analysis/r/min_did.R`, `min_did_diag.R`, `min_did_rush.R`.

- **Two-way fixed-effects (fixest), clustered SEs:** all-types large deterred permits **70 (95% CI 29–112)**; new construction 68 (33–103); dropping spatially-mixed cells 75 (37–113); rush-excluded 56–58. Brackets the flat-counterfactual 64.
- **Event study:** pre-treatment coefficients are marginally non-parallel (joint Wald p≈0.04), driven by the 2021 tax-abatement rush inflating the inside pre-period. We disclose this rather than bury it.
- **Callaway–Sant'Anna:** the "simple" ATT comes back near zero. We ran this down: CS anchors every comparison to the last pre-quarter (2022Q2), which sits on the downswing from the rush peak, flattening the estimate. It is a baseline-choice artifact, not a refutation — but it *is* a caution that the precise magnitude is sensitive to how the 2021–22 rush is handled.
- **Rush sensitivity:** excluding the abatement-rush window *widens* the raw DiD (the control's post-decline was largely the rush unwinding), consistent with the original write-up's §9.

**Bottom line:** the deterrent replicates across an independent geography and estimator, and the *direction* is stable; its *magnitude* is genuinely uncertain and rush-sensitive. (This cross-check is on permit *counts* and uses the within-district control, so its magnitude carries the same control-selection inflation as the naive within-district DiD; the defensible housing-supply number is the market-*matched* new-construction figure in §2 — ~400–500 units.)

---

## 4. What actually got built under MIN (classification)

A raw count of "large projects built inside MIN since 2022" is meaningless, because most of them are **not market-rate development responding to MIN's mandate.** Two filters matter, applied via the real zoning-permit date and ownership/program (`classify_projects.py`):

- **Entitlement timing** — MIN governs projects that filed a zoning permit *after* it took effect. Some of what carries a post-2022 building permit inside MIN was entitled *before* MIN (pre-MIN pipeline draining out) and isn't subject to the mandate.
- **Program** — LIHTC and public-housing projects are affordable regardless of MIN. Student housing *is* subject to MIN when built by a **private** developer (The Mark / Landmark) — only institution-built student housing is exempt. And **MIN covers conversions** (10+ unit additions/alterations), so "no zoning permit" is not itself an exemption.

Breaking the large building permits inside MIN by real zoning-permit date and program (counts are definition-sensitive — finalized in the Phase B canonical build):

| Group | Projects | Units | Subject to MIN? |
|---|---:|---:|---|
| **Market-rate + private student, entitled UNDER MIN** | **22** | **1,326** | **Yes — the genuine set (incl. The Mark, private)** |
| Market-rate, pre-MIN pipeline (ZP before MIN) | 63 | 3,045 | No — grandfathered |
| Conversions (no matched ZP) | 76 | 4,219 | Mostly — MIN covers conversions; "no ZP" is largely a matching artifact |
| Subsidized / LIHTC / public housing | 7 | 605 | No — affordable regardless |
| Institutional student housing (exempt) | 1 | 116 | No — built by the institution |
| MIN-affordable + MIHB program | 8 | 396 | (the actual MIN outputs) |

*(All inside-MIN ≥10u projects, 2018–2026, deduplicated by parcel; `build_canonical.py` → `canonical_min_projects.csv`.)*

So the genuine answer to "how much new development has been *entitled and built* under MIN's mandate in four years" is **22 projects / 1,326 units** (including The Mark's 363-unit private student tower) — of which **only 7 have been completed (291 units)**, 8 projects in Gauthier's CD3. A modest tally across a hot four-year window. The "recovery" some point to is dominated by pre-MIN pipeline, conversions, and subsidized deals (a PHA project, LIHTC's Frankford Plaza) — not a wave of developers choosing to build under MIN's mandate.

*(Exact project-level counts — deduplication, zoning-permit matching, and precisely how conversions and The Mark are treated — get pinned to one canonical build in the data-regeneration step. Charts will show the genuine set, never the mixed "46".)*

---

## 5. The entitlement mirage (paper permits vs. housing)

MIN's defenders point to the pipeline of zoning-permitted units. But entitlements aren't housing — and we make this point **only with numbers we produce ourselves** from the permit and parcel record (`entitlements_cd37.csv`, `canonical_min_projects.csv`):

- **Of the 22 market-rate projects genuinely entitled under MIN, only 7 have been built** (291 of 1,326 units) — roughly a third, four years in.
- **Entitlement → building-permit conversion fell** inside MIN from 76% (pre-MIN, ≥2-yr-mature cohort) to 61% (post-MIN): a growing share of MIN-area entitlements never proceed to construction.
- **133 post-MIN inside-MIN entitlements that never pulled a building permit are still classified as vacant land** — entitled, nothing built. (A smaller set — ~7 — were sold after entitlement and remain vacant, a speculative "entitle-and-flip" signature; real but not the dominant story.)

*We deliberately do NOT cite the "673 permitted / 191 affordable" figure that has circulated from the Council office (via a Nov-2025 news article). We cannot independently reproduce it, its "permitted" basis is ambiguous, and it appears to fold in LIHTC/subsidized units. Every number above comes from our own analysis of the permit and parcel record.*

---

## 6. Reconciliation with the city's own report

The 2024 Mixed Income Housing Programs Report (DPD) independently confirms the core: MIN's delivered affordable output through 2024 is **~18–23 units across four projects, every one of them in CD7 — zero in Gauthier's CD3.** The report also states the entitlement-date trigger in the city's own words, and its project appendix lets us verify that the big post-MIN University City projects are LIHTC/PHA/student, not MIN-mandate affordable housing. When the 2025 report lands, these figures get their final reconciliation.

---

## 7. Voucher search (an open question, disclosed)

A MIN amendment lets project-based vouchers count toward the affordability requirement at the full voucher payment standard, which could be how some MIN units pencil. We searched every public building-level source — the PHA Project-Based Voucher listing, the PHA Moving-to-Work Table 3/4 commitments, and HUD's Multifamily Assistance & Section 8 (PBRA) database — and found **no market-rate MIN project recorded as voucher-assisted at the building level** (PHA's vouchers go overwhelmingly to dedicated affordable/supportive developers). But that mechanism operates at the tenant/unit level and wouldn't necessarily appear in development-level data, so we **cannot confirm or refute** voucher-dependency without a per-project data request to the city. We do not assert it.

---

## 8. Limitations (stated plainly)

- **Parallel trends** is the identifying assumption, and it is marginally violated in the pre-period by the 2021–22 abatement rush (§3). We address it with rush-excluded and clean-pre-window robustness, but it is a real caveat.
- **The post-2022 slowdown is mostly macro, and the control choice is decisive.** Development fell citywide (rates, construction costs, abatement expiry), and strong markets fell hardest. The within-district DiD compares strong MIN submarkets to weak-market leftovers and so *overstates* MIN's effect (~1,000–2,200 units). Against a market-strength-matched control the defensible figure is **~400–500 deterred new-construction units** — real and positive across every specification, but modest, and outlier-sensitive once conversions are included. We do not claim a completion-rate effect (it does not survive a matched control).
- **Unit-count coverage** is ~39% of all permits; the ≥10-unit analyses use only permits with confirmed counts, which is where MIN's trigger lives.
- **Small control group** (large market-rate permits outside MIN within CD3/CD7 are few), which widens uncertainty on the outside-MIN cells.
- **Transit proximity is partly a land-value effect,** not solely a MIN effect; the TOD argument is therefore made on economic-feasibility grounds, not on any claimed density/FAR reduction (MIN does *not* reduce transit-zone FAR — see the TOD note).
- **The 2026 tail is provisional** — recent months are subject to L&I reporting lag and get re-pulled at launch.
- **Voucher-dependency is unconfirmed** (§7).

---

## Reproduce

`build_permits.py` (pull + spatial join) → `compute_stats.py {legacy|symmetric}` (DiD figures) → `classify_projects.py` (market-rate vs subsidized) → `pressure_test.py` (completions, unit-weighting, spillover, threshold) → `reconstruct_vintages.py` (boundary vintages). Independent cross-check: `analysis/r/min_did.R` (+ `_diag`, `_rush`). All intermediate CSVs in `analysis/data/`.
