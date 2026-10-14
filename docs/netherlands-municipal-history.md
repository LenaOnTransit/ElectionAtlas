# Dutch municipal election history

The existing `/municipalities/netherlands/` viewer now provides the **2003, 2006,
2010, 2012, 2017, 2021, 2023 and 2025 Tweede Kamer elections**. National election
pages link to their corresponding map, and existing `?year=2023` links continue
to work. A `?year=2025&compare=2021` link opens a particular comparison.

## Coverage and sources

All 2,542 municipal/public-body snapshots for the six newly added elections
come from the Kiesraad archive. The existing 2023/2025 result counts are retained.
Every party sum in every local return equals its published valid-vote total.
The importer audits each national party total and refuses new, unexplained
reconciliation differences.

| Election | European municipalities mapped | Local valid votes | Certified national valid votes |
| --- | ---: | ---: | ---: |
| 2003 | 489 | 9,654,475 | 9,654,475 |
| 2006 | 458 | 9,838,683 | 9,838,683 |
| 2010 | 430 | 9,416,001 | 9,416,001 |
| 2012 | 415 | 9,424,235 | 9,424,235 |
| 2017 | 388 | 10,524,838 | 10,516,041 |
| 2021 | 352 | 10,422,851 | 10,422,852 |
| 2023 | 342 | 10,432,726 | 10,432,726 |
| 2025 | 342 | 10,571,990 | 10,571,990 |

The two totals include separately retained outside-map returns where present.
The 2017 discrepancy is consistent with the official investigation of district
aggregation errors, including omitted Boxmeer and Bergeijk votes. Do not alter
local counts to force a match to the certified national result. The small 2021
party-total differences are likewise preserved. Both years have reader-facing
source explanations and pinned reconciliation manifests. National election
records are not changed.

Maps use contemporary CBS/Kadaster geometry. Rotterdam's 2010 geometry and
January population combine Rotterdam and Rozenburg because their full merger
occurred on 18 March, before the June election. The 2023 map now uses 2023
geometry, while its population retains the documented January 2025 reference.
Historical shapes can include water and archived population figures can be
rounded. No population circles are offered when figures are unavailable.

## Comparison coverage

The comparison selector allows these six explicit pairs:

| Current | Previous | Comparable municipalities |
| --- | --- | ---: |
| 2021 | 2017 | 327 / 352 |
| 2023 | 2021 | 334 / 342 |
| 2023 | 2017 | 310 / 342 |
| 2025 | 2023 | 338 / 342 |
| 2025 | 2021 | 330 / 342 |
| 2025 | 2017 | 308 / 342 |

Crosswalks follow the checked CBS annual tables in
`scripts/netherlands-boundary-transitions.json`. Whole municipalities may be
summed, including Amsterdam/Weesp and the five Land van Cuijk predecessors.
Splits, partial transfers, and later mergers involving an unavailable origin
remain unavailable. Even zero-population border corrections are excluded.
The Hague is excluded from comparisons using 2017/2021 because those archived
returns include non-resident votes; later archive groupings are different.

Older elections are standalone maps until their annual crosswalks are added.
Party IDs are aligned only for explicitly identified organisations. Separate
GroenLinks and PvdA lists are not rewritten as the later joint list. D66 and Volt
remain centre. Aggregated turnout is blank, because percentages cannot be
averaged without their eligible-voter denominators.

## Rebuilding

1. `node scripts/fetch-netherlands-geography-history.mjs`
2. Install Python import dependencies: `pyshp`, `shapely`, `pyproj`.
3. `python scripts/import-netherlands-geography-history.py`
4. `node --test scripts/check-netherlands-geography-history.mjs`
5. Run the normal `pnpm test` and `pnpm build`.

Source downloads remain in `.cache/dutch-geography`. The published asset is
`public/nl-municipal-history.json`; the audit manifest includes per-party sums,
municipal joins, geometry sources and a SHA-256. CBS boundary-transition tables
and the two reconciliation manifests are committed factual transcriptions.
Runtime uses one lazily loaded static asset and makes no database queries.
