"use client";

import { RENT_GAP_ZIPS, MIN_RENTS } from "@/data/rent-gap";

/**
 * Rent-gap "dumbbell" — one row per MIN ZIP. MIN's 40%-AMI 2BR cap is a flat
 * anchor on the left; each row shows how far the voucher standard and market
 * rent sit ABOVE it. The distance is the point: the subsidy (voucher) or margin
 * (market) that has to fill the gap the mandate leaves. Replaces a grouped bar
 * chart whose horizontal cap line read as clutter behind 30 bars.
 */

const CAP = MIN_RENTS.br2;
const usd = (n: number) => `$${Math.round(n).toLocaleString()}`;

const rows = [...RENT_GAP_ZIPS]
  .map((z) => ({
    hood: z.hood,
    voucher: z.safmr.br2,
    market: z.market_2br_est ?? z.market_allunit ?? 0,
  }))
  .filter((r) => r.market > 0)
  .sort((a, b) => b.market - a.market);

const SCALE_MIN = 0;
const SCALE_MAX = Math.ceil(Math.max(...rows.map((r) => r.market)) / 500) * 500;
const pct = (v: number) => ((v - SCALE_MIN) / (SCALE_MAX - SCALE_MIN)) * 100;
const TICKS = Array.from({ length: SCALE_MAX / 500 + 1 }, (_, i) => i * 500);

const Dot = ({ v, color, title }: { v: number; color: string; title: string }) => (
  <div
    title={`${title}: ${usd(v)}`}
    className="absolute top-1/2 w-3 h-3 rounded-full border-2 border-white shadow-sm -translate-x-1/2 -translate-y-1/2 z-10"
    style={{ left: `${pct(v)}%`, background: color }}
  />
);

export const RentGapChart = () => {
  const capPct = pct(CAP);
  return (
    <div className="bg-white rounded-xl p-5 border border-gray-200 mb-6">
      <div className="text-sm font-semibold text-gray-700 mb-1">
        2-bedroom rent by MIN ZIP: how far the voucher and market sit above MIN&rsquo;s cap
      </div>
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-500 mb-4">
        <span className="flex items-center gap-1"><i className="inline-block w-2.5 h-2.5 rounded-full" style={{ background: "#c0392b" }} /> MIN 40%-AMI cap ({usd(CAP)}, citywide)</span>
        <span className="flex items-center gap-1"><i className="inline-block w-2.5 h-2.5 rounded-full" style={{ background: "#16a34a" }} /> Voucher standard (HUD SAFMR)</span>
        <span className="flex items-center gap-1"><i className="inline-block w-2.5 h-2.5 rounded-full" style={{ background: "#3b82f6" }} /> Market 2BR (Zillow est.)</span>
      </div>

      {/* rows: grid columns [label | track | value], gap-3. The flat cap guide is
          one line positioned by the same track geometry the dots use. */}
      <div className="relative">
        <div className="absolute top-0 bottom-0 border-l-2 border-dashed border-min-red/40 z-0"
          style={{ left: `calc(8.75rem + (100% - 13rem) * ${capPct / 100})` }} />

        <div className="space-y-2.5">
          {rows.map((r) => (
            <div key={r.hood} className="grid items-center gap-3" style={{ gridTemplateColumns: "8rem 1fr 3.5rem" }}>
              <div className="text-sm text-gray-700 text-right">{r.hood}</div>
              <div className="relative h-5">
                {/* base: $0 → cap (rent the tenant actually pays at the cap) */}
                <div className="absolute top-1/2 h-0.5 bg-min-red/20 -translate-y-1/2"
                  style={{ left: 0, width: `${capPct}%` }} />
                {/* gap segment: cap → market */}
                <div className="absolute top-1/2 h-0.5 bg-gray-300 -translate-y-1/2"
                  style={{ left: `${capPct}%`, width: `${Math.max(pct(r.market) - capPct, 0)}%` }} />
                <Dot v={CAP} color="#c0392b" title="MIN cap" />
                <Dot v={r.voucher} color="#16a34a" title="Voucher" />
                <Dot v={r.market} color="#3b82f6" title="Market 2BR" />
              </div>
              <div className="text-right text-sm font-semibold text-gray-700">{usd(r.market)}</div>
            </div>
          ))}
        </div>
      </div>

      {/* x-axis ticks */}
      <div className="grid items-center gap-3 mt-1 text-[10px] text-gray-400" style={{ gridTemplateColumns: "8rem 1fr 3.5rem" }}>
        <div />
        <div className="relative h-4">
          {TICKS.map((t) => (
            <span key={t} className="absolute -translate-x-1/2" style={{ left: `${pct(t)}%` }}>{usd(t)}</span>
          ))}
        </div>
        <div />
      </div>

      <p className="text-xs text-gray-400 mt-3">
        The green dot sits above the red cap in every ZIP — a voucher pays more than MIN&rsquo;s rent
        limit everywhere the overlay reaches, which is why the MIN units that get built lean on one. The
        blue-to-red distance is the full gap an unfunded mandate leaves for the market-rate units to carry.
      </p>
    </div>
  );
};
