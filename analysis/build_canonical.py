"""
Canonical project-level dataset for the MIN analysis. ONE deduplicated source
of truth for every classification/production figure on the site, with the rules
written down so the counts stop wobbling.

DEDUP RULE: one row per parcel (opa_account_num) = the largest-unit building
permit at that parcel (collapses shell+fitout and sequential permits). Rare
case of a parcel redeveloped twice in the 8-yr window is treated as one project.

ENTITLEMENT STATUS (uses the REAL development zoning-permit date `ent`, never the
build-date fallback):
  - entitled-under-MIN : ent >= 2022-07-18  (subject to MIN's mandate)
  - pre-MIN-pipeline    : ent <  2022-07-18  (grandfathered, not subject)
  - no-ZP-conversion    : ent is null        (MIN still covers conversions; date unknown)

CLASSIFICATION (program), incorporating the legal corrections:
  - MIN-affordable / MIHB : matched to the city MIR report project lists
  - subsidized            : LIHTC / PHA / nonprofit / senior / land-trust owners
  - institutional-exempt  : student housing built by the educational institution
                            (owner = Penn/Drexel/Trustees/University) -- exempt
  - market-rate           : everything else, INCLUDING private student housing
                            (The Mark / Landmark) which IS subject to MIN

GENUINE SET = market-rate + entitled-under-MIN (the clearly-subject-to-MIN new
development actually built under the mandate).
"""
import re, pandas as pd, numpy as np
from pathlib import Path
HERE = Path(__file__).parent
MIN = pd.Timestamp("2022-07-18", tz="UTC")

MIR_MIN = ["1615 FOULKROD","1611-13 FOULKROD","1611 FOULKROD","300-10 W NORRIS","300 W NORRIS","1931-33 N 2ND","1931 N 2ND"]
MIR_MIHB = ["5310 WHITBY","3748-52 LANCASTER","3748 LANCASTER","2400-18 E HUNTINGDON","2020-24 FRANKFORD","2019-25 N 29TH",
 "5521 WAYNE","1106-14 SPRING GARDEN","701 CECIL B MOORE","6767 GERMANTOWN","4400 MARKET","892-96 N 41ST","7611-19 GERMANTOWN",
 "20-30 W ALLENS","4701 WAYNE","2400-06 MASCHER","2400 MASCHER","3618 HAVERFORD","3620 HAVERFORD","4452 GRISCOM","2640-48 E LEHIGH",
 "5139 WAYNE","1900 N FRONT","1900-22 N FRONT","2406 FRANKFORD","1828 FRANKFORD"]
SUBSIDIZED = ["HOUSING AUTH","HABITAT","PENNROSE","WODA","INGERMAN","CONIFER","JONATHAN ROSE","MICHAELS","HACE","PROJECT HOME",
 "NEWCOURTLAND","NEW COURTLAND","IMPACT SERV","MISSION FIRST","AFFORDABLE","SENIOR HOUSING","LAND TRUST","COMMUNITY JUSTICE",
 "INTERCULTURAL","CDC","COMMUNITY DEV","HOUSING TRUST","REDEVELOPMENT","TURNER COURT","PEOPLE'S EMERGENCY","EMERGENCY CENTER",
 "ESPERANZA","GAUDENZIA","LIBERTY RESOURCES","STONEWATER","MOUNT VERNON MANOR","BEECH","DIGNITY","ELDERS PLACE","WOMEN'S COMMUNITY",
 "CATCH","SUSQUEHANNA NET","OPPORTUNITIES SERV","TRIANGLE SENIOR","VOLUNTEERS OF AMERICA","NORRIS SQUARE","NUEVA"]
INSTITUTION = ["TRUSTEES OF","UNIVERSITY OF PENN","DREXEL UNIV","TEMPLE UNIV","THOMAS JEFFERSON UNIV","UNIVERSITY CITY SCIENCE"]

def classify(addr, owner):
    a = str(addr).upper(); o = " " + str(owner).upper() + " "
    if any(t in a for t in MIR_MIN):  return "MIN-affordable"
    if any(t in a for t in MIR_MIHB): return "MIHB"
    if any(k in o for k in INSTITUTION): return "institutional-exempt"
    if any(k in o for k in SUBSIDIZED):  return "subsidized"
    return "market-rate"   # includes private student housing (The Mark)

def ent_status(ent):
    if pd.isna(ent): return "no-ZP-conversion"
    return "entitled-under-MIN" if ent >= MIN else "pre-MIN-pipeline"

def main():
    p = pd.read_csv(HERE/"data"/"projects_enriched_6plus.csv",
                    parse_dates=["permitissuedate","certificateofoccupancydate","ent","ent_eff"])
    p = p[p.units >= 10].copy()
    # DEDUP: largest-unit permit per parcel
    proj = p.sort_values("units", ascending=False).drop_duplicates("opa").copy()
    proj["cls"] = [classify(a, o) for a, o in zip(proj.address, proj.owner)]
    proj["estatus"] = proj.ent.map(ent_status)
    proj["completed"] = proj.status.astype(str).str.upper().str.contains("COMPLET") | proj.certificateofoccupancydate.notna()
    ins = proj[proj.in_min == "Y"].copy()
    ins.to_csv(HERE/"data"/"canonical_min_projects.csv", index=False)

    print(f"Canonical inside-MIN >=10u projects (deduped): {len(ins)}\n")
    print("By program class x entitlement status (projects / units):")
    for cls in ["market-rate","subsidized","institutional-exempt","MIN-affordable","MIHB"]:
        s = ins[ins.cls == cls]
        if not len(s): continue
        parts = ", ".join(f"{es}:{len(g)}/{int(g.units.sum())}u" for es,g in s.groupby("estatus"))
        print(f"  {cls:22s} total {len(s):2d}/{int(s.units.sum()):5d}u   [{parts}]")

    genuine = ins[(ins.cls=="market-rate") & (ins.estatus=="entitled-under-MIN")]
    print(f"\nGENUINE SET (market-rate incl. private student, entitled UNDER MIN): "
          f"{len(genuine)} projects, {int(genuine.units.sum())} units; "
          f"completed {int(genuine.completed.sum())} ({int(genuine[genuine.completed].units.sum())}u)")
    print(f"  by district: CD3 {len(genuine[genuine.council_district==3])} "
          f"({int(genuine[genuine.council_district==3].units.sum())}u), "
          f"CD7 {len(genuine[genuine.council_district==7])} ({int(genuine[genuine.council_district==7].units.sum())}u)")
    print(f"  The Mark (3615 Chestnut) in genuine set: {genuine.address.str.contains('3615 CHESTNUT', case=False).any()}")
    print(f"\nwrote data/canonical_min_projects.csv")

if __name__ == "__main__":
    main()
