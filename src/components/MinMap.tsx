"use client";

import { useMemo, useState } from "react";
import mapData from "@/data/generated/min-map.json";

/**
 * Map of the MIN overlay as it has grown, with housing projects of 10+ homes that
 * received a zoning permit since MIN took effect. Self-contained SVG: boundaries,
 * background streets and projects all come from src/data/generated/min-map.json
 * (analysis/build_map_data.py). No map tiles or outside services.
 */

type Ring = number[][];
type Polygon = Ring[];
interface Project {
  address: string;
  lng: number;
  lat: number;
  units: number;
  zp: string;
  bp: string | null;
  stage: string;
  inside: boolean;
}

const [X0, Y0, X1, Y1] = mapData.bbox;
const W = 1000;
const COS = Math.cos((((Y0 + Y1) / 2) * Math.PI) / 180);
const K = W / ((X1 - X0) * COS);
const H = Math.round((Y1 - Y0) * K);
const px = (lng: number) => (lng - X0) * COS * K;
const py = (lat: number) => (Y1 - lat) * K;

const ringPath = (ring: Ring) =>
  ring.map(([x, y], i) => `${i ? "L" : "M"}${px(x).toFixed(1)},${py(y).toFixed(1)}`).join("") + "Z";
const polyPath = (polys: Polygon[]) => polys.map((p) => p.map(ringPath).join("")).join("");
const linePath = (line: number[][]) =>
  line.map(([x, y], i) => `${i ? "L" : "M"}${px(x).toFixed(1)},${py(y).toFixed(1)}`).join("");

const STEPS = [
  { label: "July 2022", date: "2022-07-18" },
  { label: "July 2023", date: "2023-07-18" },
  { label: "July 2024", date: "2024-07-18" },
  { label: "July 2025", date: "2025-07-18" },
  { label: "July 2026", date: "2026-07-18" },
  { label: "Today", date: mapData.pulled },
];

const STAGE_STYLE: Record<string, { fill: string; stroke: string; label: string }> = {
  zoning: { fill: "#ffffff", stroke: "#c0392b", label: "Zoning permit only" },
  building: { fill: "#f5b041", stroke: "#b9770e", label: "Building permit issued" },
  complete: { fill: "#27ae60", stroke: "#1e8449", label: "Completed" },
};
const AREA_STYLE = [
  { fill: "#c0392b", opacity: 0.14, stroke: "#c0392b", dash: undefined as string | undefined },
  { fill: "#e67e22", opacity: 0.32, stroke: "#ca6f1e", dash: undefined as string | undefined },
  { fill: "#8e44ad", opacity: 0.22, stroke: "#7d3c98", dash: "4 3" as string | undefined },
];

const radius = (units: number) => 1.6 + Math.sqrt(units) * 0.85;
const fmtDate = (iso: string) =>
  new Date(`${iso}T12:00:00`).toLocaleDateString("en-US", { month: "short", year: "numeric" });

export const MinMap = () => {
  const [step, setStep] = useState(STEPS.length - 1);
  const [picked, setPicked] = useState<Project | null>(null);
  const asOf = STEPS[step].date;

  const streets = useMemo(() => (mapData.streets as number[][][]).map(linePath).join(""), []);
  const centerCity = useMemo(() => polyPath(mapData.greaterCenterCity as Polygon[]), []);
  const stages = mapData.stages.filter((s) => s.date <= asOf);
  const shown = (mapData.projects as Project[]).filter((p) => p.zp <= asOf);
  const inside = shown.filter((p) => p.inside);
  const count = (k: string) => inside.filter((p) => p.stage === k).length;
  const homes = inside.reduce((s, p) => s + p.units, 0);

  return (
    <div className="bg-white rounded-xl p-4 md:p-5 shadow-sm">
      <div className="text-sm font-semibold text-gray-700 mb-3">
        Where MIN applies, and the housing projects of 10+ homes that have received zoning permits since it took effect
      </div>

      <div className="flex flex-wrap gap-1.5 mb-3">
        {STEPS.map((s, i) => (
          <button
            key={s.label}
            type="button"
            onClick={() => setStep(i)}
            className={`px-2.5 py-1 rounded text-xs font-medium border transition-colors ${
              i === step ? "bg-bpn-dark text-white border-bpn-dark" : "bg-white text-gray-600 border-gray-300 hover:border-gray-500"
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto rounded border border-gray-200" role="img"
        aria-label="Map of the Mixed-Income Neighborhoods overlay and housing projects of ten or more homes">
        <rect width={W} height={H} fill="#f8f9fa" />
        <path d={streets} fill="none" stroke="#dfe3e8" strokeWidth={1} />
        <path d={centerCity} fill="none" stroke="#64748b" strokeWidth={1.2} strokeDasharray="6 4" />
        {stages.map((s) => {
          const st = AREA_STYLE[mapData.stages.findIndex((x) => x.id === s.id)];
          return (
            <path key={s.id} d={polyPath(s.polygons as Polygon[])} fill={st.fill} fillOpacity={st.opacity}
              stroke={st.stroke} strokeWidth={1.2} strokeDasharray={st.dash} fillRule="evenodd" />
          );
        })}
        {shown.filter((p) => !p.inside).map((p) => (
          <circle key={`${p.address}${p.zp}`} cx={px(p.lng)} cy={py(p.lat)} r={radius(p.units)} fill="#64748b"
            fillOpacity={0.28} stroke="#64748b" strokeOpacity={0.5} strokeWidth={0.8}
            onMouseEnter={() => setPicked(p)} onClick={() => setPicked(p)} style={{ cursor: "pointer" }} />
        ))}
        {inside.map((p) => {
          const st = STAGE_STYLE[p.stage];
          return (
            <circle key={`${p.address}${p.zp}`} cx={px(p.lng)} cy={py(p.lat)} r={radius(p.units)} fill={st.fill}
              fillOpacity={0.9} stroke={st.stroke} strokeWidth={2}
              onMouseEnter={() => setPicked(p)} onClick={() => setPicked(p)} style={{ cursor: "pointer" }} />
          );
        })}
        {mapData.labels.map((l) => (
          <text key={l.name} x={px(l.lng)} y={py(l.lat)} textAnchor="middle" fontSize={15} fontWeight={600}
            fill="#334155" stroke="#f8f9fa" strokeWidth={3.5} paintOrder="stroke" style={{ pointerEvents: "none" }}>
            {l.name}
          </text>
        ))}
      </svg>

      <div className="mt-3 text-sm text-gray-700 min-h-[2.5rem]">
        {picked ? (
          <span>
            <strong>{picked.address}</strong>: {picked.units} homes. Zoning permit {fmtDate(picked.zp)}
            {picked.bp ? `; building permit ${fmtDate(picked.bp)}` : "; no building permit"}.{" "}
            {picked.inside ? `${STAGE_STYLE[picked.stage].label}, inside MIN.` : "Outside MIN."}
          </span>
        ) : (
          <span className="text-gray-400">Point at or tap a circle for the project.</span>
        )}
      </div>

      <div className="mt-2 text-sm text-gray-700">
        Inside MIN by {STEPS[step].label.toLowerCase() === "today" ? "today" : STEPS[step].label}:{" "}
        <strong>{inside.length} projects, {homes.toLocaleString()} homes</strong>. {count("zoning")} with a zoning
        permit only, {count("building")} with a building permit, {count("complete")} completed.
      </div>

      <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-[11px] text-gray-600 mt-3">
        {Object.values(STAGE_STYLE).map((s) => (
          <span key={s.label} className="flex items-center gap-1">
            <span className="inline-block w-3 h-3 rounded-full" style={{ background: s.fill, border: `2px solid ${s.stroke}` }} />
            {s.label}
          </span>
        ))}
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-full" style={{ background: "#64748b", opacity: 0.4 }} />
          Project outside MIN
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-2 h-2 rounded-full border border-gray-500" />
          <span className="inline-block w-4 h-4 rounded-full border border-gray-500" />
          10 to 300+ homes
        </span>
      </div>
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-[11px] text-gray-600 mt-1.5">
        {mapData.stages.map((s, i) => (
          <span key={s.id} className="flex items-center gap-1">
            <span className="inline-block w-3.5 h-3 rounded-sm" style={{
              background: AREA_STYLE[i].fill, opacity: AREA_STYLE[i].opacity + 0.25,
              border: `1px ${AREA_STYLE[i].dash ? "dashed" : "solid"} ${AREA_STYLE[i].stroke}` }} />
            {s.label}: {s.note.charAt(0).toLowerCase() + s.note.slice(1)}, about {(Math.round(s.acres / 10) * 10).toLocaleString()} acres
          </span>
        ))}
        <span className="flex items-center gap-1">
          <span className="inline-block w-4 border-t border-dashed border-gray-500" />
          Greater Center City
        </span>
      </div>
    </div>
  );
};
