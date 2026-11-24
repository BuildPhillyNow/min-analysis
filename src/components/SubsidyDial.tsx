"use client";

import { useState } from "react";
import { RENT_GAP_ZIPS } from "@/data/rent-gap";

/**
 * "How high would rents need to go?" — the self-finance zone.
 *
 * An unfunded IZ mandate has no public money; the market-rate units must carry the
 * affordable discount. A project self-finances when its blended rent clears the developer
 * break-even rent BE:  (1−s)·M + s·min(affRent, M) ≥ BE.  Solving for M gives the
 * self-finance line: (BE − s·affRent)/(1−s) where the affordability cap binds (affRent < BE),
 * and simply BE where it does not — i.e. at workforce income levels the affordable rent no
 * longer discounts, so the constraint is just ordinary market-rate feasibility.
 * BE (2BR break-even, ~6% yield-on-cost) is shown as a BAND across a plausible all-in development-cost
 * range. Hard construction cost is ~constant citywide; land is the geographic variable and rises with
 * rents, so a single citywide band is generous to the mandate in high-rent areas. Rough; rigorous = pro forma.
 */

const AMI40_2BR = 1075;
const MIN_SETASIDE = 20;
const MIN_AMI = 40;
const MAXRENT = 3200;
const BE_LOW = 1713; // lower-cost construction
const BE_HIGH = 2267; // higher-cost construction

const usd = (n: number) => `$${Math.round(n).toLocaleString()}`;
const affordableRent = (ami: number) => Math.round((AMI40_2BR * ami) / 40);
const selfFinanceRent = (s: number, ami: number, be: number) => {
  const aff = affordableRent(ami);
  // Non-binding (affordable rent ≥ break-even): the project just needs to clear break-even.
  if (aff >= be) return be;
  // Binding: the market-rate units must carry the affordable discount.
  return (be - s * aff) / (1 - s);
};

const ROWS = [...RENT_GAP_ZIPS]
  .map((z) => ({ hood: z.hood, rent: z.market_2br_est ?? 0 }))
  .sort((a, b) => b.rent - a.rent);

export const SubsidyDial = () => {
  const [ami, setAmi] = useState(MIN_AMI);
  const [setAside, setSetAside] = useState(MIN_SETASIDE);

  const s = setAside / 100;
  const thrLow = selfFinanceRent(s, ami, BE_LOW);
  const thrHigh = selfFinanceRent(s, ami, BE_HIGH);
  const lowPct = Math.max(0, Math.min((thrLow / MAXRENT) * 100, 100));
  const highPct = Math.max(0, Math.min((thrHigh / MAXRENT) * 100, 100));

  const rows = ROWS.map((r) => {
    const state = r.rent >= thrHigh ? "clears" : r.rent >= thrLow ? "borderline" : "short";
    const gap = Math.max(thrLow - r.rent, 0);
    return { ...r, state, gap, pct: r.rent ? (gap / r.rent) * 100 : 0 };
  });
  const nClears = rows.filter((r) => r.state === "clears").length;
  const nBorder = rows.filter((r) => r.state === "borderline").length;
  const nShort = rows.filter((r) => r.state === "short").length;
  const isMIN = ami === MIN_AMI && setAside === MIN_SETASIDE;
  // Above this AMI the affordable rent meets/exceeds break-even: the cap stops binding and the line pins to BE.
  const nonBinding = affordableRent(ami) >= BE_HIGH;

  const barColor = (st: string) =>
    st === "clears" ? "bg-bpn-green/80" : st === "borderline" ? "bg-amber-400/80" : "bg-min-red/70";

  return (
    <div className="rounded-2xl border border-gray-200 bg-white shadow-sm overflow-hidden">
      <div className="bg-bpn-dark text-white px-6 py-4">
        <h3 className="font-(family-name:--font-display) font-black text-xl">
          How high would rents have to go for the mandate to work?
        </h3>
        <p className="text-gray-300 text-sm mt-1">
          With no public subsidy, an IZ mandate only pencils once market rents reach the{" "}
          <span className="text-white font-semibold">self-finance zone</span>, where the market-rate
          units can carry the affordable ones. The dials set the mandate — how deep, how many. The bars are
          each neighborhood&rsquo;s real market rent, and they don&rsquo;t move.
        </p>
      </div>

      <div className="px-6 pt-5 pb-4 grid sm:grid-cols-2 gap-x-6 gap-y-4 border-b border-gray-100">
        <div>
          <label className="flex justify-between text-sm font-semibold text-gray-700 mb-2">
            <span>Depth of affordability</span>
            <span className="text-min-red">{ami}% AMI{ami === MIN_AMI ? " · MIN" : ""}</span>
          </label>
          <input type="range" min={30} max={150} step={5} value={ami}
            onChange={(e) => setAmi(Number(e.target.value))} className="w-full accent-min-red" />
          <div className="text-xs text-gray-400 mt-1">Mandate depth &middot; 40% = MIN&rsquo;s target &middot; 80&ndash;120% = workforce</div>
        </div>
        <div>
          <label className="flex justify-between text-sm font-semibold text-gray-700 mb-2">
            <span>Share of units required affordable</span>
            <span className="text-min-red">{setAside}%{setAside === MIN_SETASIDE ? " · MIN" : ""}</span>
          </label>
          <input type="range" min={0} max={25} step={1} value={setAside}
            onChange={(e) => setSetAside(Number(e.target.value))} className="w-full accent-min-red" />
        </div>
      </div>

      <div className="px-6 py-3 bg-bpn-cream text-sm">
        <span className="font-bold text-gray-900">
          {isMIN ? "MIN today (20% @ 40% AMI):" : `At ${setAside}% @ ${ami}% AMI:`}
        </span>{" "}
        an unfunded mandate self-finances only where 2BR rents reach the{" "}
        <strong className="text-min-red">≈ {usd(thrLow)}–{usd(thrHigh)}/mo</strong> zone (it varies with
        development cost).{" "}
        <strong>{nClears}</strong> of {rows.length} neighborhoods clear it outright,{" "}
        <strong>{nBorder}</strong> are borderline, <strong>{nShort}</strong> fall short.
      </div>

      {nonBinding && (
        <div className="px-6 pb-3 -mt-1 bg-bpn-cream text-xs text-gray-500">
          At {ami}% AMI the required rent already meets a developer&rsquo;s break-even, so the mandate no
          longer discounts anything, and the zone is now plain market-rate feasibility. Neighborhoods still
          short of it are limited by rents rather than the mandate: their market rents don&rsquo;t cover new
          construction even with no requirement.
        </div>
      )}

      <div className="px-4 sm:px-6 py-5 space-y-2">
        {rows.map((r) => (
          <div key={r.hood} className="flex items-center gap-2 sm:gap-3">
            <div className="w-20 sm:w-32 shrink-0 text-xs sm:text-sm text-gray-700 truncate">{r.hood}</div>
            <div className="flex-1 h-6 sm:h-7 rounded bg-gray-100 relative overflow-hidden">
              <div className="absolute top-0 bottom-0 bg-gray-300/50 border-x border-gray-400/60"
                style={{ left: `${lowPct}%`, width: `${Math.max(highPct - lowPct, 0)}%` }} />
              <div className={`h-full rounded ${barColor(r.state)} relative`}
                style={{ width: `${Math.min((r.rent / MAXRENT) * 100, 100)}%` }} />
            </div>
            <div className="w-12 sm:w-16 shrink-0 text-right text-xs sm:text-sm font-semibold text-gray-700">{usd(r.rent)}</div>
            <div className="hidden sm:block w-32 shrink-0 text-right text-xs">
              {r.state === "clears" ? (
                <span className="text-bpn-green font-bold">✓ breaks even</span>
              ) : r.state === "borderline" ? (
                <span className="text-amber-600 font-semibold">borderline</span>
              ) : (
                <span className="text-min-red">+{usd(r.gap)} <span className="text-gray-400">(+{r.pct.toFixed(0)}%)</span></span>
              )}
            </div>
          </div>
        ))}
        {/* mobile-only color key (the status column is hidden below sm) */}
        <div className="flex sm:hidden flex-wrap gap-x-3 gap-y-1 pt-1 text-[11px] text-gray-500">
          <span className="flex items-center gap-1"><i className="w-2.5 h-2.5 rounded-sm bg-bpn-green/80" /> breaks even</span>
          <span className="flex items-center gap-1"><i className="w-2.5 h-2.5 rounded-sm bg-amber-400/80" /> borderline</span>
          <span className="flex items-center gap-1"><i className="w-2.5 h-2.5 rounded-sm bg-min-red/70" /> falls short</span>
        </div>
        <div className="flex items-center gap-2 sm:gap-3 pt-1 text-xs text-gray-400">
          <div className="w-20 sm:w-32 shrink-0" />
          <div className="flex-1 flex items-center gap-2">
            <span className="inline-block w-6 h-3 bg-gray-300/60 border-x border-gray-400/60" /> self-finance zone ≈ {usd(thrLow)}–{usd(thrHigh)}/mo (2BR)
          </div>
        </div>
      </div>

      <div className="px-6 pb-5">
        <div className="rounded-lg bg-min-red-light border border-red-200 px-4 py-2.5 text-sm text-gray-700">
          MIN assumes <strong>high and rising rents.</strong> At its real settings (20% @ 40% AMI) most of
          the overlay sits below the zone. The mandate is a bet that these neighborhoods keep climbing toward
          luxury rents; if rents stall, it stops producing.
        </div>
        <p className="text-xs text-gray-400 mt-3">
          Rough band. The self-finance zone is the 2BR market rent at which the market-rate units&rsquo;
          margin covers the affordable discount, at roughly a 6% yield on cost across a range of all-in
          development cost. Hard construction cost is about the same citywide; land is the part that varies by
          neighborhood, and it rises with rents, so a single cost band runs generous to the mandate in the
          priciest areas. Rents from Zillow (Jun 2026), AMI rents from the 2025 MIR. This is{" "}
          <strong>cost break-even, not a bankable return</strong>: a separate 150-unit pro forma finds a
          financeable deal needs 2BR rents above the band, so even &ldquo;breaks even&rdquo; neighborhoods may
          not attract financing. The rigorous version is a full per-project pro forma.
        </p>
      </div>
    </div>
  );
};
