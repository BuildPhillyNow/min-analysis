/**
 * Figures from the November 2026 rebuild of the MIN analysis.
 * Written by analysis/export_site_data.py from the outputs of
 * analysis/project_starts.py, zoning_conversion.py and parcel_odds.py.
 * Nothing here is typed by hand; rerun the scripts to change it.
 */
import evidence from "@/data/generated/min-evidence.json";

export const E = evidence;

/** "−69%" from -69; "+7%" from 7 */
export const pct = (n: number) => `${n < 0 ? "−" : "+"}${Math.abs(n)}%`;
/** "−5" from -5, "12" from 12: a signed number with a real minus sign */
export const sg = (n: number) => (n < 0 ? `−${Math.abs(n)}` : String(n));
/** 798 -> "800", 94 -> "100": rounded to the nearest hundred for prose */
export const r100 = (n: number) => (Math.round(n / 100) * 100).toLocaleString();
/** "69%" from -69 */
export const drop = (n: number) => `${Math.abs(n)}%`;
