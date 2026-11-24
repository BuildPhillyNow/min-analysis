"use client";

import { useEffect } from "react";
import Link from "next/link";
import { PageSection } from "@/components/layout/PageSection";
import { Callout } from "@/components/ui/Callout";
import { DataTable } from "@/components/ui/DataTable";
import { SubsidyDial } from "@/components/SubsidyDial";
import { RentGapChart } from "@/components/RentGapChart";
import { ProductionDeclineChart } from "@/components/ProductionDeclineChart";
import { UNIT_LOSS, MIN_PIPELINE, INSIDE_MIN_BUILT } from "@/data/min-stats";
import { MIH_2025_REPORT, CUMULATIVE_COMPARISON } from "@/data/mihb-stats";
import { RENT_GAP_ZIPS, MIN_RENTS } from "@/data/rent-gap";
import { MinMap } from "@/components/MinMap";
import { E, drop, sg, r100 } from "@/data/evidence";

const fmt = (n: number) => n.toLocaleString();
const usd = (n: number) => `$${Math.round(n).toLocaleString()}`;

// Q5 — Mayor Parker's H.O.M.E. Initiative (phila.gov, Mar 2025 / Mar 2026)
const HOME = { total: "$2 billion", homes: "30,000", newUnits: "13,500", bond: "$800 million" };

// Close — subsidy per unit to reach each affordability level (avg MIN 2BR, RENT_GAP_ZIPS)
const avgMarket2br = Math.round(
  RENT_GAP_ZIPS.reduce((s, z) => s + (z.market_2br_est ?? 0), 0) / RENT_GAP_ZIPS.length,
);
const closeRows = [40, 50, 60, 80].map((L) => {
  const rent = Math.round((MIN_RENTS.br2 * L) / 40);
  return { L, rent, sub: Math.max(avgMarket2br - rent, 0) };
});

const HeroStat = ({ value, label, red = true }: { value: string; label: string; red?: boolean }) => (
  <div className="bg-white/10 rounded-xl p-4">
    <div className={`font-(family-name:--font-display) font-black text-3xl md:text-4xl ${red ? "text-min-red" : "text-white"}`}>
      {value}
    </div>
    <div className="text-xs text-gray-400 mt-1">{label}</div>
  </div>
);

export default function HomePage() {
  // Deep links / cross-page nav land as "/#q1"; scroll after charts have sized the page.
  useEffect(() => {
    const id = window.location.hash.slice(1);
    if (!id) return;
    const t = setTimeout(() => {
      document.getElementById(id)?.scrollIntoView({ block: "start" });
    }, 400);
    return () => clearTimeout(t);
  }, []);

  return (
    <>
      {/* 0 — HOOK */}
      <section id="top" className="bg-bpn-dark text-white py-16 md:py-24">
        <div className="max-w-5xl mx-auto px-4 text-center">
          <p className="text-sm uppercase tracking-widest text-gray-400 mb-4">
            Build Philly Now &middot; November 2026
          </p>
          <h1 className="font-(family-name:--font-display) text-4xl md:text-6xl font-black leading-tight mb-6">
            The Mixed-Income Neighborhoods Overlay
          </h1>
          <p className="text-lg md:text-xl text-gray-300 max-w-3xl mx-auto mb-10">
            MIN was meant to produce affordable housing through private development. In four years it has
            produced {UNIT_LOSS.affordableUnitsProduced} affordable units. Over the same period, the number of
            housing projects starting inside the overlay fell {drop(E.main.projects.insideChg)}, against{" "}
            {drop(E.main.projects.controlChg)} in comparable parts of the city. In its West Philadelphia half the drop
            was {drop(E.district3.projects.insideChg)}. The record, in five questions.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
            <HeroStat value={String(UNIT_LOSS.affordableUnitsProduced)} label="affordable units produced, four years" red={false} />
            <HeroStat value={`−${drop(E.main.projects.insideChg)}`} label="housing projects starting inside MIN" />
            <HeroStat value={`−${drop(E.main.projects.controlChg)}`} label="the same measure in comparable areas" red={false} />
            <HeroStat value="$0" label="to the Housing Trust Fund" />
          </div>
        </div>
      </section>

      {/* 1 — Q1 */}
      <PageSection id="q1" heading="1. Is MIN producing affordable housing?">
        <p className="text-gray-700 mb-4">
          Since taking effect in July 2022, MIN has produced{" "}
          <strong>{MIN_PIPELINE.delivered.affordableUnits} affordable units</strong> across{" "}
          {MIN_PIPELINE.delivered.projects} completed developments, per the City&rsquo;s 2025 Mixed Income
          Housing Program Report. Of the {MIH_2025_REPORT.affordableSince2017} affordable units the whole
          mixed-income program (voluntary bonus included) has created citywide since 2017, MIN accounts for{" "}
          {MIH_2025_REPORT.minAffordable}. Its last completion was {INSIDE_MIN_BUILT.lastCompletion}, a year
          ago; none has finished since.
        </p>
        <Callout variant="info" title="The pipeline is not yet housing">
          <p>
            The City&rsquo;s 2025 report lists {MIN_PIPELINE.cityPipeline2025.projects} more MIN developments
            in the pipeline, holding {MIN_PIPELINE.cityPipeline2025.affordableUnits} affordable units. None is
            built. Approved units are not occupied units.
          </p>
        </Callout>
        <p className="text-gray-600 mt-6">
          The larger question is how much housing it prevented.
        </p>
      </PageSection>

      {/* 2 — Q2 */}
      <PageSection id="q2" background="cream" heading="2. Is it costing us housing overall?">
        <p className="text-gray-700 mb-6">
          Fewer housing projects are starting inside the overlay, and in its West Philadelphia half the drop is far
          steeper than in comparable parts of the city. In the four years before the 2021 tax-abatement rush, about{" "}
          {Math.round(E.main.projects.insideBase)} projects of 10 or more homes started inside MIN&rsquo;s boundaries
          each year. Since MIN took effect in July 2022, about {Math.round(E.main.projects.insidePost)} a year have.
          That is a <strong>{drop(E.main.projects.insideChg)} decline</strong>. In areas outside MIN with similar
          home prices, starts fell {drop(E.main.projects.controlChg)}. Counted in homes, the declines are{" "}
          {drop(E.main.units.insideChg)} and {drop(E.main.units.controlChg)}.
        </p>

        <div className="mb-3">
          <ProductionDeclineChart />
        </div>
        <p className="text-sm text-gray-500 mb-6">
          A project is counted in the year of its first permit, usually the zoning permit. Comparable areas are
          census tracts outside MIN whose home sale prices before 2020 fall in the same range as the tracts inside
          it. The gap between the top and bottom bars is {E.main.projects.gap} percentage points. Large projects are few and
          uneven from year to year, so the estimate is imprecise: its 95% range is {sg(E.main.projects.gapLow)} to{" "}
          {E.main.projects.gapHigh} points for projects and {sg(E.main.units.gapLow)} to {E.main.units.gapHigh} for
          homes. Both ranges include zero, so for the overlay as a whole a gap of this size could be chance. Other
          ways of choosing comparable areas give gaps of {E.gapRangeAcrossControls.projects[0]} to{" "}
          {E.gapRangeAcrossControls.projects[1]} points for projects and {E.gapRangeAcrossControls.units[0]} to{" "}
          {E.gapRangeAcrossControls.units[1]} for homes. The gap is clear in District 3 and not in District 7.
        </p>
        <p className="text-gray-700 mb-6">
          A second test looks at sites instead of projects. Among {E.parcelOdds.sites.toLocaleString()} privately
          owned parcels zoned for 10 or more homes, a site inside MIN became about half as likely to get a project
          as a site in a tract with similar prices outside it (odds ratio {E.parcelOdds.matched.or}, 95% range{" "}
          {E.parcelOdds.matched.low} to {E.parcelOdds.matched.high}).
        </p>

        <h3 className="font-(family-name:--font-display) text-lg font-black mb-3">
          Where MIN applies and what has been proposed there
        </h3>
        <div className="mb-3">
          <MinMap />
        </div>
        <p className="text-sm text-gray-500 mb-6">
          MIN has been enlarged twice. In April 2023 the 54th to 63rd Street corridor was added. In June 2026 the
          City widened its transit overlay to a quarter mile around 13 Market-Frankford Line stations, and every
          transit-overlay lot in Council District 7 is in MIN. The City has not yet redrawn its MIN map for that
          change, so the 2026 area shown here is approximate. Circles are projects of 10+ homes with a zoning permit
          issued since July 18, 2022; colors show each project&rsquo;s status today.
        </p>

        <h3 className="font-(family-name:--font-display) text-lg font-black mb-3">
          University City stopped tracking Center City
        </h3>
        <p className="text-gray-700 mb-4">
          The clearest case is University City, the one place outside Center City where high-rise housing has been
          built in volume. University City here means the part of the overlay inside the University City
          District&rsquo;s boundary, from the Schuylkill River west to 50th Street. In the four years before the
          abatement rush, {E.ucSize.uc.before.projects} projects of 10 or more homes started there, with{" "}
          {E.ucSize.uc.before.homes.toLocaleString()} homes. In four years under MIN,{" "}
          {E.ucSize.uc.underMin.projects} have, with {E.ucSize.uc.underMin.homes.toLocaleString()} homes. The
          Center City core kept most of its pace.
        </p>
        <DataTable
          caption="Housing projects of 10+ homes started, July 2016–July 2020 against July 2022–July 2026"
          headers={["", "Projects before", "Under MIN", "Homes before", "Under MIN", "Projects of 100+ homes before", "Under MIN"]}
          rows={(
            [["University City (inside MIN)", E.ucSize.uc], ["Center City core", E.ucSize.core], ["Greater Center City", E.ucSize.greater]] as const
          ).map(([name, x]) => [
            name, String(x.before.projects), String(x.underMin.projects), x.before.homes.toLocaleString(),
            x.underMin.homes.toLocaleString(), String(x.before.big), String(x.underMin.big),
          ])}
          highlightRow={0}
        />
        <p className="text-gray-700 mt-4 mb-4">
          The largest University City project started before MIN had {E.ucSize.uc.before.largest} homes. The
          largest started under it has {E.ucSize.uc.underMin.largest}. Of the earlier projects,{" "}
          {E.ucSize.ucBeforeEastOf40th} were east of 40th Street, beside the universities and hospitals. Of the projects started under
          MIN, {E.ucSize.ucUnderMinEastOf40th === 0 ? "none is" : `${E.ucSize.ucUnderMinEastOf40th} are`}.
        </p>
        <p className="text-sm text-gray-500 mb-6">
          Project starts fell {drop(E.ucVsCore.projects.insideChg)} in University City,{" "}
          {drop(E.ucVsCore.projects.controlChg)} in the Center City core and{" "}
          {drop(E.ucVsGreater.projects.controlChg)} in greater Center City. The gap is{" "}
          {E.ucVsCore.projects.gap} points against the core (95% range {sg(E.ucVsCore.projects.gapLow)} to{" "}
          {E.ucVsCore.projects.gapHigh}) and {E.ucVsGreater.projects.gap} against greater Center City (
          {sg(E.ucVsGreater.projects.gapLow)} to {E.ucVsGreater.projects.gapHigh}). Had homes started in University City
          at greater Center City&rsquo;s pace, about {r100(E.ucVsGreater.units.shortfall)} more would have started
          there in four years (range {r100(E.ucVsGreater.units.shortfallLow)} to{" "}
          {r100(E.ucVsGreater.units.shortfallHigh)}). The counts are small. Other explanations, such as the wave of
          laboratory construction in University City after 2021, have not been tested.
        </p>

        <h3 className="font-(family-name:--font-display) text-lg font-black mb-3">
          By council district
        </h3>
        <DataTable
          caption="Project starts of 10+ homes a year, 2016–2020 against July 2022–July 2026, and the gap against comparable areas"
          headers={["Part of MIN", "Before", "Under MIN", "Change", "Comparable areas", "Gap (95% range)"]}
          rows={[
            ["District 3", `${E.district3.projects.insideBase}/yr`, `${E.district3.projects.insidePost}/yr`,
              `−${drop(E.district3.projects.insideChg)}`, `−${drop(E.district3.projects.controlChg)}`,
              `${E.district3.projects.gap} points (${sg(E.district3.projects.gapLow)} to ${E.district3.projects.gapHigh})`],
            ["District 7", `${E.district7.projects.insideBase}/yr`, `${E.district7.projects.insidePost}/yr`,
              `−${drop(E.district7.projects.insideChg)}`, `−${drop(E.district7.projects.controlChg)}`,
              `${E.district7.projects.gap} points (${sg(E.district7.projects.gapLow)} to ${E.district7.projects.gapHigh})`],
          ]}
        />
        <p className="text-sm text-gray-500 mt-3 mb-6">
          MIN covers parts of Council Districts 3 and 7. Under the current council map, about 1,340 of its roughly
          38,500 parcels sit in District 4 and about 260 in District 8. The District 7 range includes zero, so the
          gap there could be chance. If project starts in District 3&rsquo;s part of MIN had fallen only as much as
          in comparable areas, about {r100(E.district3.units.shortfall)} more homes would have started there in four
          years (range {r100(E.district3.units.shortfallLow)} to {r100(E.district3.units.shortfallHigh)}).
        </p>

        <Callout variant="info" title="What the evidence does not show">
          <p className="mb-2">
            These comparisons cannot prove MIN caused the decline. Interest rates, construction costs and the end of
            the full tax abatement hit the whole city. The question is whether they hit MIN areas harder, and three
            findings limit the answer.
          </p>
          <p className="mb-2">
            For the overlay as a whole, the gap in project starts is within what chance could produce. It is clear
            in District 3 and in University City, and not in District 7.
          </p>
          <p className="mb-2">
            Close to the MIN line the gap nearly disappears. Within 1,500 feet of the boundary, project starts fell{" "}
            {drop(E.boundary1500.projects.insideChg)} just inside it and {drop(E.boundary1500.projects.controlChg)}{" "}
            just outside. The neighborhoods next to MIN, such as Fishtown, had their own slump.
          </p>
          <p>
            Projects that did get zoning permits under MIN went on to building permits at the same rate as
            comparable projects elsewhere: about {Math.round(E.conversion.insideUnderMin.ever / 10)} in 10 in both.
            The difference is in how many projects are proposed, not in how many of those proposed get built.
          </p>
        </Callout>
        <p className="text-gray-600 mt-6">
          This might be acceptable if a mandate were the only way to obtain affordability from private development.
          It is not.
        </p>
      </PageSection>

      {/* 3 — Q3 */}
      <PageSection id="q3" heading="3. Is the mandate necessary, and can it work on its own?">
        <p className="text-gray-700 mb-4">
          Most affordable units built inside the overlay come from subsidy, not the mandate. Since July 2022,
          large projects inside MIN account for{" "}
          <strong>{INSIDE_MIN_BUILT.affordableSubsidized} affordable units from subsidized developments</strong>{" "}
          (LIHTC or public housing) and <strong>{INSIDE_MIN_BUILT.affordableMandate} from MIN&rsquo;s requirement</strong>.
          Affordable housing in Philadelphia comes mainly through LIHTC, vouchers, and the voluntary bonus.
        </p>
        <p className="text-gray-700 mb-6">
          The MIN units that do get built typically rely on a housing voucher. HUD&rsquo;s voucher payment standard
          exceeds MIN&rsquo;s 40%-AMI rent cap in every ZIP the overlay covers.
        </p>

        <RentGapChart />

        <p className="text-gray-700 mb-6">
          Without a voucher, an unfunded mandate can pay for the affordable units only out of the market-rate units
          in the same building. That cross-subsidy works only where rents clear a break-even set by development cost.
          The dial below shows where each MIN neighborhood lands, for any mandate you set.
        </p>
        <SubsidyDial />
        <p className="text-gray-600 mt-6">
          If the goal is affordable units from private development, the City already runs a program that does more.
        </p>
      </PageSection>

      {/* 4 — Q4 */}
      <PageSection id="q4" background="cream" heading="4. How does it compare with the voluntary bonus?">
        <p className="text-gray-700 mb-6">
          Philadelphia runs two programs for this: the voluntary Mixed Income Housing Bonus and the mandatory MIN
          overlay. The voluntary one has produced more.
        </p>
        <DataTable
          headers={["", "MIHB — voluntary bonus", "MIN — mandate"]}
          rows={[
            ["Affordable units built, since 2017", fmt(CUMULATIVE_COMPARISON.mihb.affordableCreated), fmt(CUMULATIVE_COMPARISON.min.affordableDelivered)],
            ["Contributed to the Housing Trust Fund", CUMULATIVE_COMPARISON.mihb.revenueLabel, CUMULATIVE_COMPARISON.min.revenueLabel],
            ["Mechanism", "Incentivizes added density", "20% at 40% AMI required, no subsidy"],
            ["Fee-in-lieu option", "Available by right", "Last 5 of 20 points only, by waiver"],
          ]}
        />
        <p className="text-gray-700 mt-4">
          The incentive has produced roughly ten times the affordable units of the mandate, and funds the trust fund
          the mandate does not. MIN does allow a payment in lieu, but only for part of the requirement. Under
          &sect;14-533(3)(b)(.1), a developer can ask the Department of Planning and Development for a waiver to pay a
          fee, or to build the units off site within half a mile, for the last 5 of the 20 points. The fee is $9 per
          square foot of the maximum floor area allowed in RM-2/3/4, RMX, IRMX and CMX-3/4/5 districts, and $10,900
          per allowed unit in RM-1 and CMX-1/2/2.5. The first 15% must be built on site, with no buyout. The option
          has raised nothing. The City&rsquo;s 2024 program report says no MIN project had been granted a waiver, and
          its 2025 report lists no MIN payment.
        </p>
        <p className="text-gray-600 mt-6">
          The comparison matters now, because MIN&rsquo;s record bears on the City&rsquo;s largest housing commitment.
        </p>
      </PageSection>

      {/* 5 — Q5 */}
      <PageSection id="q5" heading="5. What is it doing to the H.O.M.E. Initiative?">
        <p className="text-gray-700 mb-6">
          The Parker administration&rsquo;s {HOME.total} H.O.M.E. Initiative aims to create and preserve{" "}
          {HOME.homes} homes, {HOME.newUnits} of them new construction, financed partly by an {HOME.bond} bond.
          MIN works against it three ways.
        </p>
        <div className="grid md:grid-cols-3 gap-4">
          <Callout variant="warning" title="Supply">
            <p>The plan counts on {HOME.newUnits} new homes. Project starts inside MIN are down {drop(E.main.projects.insideChg)} from their pace before 2020, against {drop(E.main.projects.controlChg)} in comparable areas.</p>
          </Callout>
          <Callout variant="warning" title="Money">
            <p>The plan borrows an {HOME.bond} bond to fund affordable housing. MIN&rsquo;s narrow fee-in-lieu option has raised {CUMULATIVE_COMPARISON.min.revenueLabel} since 2022, against MIHB&rsquo;s {CUMULATIVE_COMPARISON.mihb.revenueLabel} &mdash; trust-fund revenue that costs nothing to borrow.</p>
          </Callout>
          <Callout variant="warning" title="Transit">
            <p>Inside the overlay, the larger buildings the zoning code allows near transit (Table 14-533-4) come only with the 20% requirement. Transit-oriented zoning adds homes there only where a project can carry the mandate.</p>
          </Callout>
        </div>
        <p className="text-gray-600 mt-6">
          The record points to one conclusion.
        </p>
      </PageSection>

      {/* 6 — CLOSE */}
      <PageSection id="close" background="cream" heading="Fund it, or repeal it.">
        <p className="text-gray-700 mb-4">
          An unfunded mandate has no budget. It hands the cost of the affordable units to the developer and hopes the
          market absorbs it; where it doesn&rsquo;t, the units go unbuilt. Two responses fit the evidence, and this
          analysis favors neither: fund the affordability, or drop the requirement. The one the evidence rejects is
          treating the mandate as free.
        </p>
        <p className="text-gray-700 mb-4">
          That cost is estimable. Renting a 2-bedroom at each affordability level instead of at market takes roughly
          this monthly subsidy in the average MIN neighborhood.
        </p>
        <DataTable
          caption="Monthly subsidy per affordable 2-bedroom, by depth of affordability (average MIN neighborhood)"
          headers={["Affordability level", "Allowed rent", "Subsidy per unit / mo", "Per unit / yr"]}
          rows={closeRows.map((r) => [
            `${r.L}% AMI${r.L === 40 ? " (MIN's requirement)" : ""}`,
            usd(r.rent),
            r.sub > 0 ? usd(r.sub) : "about $0",
            r.sub > 0 ? usd(r.sub * 12) : "about $0",
          ])}
        />
        <p className="text-sm text-gray-500 mt-2 mb-6">
          MIN sets its requirement at the deepest level, 40% of AMI, unfunded. Shallower requirements cost far less; by
          60% of AMI, much of the overlay&rsquo;s market rents already meet the cap.
        </p>
        <Callout variant="info" title="Other jurisdictions have addressed this">
          <p>
            Oregon has made unfunded inclusionary zoning unlawful; Florida requires localities to offset its full cost.
            The shared principle: affordable units are a public good, and should be paid for publicly rather than
            mandated for free.
          </p>
        </Callout>
        <div className="flex flex-wrap gap-3 mt-8">
          <Link href="/memo/" className="px-5 py-2.5 bg-bpn-dark text-white rounded-lg text-sm font-medium hover:bg-gray-800">
            Read the full memo
          </Link>
          <Link href="/data/" className="px-5 py-2.5 border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:bg-white">
            Data and methodology
          </Link>
        </div>
      </PageSection>
    </>
  );
}
