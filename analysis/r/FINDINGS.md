# Independent R DiD cross-check — findings

**Data:** `analysis/data/min_permits_enriched_2025.csv` (11,431 L&I permits, CD3+CD7, Jan 2019–Dec 2025). Treatment: MIN effective Jul 18 2022 (first post quarter 2022Q3).

**Method (independent of the Python 2×2):** balanced panel of **spatial grid cells (~445m × ~430m) × quarter**, treatment = cell inside MIN. Two-way fixed effects (cell + quarter), SEs clustered by cell. Poisson (rate) + OLS (levels). Plus Callaway–Sant'Anna and an abatement-rush sensitivity.

## Headline: the deterrent replicates
| Estimator | Deterred large permits | 95% CI |
|---|---|---|
| Python flat 0% counterfactual (site headline) | 64 | — |
| TWFE-OLS, all-types ≥10u | 70 | 29–112 |
| TWFE-OLS, new-construction ≥10u | 68 | 33–103 |
| TWFE-OLS, drop spatially-mixed cells | 75 | 37–113 |
| Rush-excluded TWFE, all-types | 56 | 17–95 |
| Rush-excluded TWFE, new-construction | 58 | 25–90 |

Deterred **units** (× pre-MIN inside large-project size, trimmed mean 46.6–49.3): TWFE ≈ **3,300** (CI 1,360–5,200); direct units-model 4,472 (1,184–7,761). **~3,000 sits inside every CI.**

## The abatement-rush test — effect STRENGTHENS when the rush is removed
2×2 annualized large-permit rates, three pre-windows:

| Pre window | Inside → | Outside → | DiD | Flat-lost | DiD-adj lost | Units (trim) |
|---|---|---|---|---|---|---|
| Full (2019Q1–2022Q2) | 35.4→16.9 (−52%) | 10.6→7.7 (−27%) | 25pp | 65 | 31 | ~3,200 |
| Rush-excluded (drop 21Q4–22Q2) | 31.3→16.9 (−46%) | 9.1→7.7 (−15%) | 31pp | 50 | 34 | ~2,500 |
| Clean pre-rush (2019Q1–2021Q2) | 31.6→16.9 (−47%) | 8.0→7.7 (−4%) | **43pp** | 52 | 48 | ~2,500 |

Removing the rush **widens** the DiD (25→43pp) — because the control group's post-decline was itself largely the rush unwinding; strip it out and the control is nearly flat while inside still collapses. This matches the March-2026 writeup §9 (excl. rush → −52.7pp). The rush was masking, not manufacturing, the effect.

## The one estimator that disagreed — and why it's not a refutation
Callaway–Sant'Anna "simple" ATT ≈ **−0.003 (SE 0.016), ~0 permits.** Diagnosis: CS anchors every comparison to the last pre-quarter (2022Q2), which is already on the **downswing from the 2021Q4 rush peak** (CS pre-treatment ATTs are large-positive, peaking at e=−3). Anchoring the counterfactual to a rush-contaminated baseline flattens the post estimate. CS pre-trend ATTs being non-zero is itself the tell: **raw pre-trends are not parallel** because of the rush. The fix — using a clean pre-rush window — restores a strong effect (43pp). CS-near-zero is a baseline-choice artifact, not evidence of no effect, but it IS a caution that the *precise magnitude* depends on rush treatment.

## Honest bottom line
- The MIN construction deterrent is **real and robust** across estimators, geographies (in_min flag vs independent grid), and pre-windows. Direction and significance never flip.
- Defensible deterred-units range: **~2,000–3,200**. The site's ~3,000 is the **upper-middle** (flat 0% counterfactual). The control-differenced, rush-clean central estimate is nearer **~2,000–2,500**.
- **Recommendation:** present a range (~2,000–3,000) with confidence intervals, lead with the conservative DiD-adjusted central figure, and disclose the abatement-rush pre-trend caveat + that the effect strengthens when the rush is removed. This pre-empts the exact attack a hostile analyst would make.

Reproduce: `Rscript min_did.R` (main + event study/plot), `min_did_diag.R` (CS reconciliation), `min_did_rush.R` (rush table).
