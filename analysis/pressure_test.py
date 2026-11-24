"""
Pressure-test the MIN deterrent: does an effect survive in ANY defensible cut
after we go market-rate-only + entitlement-dated? Cuts: completions,
unit-weighted, hot-submarket (high-capacity zones), spillover (distant control),
and 9-unit threshold gaming vs zoned capacity.
"""
import re, numpy as np, pandas as pd
from pathlib import Path
HERE=Path(__file__).parent
MIN=pd.Timestamp("2022-07-18",tz="UTC"); PRE_Y=POST_Y=4.0
WIN0=pd.Timestamp("2018-07-18",tz="UTC"); WIN1=pd.Timestamp("2026-07-17",tz="UTC")

MIR_MIN=["1615 FOULKROD","1611-13 FOULKROD","1611 FOULKROD","300-10 W NORRIS","300 W NORRIS","1931-33 N 2ND","1931 N 2ND"]
MIR_MIHB=["5310 WHITBY","3748-52 LANCASTER","3748 LANCASTER","2400-18 E HUNTINGDON","2020-24 FRANKFORD","2019-25 N 29TH",
 "5521 WAYNE","1106-14 SPRING GARDEN","701 CECIL B MOORE","6767 GERMANTOWN","4400 MARKET","892-96 N 41ST","7611-19 GERMANTOWN",
 "20-30 W ALLENS","4701 WAYNE","2400-06 MASCHER","2400 MASCHER","3618 HAVERFORD","3620 HAVERFORD","4452 GRISCOM","2640-48 E LEHIGH",
 "5139 WAYNE","1900 N FRONT","1900-22 N FRONT","2406 FRANKFORD","1828 FRANKFORD"]
SUB=["HOUSING AUTH","HABITAT","PENNROSE","WODA","INGERMAN","CONIFER","JONATHAN ROSE","MICHAELS","HACE","PROJECT HOME",
 "NEWCOURTLAND","NEW COURTLAND","IMPACT SERV","MISSION FIRST","AFFORDABLE","SENIOR HOUSING","LAND TRUST","COMMUNITY JUSTICE",
 "INTERCULTURAL","CDC","COMMUNITY DEV","HOUSING TRUST","REDEVELOPMENT","TURNER COURT","PEOPLE'S EMERGENCY","EMERGENCY CENTER",
 "ESPERANZA","GAUDENZIA","LIBERTY RESOURCES","STONEWATER","MOUNT VERNON MANOR","BEECH","DIGNITY","ELDERS PLACE","WOMEN'S COMMUNITY",
 "CATCH","SUSQUEHANNA NET","OPPORTUNITIES SERV","TRIANGLE SENIOR","VOLUNTEERS OF AMERICA","NORRIS SQUARE","NUEVA"]
STU=["MARK AT","LANDMARK","STUDENT","CAMPUS APART","SCAPE","THE RADIAN","UNIVERSITY PARK"]
def classify(addr,owner):
    a=str(addr).upper()
    if any(t in a for t in MIR_MIN): return "MIN-program"
    if any(t in a for t in MIR_MIHB): return "MIHB-program"
    o=" "+str(owner).upper()+" "
    if any(k in o for k in STU): return "student"
    if any(k in o for k in SUB): return "subsidized"
    return "market-rate"

def rates(x,dcol,ps=WIN0,pe=MIN,qs=MIN,qe=WIN1,val=None):
    pre=x[(x[dcol]>=ps)&(x[dcol]<pe)]; post=x[(x[dcol]>=qs)&(x[dcol]<=qe)]
    if val: a,b=pre[val].sum(),post[val].sum()
    else: a,b=len(pre),len(post)
    py=(pe-ps).days/365.25; oy=(qe-qs).days/365.25
    return a,b,a/py,b/oy,(a/py-b/oy)/(a/py)*100 if a else 0
def did(sub,dcol,label,val=None):
    ins=sub[sub.in_min=="Y"]; out=sub[sub.in_min=="N"]
    ia,ib,ipr,ipo,idec=rates(ins,dcol,val=val); oa,ob,opr,opo,odec=rates(out,dcol,val=val)
    print(f"  {label:34s} inside {ia:>5.0f}->{ib:<5.0f}(-{idec:2.0f}%)  outside {oa:>4.0f}->{ob:<4.0f}(-{odec:3.0f}%)  DiD={idec-odec:+.0f}pp")

p=pd.read_csv(HERE/"data"/"projects_enriched_6plus.csv",
              parse_dates=["permitissuedate","permitcompleteddate","certificateofoccupancydate","ent","ent_eff"])
p["cls"]=[classify(a,o) for a,o in zip(p.address,p.owner)]
p["large"]=p.units>=10
mr=p[(p.cls=="market-rate")&p.large].copy()
print(f"market-rate large: {len(mr)} | zones: {mr.zoning.notna().sum()} have zoning\n")

print("=== BASELINE (market-rate large, all types) ===")
did(mr,"ent_eff","entitlement-dated (strict)"); did(mr,"permitissuedate","build-dated")

print("\n=== CUT 1: UNIT-WEIGHTED (sum of units, not permit counts) ===")
did(mr,"ent_eff","entitlement, units",val="units"); did(mr,"permitissuedate","build, units",val="units")

print("\n=== CUT 2: COMPLETIONS (delivered — status Completed or has CO date) ===")
comp=mr[(mr.status.astype(str).str.upper().str.contains("COMPLET"))|(mr.certificateofoccupancydate.notna())]
did(comp,"ent_eff","completed, permits"); did(comp,"ent_eff","completed, units",val="units")
# completion rate among post-MIN entitled large
def comprate(sub):
    done=(sub.status.astype(str).str.upper().str.contains("COMPLET"))|(sub.certificateofoccupancydate.notna())
    return done.mean()*100,len(sub)
for lab,mask in [("inside post-MIN entitled",(mr.in_min=="Y")&(mr.ent_eff>=MIN)),("outside post-MIN entitled",(mr.in_min=="N")&(mr.ent_eff>=MIN)),
                 ("inside pre-MIN entitled",(mr.in_min=="Y")&(mr.ent_eff<MIN)),("outside pre-MIN entitled",(mr.in_min=="N")&(mr.ent_eff<MIN))]:
    r,n=comprate(mr[mask]); print(f"    completion rate {lab:26s}: {r:.0f}% (n={n})")

print("\n=== CUT 3: HOT SUBMARKET (high-capacity zones CMX-2.5/3/4/5, RMX-3, IRMX) ===")
HOT=["CMX2.5","CMX3","CMX4","CMX5","RMX3","IRMX","CMX-2.5","CMX-3","CMX-4","CMX-5","RMX-3"]
mr["zn"]=mr.zoning.astype(str).str.upper().str.replace(" ","").str.replace("-","")
hot=mr[mr.zn.isin([z.replace("-","") for z in HOT])]
did(hot,"ent_eff","hot zones, entitlement"); did(hot,"permitissuedate","hot zones, build")

print("\n=== CUT 4: SPILLOVER (control = OUTSIDE parcels far from MIN, dist>1320ft) ===")
far=mr[(mr.in_min=="Y")|((mr.in_min=="N")&(mr.dist_min_ft>1320))]
near=mr[(mr.in_min=="N")&(mr.dist_min_ft<=1320)]
did(far,"ent_eff","distant control, entitlement"); did(far,"permitissuedate","distant control, build")
# is near-boundary outside more active post than distant? (spillover signature)
for lab,sub in [("outside NEAR MIN (<1320ft)",near),("outside FAR (>1320ft)",mr[(mr.in_min=='N')&(mr.dist_min_ft>1320)])]:
    a,b,_,_,dec=rates(sub,"ent_eff"); print(f"    {lab:26s}: {a}->{b} (-{dec:.0f}%)")

print("\n=== CUT 5: THRESHOLD GAMING (bunching just under 10 units) ===")
allp=p[p.cls=="market-rate"].copy()  # include 6-9u
def band(sub,lo,hi): return ((sub.units>=lo)&(sub.units<=hi)).sum()
for grp,mask in [("INSIDE",allp.in_min=="Y"),("OUTSIDE",allp.in_min=="N")]:
    sub=allp[mask]
    for per,pm in [("pre",sub.ent_eff<MIN),("post",sub.ent_eff>=MIN)]:
        s=sub[pm]; under=band(s,7,9); over=band(s,10,12); nine=band(s,9,9)
        print(f"  {grp} {per}: 7-9u={under:3d}  10-12u={over:3d}  ratio={under/over if over else float('nan'):.2f}  (exactly 9u={nine})")
# inside post-MIN 7-9u projects on parcels that could support 10+ (large lots / high-density zones)
gcand=allp[(allp.in_min=="Y")&(allp.ent_eff>=MIN)&(allp.units>=7)&(allp.units<=9)&(allp.typeofwork=="New Construction")]
print(f"\n  Inside post-MIN NEW 7-9u projects: {len(gcand)}")
for _,r in gcand.iterrows():
    cap = (r.total_area*2.5/900) if pd.notna(r.total_area) else np.nan  # conservative GFA~2.5x, 900 sqft/unit
    print(f"    {r.address:24.24s} {r.units:.0f}u  zoning={r.zoning}  lot={r.total_area}  est_capacity~{cap:.0f}" + ("  <= COULD EXCEED 10" if cap>=10 else ""))
PY
