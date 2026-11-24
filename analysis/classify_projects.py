"""
Classify every large (>=10u) inside-MIN building permit by ownership/program so
subsidized, public, and student-housing projects can be separated from genuine
market-rate development. Market-rate is what MIN's mandate actually deters;
subsidized/public/student projects are either exempt or affordable by other means
and should not count as "market-rate development recovering under MIN."

Sources of truth, in priority order:
  1. City MIR 2024 report (MIN & MIHB program projects, by address) -- authoritative.
  2. Owner/developer name heuristics for LIHTC / public / nonprofit / senior / student.
  3. Otherwise -> market-rate.

Also tags entitlement timing (earliest dev zoning permit vs MIN date 2022-07-18),
since the city defines MIN applicability by zoning-application date after 7/18/2022.

Output: analysis/data/min_large_projects_classified.csv
"""
import requests, pandas as pd
from pathlib import Path
HERE = Path(__file__).parent
CARTO = "https://phl.carto.com/api/v2/sql"
MIN = pd.Timestamp("2022-07-18", tz="UTC")

def q(sql):
    r = requests.get(CARTO, params={"q": sql}, timeout=120); r.raise_for_status()
    return pd.DataFrame(r.json()["rows"])

# --- MIR 2024 report project addresses (normalized street tokens) ---
MIR_MIN = ["1615 FOULKROD", "1611-13 FOULKROD", "1611 FOULKROD", "300-10 W NORRIS", "300 W NORRIS",
           "1931-33 N 2ND", "1931 N 2ND"]
MIR_MIHB = ["5310 WHITBY","3748-52 LANCASTER","2400-18 E HUNTINGDON","2020-24 FRANKFORD","2019-25 N 29TH",
            "5521 WAYNE","1106-14 SPRING GARDEN","701 CECIL B MOORE","6767 GERMANTOWN","4400 MARKET",
            "892-96 N 41ST","7611-19 GERMANTOWN","20-30 W ALLENS","4701 WAYNE","2400-06 MASCHER","2400 MASCHER",
            "3618 HAVERFORD","3620 HAVERFORD","4452 GRISCOM","2640-48 E LEHIGH","5139 WAYNE","1900 N FRONT",
            "1900-22 N FRONT","2406 FRANKFORD","1828 FRANKFORD"]

SUBSIDIZED_KW = ["HOUSING AUTH","PHA","HABITAT","PENNROSE","WODA","INGERMAN","CONIFER","JONATHAN ROSE",
    "MICHAELS","HACE","PROJECT HOME","NEWCOURTLAND","IMPACT SERV","MISSION FIRST","AFFORDABLE","SENIOR HOUSING",
    "LAND TRUST","COMMUNITY JUSTICE","INTERCULTURAL","CDC","COMMUNITY DEV","HOUSING TRUST","REDEVELOPMENT",
    "TURNER COURT","NEIGHBORHOOD RESTORATIONS","VOLUNTEERS OF AMERICA","APM","ASOCIACION","NORRIS"]
STUDENT_KW = ["MARK AT","LANDMARK","STUDENT","UNIVERSITY","CAMPUS","THE RADIAN","VUE","SCAPE"]

def norm(a): return str(a).strip().upper()
def in_list(addr, lst):
    a = norm(addr)
    return any(tok in a for tok in lst)

def classify(row, owner, contractor):
    a = norm(row.address); blob = f"{owner or ''} {contractor or ''}".upper()
    if in_list(a, MIR_MIN):   return "MIN-affordable (city report)"
    if in_list(a, MIR_MIHB):  return "MIHB (city report)"
    if any(k in blob for k in STUDENT_KW):     return "student housing (verify)"
    if any(k in blob for k in SUBSIDIZED_KW):  return "subsidized/public/LIHTC"
    return "market-rate"

def main():
    d = pd.read_csv(HERE/"data"/"min_permits_rebuilt.csv", parse_dates=["permitissuedate"])
    d["is_large"] = d.numberofunits.fillna(0) >= 10
    d["opa"] = d.opa_account_num.astype(str).str.split(".").str[0]
    lg = d[(d.in_min=="Y") & d.is_large].copy()

    # owners
    opas = [o for o in lg.opa.unique() if o and o!="nan"]
    own = {}
    for i in range(0, len(opas), 80):
        inc = ",".join(f"'{o}'" for o in opas[i:i+80])
        r = q(f"SELECT DISTINCT opa_account_num, opa_owner, contractorname FROM permits WHERE opa_account_num IN ({inc})")
        for _, x in r.iterrows():
            o = str(x.opa_account_num).split(".")[0]
            own.setdefault(o, (x.opa_owner, x.contractorname))
    # entitlement (earliest dev zoning permit per parcel)
    zp = q("""SELECT opa_account_num, permitissuedate FROM permits WHERE council_district IN ('3','7')
              AND permittype IN ('Zoning','Zoning Permit')
              AND typeofwork IN ('New construction, addition, GFA change','Combined Lot Line Relocation and New Development','New Construction')""")
    zp["zdate"] = pd.to_datetime(zp.permitissuedate, utc=True, errors="coerce")
    zp["opa"] = zp.opa_account_num.astype(str).str.split(".").str[0]
    ent = zp.dropna(subset=["zdate"]).groupby("opa")["zdate"].min()

    lg["opa_owner"] = lg.opa.map(lambda o: own.get(o, (None,None))[0])
    lg["contractor"] = lg.opa.map(lambda o: own.get(o, (None,None))[1])
    lg["classification"] = lg.apply(lambda r: classify(r, r.opa_owner, r.contractor), axis=1)
    lg["entitlement_date"] = lg.opa.map(ent)
    lg["entitled_period"] = lg.apply(lambda r: ("pre-MIN" if pd.notna(r.entitlement_date) and r.entitlement_date < MIN
                                     else ("post-MIN" if pd.notna(r.entitlement_date) else "no-ZP")), axis=1)
    lg["build_period"] = (lg.permitissuedate >= MIN).map({True:"post", False:"pre"})

    out = lg[["address","numberofunits","council_district","typeofwork","status",
              "permitissuedate","entitlement_date","build_period","entitled_period",
              "classification","opa_owner","contractor","opa"]].copy()
    out = out.rename(columns={"permitissuedate":"building_permit_date","numberofunits":"units",
                              "council_district":"cd"}).sort_values(["build_period","units"], ascending=[True,False])
    p = HERE/"data"/"min_large_projects_classified.csv"
    out.to_csv(p, index=False)
    print(f"Wrote {p}  ({len(out)} large inside-MIN projects)\n")

    # summary: post-MIN-build large projects by classification
    post = out[out.build_period=="post"]
    print("POST-MIN BUILD large inside-MIN projects by classification:")
    g = post.groupby("classification").agg(projects=("units","size"), units=("units","sum")).sort_values("units",ascending=False)
    print(g.to_string())
    mr = post[post.classification=="market-rate"]
    print(f"\nMARKET-RATE post-MIN-build large inside-MIN: {len(mr)} projects, {mr.units.sum():.0f} units")
    print(f"  of which post-MIN ENTITLED (truly new market-rate under MIN): {(mr.entitled_period=='post-MIN').sum()} projects")
    print("\nMarket-rate, post-MIN entitled (the genuine 'built new under MIN' set):")
    for _,r in mr[mr.entitled_period=='post-MIN'].sort_values("units",ascending=False).iterrows():
        print(f"  {r.address:26.26s} {r.units:4.0f}u CD{r.cd}  ZP {str(r.entitlement_date)[:10]}  {r.opa_owner}")

if __name__ == "__main__":
    main()
