#!/usr/bin/env Rscript
# =====================================================================
# Independent DiD cross-check of the MIN parcel-level impact analysis.
#
# Purpose: validate the Python 2x2 rate-DiD (min-stats.ts) with a proper
# panel difference-in-differences that yields standard errors, confidence
# intervals, an event-study parallel-trends test, and a Callaway-Sant'Anna
# robustness estimate. Built on an INDEPENDENT panel construction
# (spatial grid cells x quarter) rather than reusing any Python-derived
# numbers.
#
# Key estimand note: a DiD is inherently CONTROL-DIFFERENCED — it subtracts
# the outside-MIN trend. The BPN headline (~3,000 units) uses a FLAT 0%
# counterfactual that does NOT subtract the control decline. So the DiD's
# natural deterred-units figure should land BELOW 3,000, nearer BPN's own
# "DiD-adjusted" estimate. We report both so the comparison is apples-to-apples.
#
# Treatment date: July 18, 2022 (Bill 220519) -> first post quarter 2022Q3.
# =====================================================================

suppressPackageStartupMessages({
  library(data.table); library(fixest); library(ggplot2)
})
have_did <- requireNamespace("did", quietly = TRUE)

CSV <- "/Users/jongeeting/Projects/min-analysis/analysis/data/min_permits_enriched_2025.csv"
OUT <- "/Users/jongeeting/Projects/min-analysis/analysis/r/out"
dir.create(OUT, showWarnings = FALSE, recursive = TRUE)
PRE_Y <- 3.54; POST_Y <- 3.45          # match Python annualization
GRID_LAT <- 0.004; GRID_LNG <- 0.005   # ~445m x ~430m cells at 40N

d <- fread(CSV)
d <- d[!is.na(lng) & !is.na(lat) & !is.na(quarter)]
d[, yr := as.integer(substr(quarter, 1, 4))]
d[, qn := as.integer(substr(quarter, 6, 6))]
d[, qidx := (yr - 2019) * 4 + qn]                 # 2019Q1=1 ... 2025Q4=28
Q_TREAT <- (2022 - 2019) * 4 + 3                  # 2022Q3 = 15 (first post quarter)
d[, post := as.integer(qidx >= Q_TREAT)]
d[, nc := as.integer(typeofwork == "New Construction")]
d[, large := as.integer(is_large %in% c("True", TRUE, "TRUE", "true"))]
d[, units := as.numeric(numberofunits)]

# ---- spatial grid cells (independent geography, not the Python in_min flag) ----
d[, clat := floor(lat / GRID_LAT)]
d[, clng := floor(lng / GRID_LNG)]
d[, cell := paste(clat, clng, sep = "_")]

# cell treatment = share of the cell's permits that fall inside MIN
cellinfo <- d[, .(share_in = mean(in_min == "Y"), n = .N), by = cell]
cellinfo[, treated := as.integer(share_in >= 0.5)]
cellinfo[, mixed := as.integer(share_in > 0.2 & share_in < 0.8)]
d <- merge(d, cellinfo[, .(cell, treated, mixed, cell_n = n)], by = "cell")

cat(sprintf("Permits: %d | cells: %d (treated %d, control %d, mixed %d)\n",
            nrow(d), nrow(cellinfo), sum(cellinfo$treated),
            sum(cellinfo$treated == 0), sum(cellinfo$mixed)))

# ---- build a balanced cell x quarter panel of counts ----
build_panel <- function(dat) {
  agg <- dat[, .(n_large    = sum(large),
                 n_large_nc = sum(large * nc),
                 u_large    = sum(units * large, na.rm = TRUE)),
             by = .(cell, qidx)]
  cells <- unique(dat$cell); qs <- 1:28
  full <- CJ(cell = cells, qidx = qs)
  p <- merge(full, agg, by = c("cell", "qidx"), all.x = TRUE)
  p[is.na(n_large),    n_large    := 0]
  p[is.na(n_large_nc), n_large_nc := 0]
  p[is.na(u_large),    u_large    := 0]
  p <- merge(p, cellinfo[, .(cell, treated, mixed)], by = "cell")
  p[, post := as.integer(qidx >= Q_TREAT)]
  p[, treatpost := treated * post]
  p[, cellid := .GRP, by = cell]
  p[, etime := qidx - (Q_TREAT - 1)]   # e=0 is last pre-quarter (baseline ref)
  p[]
}
pan <- build_panel(d)
n_treated_cq_post <- pan[treated == 1 & post == 1, .N]

# =====================================================================
# 1. TWFE DiD — Poisson (rate) and OLS (levels), clustered by cell
# =====================================================================
res <- list()
run_twfe <- function(pan, y, tag) {
  fp <- feglm(as.formula(sprintf("%s ~ treatpost | cellid + qidx", y)),
              data = pan, family = "poisson", cluster = ~cell)
  fo <- feols(as.formula(sprintf("%s ~ treatpost | cellid + qidx", y)),
              data = pan, cluster = ~cell)
  b <- coef(fp)["treatpost"]; ci <- as.numeric(confint(fp)["treatpost", ])
  bo <- coef(fo)["treatpost"]; cio <- as.numeric(confint(fo)["treatpost", ])
  cat(sprintf("\n[%s]\n  Poisson treatpost = %.3f  => rate change %+.1f%% (95%% CI %+.1f%% .. %+.1f%%), p=%.4g\n",
              tag, b, 100*(exp(b)-1), 100*(exp(ci[1])-1), 100*(exp(ci[2])-1),
              pvalue(fp)["treatpost"]))
  cat(sprintf("  OLS  treatpost = %.4f per cell-quarter (95%% CI %.4f .. %.4f)\n",
              bo, cio[1], cio[2]))
  # deterred count (control-differenced): -OLS coef * treated cell-quarters post
  lost <- -bo * n_treated_cq_post
  lost_ci <- sort(-c(cio[1], cio[2]) * n_treated_cq_post)
  cat(sprintf("  => DiD-implied deterred %s (net of control): %.0f (95%% CI %.0f .. %.0f)\n",
              y, lost, lost_ci[1], lost_ci[2]))
  list(tag=tag, y=y, pois_b=unname(b), pois_pct=100*(exp(b)-1),
       pois_ci_pct=100*(exp(ci)-1), ols_b=unname(bo), ols_ci=unname(cio),
       lost=unname(lost), lost_ci=unname(lost_ci), p=unname(pvalue(fp)["treatpost"]))
}
res$large_nc <- run_twfe(pan, "n_large_nc", "New construction >=10u (primary)")
res$large    <- run_twfe(pan, "n_large",    "All types >=10u")
res$units    <- run_twfe(pan, "u_large",    "Units in >=10u projects")

# robustness: drop spatially mixed cells
pan_clean <- pan[mixed == 0]
res$large_nc_clean <- run_twfe(pan_clean, "n_large_nc", "New construction >=10u (drop mixed cells)")

# =====================================================================
# 2. Event study (parallel-trends check) on primary outcome
# =====================================================================
es <- feols(n_large_nc ~ i(etime, treated, ref = 0) | cellid + qidx,
            data = pan, cluster = ~cell)
esd <- as.data.table(broom::tidy(es, conf.int = TRUE))
esd <- esd[grepl("etime", term)]
esd[, e := as.integer(gsub(".*etime::(-?[0-9]+):.*", "\\1", term))]
fwrite(esd[order(e), .(e, estimate, conf.low, conf.high, std.error, p.value)],
       file.path(OUT, "event_study.csv"))
pre_joint <- tryCatch(wald(es, "etime::-([0-9]|1[0-3]):treated"), error=function(e) NA)
cat("\n[Event study] pre-treatment coefficients (e<0) should be ~0 for parallel trends.\n")
print(esd[order(e), .(e, estimate, conf.low, conf.high)])

p_es <- ggplot(esd[order(e)], aes(e, estimate)) +
  geom_hline(yintercept = 0, linetype = 2, color = "grey50") +
  geom_vline(xintercept = 0.5, linetype = 3, color = "firebrick") +
  geom_pointrange(aes(ymin = conf.low, ymax = conf.high)) +
  labs(title = "MIN event study — new-construction >=10u permits (cell x quarter)",
       subtitle = "Effect relative to last pre-treatment quarter (e=0); vertical line = MIN effect (2022Q3)",
       x = "Quarters relative to MIN", y = "DiD coefficient (permits per cell-quarter)") +
  theme_minimal(base_size = 11)
ggsave(file.path(OUT, "event_study.png"), p_es, width = 9, height = 5, dpi = 130)

# =====================================================================
# 3. Callaway-Sant'Anna robustness (canonical, citable)
# =====================================================================
cs_summary <- NULL
if (have_did) {
  pan[, gvar := ifelse(treated == 1, Q_TREAT, 0)]
  att <- did::att_gt(yname = "n_large_nc", tname = "qidx", idname = "cellid",
                     gname = "gvar", data = pan, control_group = "nevertreated",
                     panel = TRUE, allow_unbalanced_panel = TRUE, bstrap = TRUE, cband = TRUE)
  ov <- did::aggte(att, type = "simple", na.rm = TRUE)
  cs_summary <- list(att = unname(ov$overall.att), se = unname(ov$overall.se),
                     ci = unname(ov$overall.att + c(-1.96, 1.96) * ov$overall.se))
  cat(sprintf("\n[Callaway-Sant'Anna] overall ATT on new-construction >=10u = %.4f (SE %.4f)\n",
              cs_summary$att, cs_summary$se))
  cat(sprintf("  => CS-implied deterred NC permits (net of control): %.0f (95%% CI %.0f .. %.0f)\n",
              -cs_summary$att * n_treated_cq_post,
              -cs_summary$ci[2] * n_treated_cq_post, -cs_summary$ci[1] * n_treated_cq_post))
} else {
  cat("\n[Callaway-Sant'Anna] 'did' package unavailable — skipped.\n")
}

# =====================================================================
# 4. Translate to deterred UNITS and compare to the BPN headline
# =====================================================================
# unit-size estimators from pre-MIN inside-MIN large projects (matches Python)
pre_in_large <- d[large == 1 & in_min == "Y" & period == "pre" & !is.na(units), units]
q <- quantile(pre_in_large, c(.05, .95))
tm <- mean(pre_in_large[pre_in_large >= q[1] & pre_in_large <= q[2]])
u_mean <- mean(pre_in_large); u_med <- median(pre_in_large)

# (a) Flat 0% counterfactual reproduced in R (matches BPN headline logic)
mk <- d[large == 1 & in_min == "Y"]
lp_pre <- mk[period == "pre", .N]; lp_post <- mk[period == "post", .N]
flat_expected <- lp_pre / PRE_Y * POST_Y
flat_lost <- flat_expected - lp_post
cat(sprintf("\n[Flat 0%% counterfactual, reproduced in R] inside large: %d pre -> %d post; expected %.0f; lost %.0f permits\n",
            lp_pre, lp_post, flat_expected, flat_lost))
cat(sprintf("  Flat-counterfactual deterred units: mean %.0f / trimmed %.0f / median %.0f\n",
            flat_lost*u_mean, flat_lost*tm, flat_lost*u_med))

# (b) DiD control-differenced deterred units (from OLS all-types large lost permits)
did_lost_permits <- res$large$lost
did_lost_ci <- res$large$lost_ci
cat(sprintf("\n[DiD control-differenced] deterred all-types large permits: %.0f (95%% CI %.0f .. %.0f)\n",
            did_lost_permits, did_lost_ci[1], did_lost_ci[2]))
cat(sprintf("  DiD deterred units @ trimmed %.1f u/permit: %.0f (95%% CI %.0f .. %.0f)\n",
            tm, did_lost_permits*tm, did_lost_ci[1]*tm, did_lost_ci[2]*tm))
cat(sprintf("  DiD deterred units range (median %.0f .. mean %.0f u/permit): %.0f .. %.0f\n",
            u_med, u_mean, did_lost_permits*u_med, did_lost_permits*u_mean))

summary_out <- list(
  meta = list(csv = CSV, n_permits = nrow(d), n_cells = nrow(cellinfo),
              n_treated_cellquarters_post = n_treated_cq_post,
              grid_deg = c(GRID_LAT, GRID_LNG), q_treat = Q_TREAT),
  unit_estimators = list(mean = u_mean, trimmed = tm, median = u_med, n_pre_inside = length(pre_in_large)),
  twfe = res,
  callaway_santanna = cs_summary,
  flat_counterfactual = list(lost_permits = flat_lost,
                             units_mean = flat_lost*u_mean, units_trimmed = flat_lost*tm,
                             units_median = flat_lost*u_med),
  did_units = list(lost_permits = did_lost_permits, lost_permits_ci = did_lost_ci,
                   units_trimmed = did_lost_permits*tm,
                   units_ci = c(did_lost_ci[1]*tm, did_lost_ci[2]*tm),
                   units_range = c(did_lost_permits*u_med, did_lost_permits*u_mean))
)
jsonlite::write_json(summary_out, file.path(OUT, "min_did_summary.json"),
                     auto_unbox = TRUE, pretty = TRUE, digits = 4)
cat("\nWrote:", file.path(OUT, "min_did_summary.json"), "and event_study.{csv,png}\n")
