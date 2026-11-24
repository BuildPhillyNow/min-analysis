/**
 * Peer city inclusionary zoning program comparisons.
 *
 * Sources:
 * - Sightline Institute: "To Fix Inclusionary Zoning, Fund It" (Oct 2024)
 * - Sightline Institute: "Portland's IZ Program Is Finally Performing" (Nov 2025)
 * - Sightline Institute: "Oregon's New Path to Inclusionary Housing" (Mar 2026)
 * - Sightline Institute: "Now Fully Funded, Portland's Mandate Should Be a Model" (Feb 2024)
 * - City of Portland PHB: Inclusionary Housing data
 * - Baltimore City Council legislation (2024)
 * - Chicago ARO program data
 */

export interface CityProgram {
  city: string;
  state: string;
  programName: string;
  type: "funded" | "unfunded" | "reformed";
  setAside: string;
  amiTarget: string;
  deedRestrictionYears: number;
  triggerSize: string;
  fundingMechanism: string;
  costPerUnit: string | null;
  outcome: string;
  thresholdGaming: string | null;
  yearEnacted: number;
  yearReformed: number | null;
  keyLesson: string;
}

export const PEER_PROGRAMS: CityProgram[] = [
  {
    city: "Portland",
    state: "Oregon",
    programName: "Inclusionary Housing (post-reform)",
    type: "reformed",
    setAside: "10–20%",
    amiTarget: "60–80% AMI (flexible)",
    deedRestrictionYears: 99,
    triggerSize: "20+ units",
    fundingMechanism: "Full property tax exemption (10yr downtown, expanded citywide 2024). ~$220K subsidy per below-market unit.",
    costPerUnit: "~$220,000 (vs ~$250,000 for 100% affordable buildings)",
    outcome: "After 2024 full funding: threshold gaming returned to normal, projects restarted, ~300 rent-restricted homes/year projected. 1,967 affordable units created 2016–2024, 674 in pipeline.",
    thresholdGaming: "Pre-reform: share of projects at 19 units (just under threshold) DOUBLED to ~50% of multifamily projects. Post-reform: returned to normal.",
    yearEnacted: 2017,
    yearReformed: 2024,
    keyLesson: "Underfunded IZ suppressed housing for 7 years. Full funding reversed the damage. The affordable units 'hitch a ride' on market-rate projects at lower public cost than standalone affordable buildings.",
  },
  {
    city: "Philadelphia",
    state: "Pennsylvania",
    programName: "MIN Overlay",
    type: "unfunded",
    setAside: "20%",
    amiTarget: "40% AMI",
    deedRestrictionYears: 50,
    triggerSize: "10+ units",
    fundingMechanism: "None. Developer absorbs full cost. Payment in lieu allowed only for the last 5 of the 20 points, by waiver (§14-533(3)(b)(.1)); $0 collected.",
    costPerUnit: null,
    outcome: "19 affordable units delivered (per City 2025 MIR). Project starts of 10+ homes inside MIN down 61% from 2016–2020, against 47% in comparable areas; down 79% in its West Philadelphia half. $0 revenue to city.",
    thresholdGaming: "No threshold gaming detected — developers are not downsizing, they are simply not building.",
    yearEnacted: 2022,
    yearReformed: null,
    keyLesson: "The most aggressive unfunded IZ in the country. 20% at 40% AMI with no subsidy makes the math impossible for most projects. The result: a freeze, not a shift.",
  },
  {
    city: "Baltimore",
    state: "Maryland",
    programName: "Inclusionary Housing (reformed 2024)",
    type: "reformed",
    setAside: "5% + 5%",
    amiTarget: "50% + 60% AMI",
    deedRestrictionYears: 30,
    triggerSize: "20+ units",
    fundingMechanism: "Annual tax credit matching actual forgone rent revenue. Auto-calibrates to market conditions.",
    costPerUnit: null,
    outcome: "Previous law (2007–2022): 34 affordable units in 14 years. City never funded the gap, so developers got waivers. 2024 reform designed to avoid this by auto-calibrating.",
    thresholdGaming: null,
    yearEnacted: 2007,
    yearReformed: 2024,
    keyLesson: "Unfunded mandates produce waivers, not housing. Baltimore's auto-calibrating tax credit is designed to prevent the funding gap that killed the original program.",
  },
  {
    city: "Shoreline",
    state: "Washington",
    programName: "Mandatory Inclusionary Housing",
    type: "funded",
    setAside: "20%",
    amiTarget: "70–80% AMI",
    deedRestrictionYears: 99,
    triggerSize: "All multifamily near light rail",
    fundingMechanism: "20-year property tax exemption on residential portion.",
    costPerUnit: null,
    outcome: "Four 7-story buildings completed or under construction near two light rail stations. Some projects on hold due to interest rates.",
    thresholdGaming: null,
    yearEnacted: 2019,
    yearReformed: null,
    keyLesson: "Pairing IZ with transit upzoning and tax exemptions can produce density near transit. But even funded programs are sensitive to interest rate environments.",
  },
  {
    city: "Chicago",
    state: "Illinois",
    programName: "Affordable Requirements Ordinance (ARO)",
    type: "unfunded",
    setAside: "20%",
    amiTarget: "60% AMI",
    deedRestrictionYears: 30,
    triggerSize: "7+ units (with zoning change/city benefit)",
    fundingMechanism: "Fee-in-lieu available: $175K/unit downtown, $50K in low-income areas. Tax abatement (3yr full, then phased).",
    costPerUnit: null,
    outcome: "Only 2,798 affordable units since 2007. Concentrated in richest neighborhoods. Developers routinely pay fee rather than build. 'Further from full funding' per Sightline analysis.",
    thresholdGaming: null,
    yearEnacted: 2007,
    yearReformed: null,
    keyLesson: "Fee-in-lieu leakage: when the fee is cheap enough, developers pay it and the mandate produces revenue but few actual affordable units in the neighborhoods that need them most.",
  },
];

// ===== Oregon SB 1521 =====

export const OREGON_SB1521 = {
  passedDate: "March 4, 2026 (awaiting governor's signature)",
  scope: "Five-county Portland metro area (Multnomah, Washington, Clackamas, Columbia, Yamhill)",
  keyProvision: "Jurisdictions with inclusionary zoning programs must fully offset the cost of their mandates through tax breaks, fee waivers, or grants.",
  complianceDeadlines: {
    rental: "2028",
    overall: "2029",
  },
  enforcement: "Non-compliant IZ regulations become unenforceable on operative dates.",
  flexibility: "Cities can design varied affordability targets within buildings, set lower price targets, and use multiple funding mechanisms — as long as costs and benefits are roughly in balance.",
  significance: "First state legislation in the US to explicitly prohibit unfunded inclusionary zoning. Passed both chambers; awaiting governor's signature as of March 2026.",
  philadelphiaRelevance: "Philadelphia's MIN overlay — 20% at 40% AMI with no public subsidy — would be illegal under Oregon law. If Oregon can require funding, Philadelphia can too.",
  sponsor: "Sen. Khanh Pham (D-Portland)",
  quote: "Senate Bill 1521 is the Oregon legislature's attempt to ensure that any inclusionary zoning program cost-effectively empowers communities to build both market-rate and affordable homes.",
  comparison: "Similar to Florida's Live Local Act (2023), which also requires jurisdictions to fully fund local IZ mandates, but Oregon's approach uses standardized calculations rather than Florida's per-project model.",
};

// ===== Policy comparison table =====

export const POLICY_COMPARISON = {
  headers: ["Dimension", "Portland (reformed)", "Baltimore (reformed)", "Shoreline", "Philadelphia MIN", "Philadelphia MIHB"],
  rows: [
    ["Approach", "Mandatory + funded", "Mandatory + auto-calibrated", "Mandatory + funded", "Mandatory + unfunded", "Voluntary + funded"],
    ["Set-aside", "10–20%", "5% + 5%", "20%", "20%", "10%"],
    ["AMI target", "60–80%", "50% + 60%", "70–80%", "40%", "50% or 60%"],
    ["Public subsidy", "~$220K/unit tax exemption", "Tax credit matching costs", "20yr tax exemption", "None ($0)", "Density bonus + fee option"],
    ["Fee-in-lieu", "Available", "Not applicable", "Not available", "Last 5 of 20 points, by waiver", "Available (primary option)"],
    ["Trigger", "20+ units", "20+ units", "All multifamily", "10+ units", "Any size (voluntary)"],
    ["Duration", "99 years", "30 years", "99 years", "50 years", "50 years"],
    ["Threshold gaming", "Was 50%, now normal", "N/A", "N/A", "None (freeze)", "N/A"],
    ["Revenue to city", "Tax revenue forgone", "Tax revenue forgone", "Tax revenue forgone", "$0", "$37.0M to HTF"],
    ["Housing effect", "Production restarted", "Too early to tell", "Building near rail", "−37 pp DiD collapse", "Incentivizes density"],
  ],
};
