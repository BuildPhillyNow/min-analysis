"use client";

import { PageSection } from "@/components/layout/PageSection";
import { DataTable } from "@/components/ui/DataTable";
import { UNIT_LOSS, MIN_PIPELINE } from "@/data/min-stats";
import { MIHB_CUMULATIVE, CUMULATIVE_COMPARISON } from "@/data/mihb-stats";
import { E, drop, sg, r100 } from "@/data/evidence";

const fmt = (n: number) => n.toLocaleString();

export default function MemoPage() {
  return (
    <>
      {/* Memo Header */}
      <div className="bg-white border-b-4 border-bpn-green">
        <div className="max-w-4xl mx-auto px-4 py-12">
          <div className="flex items-center gap-3 mb-6">
            <img src="/images/bpn-icon-green.png" alt="BPN" className="h-10" />
            <span className="font-(family-name:--font-display) font-bold text-lg text-gray-800">
              Build Philly Now
            </span>
          </div>
          <div className="text-sm text-gray-500 uppercase tracking-widest mb-4">
            Memorandum
          </div>
          <div className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-1 text-sm text-gray-700 mb-6">
            <span className="font-bold">TO:</span>
            <span>Members of Philadelphia City Council</span>
            <span className="font-bold">FROM:</span>
            <span>Jon Geeting, Build Philly Now</span>
            <span className="font-bold">DATE:</span>
            <span>March 2026, revised November 2026</span>
            <span className="font-bold">RE:</span>
            <span>
              The Mixed-Income Neighborhoods Overlay: A Parcel-Level Impact
              Analysis and Recommendations for Reform
            </span>
          </div>
          <div className="flex flex-wrap gap-3 print:hidden">
            <a
              href="/BPN_MIN_Memo.pdf"
              download
              className="inline-block px-4 py-2 bg-bpn-green text-white rounded text-sm font-medium hover:bg-bpn-green-dark transition-colors"
            >
              Download Memo (PDF) →
            </a>
            <a
              href="/data/"
              className="inline-block px-4 py-2 border border-bpn-green text-bpn-green rounded text-sm font-medium hover:bg-bpn-cream transition-colors"
            >
              Full Data Package →
            </a>
          </div>
        </div>
      </div>

      {/* Executive Summary */}
      <PageSection>
        <div className="max-w-4xl mx-auto prose-sm">
          <h2 className="font-(family-name:--font-display) text-2xl font-black mb-4">
            Executive Summary
          </h2>
          <p className="text-gray-700 mb-3">
            Philadelphia&rsquo;s Mixed-Income Neighborhoods (MIN) overlay imposed a
            20% affordable housing requirement at 40% of Area Median Income (AMI),
            with no public subsidy,
            on residential developments of 10 or more units in portions of Council
            Districts 3 and 7. It took effect July 18, 2022. Under the current council
            district map, about 1,340 of the overlay&rsquo;s roughly 38,500 parcels sit in
            District 4 and about 260 in District 8.
          </p>
          <p className="text-gray-700 mb-3">
            This memo compares housing projects of 10 or more homes that started inside
            the overlay with projects in comparable parts of the city, before and after
            MIN took effect. It draws on {fmt(E.cohortProjects)} projects that started
            between 2012 and 2026. The analysis was rebuilt from City permit data in
            November 2026 and replaces the estimates in earlier versions of this memo.
            The decline is steeper inside MIN than outside it. The difference is clear in
            the West Philadelphia half of the overlay and in University City; for the
            overlay as a whole it is within the range chance could produce.
          </p>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 my-6">
            <div className="bg-min-red-light rounded-lg p-3 text-center border border-red-200">
              <div className="font-(family-name:--font-display) font-black text-2xl text-min-red">
                −{drop(E.main.projects.insideChg)}
              </div>
              <div className="text-xs text-gray-600">housing projects starting inside MIN, against 2016&ndash;2020</div>
            </div>
            <div className="bg-gray-100 rounded-lg p-3 text-center">
              <div className="font-(family-name:--font-display) font-black text-2xl">
                −{drop(E.main.projects.controlChg)}
              </div>
              <div className="text-xs text-gray-600">the same measure in comparable areas outside MIN</div>
            </div>
            <div className="bg-gray-100 rounded-lg p-3 text-center">
              <div className="font-(family-name:--font-display) font-black text-2xl">
                {UNIT_LOSS.affordableUnitsProduced}
              </div>
              <div className="text-xs text-gray-600">affordable units delivered</div>
            </div>
            <div className="bg-gray-100 rounded-lg p-3 text-center">
              <div className="font-(family-name:--font-display) font-black text-2xl">
                {CUMULATIVE_COMPARISON.min.revenueLabel}
              </div>
              <div className="text-xs text-gray-600">paid to the Housing Trust Fund under MIN</div>
            </div>
          </div>

          <p className="text-gray-700">
            Near transit, the larger buildings the zoning code allows inside MIN come
            only with the 20% requirement, so transit-oriented zoning adds homes there
            only where a project can carry the mandate. Meanwhile, the city&rsquo;s voluntary Mixed Income Housing Bonus
            (MIHB) has built {MIHB_CUMULATIVE.totalAffordableCreated} affordable
            units and {MIHB_CUMULATIVE.contributionsLabel} in Housing
            Trust Fund revenue using the incentive-based approach MIN rejected.
            Portland, Oregon faced the same problems, reformed its program with full
            public funding, and saw construction restart. Oregon has since made
            unfunded inclusionary zoning illegal.
          </p>
        </div>
      </PageSection>

      {/* Section 1: Project starts */}
      <PageSection background="cream">
        <div className="max-w-4xl mx-auto">
          <h2 className="font-(family-name:--font-display) text-xl font-black mb-4">
            1. Fewer Projects Are Starting Inside MIN
          </h2>
          <DataTable
            caption="Housing projects of 10+ homes, by the year of each project's first permit. Before = July 2016 to July 2020; under MIN = July 2022 to July 2026."
            headers={["", "Before, per year", "Under MIN, per year", "Change"]}
            rows={[
              ["Projects inside MIN", String(E.main.projects.insideBase), String(E.main.projects.insidePost), `−${drop(E.main.projects.insideChg)}`],
              ["Projects in comparable areas", String(E.main.projects.controlBase), String(E.main.projects.controlPost), `−${drop(E.main.projects.controlChg)}`],
              ["Homes inside MIN", fmt(Math.round(E.main.units.insideBase)), fmt(Math.round(E.main.units.insidePost)), `−${drop(E.main.units.insideChg)}`],
              ["Homes in comparable areas", fmt(Math.round(E.main.units.controlBase)), fmt(Math.round(E.main.units.controlPost)), `−${drop(E.main.units.controlChg)}`],
            ]}
          />
          <p className="text-sm text-gray-600 mt-3">
            Comparable areas are census tracts outside MIN whose home sale prices before
            2020 fall in the same range as the tracts inside it. The baseline ends in
            July 2020 because the two years after it were distorted by the deadlines for
            the 10-year tax abatement, which pulled projects forward across the city.
          </p>
          <p className="text-sm text-gray-600 mt-3">
            The gap is {E.main.projects.gap} percentage points in projects and{" "}
            {E.main.units.gap} in homes. Large projects are few and uneven from year to
            year, so the estimates are imprecise. The 95% range is{" "}
            {sg(E.main.projects.gapLow)} to {E.main.projects.gapHigh} points for projects
            and {sg(E.main.units.gapLow)} to {E.main.units.gapHigh} for homes. Both ranges
            include zero, so for the overlay as a whole a gap of this size could be
            chance. Four other
            ways of choosing comparable areas give gaps of{" "}
            {E.gapRangeAcrossControls.projects[0]} to {E.gapRangeAcrossControls.projects[1]}{" "}
            points for projects and {E.gapRangeAcrossControls.units[0]} to{" "}
            {E.gapRangeAcrossControls.units[1]} for homes. Leaving out the first three
            months under MIN, when most permits had been filed before it took effect,
            gives {E.excludeFirstThreeMonths.projects.gap} and{" "}
            {E.excludeFirstThreeMonths.units.gap}.
          </p>
          <p className="text-sm text-gray-600 mt-3">
            If project starts inside MIN had fallen only as much as in comparable areas,
            about {r100(E.main.units.shortfall)} more homes would have started in the four
            years. The range on that figure runs from no shortfall to{" "}
            {r100(E.main.units.shortfallHigh)}. For District 3&rsquo;s part of the overlay
            alone the figure is about {r100(E.district3.units.shortfall)}, with a range of{" "}
            {r100(E.district3.units.shortfallLow)} to {r100(E.district3.units.shortfallHigh)}.
          </p>
          <p className="text-sm text-gray-600 mt-3">
            A second test looks at sites instead of projects. Among{" "}
            {fmt(E.parcelOdds.sites)} privately owned parcels zoned for 10 or more homes,
            a site inside MIN became about half as likely to get a project as a site in
            a tract with similar prices outside it (odds ratio {E.parcelOdds.matched.or},
            95% range {E.parcelOdds.matched.low} to {E.parcelOdds.matched.high}).
          </p>

          <h3 className="font-(family-name:--font-display) text-lg font-black mt-8 mb-3">
            By council district
          </h3>
          <DataTable
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
          <p className="text-sm text-gray-600 mt-3">
            The District 7 range includes zero, so the gap there could be chance.
          </p>
        </div>
      </PageSection>

      {/* Section 2: University City */}
      <PageSection>
        <div className="max-w-4xl mx-auto">
          <h2 className="font-(family-name:--font-display) text-xl font-black mb-4">
            2. University City Stopped Tracking Center City
          </h2>
          <p className="text-gray-700 mb-4">
            University City is the one place outside Center City where high-rise
            housing has been built in volume. Here it means the part of the overlay
            inside the University City District&rsquo;s boundary, from the Schuylkill
            River west to 50th Street. In the four years before the abatement rush,{" "}
            {E.ucSize.uc.before.projects} projects of 10 or more homes started there,
            with {fmt(E.ucSize.uc.before.homes)} homes. In four years under MIN,{" "}
            {E.ucSize.uc.underMin.projects} have, with {fmt(E.ucSize.uc.underMin.homes)}{" "}
            homes. The Center City core kept most of its pace.
          </p>
          <DataTable
            caption="Housing projects of 10+ homes started, July 2016–July 2020 against July 2022–July 2026"
            headers={["", "Projects before", "Under MIN", "Homes before", "Under MIN", "100+ home projects before", "Under MIN"]}
            rows={(
            [["University City (inside MIN)", E.ucSize.uc], ["Center City core", E.ucSize.core], ["Greater Center City", E.ucSize.greater]] as const
          ).map(([name, x]) => [
            name, String(x.before.projects), String(x.underMin.projects), x.before.homes.toLocaleString(),
            x.underMin.homes.toLocaleString(), String(x.before.big), String(x.underMin.big),
          ])}
            highlightRow={0}
          />
          <p className="text-sm text-gray-600 mt-3">
            The largest University City project started before MIN had{" "}
            {E.ucSize.uc.before.largest} homes; the largest started under it has{" "}
            {E.ucSize.uc.underMin.largest}. Of the earlier projects,{" "}
            {E.ucSize.ucBeforeEastOf40th} were east of 40th Street, beside the universities and hospitals.
            Of the projects started under MIN,{" "}
            {E.ucSize.ucUnderMinEastOf40th === 0 ? "none is" : `${E.ucSize.ucUnderMinEastOf40th} are`}.
          </p>
          <p className="text-sm text-gray-600 mt-3">
            Project starts fell {drop(E.ucVsCore.projects.insideChg)} in University City,{" "}
            {drop(E.ucVsCore.projects.controlChg)} in the Center City core and{" "}
            {drop(E.ucVsGreater.projects.controlChg)} in greater Center City. The gap is{" "}
            {E.ucVsCore.projects.gap} points against the core (95% range{" "}
            {sg(E.ucVsCore.projects.gapLow)} to {E.ucVsCore.projects.gapHigh}) and{" "}
            {E.ucVsGreater.projects.gap} against greater Center City (
            {sg(E.ucVsGreater.projects.gapLow)} to {E.ucVsGreater.projects.gapHigh}). Had homes
            started in University City at greater Center City&rsquo;s pace, about{" "}
            {r100(E.ucVsGreater.units.shortfall)} more would have started there in four
            years (range {r100(E.ucVsGreater.units.shortfallLow)} to{" "}
            {r100(E.ucVsGreater.units.shortfallHigh)}). The counts are small. Other
            explanations, such as the wave of laboratory construction in University City
            after 2021, have not been tested here.
          </p>
        </div>
      </PageSection>

      {/* Section 3: Limits */}
      <PageSection background="cream">
        <div className="max-w-4xl mx-auto">
          <h2 className="font-(family-name:--font-display) text-xl font-black mb-4">
            3. What the Evidence Does Not Show
          </h2>
          <p className="text-gray-700 mb-4">
            These comparisons cannot prove MIN caused the decline. Five findings limit
            what can be claimed.
          </p>
          <p className="text-gray-700 mb-3">
            <strong>For the overlay as a whole, the gap could be chance.</strong> The
            range on the overlay-wide gap in project starts includes zero. The gap is
            clear in District 3 and in University City, and not in District 7.
          </p>
          <p className="text-gray-700 mb-3">
            <strong>Close to the MIN line the gap nearly disappears.</strong> Within
            1,500 feet of the boundary, project starts fell{" "}
            {drop(E.boundary1500.projects.insideChg)} just inside it and{" "}
            {drop(E.boundary1500.projects.controlChg)} just outside. A site-by-site model
            of {fmt(E.parcelOdds.sites)} parcels zoned for 10 or more homes finds the
            same thing: against the city as a whole, a MIN site&rsquo;s odds of getting
            a project fell by more than half (odds ratio {E.parcelOdds.citywide.or}, 95%
            range {E.parcelOdds.citywide.low} to {E.parcelOdds.citywide.high}), but
            among sites within 1,500 feet of the line there is no difference (
            {E.parcelOdds.near1500.or}, range {E.parcelOdds.near1500.low} to{" "}
            {E.parcelOdds.near1500.high}). Neighborhoods next to MIN, such as Fishtown,
            had their own slump.
          </p>
          <p className="text-gray-700 mb-3">
            <strong>Projects that get zoning permits under MIN go on to building
            permits at the same rate as elsewhere.</strong>
          </p>
          <DataTable
            caption="Projects of 10+ homes that received a zoning permit after July 18, 2022: share with a building permit"
            headers={["", "Projects", "Within 12 months", "Within 18 months", "Within 24 months", "To date"]}
            rows={[
              ["Inside MIN", String(E.conversion.insideUnderMin.projects), `${E.conversion.insideUnderMin.m12}%`, `${E.conversion.insideUnderMin.m18}%`, `${E.conversion.insideUnderMin.m24}%`, `${E.conversion.insideUnderMin.ever}%`],
              ["Comparable areas", String(E.conversion.controlUnderMin.projects), `${E.conversion.controlUnderMin.m12}%`, `${E.conversion.controlUnderMin.m18}%`, `${E.conversion.controlUnderMin.m24}%`, `${E.conversion.controlUnderMin.ever}%`],
            ]}
          />
          <p className="text-sm text-gray-600 mt-3 mb-3">
            For zoning permits issued in 2020 to 2022, about{" "}
            {E.conversion.insideBefore.m24}% inside MIN and {E.conversion.controlBefore.m24}%
            in comparable areas reached a building permit within two years. Conversion
            has slowed everywhere. The difference under MIN is in how many projects are
            proposed, not in how many of those proposed get built.
          </p>
          <p className="text-gray-700 mb-3">
            <strong>MIN areas were growing faster than comparable areas before
            2020.</strong> Some cooling was possible without MIN. In the last two years
            the share of project starts in MIN areas has been below its level in 2012 to
            2016, before that growth.
          </p>
          <p className="text-gray-700 mb-3">
            <strong>New construction alone is less clear.</strong> For projects that
            include new residential construction, the gap is{" "}
            {E.newResidential.projects.gap} points in projects (range{" "}
            {sg(E.newResidential.projects.gapLow)} to {E.newResidential.projects.gapHigh}).
            The main comparison counts renovations and conversions, which MIN also
            regulates.
          </p>
          <p className="text-sm text-gray-600 mt-4">
            Earlier versions of this memo estimated that MIN deterred about 450
            new-construction homes, or 1,000 to 1,400 homes counting conversions, and
            showed larger figures from a comparison within Districts 3 and 7. We have
            withdrawn those estimates. The code that produced them was not preserved,
            they could not be reproduced as stable results, and they relied on City
            unit counts that are incomplete before 2020.
          </p>
        </div>
      </PageSection>

      {/* Section 4: MIHB Comparison */}
      <PageSection>
        <div className="max-w-4xl mx-auto">
          <h2 className="font-(family-name:--font-display) text-xl font-black mb-4">
            4. The Voluntary Bonus Outperformed the Mandate
          </h2>
          <DataTable
            headers={["Metric", "MIHB (Voluntary)", "MIN (Mandatory)"]}
            rows={[
              ["Affordable units built", fmt(CUMULATIVE_COMPARISON.mihb.affordableCreated), fmt(CUMULATIVE_COMPARISON.min.affordableDelivered)],
              ["In pipeline (approved)", fmt(CUMULATIVE_COMPARISON.mihb.affordableInPipeline), fmt(CUMULATIVE_COMPARISON.min.affordableInPipeline)],
              ["Revenue to city", CUMULATIVE_COMPARISON.mihb.revenueLabel, CUMULATIVE_COMPARISON.min.revenueLabel],
              ["Effect on production", "Incentivizes density", "Deters construction"],
              ["Geography", "Citywide", "Parts of Districts 3 and 7; about 1,600 parcels now in Districts 4 and 8"],
            ]}
          />
          <p className="text-gray-700 mt-4">
            MIN lets a developer pay a fee for only the last 5 of its 20 points, and only
            with a Planning and Development waiver (&sect;14-533(3)(b)(.1)). The fee is
            $9 per square foot of the maximum floor area allowed in RM-2/3/4, RMX, IRMX
            and CMX-3/4/5 districts, and $10,900 per allowed unit in RM-1 and
            CMX-1/2/2.5. The first 15% requires on-site units with no buyout.
            The option has raised {CUMULATIVE_COMPARISON.min.revenueLabel}. The
            City&rsquo;s 2024 program report says no MIN project had been granted a
            waiver, and its 2025 report lists no MIN payment.
          </p>
        </div>
      </PageSection>

      {/* Section 5: MIN Pipeline */}
      <PageSection background="cream">
        <div className="max-w-4xl mx-auto">
          <h2 className="font-(family-name:--font-display) text-xl font-black mb-4">
            5. MIN&rsquo;s Pipeline
          </h2>
          <DataTable
            headers={["Status", "Projects", "Total Units", "Affordable"]}
            rows={[
              ["Delivered (CO)", String(MIN_PIPELINE.delivered.projects), fmt(MIN_PIPELINE.delivered.totalUnits), fmt(MIN_PIPELINE.delivered.affordableUnits)],
              ["Under construction", String(MIN_PIPELINE.underConstruction.projects), fmt(MIN_PIPELINE.underConstruction.totalUnits), fmt(MIN_PIPELINE.underConstruction.affordableUnits)],
              ["Expired ZP", String(MIN_PIPELINE.zoningOnly.expired.projects), fmt(MIN_PIPELINE.zoningOnly.expired.totalUnits), fmt(MIN_PIPELINE.zoningOnly.expired.affordableUnits)],
              ["Stalled (18+ mo)", String(MIN_PIPELINE.zoningOnly.stalled.projects), fmt(MIN_PIPELINE.zoningOnly.stalled.totalUnits), fmt(MIN_PIPELINE.zoningOnly.stalled.affordableUnits)],
              ["Recent ZP", String(MIN_PIPELINE.zoningOnly.recent.projects), fmt(MIN_PIPELINE.zoningOnly.recent.totalUnits), fmt(MIN_PIPELINE.zoningOnly.recent.affordableUnits)],
            ]}
          />
          <p className="text-xs text-gray-500 mt-2">
            3 zoning permits have expired. Average time since ZP for paper-only
            projects: {MIN_PIPELINE.zoningOnly.avgMonthsSinceZP} months. None of
            the 18 projects are subsidized/LIHTC — all private market.
          </p>
        </div>
      </PageSection>

      {/* Section 6: TOC Impact */}
      <PageSection>
        <div className="max-w-4xl mx-auto">
          <h2 className="font-(family-name:--font-display) text-xl font-black mb-4">
            6. MIN and Transit-Oriented Zoning
          </h2>
          <p className="text-gray-700 mb-3">
            The Transit-Oriented Communities (/TOC) overlay, amended in June 2026, covers
            lots within a quarter mile of 13 Market-Frankford Line stations. It overlaps
            MIN in West Philadelphia and Kensington, and every /TOC lot in the 7th
            Council District is now inside MIN (&sect;14-533(1)(b)).
          </p>
          <p className="text-gray-700 mb-3">
            MIN does not take density away near transit. &sect;14-513(5)(a)(.2) leaves MIN
            lots out of the 30% floor-area increase that /TOC gives CMX-3, CMX-4 and CMX-5
            lots, but MIN&rsquo;s own table sets higher limits: 800% of lot area for
            CMX-3 inside /TOC, against 650% with the /TOC increase alone, 750% against
            650% for CMX-4, and 1,600% against 1,560% for CMX-5 (Table 14-533-4). Those
            limits apply to projects that are subject to the 20% requirement. The added
            homes near transit therefore depend on whether projects can carry the mandate
            without subsidy.
          </p>
          <p className="text-sm text-gray-600 mt-3">
            Earlier versions of this memo reported a 1,364-unit loss from a statutory block
            on the transit floor-area bonus, and a district table built on it. We have
            withdrawn those figures. They treated the exclusion in &sect;14-513(5)(a)(.2) as
            a net loss of floor area, which it is not, and added a deterrent rate taken
            from the within-district comparison. We have not published a replacement
            estimate for transit zones.
          </p>
        </div>
      </PageSection>

      {/* Section 7: Peer Cities */}
      <PageSection background="cream">
        <div className="max-w-4xl mx-auto">
          <h2 className="font-(family-name:--font-display) text-xl font-black mb-4">
            7. Other Cities Found a Better Way
          </h2>
          <p className="text-gray-700 mb-4">
            Portland enacted an unfunded IZ mandate in 2017. Permits fell 40%.
            Threshold gaming doubled. In 2024, Portland and Multnomah County fully
            funded the program (~$220K/unit subsidy). Gaming returned to normal.
            Construction restarted. On March 4, 2026, Oregon passed SB 1521 making
            unfunded IZ illegal statewide. Philadelphia&rsquo;s MIN — 20% at 40%
            AMI with no subsidy — would not survive that standard.
          </p>
        </div>
      </PageSection>

      {/* Section 8: Recommendations */}
      <PageSection>
        <div className="max-w-4xl mx-auto">
          <h2 className="font-(family-name:--font-display) text-xl font-black mb-4">
            8. Recommendations
          </h2>
          <div className="space-y-4">
            <div className="flex gap-3">
              <span className="font-(family-name:--font-display) font-black text-xl text-bpn-green">1.</span>
              <div>
                <strong>Fund the gap.</strong> Close the $175K–$225K per-unit gap
                between market and affordable rents using the Housing Trust Fund, tax abatement
                savings, and PILOT revenue — as Portland now does at ~$220K/unit.
              </div>
            </div>
            <div className="flex gap-3">
              <span className="font-(family-name:--font-display) font-black text-xl text-bpn-green">2.</span>
              <div>
                <strong>Adjust rates and ratios.</strong> Align set-aside percentages
                and AMI targets with what the market can deliver given available
                funding. Portland offers 10% at 60% AMI or 20% at 80% AMI.
              </div>
            </div>
            <div className="flex gap-3">
              <span className="font-(family-name:--font-display) font-black text-xl text-bpn-green">3.</span>
              <div>
                <strong>Broaden the fee-in-lieu waiver.</strong>{" "}
                MIN&rsquo;s buyout reaches only the last 5 of its 20 points and needs a
                discretionary waiver; it has raised {CUMULATIVE_COMPARISON.min.revenueLabel}{" "}
                since 2022. Widening it &mdash; or pairing the mandate with subsidy &mdash;
                would let projects that cannot carry 20% at 40% AMI contribute to the
                Housing Trust Fund instead of not building at all.
              </div>
            </div>
            <div className="flex gap-3">
              <span className="font-(family-name:--font-display) font-black text-xl text-bpn-green">4.</span>
              <div>
                <strong>Require calibration studies.</strong> Review the program every
                two years against construction costs and market rents, as Oregon now requires.
              </div>
            </div>
          </div>
        </div>
      </PageSection>

      {/* Closing */}
      <PageSection background="cream">
        <div className="max-w-3xl mx-auto text-center">
          <p className="text-gray-700 text-lg">
            Mixed-income neighborhoods are a sound goal, and the mechanism needs to
            change. Portland funded its program and construction restarted. Oregon
            then barred the unfunded version. Philadelphia can follow either step.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-3 print:hidden">
            <a href="/#q2" className="px-4 py-2 bg-bpn-dark text-white rounded text-sm font-medium hover:bg-gray-800">
              The evidence →
            </a>
            <a href="/data/" className="px-4 py-2 bg-bpn-green text-white rounded text-sm font-medium hover:bg-bpn-green-dark">
              Data Download →
            </a>
            <a href="https://map.buildphillynow.org" className="px-4 py-2 border border-bpn-green text-bpn-green rounded text-sm font-medium hover:bg-bpn-cream">
              Explore the Map →
            </a>
          </div>
        </div>
      </PageSection>
    </>
  );
}
