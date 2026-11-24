import { PageHero } from "@/components/layout/PageHero";
import { PageSection } from "@/components/layout/PageSection";
import { DataTable } from "@/components/ui/DataTable";
import { DATA_FILES } from "@/data/min-stats";
import { E, drop, sg } from "@/data/evidence";

const fmt = (n: number) => n.toLocaleString();

export default function DataPage() {
  return (
    <>
      <PageHero
        title="Data &amp; Methodology"
        subtitle="Every claim in this analysis is backed by publicly available data. Download the datasets, review the methodology, and verify the findings."
      />

      {/* Downloads */}
      <PageSection>
        <div className="max-w-4xl mx-auto">
          <h2 className="font-(family-name:--font-display) text-2xl font-black mb-4">
            Data Downloads
          </h2>
          <p className="text-gray-700 mb-6">
            The datasets behind the comparisons on this site are available for
            download. The first two were built in November 2026 from City permit
            records and are the basis of the current findings. The last three belong
            to the earlier version of the analysis and are kept for reference.
          </p>

          <div className="space-y-4">
            {DATA_FILES.map((file) => (
              <div
                key={file.name}
                className="bg-bpn-card rounded-xl p-5 flex items-start justify-between gap-4"
              >
                <div>
                  <div className="font-mono text-sm font-semibold text-gray-800">
                    {file.name}
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{file.description}</p>
                  {file.rows && (
                    <span className="text-xs text-gray-500">
                      {file.rows.toLocaleString()} rows
                      {file.cols ? ` × ${file.cols} columns` : ""}
                    </span>
                  )}
                </div>
                <a
                  href={`/data/${file.name}`}
                  className="shrink-0 px-3 py-1.5 bg-bpn-green text-white rounded text-xs font-medium hover:bg-bpn-green-dark transition-colors"
                  download
                >
                  Download
                </a>
              </div>
            ))}
          </div>

          <p className="text-sm text-gray-500 mt-4">
            Questions about the files? Contact{" "}
            <a href="mailto:jon@buildphillynow.org" className="underline">
              jon@buildphillynow.org
            </a>.
          </p>
        </div>
      </PageSection>

      {/* Methodology */}
      <PageSection background="cream">
        <div className="max-w-4xl mx-auto">
          <h2 className="font-(family-name:--font-display) text-2xl font-black mb-4">
            Methodology
          </h2>
          <p className="text-gray-700 mb-4">
            The analysis was rebuilt in November 2026. It asks one question: after MIN
            took effect, did housing projects of 10 or more homes become scarcer inside
            the overlay than in comparable parts of the city?
          </p>

          <DataTable
            headers={["Element", "Detail"]}
            rows={[
              ["Projects", `${fmt(E.cohortProjects)} housing and mixed-use projects of 10+ homes citywide that started between July 2012 and July 2026`],
              ["What a project is", "Build Philly Now's grouping of City permits into developments. The City's records can show one development several times: once at the zoning stage and again at the building stage, or once per building permit, most often before 2020. Records on the same parcel or address that start within three years of each other are merged into one project. A project starts on the date of its first permit, usually the zoning permit."],
              ["Homes per project", "The largest unit count on the project's permits, from City unit fields and permit text. Coverage is 76% to 82% of housing projects in every year since 2012."],
              ["Before", `${E.baseline}: the four years before the tax-abatement deadlines of 2020 and 2021 pulled projects forward`],
              ["Under MIN", `${E.post}`],
              ["Inside MIN", "The project's parcel is inside the MIN boundary in force when the project started (the original 2022 boundary; plus the 54th to 63rd Street corridor from April 25, 2023)"],
              ["Comparable areas", "Projects outside MIN in census tracts whose median home sale price per square foot, July 2016 to July 2020, falls between the 5th and 95th percentile of the tracts where MIN projects sit"],
              ["Uncertainty", "95% ranges from resampling census tracts 3,000 times"],
            ]}
          />

          <h3 className="font-(family-name:--font-display) text-lg font-bold mt-8 mb-3">
            Results, including the ones that cut the other way
          </h3>
          <DataTable
            headers={["Test", "Result"]}
            rows={[
              ["Project starts, MIN against comparable areas", `−${drop(E.main.projects.insideChg)} against −${drop(E.main.projects.controlChg)}; gap ${E.main.projects.gap} points (${sg(E.main.projects.gapLow)} to ${E.main.projects.gapHigh}); the range includes zero`],
              ["Homes in those projects", `−${drop(E.main.units.insideChg)} against −${drop(E.main.units.controlChg)}; gap ${E.main.units.gap} points (${sg(E.main.units.gapLow)} to ${E.main.units.gapHigh})`],
              ["Four other definitions of comparable areas", `Gaps of ${E.gapRangeAcrossControls.projects[0]} to ${E.gapRangeAcrossControls.projects[1]} points (projects) and ${E.gapRangeAcrossControls.units[0]} to ${E.gapRangeAcrossControls.units[1]} (homes)`],
              ["Leaving out the first three months under MIN", `Gaps of ${E.excludeFirstThreeMonths.projects.gap} points (projects) and ${E.excludeFirstThreeMonths.units.gap} (homes)`],
              ["District 3", `Gap ${E.district3.projects.gap} points (${sg(E.district3.projects.gapLow)} to ${E.district3.projects.gapHigh})`],
              ["District 7", `Gap ${E.district7.projects.gap} points (${sg(E.district7.projects.gapLow)} to ${E.district7.projects.gapHigh}); the range includes zero`],
              ["If repeat records are merged within two years, or within five", `Gaps of ${E.repeatFilings.within2.projects.gap} and ${E.repeatFilings.within5.projects.gap} points (projects); ${E.repeatFilings.within2.units.gap} and ${E.repeatFilings.within5.units.gap} (homes)`],
              ["If repeat records are not merged", `Gap ${E.repeatFilings.notMerged.projects.gap} points (${E.repeatFilings.notMerged.projects.gapLow} to ${E.repeatFilings.notMerged.projects.gapHigh}). This overstates the gap: repeat records are more common before 2020 and inside MIN.`],
              ["University City (MIN inside the University City District) against the Center City core", `−${drop(E.ucVsCore.projects.insideChg)} against −${drop(E.ucVsCore.projects.controlChg)}; gap ${E.ucVsCore.projects.gap} points (${sg(E.ucVsCore.projects.gapLow)} to ${E.ucVsCore.projects.gapHigh})`],
              ["University City against greater Center City", `Gap ${E.ucVsGreater.projects.gap} points (${sg(E.ucVsGreater.projects.gapLow)} to ${E.ucVsGreater.projects.gapHigh})`],
              ["Projects that include new residential construction only", `Gap ${E.newResidential.projects.gap} points (${sg(E.newResidential.projects.gapLow)} to ${E.newResidential.projects.gapHigh}); the range includes zero`],
              ["Within 1,500 feet of the MIN boundary, inside against outside", `−${drop(E.boundary1500.projects.insideChg)} against −${drop(E.boundary1500.projects.controlChg)}; gap ${E.boundary1500.projects.gap} points (${sg(E.boundary1500.projects.gapLow)} to ${E.boundary1500.projects.gapHigh}); no clear difference`],
              ["District 3 outside University City against greater Center City", `Gap ${E.d3OutsideUc.projects.gap} points (${sg(E.d3OutsideUc.projects.gapLow)} to ${E.d3OutsideUc.projects.gapHigh})`],
              ["Site-by-site model, tracts with similar prices", `A MIN site's odds of getting a project, relative to other sites: ${E.parcelOdds.matched.or} (${E.parcelOdds.matched.low} to ${E.parcelOdds.matched.high})`],
              ["Site-by-site model, citywide", `A MIN site's odds of getting a project, relative to other sites: ${E.parcelOdds.citywide.or} (${E.parcelOdds.citywide.low} to ${E.parcelOdds.citywide.high})`],
              ["Site-by-site model, within 1,500 feet of the boundary", `${E.parcelOdds.near1500.or} (${E.parcelOdds.near1500.low} to ${E.parcelOdds.near1500.high}); no difference`],
              ["Zoning permit to building permit within 24 months, under MIN", `${E.conversion.insideUnderMin.m24}% inside MIN, ${E.conversion.controlUnderMin.m24}% in comparable areas; no difference`],
            ]}
          />
          <p className="text-sm text-gray-600 mt-3">
            The site-by-site model covers {fmt(E.parcelOdds.sites)} privately owned
            parcels whose zoning allows 10 or more homes by right,{" "}
            {fmt(E.parcelOdds.sitesInside)} of them inside MIN. It uses Build Philly
            Now&rsquo;s zoning capacity data, which is not part of the downloads.
          </p>

          <h3 className="font-(family-name:--font-display) text-lg font-bold mt-8 mb-3">
            Limitations
          </h3>
          <ul className="list-disc pl-5 text-gray-700 text-sm space-y-2">
            <li>
              <strong>This is a comparison, not an experiment.</strong> MIN areas and
              comparable areas differ in ways that sale prices do not capture. The
              boundary results above suggest that neighborhoods next to MIN had a
              slump of their own.
            </li>
            <li>
              <strong>Trends before MIN were not parallel.</strong> Project starts in
              MIN areas were growing faster than in comparable areas from 2018 to 2020.
            </li>
            <li>
              <strong>Small numbers.</strong> About {Math.round(E.main.projects.insidePost * 4)}{" "}
              projects of 10+ homes have started inside MIN since July 2022. A few
              projects either way move every figure, which is why ranges are shown.
            </li>
            <li>
              <strong>Renovations.</strong> A renovation of an existing apartment
              building is counted as a project with that building&rsquo;s homes, though
              it adds none. The records do not separate these from conversions of
              other buildings into housing.
            </li>
            <li>
              <strong>Repeat records.</strong> Merging repeat records for one
              development depends on a rule, here three years on the same parcel or
              address. The results table shows the gap under other rules.
            </li>
            <li>
              <strong>University City.</strong> University City is drawn with the
              University City District&rsquo;s boundary. The MIN blocks of District 3
              outside it, such as Mantua and Belmont, are reported separately.
            </li>
            <li>
              <strong>Unit counts.</strong> About one in five housing projects has no
              unit count and cannot be classified as 10+ homes. Projects still at the
              zoning stage are the most likely to be missing.
            </li>
            <li>
              <strong>The abatement rush.</strong> Using a baseline that includes
              2020 to 2022 shrinks the gap, because comparable areas had a larger
              rush than MIN areas did. The baseline here excludes those years for that
              reason.
            </li>
            <li>
              <strong>Districts 4 and 8.</strong> Under the current council map, about
              1,340 of the overlay&rsquo;s roughly 38,500 parcels sit in District 4 and
              about 260 in District 8 (Build Philly Now parcel data, October 2026).
              They are counted as inside MIN.
            </li>
            <li>
              <strong>Earlier estimates withdrawn.</strong> Earlier versions of this
              site estimated that MIN deterred about 450 new-construction homes, or
              1,000 to 1,400 counting conversions, and an estimate of lost Housing
              Trust Fund revenue built on those. The code behind them was not
              preserved and they could not be reproduced as stable results.
            </li>
          </ul>

          <h3 className="font-(family-name:--font-display) text-lg font-bold mt-8 mb-3">
            Transit Zones
          </h3>
          <p className="text-gray-700 mb-3">
            Earlier versions of this site estimated how many homes MIN would cost the
            Transit-Oriented Communities (/TOC) overlay, including a 1,364-unit loss
            from a statutory block on the transit floor-area bonus. We have withdrawn
            that estimate. &sect;14-513(5)(a)(.2) does leave MIN lots out of the 30%
            floor-area increase, but Table 14-533-4 gives those lots higher limits
            (for CMX-3 inside /TOC, 800% of lot area against 650%), available to
            projects subject to the 20% requirement. The site now makes no unit
            estimate specific to transit zones.
          </p>
        </div>
      </PageSection>

      {/* Data Sources */}
      <PageSection>
        <div className="max-w-4xl mx-auto">
          <h2 className="font-(family-name:--font-display) text-2xl font-black mb-4">
            Data Sources
          </h2>

          <div className="space-y-3">
            {[
              {
                name: "L&I Building Permits",
                source: "City of Philadelphia CARTO (permits table)",
                url: "https://phl.carto.com",
              },
              {
                name: "OPA Property Data",
                source: "City of Philadelphia CARTO (opa_properties_public table)",
                url: "https://phl.carto.com",
              },
              {
                name: "Zoning Overlays Shapefile",
                source: "Philadelphia City Planning Commission via OpenDataPhilly",
                url: "https://opendataphilly.org",
              },
              {
                name: "Council District Boundaries",
                source: "City of Philadelphia ArcGIS (2024 redistricting boundaries)",
                url: "https://services.arcgis.com/fLeGjb7u4uXqeF9q/arcgis/rest/services/Council_Districts_2024",
              },
              {
                name: "Affordable Housing Inventory",
                source: "City of Philadelphia (Affordable_Housing.csv)",
                url: "https://opendataphilly.org",
              },
              {
                name: "Mixed Income Housing Programs Reports",
                source: "City of Philadelphia Department of Planning and Development (2019–2025)",
                url: "https://www.phila.gov/documents/mixed-income-housing-program-report/",
              },
              {
                name: "Portland IZ Program Data",
                source: "Sightline Institute; City of Portland PHB",
                url: "https://www.sightline.org/2025/11/25/portlands-inclusionary-zoning-program-is-finally-performing-new-data-suggests/",
              },
              {
                name: "Oregon SB 1521",
                source: "Oregon Legislative Assembly (2026)",
                url: "https://www.sightline.org/2026/03/05/oregons-new-path-to-inclusionary-housing-fully-funded-and-flexible/",
              },
            ].map((source) => (
              <div key={source.name} className="flex items-start justify-between gap-4 bg-bpn-card rounded-lg p-3">
                <div>
                  <div className="text-sm font-semibold text-gray-800">{source.name}</div>
                  <div className="text-xs text-gray-600">{source.source}</div>
                </div>
                <a
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="shrink-0 text-xs text-bpn-green hover:underline"
                >
                  Source →
                </a>
              </div>
            ))}
          </div>
        </div>
      </PageSection>

      {/* Contact */}
      <PageSection background="cream">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="font-(family-name:--font-display) text-2xl font-black mb-4">
            Questions or Feedback
          </h2>
          <p className="text-gray-700 mb-4">
            This analysis was prepared by Build Philly Now using publicly available
            data. All code, data, and methodology are available for review.
          </p>
          <p className="text-gray-700">
            Contact:{" "}
            <a href="mailto:jon@buildphillynow.org" className="text-bpn-green hover:underline font-medium">
              jon@buildphillynow.org
            </a>
          </p>
          <p className="text-gray-700 mt-2">
            Explore the data:{" "}
            <a href="https://map.buildphillynow.org" className="text-bpn-green hover:underline font-medium">
              map.buildphillynow.org
            </a>
          </p>
        </div>
      </PageSection>
    </>
  );
}
