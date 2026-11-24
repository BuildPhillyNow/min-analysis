#!/usr/bin/env Rscript
# Diagnostics: reconcile TWFE vs Callaway-Sant'Anna, and test abatement-rush
# sensitivity. Self-contained (re-builds the panel).
suppressPackageStartupMessages({library(data.table); library(fixest); library(did)})
CSV <- "/Users/jongeeting/Projects/min-analysis/analysis/data/min_permits_enriched_2025.csv"
GRID_LAT <- 0.004; GRID_LNG <- 0.005
d <- fread(CSV); d <- d[!is.na(lng) & !is.na(lat) & !is.na(quarter)]
d[, yr := as.integer(substr(quarter,1,4))]; d[, qn := as.integer(substr(quarter,6,6))]
d[, qidx := (yr-2019)*4 + qn]; Q_TREAT <- 15
d[, nc := as.integer(typeofwork=="New Construction")]
d[, large := as.integer(is_large %in% c("True",TRUE,"TRUE","true"))]
d[, units := as.numeric(numberofunits)]
d[, clat := floor(lat/GRID_LAT)]; d[, clng := floor(lng/GRID_LNG)]; d[, cell := paste(clat,clng,sep="_")]
cellinfo <- d[, .(share_in=mean(in_min=="Y"), n=.N), by=cell]
cellinfo[, treated := as.integer(share_in>=0.5)]
agg <- d[, .(n_large=sum(large), n_large_nc=sum(large*nc), u_large=sum(units*large,na.rm=TRUE)), by=.(cell,qidx)]
full <- CJ(cell=unique(d$cell), qidx=1:28)
pan <- merge(full, agg, by=c("cell","qidx"), all.x=TRUE)
for(v in c("n_large","n_large_nc","u_large")) pan[is.na(get(v)), (v):=0]
pan <- merge(pan, cellinfo[,.(cell,treated)], by="cell")
pan[, post := as.integer(qidx>=Q_TREAT)]; pan[, treatpost := treated*post]
pan[, cellid := .GRP, by=cell]; pan[, gvar := ifelse(treated==1, Q_TREAT, 0)]
NT <- pan[treated==1 & post==1, .N]
cat(sprintf("treated cell-quarters (post) = %d\n\n", NT))

cs_run <- function(y, tag){
  a <- did::att_gt(yname=y, tname="qidx", idname="cellid", gname="gvar", data=pan,
                   control_group="nevertreated", panel=TRUE, bstrap=TRUE, cband=TRUE,
                   base_period="universal")
  s <- did::aggte(a, type="simple", na.rm=TRUE)
  dyn <- did::aggte(a, type="dynamic", na.rm=TRUE)
  # mean of post-treatment dynamic ATTs (e>=0)
  post_e <- dyn$egt >= 0
  mean_post <- mean(dyn$att.egt[post_e])
  cat(sprintf("[CS %s]\n  simple ATT = %.4f (SE %.4f) -> total %.0f permits/units\n",
              tag, s$overall.att, s$overall.se, -s$overall.att*NT))
  cat(sprintf("  dynamic mean(e>=0) = %.4f -> total %.0f\n", mean_post, -mean_post*NT))
  # pre-trend joint (e<0)
  pre_e <- dyn$egt < 0
  cat(sprintf("  pre-treatment dynamic ATTs (e<0): mean %.4f, range %.3f..%.3f\n",
              mean(dyn$att.egt[pre_e]), min(dyn$att.egt[pre_e]), max(dyn$att.egt[pre_e])))
  invisible(list(a=a,dyn=dyn,s=s))
}
r_nc <- cs_run("n_large_nc", "new-construction >=10u")
cat("\n"); r_all <- cs_run("n_large", "all-types >=10u")
cat("\n"); r_u  <- cs_run("u_large", "units in >=10u")

cat("\n--- print CS dynamic event-study (all-types) ---\n")
print(data.table(e=r_all$dyn$egt, att=round(r_all$dyn$att.egt,4)))

# ---- Abatement-rush sensitivity: drop 2021Q4-2022Q2 (qidx 12,13,14) ----
cat("\n===== RUSH-EXCLUDED (drop qidx 12-14) =====\n")
panx <- pan[!(qidx %in% c(12,13,14))]
NTx <- panx[treated==1 & post==1, .N]
for(y in c("n_large_nc","n_large")){
  fo <- feols(as.formula(sprintf("%s ~ treatpost | cellid + qidx", y)), data=panx, cluster=~cell)
  b <- coef(fo)["treatpost"]; ci <- as.numeric(confint(fo)["treatpost",])
  cat(sprintf("[rush-excl OLS %s] %.4f/cell-qtr (CI %.4f..%.4f) -> deterred %.0f (CI %.0f..%.0f)\n",
              y, b, ci[1], ci[2], -b*NTx, -ci[2]*NTx, -ci[1]*NTx))
}
# rush-excluded event-study pre-trend test (NC)
esx <- feols(n_large_nc ~ i(etime, treated, ref=0) | cellid + qidx,
             data=panx[, etime := qidx-(Q_TREAT-1)], cluster=~cell)
cat("\n[rush-excl] pre-trend Wald (NC):\n")
print(tryCatch(wald(esx, "etime::-([2-9]|1[01]):treated"), error=function(e) e$message))

# ---- Transparent 2-group aggregate DiD (district x MIN), matches Python framing ----
cat("\n===== TRANSPARENT district x MIN aggregate DiD =====\n")
d[, grp := paste0("CD", council_district, "_", ifelse(in_min=="Y","in","out"))]
ag2 <- d[, .(n_large=sum(large)), by=.(grp, qidx, inmin=in_min=="Y", post=as.integer(qidx>=Q_TREAT))]
full2 <- CJ(grp=unique(d$grp), qidx=1:28)
ag2 <- merge(full2, d[,.(grp,inmin=in_min=="Y")][!duplicated(grp)], by="grp")
ag2 <- merge(ag2, d[, .(n_large=sum(large)), by=.(grp,qidx)], by=c("grp","qidx"), all.x=TRUE)
ag2[is.na(n_large), n_large:=0]; ag2[, post:=as.integer(qidx>=Q_TREAT)]; ag2[, tp:=as.integer(inmin)*post]
f2 <- feols(n_large ~ tp | grp + qidx, data=ag2, cluster=~grp)
print(summary(f2))
