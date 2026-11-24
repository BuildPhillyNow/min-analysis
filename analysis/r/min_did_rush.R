#!/usr/bin/env Rscript
# Abatement-rush robustness: is the MIN deterrent an artifact of the 2021-22
# tax-abatement rush inflating the pre-MIN baseline? Test three pre-windows.
suppressPackageStartupMessages({library(data.table); library(fixest)})
CSV <- "/Users/jongeeting/Projects/min-analysis/analysis/data/min_permits_enriched_2025.csv"
d <- fread(CSV); d <- d[!is.na(quarter)]
d[, yr := as.integer(substr(quarter,1,4))]; d[, qn := as.integer(substr(quarter,6,6))]
d[, qidx := (yr-2019)*4 + qn]
d[, large := as.integer(is_large %in% c("True",TRUE,"TRUE","true"))]
d[, inside := in_min=="Y"]; d[, units := as.numeric(numberofunits)]
Q_TREAT <- 15  # 2022Q3

# unit-size estimators from pre-MIN inside-MIN large projects (matches Python/site)
pu <- d[large==1 & inside & qidx<Q_TREAT & !is.na(units), units]
q <- quantile(pu, c(.05,.95)); tm <- mean(pu[pu>=q[1] & pu<=q[2]])
u_mean <- mean(pu); u_med <- median(pu)
cat(sprintf("Unit-size estimators (pre inside large, n=%d): mean %.1f  trimmed %.1f  median %.1f\n\n",
            length(pu), u_mean, tm, u_med))

windows <- list(
  "Full pre (2019Q1-2022Q2)"       = 1:14,
  "Rush-excluded (drop 21Q4-22Q2)" = c(1:11),          # drop qidx 12,13,14
  "Clean pre-rush (2019Q1-2021Q2)" = 1:10
)
post_q <- Q_TREAT:28
POST_Y <- length(post_q)/4

cat(sprintf("%-34s | inside pre->post (ann) | outside pre->post (ann) | DiD pp | flat-lost | DiD-lost | units(trim)\n", "PRE WINDOW"))
cat(strrep("-",150), "\n")
for(nm in names(windows)){
  preq <- windows[[nm]]; PRE_Y <- length(preq)/4
  ip <- d[large==1 & inside & qidx %in% preq, .N]; ipo <- d[large==1 & inside & qidx %in% post_q, .N]
  op <- d[large==1 & !inside & qidx %in% preq, .N]; opo <- d[large==1 & !inside & qidx %in% post_q, .N]
  ipr<-ip/PRE_Y; ipor<-ipo/POST_Y; opr<-op/PRE_Y; opor<-opo/POST_Y
  idec <- (ipr-ipor)/ipr*100; odec <- (opr-opor)/opr*100
  did_pp <- idec - odec
  flat_lost <- ipr*POST_Y - ipo                       # 0% counterfactual (BPN headline logic)
  # DiD-adjusted lost: inside expected under control's growth factor
  did_lost <- ipr*(opor/opr)*POST_Y - ipo             # apply control's change to inside baseline
  cat(sprintf("%-34s | %4.1f -> %4.1f (-%4.1f%%) | %4.1f -> %4.1f (%+5.1f%%) | %5.1f | %6.0f | %6.0f | %5.0f (%.0f-%.0f)\n",
              nm, ipr, ipor, idec, opr, opor, -odec, did_pp,
              flat_lost, did_lost, flat_lost*tm, did_lost*u_med, flat_lost*u_mean))
}
cat("\nNotes:\n")
cat(" - flat-lost = inside continues at full pre-rate (0% growth); ignores control decline. BPN headline uses this.\n")
cat(" - DiD-lost  = inside baseline scaled by the CONTROL group's own change (control-differenced).\n")
cat(" - units(trim) applies trimmed mean 46.6 u/permit to flat-lost; parenthetical = DiD-lost x median .. flat-lost x mean.\n")
