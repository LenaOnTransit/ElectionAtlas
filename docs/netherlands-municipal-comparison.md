# Dutch municipal comparison

Public route: `/municipalities/netherlands/`. The 342 European Netherlands municipalities use certified Tweede Kamer results for 22 November 2023 and 29 October 2025. Three Caribbean public bodies and non-resident postal voting appear in the separate outside-map table.

## Rebuilding data

Run `python scripts/import-netherlands-municipal.py`, then `pnpm test` and `pnpm build`. The importer uses curl and Python standard-library modules. It caches official Kiesraad snapshots and CBS/PDOK 2025 boundaries in `.cache/netherlands-municipal/`; no database changes or credentials are needed. The build ships `public/nl-municipal-2023-2025.json` and an audit manifest in `scripts/netherlands-municipal-sources.json`. Party presentation colours are maintained in `scripts/netherlands-municipal-party-colors.json`. Changing the importer’s default bloc sets and rebuilding changes the initial published grouping.

Every area must have all participating lists and the sum of its party votes must equal valid candidate votes. All 346 areas per year are summed by party and must exactly equal the national certified result before output is written. Matching uses names plus province where necessary: Bergen in Limburg and Bergen in Noord-Holland are separate. Maps use simplified land boundaries with interior symbol anchors; water polygons are omitted. Population is consistently CBS 1 January 2025 for both years.

## Calculations

Winner = party with most valid candidate votes; a tie is grey. Margin = 100 × (first votes − second votes) / valid votes. Margin colour saturates at 30 percentage points while the displayed numeric margin remains exact.

Left–right shift = (left vote share − right vote share) in 2025 minus that balance in 2023. Positive changes point left; negative changes point right. For example, left +5 pp and right −5 pp creates a +10 pp balance change. Official local turnout can exceed 100% when voter-pass holders from other municipalities vote there; these published figures are preserved. All valid votes stay in the denominator; centre and unclassified votes count toward neither bloc. Arrow shaft length is proportional to the absolute change and normalized against the largest change across all 342 municipalities under the current grouping. Search and the threshold filter do not change that normalization. This is an aggregate comparison, not evidence of individual voters switching parties.

The broad left/right classification is fixed and editorial, independent of hidden ideology axes. D66 and Volt are centre on our international ideological spectrum. Browser overrides and classification editing are unavailable. Each year opens in a standalone results view; only 2025 offers an explicit comparison with 2023. Population mode places circles at geographic anchors; circle **area**, not radius, is proportional to population. Circles can overlap; sizing, zoom and the municipality selector make small areas accessible.

## Runtime

The map is loaded only when the municipal route opens. Results are a static public asset and do not add Supabase polling or municipal database queries. Existing national election records are untouched. Controls and map features support keyboard selection, with a search/select alternative to navigating all polygons.

The municipal route now uses our [shared election geography engine](election-geography-engine.md). The Dutch asset is adapted to the versioned engine schema at load time; country/year-specific defaults and copy remain in the adapter. Future geographic datasets can reuse the same renderer and loader.
