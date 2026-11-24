/**
 * Key policy events for the MIN timeline chart annotations.
 *
 * Sources:
 * - Philadelphia City Council legislation records
 * - Bisnow Philadelphia (2025)
 * - Philadelphia Inquirer (Jan 2023)
 * - Axios Philadelphia (Jan 2022)
 */

export interface TimelineEvent {
  quarter: string;
  label: string;
  description: string;
  type: "policy" | "market" | "expansion";
}

export const TIMELINE_EVENTS: TimelineEvent[] = [
  {
    quarter: "2020Q4",
    label: "Abatement deadline (original)",
    description:
      "Original Dec 31, 2020 deadline for 100% 10-year tax abatement applications. Extended to 2021 due to COVID.",
    type: "market",
  },
  {
    quarter: "2021Q2",
    label: "MIN introduced",
    description:
      "June 24, 2021 — CMs Gauthier and Quiñones Sánchez introduce the Mixed Income Neighborhoods Overlay Bill.",
    type: "policy",
  },
  {
    quarter: "2021Q4",
    label: "Abatement rush + MIN passes",
    description:
      "Dec 31, 2021 — Extended abatement deadline. Developers flood L&I with permits. Dec 16 — MIN bill receives final Council approval (Bill 220519).",
    type: "market",
  },
  {
    quarter: "2022Q1",
    label: "New abatement rules take effect",
    description:
      "Jan 1, 2022 — Tax abatement reduced to 10%/year phase-down. 1% construction tax imposed on all new permits.",
    type: "market",
  },
  {
    quarter: "2022Q3",
    label: "MIN takes effect",
    description:
      "July 18, 2022 — MIN overlay becomes effective. 20% affordability mandate at 40% AMI on 10+ unit projects, no public subsidy.",
    type: "policy",
  },
  {
    quarter: "2022Q2",
    label: "Gauthier TOD stations + AHP",
    description:
      "May 2022 — Bill 220452 designates 52nd, 56th, 60th, 63rd St as TOD stations. Affordable Housing Preservation overlay (AHP) also passes.",
    type: "expansion",
  },
  {
    quarter: "2023Q1",
    label: "MIN expansion: Market St corridor",
    description:
      "Jan 2023 — CMs Gauthier and Jones introduce bill to add Market St (54th–63rd) and surrounding blocks to MIN overlay.",
    type: "expansion",
  },
  {
    quarter: "2024Q4",
    label: "MIN expansion: Buckius/Tioga",
    description:
      "Dec 2024 — Bill to expand MIN into Buckius St and Tioga St areas (Kensington/Northeast portions).",
    type: "expansion",
  },
];

/** The quarter where MIN takes effect — used to draw the dividing line */
export const MIN_EFFECTIVE_QUARTER = "2022Q3";

/** Abatement rush window */
export const ABATEMENT_RUSH_START = "2021Q4";
export const ABATEMENT_RUSH_END = "2022Q1";
