"""
Market-rate-only, entitlement-dated MIN DiD -- the clean causal backbone.

Removes every confound surfaced in this analysis:
  * Excludes subsidized / public / LIHTC / student / MIHB / MIN-program projects
    (those aren't market-rate development responding to MIN's mandate), on BOTH
    the inside (treatment) and outside (control) groups.
  * Dates each project by its ENTITLEMENT (earliest development zoning permit) --
    the city's own MIN-applicability rule is "zoning permit application after
    July 18, 2022." Falls back to building-permit date for by-right projects
    with no development ZP (conversions entitled at build).
  * Symmetric 4-year window (2018-07-18 .. 2026-07-17).

Reports inside vs outside, DiD, and deterred permits/units, by both entitlement
date (primary) and build date (comparison).
"""
import re, requests
import numpy as np, pandas as pd
from pathlib import Path
HERE = Path(__file__).parent
CARTO = "https://phl.carto.com/api/v2/sql"
MIN = pd.Timestamp("2022-07-18", tz="UTC")
WIN = (pd.Timestamp("2018-07-18", tz="UTC"), pd.Timestamp("2026-07-17", tz="UTC"))
PRE_Y = POST_Y = 4.0

# --- classification (applied to inside AND outside large projects) ---
MIR_MIN = ["1615 FOULKROD","1611-13 FOULKROD","1611 FOULKROD","300-10 W NORRIS","300 W NORRIS","1931-33 N 2ND","1931 N 2ND"]
MIR_MIHB = ["5310 WHITBY","3748-52 LANCASTER","3748 LANCASTER","2400-18 E HUNTINGDON","2020-24 FRANKFORD","2019-25 N 29TH",
  "5521 WAYNE","1106-14 SPRING GARDEN","701 CECIL B MOORE","6767 GERMANTOWN","4400 MARKET","892-96 N 41ST",
  "7611-19 GERMANTOWN","20-30 W ALLENS","4701 WAYNE","2400-06 MASCHER","2400 MASCHER","3618 HAVERFORD","3620 HAVERFORD",
  "4452 GRISCOM","2640-48 E LEHIGH","5139 WAYNE","1900 N FRONT","1900-22 N FRONT","2406 FRANKFORD","1828 FRANKFORD","3748 LANCASTER"]
SUBSIDIZED = ["HOUSING AUTH","HABITAT","PENNROSE","WODA","INGERMAN","CONIFER","JONATHAN ROSE","MICHAELS","HACE",
  "PROJECT HOME","NEWCOURTLAND","NEW COURTLAND","IMPACT SERV","MISSION FIRST","AFFORDABLE","SENIOR HOUSING","LAND TRUST",
  "COMMUNITY JUSTICE","INTERCULTURAL","CDC","COMMUNITY DEV","HOUSING TRUST","REDEVELOPMENT","TURNER COURT",
  "PEOPLE'S EMERGENCY","EMERGENCY CENTER","ESPERANZA","GAUDENZIA","LIBERTY RESOURCES","LIBERTY HOUSING","STONEWATER",
  "MOUNT VERNON MANOR","BEECH","DIGNITY","ELDERS PLACE","WOMEN'S COMMUNITY","CATCH","SUSQUEHANNA NET","OPPORTUNITIES SERV",
  "TRIANGLE SENIOR","APM","ASOCIACION","VOLUNTEERS OF AMERICA","NORRIS SQUARE","NUEVA","GERMANTOWN DEVELOPMENT"]
STUDENT = ["MARK AT","LANDMARK","STUDENT","CAMPUS APART","SCAPE","THE RADIAN","THE VUE","UNIVERSITY PARK","UNIVERSITY CITY STUDENT"]
def norm(a): return " "+re.sub(r'\s+',' ',str(a).upper().strip())+" "
def has(a,lst):
    A=norm(a); return any(f" {t} " in A or A.strip().startswith(t) or t in A for t in lst)
def classify(addr, owner):
    a=str(addr).upper()
    if any(t in a for t in MIR_MIN):  return "MIN-program"
    if any(t in a for t in MIR_MIHB): return "MIHB-program"
    o=" "+str(owner).upper()+" "
    if any(f"{k}" in o for k in STUDENT):     return "student"
    if any(f"{k}" in o for k in SUBSIDIZED):  return "subsidized"
    return "market-rate"

def q(sql):
    r=requests.get(CARTO,params={"q":sql},timeout=120); r.raise_for_status(); return pd.DataFrame(r.json()["rows"])

def main():
    d=pd.read_csv(HERE/"data"/"min_permits_rebuilt.csv", parse_dates=["permitissuedate"])
    d=d[(d.permitissuedate>=WIN[0])&(d.permitissuedate<=WIN[1])].copy()
    d["is_large"]=d.numberofunits.fillna(0)>=10
    d["opa"]=d.opa_account_num.astype(str).str.split(".").str[0]
    lg=d[d.is_large].copy()

    # owners
    opas=[o for o in lg.opa.unique() if o and o!="nan"]
    own={}
    for i in range(0,len(opas),80):
        inc=",".join(f"'{o}'" for o in opas[i:i+80])
        r=q(f"SELECT DISTINCT opa_account_num,opa_owner FROM permits WHERE opa_account_num IN ({inc})")
        for _,x in r.iterrows(): own.setdefault(str(x.opa_account_num).split(".")[0], x.opa_owner)
    lg["opa_owner"]=lg.opa.map(own)
    lg["cls"]=lg.apply(lambda r: classify(r.address, r.opa_owner), axis=1)

    # entitlement date (earliest dev zoning permit per parcel, CD3/7)
    zp=q("""SELECT opa_account_num,permitissuedate FROM permits WHERE council_district IN ('3','7')
            AND permittype IN ('Zoning','Zoning Permit')
            AND typeofwork IN ('New construction, addition, GFA change','Combined Lot Line Relocation and New Development','New Construction')""")
    zp["zdate"]=pd.to_datetime(zp.permitissuedate,utc=True,errors="coerce")
    zp["opa"]=zp.opa_account_num.astype(str).str.split(".").str[0]
    ent=zp.dropna(subset=["zdate"]).groupby("opa")["zdate"].min()
    lg["ent"]=lg.opa.map(ent)
    lg["ent_eff"]=lg.ent.fillna(lg.permitissuedate)     # by-right fallback

    mr=lg[lg.cls=="market-rate"].copy()
    print(f"Large projects: {len(lg)} | market-rate: {len(mr)} (excluded: "
          f"{dict(lg[lg.cls!='market-rate'].cls.value_counts())})\n")

    def block(sub, datecol, label):
        ins=sub[sub.in_min=="Y"]; out=sub[sub.in_min=="N"]
        def rt(x):
            pre=(x[datecol]<MIN).sum(); post=(x[datecol]>=MIN).sum()
            return pre,post,pre/PRE_Y,post/POST_Y,(pre/PRE_Y-post/POST_Y)/(pre/PRE_Y)*100 if pre else 0
        ip,ipo,ipr,ipor,idec=rt(ins); op,opo,opr,opor,odec=rt(out)
        did=idec-odec
        flat=ipr*POST_Y-ipo
        ctl=opor/opr if opr else np.nan
        didadj=ipr*ctl*POST_Y-ipo
        print(f"[{label}]")
        print(f"  inside : {ip:3d}->{ipo:3d}  ({ipr:.1f}->{ipor:.1f}/yr, -{idec:.0f}%)")
        print(f"  outside: {op:3d}->{opo:3d}  ({opr:.1f}->{opor:.1f}/yr, -{odec:.0f}%)")
        print(f"  DiD = {did:.0f}pp | flat-counterfactual lost = {flat:.0f} | DiD-adjusted lost = {didadj:.0f} permits")
        return ip,ipo,flat,didadj

    print("="*70,"\nMARKET-RATE ONLY, symmetric 4-year window\n"+"="*70)
    for typ,mask in [("ALL TYPES >=10u", mr.is_large),("NEW CONSTRUCTION >=10u", mr.typeofwork=="New Construction")]:
        sub=mr[mask]
        print(f"\n### {typ}")
        block(sub,"ent_eff","by ENTITLEMENT date (primary — city MIN rule)")
        block(sub,"permitissuedate","by BUILD date (comparison)")

    # deterred units: unit-size from pre-MIN inside market-rate large (entitlement-dated)
    pin=mr[(mr.in_min=="Y")&(mr.ent_eff<MIN)&mr.numberofunits.notna()].numberofunits
    lo,hi=np.percentile(pin,[5,95]); tm=pin[(pin>=lo)&(pin<=hi)].mean()
    print(f"\nMarket-rate unit-size (pre-MIN inside, entitlement-dated, n={len(pin)}): mean {pin.mean():.1f} / trimmed {tm:.1f} / median {pin.median():.1f}")
    allt=mr[mr.is_large]; ins=allt[allt.in_min=="Y"]
    ip=(ins.ent_eff<MIN).sum(); ipo=(ins.ent_eff>=MIN).sum(); flat=ip/PRE_Y*POST_Y-ipo
    print(f"Deterred (flat, entitlement-dated all-types): {flat:.0f} permits -> ~{flat*tm:.0f} units (trimmed), range {flat*pin.median():.0f}-{flat*pin.mean():.0f}")
    mr.to_csv(HERE/"data"/"marketrate_large_projects.csv", index=False)
    print(f"\nWrote {HERE/'data'/'marketrate_large_projects.csv'}")

if __name__=="__main__":
    main()
