/**
 * Rent-gap dataset: HUD Small Area FMR (voucher payment standard) vs. MIN's
 * required 40%-AMI rent vs. Zillow market rent, for the ZIP codes where MIN's
 * developments actually sit.
 *
 * Sources are attributed in RENT_GAP_META. SAFMR and MIN rents are official and
 * bedroom-specific; the market column is a ZORI-derived approximation (Zillow is
 * all-unit blended, not bedroom-split), so SAFMR-vs-MIN is the rigorous comparison.
 * Generated from src/data/generated/rent-gap.json (see provenance CSV alongside it).
 */
import raw from "./generated/rent-gap.json";

export interface RentGapZip {
  zip: string;
  hood: string;
  safmr: { br0: number; br1: number; br2: number; br3: number };
  market_allunit: number | null;
  market_2br_est: number | null;
  safmr_minus_min_2br: number;
  market_minus_min_2br: number | null;
}

export const MIN_RENTS = raw.minRents as {
  br0: number;
  br1: number;
  br2: number;
  br3: number;
};

/** MIN-project ZIPs, sorted ascending by the SAFMR − MIN 2BR gap */
export const RENT_GAP_ZIPS = raw.zips as RentGapZip[];

export const RENT_GAP_META = raw.meta as {
  safmrSource: string;
  minSource: string;
  marketSource: string;
  note: string;
};
