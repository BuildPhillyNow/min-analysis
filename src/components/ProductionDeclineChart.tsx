import { E } from "@/data/evidence";

/**
 * Indexed decline chart. Each bar is yearly project starts under MIN as a share of
 * the same area's own 2016-2020 rate (=100%). Indexing lets two areas of very
 * different size be read on one scale. Plain HTML/CSS.
 */

const p = E.main.projects;
const rows = [
  {
    label: "Inside MIN",
    pct: 100 + p.insideChg,
    sub: `${p.insideBase} → ${p.insidePost} projects a year`,
    color: "#c0392b",
  },
  {
    label: "MIN in District 3 (West Philadelphia)",
    pct: 100 + E.district3.projects.insideChg,
    sub: `${E.district3.projects.insideBase} → ${E.district3.projects.insidePost} projects a year`,
    color: "#922b21",
  },
  {
    label: "MIN in District 7 (Kensington to Frankford)",
    pct: 100 + E.district7.projects.insideChg,
    sub: `${E.district7.projects.insideBase} → ${E.district7.projects.insidePost} projects a year`,
    color: "#d98880",
  },
  {
    label: "Comparable areas outside MIN",
    pct: 100 + p.controlChg,
    sub: `${p.controlBase} → ${p.controlPost} projects a year`,
    color: "#94a3b8",
  },
];

export const ProductionDeclineChart = () => (
  <div className="bg-white rounded-xl p-5 shadow-sm">
    <div className="text-sm font-semibold text-gray-700 mb-5">
      Housing projects of 10+ homes starting each year, as a share of the same area&rsquo;s 2016&ndash;2020 rate
    </div>

    <div className="space-y-5">
      {rows.map((r) => (
        <div key={r.label}>
          <div className="flex items-baseline justify-between mb-1.5">
            <span className="text-sm font-medium text-gray-800">{r.label}</span>
            <span className="text-xs text-gray-400">{r.sub}</span>
          </div>
          <div className="relative h-9 rounded bg-gray-100">
            <div className="absolute inset-y-0 right-0 border-r-2 border-dashed border-gray-400" />
            <div className="h-full rounded flex items-center justify-end pr-2 min-w-[2.5rem]"
              style={{ width: `${r.pct}%`, background: r.color }}>
              <span className="text-white text-sm font-bold">{r.pct}%</span>
            </div>
          </div>
        </div>
      ))}
    </div>

    <div className="flex justify-between text-[11px] text-gray-400 mt-2">
      <span>0</span>
      <span>100% = each area&rsquo;s 2016&ndash;2020 yearly rate</span>
    </div>
  </div>
);
