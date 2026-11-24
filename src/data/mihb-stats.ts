/**
 * Mixed Income Housing Bonus (MIHB) program data.
 *
 * Sources:
 * - 2019 Mixed Income Housing Bonus Report (City of Philadelphia DPD)
 * - 2020 Mixed Income Housing Bonus Report (City of Philadelphia DPD)
 * - 2021 Mixed Income Housing Bonus Report (City of Philadelphia DPD)
 * - 2023 Mixed Income Housing Programs Report (City of Philadelphia DPD)
 * - 2025 Mixed Income Housing Program Report (City of Philadelphia DPD, Aug 2026) — latest
 *
 * MIHB is the voluntary density bonus program (§14-702(7)).
 * MIN is the mandatory overlay (§14-533).
 * Both produce affordable housing, but through fundamentally different mechanisms.
 */

// ===== MIHB Annual Data =====

export const MIHB_ANNUAL = [
  {
    year: 2019,
    projects: 7,
    payments: 2334542,
    affordableUnitsStarted: 4,
    bonusMarketUnits: 66,
    note: "First year of expanded program. 25 total developers.",
  },
  {
    year: 2020,
    projects: 33,
    payments: 3642446,
    affordableUnitsStarted: 17,
    bonusMarketUnits: 160,
    note: "COVID year. 78 total developers. 86% chose fee-in-lieu.",
  },
  {
    year: 2021,
    projects: 90,
    payments: 20344491,
    affordableUnitsStarted: 82,
    bonusMarketUnits: 794,
    note: "Tax abatement rush. 77% chose payment. Formula increased mid-year.",
  },
  {
    year: 2022,
    projects: 7,
    payments: 1276458,
    affordableUnitsStarted: 32,
    bonusMarketUnits: 145,
    note: "Post-abatement crash. MIN takes effect Jul 18. Avg payment $182K.",
  },
  {
    year: 2023,
    projects: 3,
    payments: 7321356,
    affordableUnitsStarted: 48,
    bonusMarketUnits: null,
    note: "Fewer but larger payments ($2.44M avg). Nearly 90% chose low-income.",
  },
  {
    year: 2024,
    projects: null,
    payments: 1458073, // "Total Payments Received in 2024", 2024 report p. 14
    affordableUnitsStarted: 136,
    bonusMarketUnits: 1060,
    note: "20 projects got CO. 61 aff units created. First MIN CO (1615 Foulkrod).",
  },
  {
    year: 2025,
    projects: 4,
    payments: 585767,
    affordableUnitsStarted: 72,
    bonusMarketUnits: 473,
    note: "Per 2025 MIR: 17 developments completed, 72 aff + 473 market-rate units. First year payments fell below $1M since 2019. 14 new MIN units (40% AMI). $0 from MIN.",
  },
];

// ===== MIHB Cumulative (from 2024 report — most recent) =====

export const MIHB_CUMULATIVE = {
  /** Through end of 2025 (from 2025 Mixed Income Housing Program Report) */
  asOf: "December 2025",
  /** BUILT (CO'd) affordable units per 2025 MIR: 213 total MIH − 19 MIN = 194 MIHB */
  totalAffordableCreated: 194,
  /** Approved for construction, not yet built (2025 MIR pipeline: 123 total − 21 MIN ≈ 102) */
  totalAffordableInPipeline: 102,
  /** Deprecated created+under-construction figure (300) from the 2024 report — do not present as "built" */
  totalAffordableUnderConstruction: 159,
  totalAffordableCombined: 300,
  totalContributions: 36963133, // sum of MIHB_ANNUAL payments 2019–2025 (2024 = $1,458,073 per the 2024 report)
  contributionsLabel: "$37.0M",
  /** From 2021 data: ~77% chose fee-in-lieu, ~23% built units on-site */
  feeInLieuPct: 77,
  onSitePct: 23,
  /** Average payments by year */
  avgPayment2022: 182351,
  avgPayment2023: 2440452,
  /** 2024 highlights */
  projectsCompletedIn2024: 20,
  affordableUnitsCreatedIn2024: 61,
  affordableLeasedIn2024: 41,
  projectsUnderConstruction: 22,
  affordableUnderConstruction: 136,
  marketRateUnderConstruction: 1060,
};

// ===== 2025 Mixed Income Housing Program Report — authoritative headline facts =====
// Combined MIH program (MIHB + MIN). Source: City of Philadelphia DPD, Aug 2026.

export const MIH_2025_REPORT = {
  asOf: "December 2025",
  /** Since 2017 (whole MIH program, completed) */
  developmentsSince2017: 49,
  affordableSince2017: 213,
  marketRateSince2017: 1511,
  /** Split of the 213 completed affordable units */
  minAffordable: 19, // 40% AMI, since MIN took effect Jul 2022
  mihbAffordable: 194, // 213 − 19
  /** 2025 alone */
  developments2025: 17,
  affordable2025: 72,
  marketRate2025: 473,
  minNew2025: 14,
  payments2025: 585767,
  paymentsProjects2025: 4, // all MIHB; $0 from MIN
  /** Pipeline (approved for construction, not yet built) */
  pipelineDevelopments: 30,
  pipelineAffordable: 123,
  pipelineMarketRate: 891,
  pipelineMinProjects: 5,
  pipelineMinAffordable: 21,
};

// ===== MIHB Fee-in-Lieu Rates (from 2023 report, page 8) =====

export const MIHB_FEE_RATES = {
  /** FAR-bonus zones: CMX-3/4/5/RMX-3 etc */
  farZones: {
    min: { rate: 9, unit: "$/sqft × Total GFA", label: "MIN" },
    mihbLow: { rate: 14.60, unit: "$/sqft × Total GFA", label: "MIHB Low Income" },
    mihbModerate: { rate: 11.30, unit: "$/sqft × Total GFA", label: "MIHB Moderate" },
  },
  /** Density-bonus zones: RM-1, CMX-1/2/2.5 */
  densityZones: {
    min: { rate: 10900, unit: "$/DU × Total DU Allowed", label: "MIN" },
    mihbLow: { rate: 17700, unit: "$/DU × Total DU Allowed", label: "MIHB Low Income" },
    mihbModerate: { rate: 13600, unit: "$/DU × Total DU Allowed", label: "MIHB Moderate" },
  },
};

// ===== Year-by-Year Comparison Table =====
// Affordable units = units with deed restrictions under either program
// Market-rate bonus = additional units enabled by the density/FAR bonus
// Sources: Annual Mixed Income Housing Program Reports (2019–2024)

export const YEAR_BY_YEAR = [
  {
    year: 2019,
    mihb: { affordableBP: 4, affordableCO: 0, marketRateBonus: 66, revenue: 2300000 },
    min: { affordableBP: 0, affordableCO: 0, marketRate: 0, revenue: 0, note: "Not yet enacted" },
  },
  {
    year: 2020,
    mihb: { affordableBP: 17, affordableCO: 4, marketRateBonus: 160, revenue: 3600000 },
    min: { affordableBP: 0, affordableCO: 0, marketRate: 0, revenue: 0, note: "Not yet enacted" },
  },
  {
    year: 2021,
    mihb: { affordableBP: 82, affordableCO: 7, marketRateBonus: 794, revenue: 20300000 },
    min: { affordableBP: 0, affordableCO: 0, marketRate: 0, revenue: 0, note: "Passed Dec 16, 2021" },
  },
  {
    year: 2022,
    mihb: { affordableBP: 32, affordableCO: 7, marketRateBonus: 145, revenue: 1300000 },
    min: { affordableBP: 0, affordableCO: 0, marketRate: 0, revenue: 0, note: "Takes effect Jul 18. 1 ZP issued Oct." },
  },
  {
    year: 2023,
    mihb: { affordableBP: 48, affordableCO: 20, marketRateBonus: null, revenue: 7300000 },
    min: { affordableBP: 5, affordableCO: 0, marketRate: 18, revenue: 0, note: "1615 Foulkrod BP issued (23u total, 5 aff)" },
  },
  {
    year: 2024,
    mihb: { affordableBP: 136, affordableCO: 61, marketRateBonus: 1060, revenue: 1500000 },
    min: { affordableBP: 11, affordableCO: 5, marketRate: 41, revenue: 0, note: "2 more reach BP. First CO: 1615 Foulkrod (5 aff units leased)" },
  },
  {
    year: 2025,
    mihb: { affordableBP: null, affordableCO: 58, marketRateBonus: 473, revenue: 585767 },
    min: { affordableBP: 21, affordableCO: 14, marketRate: null, revenue: 0, note: "14 new MIN units (40% AMI); total MIN now 19. Pipeline 5 projects / 21 aff. $0 revenue." },
  },
];

export const CUMULATIVE_COMPARISON = {
  mihb: {
    affordableCreated: 194, // built (CO'd), 2025 MIR
    affordableInPipeline: 102, // approved, not yet built
    affordableUnderConstruction: 102,
    affordableTotal: 194, // built only — the honest "delivered" number
    totalRevenue: 36963133,
    revenueLabel: "$37.0M",
    marketRateBonusUnits: "1,000+",
    programYears: "2019–2025 (7 years)",
  },
  min: {
    affordableDelivered: 19, // 2025 MIR
    affordableInPipeline: 21, // 2025 MIR pipeline
    affordableUnderConstruction: 21,
    affordablePaperOnly: 112, // our zoning-only tally (zoning permit, no building permit)
    totalRevenue: 0,
    revenueLabel: "$0",
    estimatedUnitsLost: 1200, // matched control, all types incl. conversions (~1,000–1,400)
    estimatedAffordableLost: 240,
    programYears: "Jul 2022 – 2025 report (no new completions in 2026, per CARTO)",
  },
};

// ===== MIN vs MIHB Comparison =====

export const MIN_VS_MIHB = {
  mihb: {
    name: "Mixed Income Housing Bonus (MIHB)",
    type: "Voluntary incentive",
    mechanism: "Density bonus in exchange for affordable units or payment to Housing Trust Fund",
    geography: "Citywide",
    affordableDelivered: 194, // built (CO'd), 2025 MIR
    affordableUnderConstruction: 102, // approved pipeline
    affordableCombined: 194, // built only
    revenueToCity: 36963133,
    revenueLabel: "$37.0M",
    feeInLieuAvailable: true,
    effectOnProduction: "Incentivizes additional density — developers build MORE because of the program",
    affordabilityLevel: "50% or 60% AMI (developer chooses)",
    setAsidePct: 10,
  },
  min: {
    name: "Mixed Income Neighborhoods Overlay (MIN)",
    type: "Mandatory requirement",
    mechanism: "20% affordability mandate on 10+ unit projects, no public subsidy",
    geography: "Parts of Council Districts 3 and 7",
    affordableDelivered: 19, // 2025 MIR
    affordableUnderConstruction: 21, // 2025 MIR pipeline
    affordablePaperOnly: 112,
    revenueToCity: 0,
    revenueLabel: "$0",
    /** Narrow: waiver only, last 5 of 20 points (§14-533(3)(b)(.1)). Not rendered. */
    feeInLieuAvailable: true,
    effectOnProduction: "Deters construction — developers build LESS or not at all",
    affordabilityLevel: "40% AMI (no choice)",
    setAsidePct: 20,
  },
};

// ===== Lost MIHB Revenue Estimate =====
// MIN allows a payment in lieu only by waiver, for the last 5 of its 20 points
// (§14-533(3)(b)(.1)); the City reports $0 collected. This block prices foregone
// MIHB fees on units that were never built.
// If lost projects had been built under MIHB instead:

export const LOST_REVENUE = {
  /** Matched-control deterred units (METHODOLOGY.md §2) — supersedes the ~3,000 within-district figure */
  lostUnits: 450,
  /** ~77% of deterred units would have chosen fee-in-lieu (citywide MIHB behavior) */
  feeInLieuRate: 0.77,
  estimatedFeePayingUnits: 347, // 450 × 0.77
  /** MIHB fee for density zones: $10,900/DU (MIN rate, most conservative) */
  perUnitFee: 10900,
  /** Estimated lost HTF revenue: 347 × $10,900 */
  estimatedLostRevenue: 3782700,
  estimatedLostRevenueLabel: "~$3.8M",
  /** At ~$15,000 per BSRP grant */
  bsrpGrantSize: 15000,
  /** Households that could have received home repairs */
  householdsHelped: 252,
  /** Basic Systems Repair Program grant maximum */
  bsrpMaxGrant: 20000,
  /** Note about the estimate */
  note: "Rescaled to the market-strength-matched deterrent (~450 new-construction units, methodology §2), applying the ~77% fee-in-lieu share. Uses the conservative MIN fee rate ($10,900/DU); at the MIHB low-income rate ($17,700/DU) the estimate is ~$6.1M. Supersedes the earlier within-district figure (~$25–33M), which rested on the inflated within-district deterrent.",
  /** Alternative calculation at MIHB Low Income rate */
  atMihbLowRate: {
    perUnitFee: 17700,
    estimatedLostRevenue: 6142050, // 347 × $17,700
    estimatedLostRevenueLabel: "~$6.1M",
    householdsHelped: 409,
  },
};

/**
 * CD3+CD7 specific lost revenue analysis.
 *
 * This is NOT the citywide MIHB revenue — MIN only applies in CD3+CD7.
 * We can't blame MIN for the citywide MIHB revenue drop (which was driven
 * by the tax abatement phaseout). But we CAN estimate what CD3+CD7 would
 * have contributed to the HTF if the deterred projects had been built under MIHB.
 *
 * The HOME bond (Neighborhood Preservation Initiative, 2023) borrowed
 * $400M+ for housing programs. MIHB revenue comes to the city for free.
 * Every dollar MIN suppressed had to be borrowed at municipal bond rates instead.
 */
export const CD3_CD7_LOST_REVENUE = {
  /** Matched-control deterred units inside MIN (METHODOLOGY.md §2) — supersedes ~3,000 */
  lostUnitsInsideMin: 450,
  /** Not all lost units would have used MIHB — ~77% chose fee-in-lieu citywide */
  feeInLieuRate: 0.77,
  /** Units that would have paid fee: 450 × 77% = ~347 */
  estimatedFeePayingUnits: 347,
  /** Conservative fee: $10,900/DU (MIN rate for density zones) */
  conservativeFee: 10900,
  /** Conservative lost revenue: 347 × $10,900 = ~$3.8M */
  conservativeLostRevenue: 3782300,
  conservativeLostRevenueLabel: "~$3.8M",
  /** At MIHB rate: 347 × $17,700 = ~$6.1M */
  mihbRateLostRevenue: 6141900,
  mihbRateLostRevenueLabel: "~$6.1M",
  /** BSRP equivalents at $15K/grant */
  conservativeBsrpGrants: 252,
  mihbRateBsrpGrants: 409,
  /** HOME bond comparison */
  homeBond: {
    totalBorrowed: 400000000,
    borrowingCostNote: "Municipal bonds carry interest costs; MIHB revenue is free",
    annualDebtService: "~$25M/year (estimated 30-year bond at ~4.5%)",
  },
};

// ===== Banned Density Bonuses =====
// MIN blocks access to floor area bonuses for CMX-3/4/5/RMX-3.
// These bonuses are the mechanism through which MIHB generates both
// affordable units AND fee-in-lieu revenue.

export const BANNED_BONUSES = {
  blockedZones: ["CMX-3", "CMX-4", "CMX-5", "RMX-3"],
  blockedBonusTypes: [
    { name: "Public Space", section: "§14-702(6)", note: "Only available if Mixed Income Housing bonus is also earned" },
    { name: "Transit Improvements", section: "§14-702(8)", note: "Only available if Mixed Income Housing bonus is also earned" },
    { name: "Underground Parking", section: "§14-702(9)", note: "Only available if Mixed Income Housing bonus is also earned" },
    { name: "Green Building", section: "§14-702(10)", note: "Only available if Mixed Income Housing bonus is also earned" },
  ],
  // RETIRED Nov 2026: tocFarBonusBlocked / tocUnitsBlockedByFar (1,364). §14-513(5)(a)(.2)
  // leaves MIN lots out of the 30% /TOC FAR increase, but Table 14-533-4 gives them
  // higher limits (CMX-3 in /TOC 800% vs 650%), so there is no net FAR loss.
  explanation: "MIN does not just impose an affordability mandate — it also blocks access to the floor area bonuses that are the primary mechanism for MIHB revenue generation. In CMX-3/4/5/RMX-3 zones, developers cannot earn any bonus except Mixed Income Housing, and only if they meet MIN's 20% at 40% AMI threshold first. This creates a catch-22: the bonus that would make the project economically viable is conditioned on meeting an affordability requirement that makes the project economically unviable.",
};
