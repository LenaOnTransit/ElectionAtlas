# Subnational election geography engine

The existing `/municipalities/netherlands/` route now uses the shared renderer in `app/geography/view.tsx`. Election selection, area search/selection, winner colours, exact winning margins, population circles, pan/zoom, accessible palettes/patterns, results tables, source links and optional comparisons all read a versioned dataset. There are no country IDs, election years, default municipality IDs or country-specific calculations in the engine.

## Layers and joins

- `units`: stable area IDs, names and optional population. Include postal/non-resident areas here too; they need not have geometry.
- `boundaries`: named boundary sets with an SVG viewport and `features[unitId] = {path, center}`. Geometry stays separate from vote totals. Importers project/simplify GeoJSON or other source boundaries into these SVG paths; the renderer does not fetch or infer boundaries.
- `elections`: IDs, labels/dates, name, country, vote basis, boundary-set reference, election-specific party metadata, and `results[unitId]`.
- `parties`: stable comparable IDs, names, colours and optional fixed left/right/centre/unclassified grouping. Metadata can differ by election. Align renamed/merged party IDs deliberately in the importer; the engine does not infer equivalence.
- `results`: integer party vote totals, the valid-vote denominator, optional turnout and source. Party totals must reconcile exactly to valid votes. Missing unit records mean unavailable, not zero; a zero denominator has no winner or shift.
- `previousElectionId`: an optional explicit reference to a comparable election. The engine enables comparison only if both records use the same boundary-set ID and vote basis. Changing boundaries require an importer to harmonize both elections onto a documented common geography; raw incompatible units are never automatically compared.

The TypeScript contract is `lib/election-geography.d.mts`. The runtime validator in `lib/election-geography.mjs` rejects broken unit/party/geometry joins, duplicate IDs, invalid counts, unreconciled totals and unsafe source URLs. `geographyView` joins geometry/results and computes comparison coverage and stable arrow normalization once per election selection.

Population is optional. Units without a population figure remain selectable by boundary in circle mode. No population layer appears when none is available. Population labels identify the reference date supplied by the dataset; they are not assumed to be election-day estimates.

## Reusing it for the next dataset

Produce a static JSON file matching `GeographyDataset` in `public/`, then mount the existing loader in the desired public route:

```tsx
import GeographyLoader from '../geography/loader';

<GeographyLoader
  asset="example-regional-results.json"
  title="Example regional election results"
/>
```

That file needs `version: 1`, a dataset ID/title, singular/plural unit labels, a default election ID, description/coverage text, notes/sources/review date, boundary sets, units and elections. Country-specific prose belongs in this file. A dataset with one election and no `previousElectionId` still uses winner, margin and optional population views. Party classifications are optional; comparisons of party shares remain available without them, but left–right arrows do not.

`GeographyLoader` also accepts a pure `adapt(source)` function for older source formats and an optional initial election ID. `ElectionGeography` accepts a validated dataset directly for embedding, with optional initial view settings; by default it opens standalone results, never comparison. Register the new route and its public SEO fallback using the site's normal routing/page generation when adding actual coverage. No new map engine is needed.

## Existing Dutch data

`lib/netherlands-geography.mjs` adapts the certified `nl-municipal-2023-2025.json` asset without modifying it or the national election records. The source importer, national reconciliation checks, sources and current route remain intact; legacy `?year=2023` links select the same election. Only the 2025 election explicitly links to 2023. Both share the documented CBS 2025 boundary set. D66 and Volt remain centre, and classifications have no reader editing controls.

The legacy arithmetic module now re-exports shared calculations for the Dutch importer audit. Dataset-specific information, default Amsterdam selection, source dates and explanatory notes live in the adapter, not the map renderer.

## Calculations and limitations

Margin is the first party's vote share minus the second's, using unrounded counts; a sole participating party has a 100-point lead. A tie is grey. Margin colour saturates at 30 points, but numeric values remain exact.

Left–right shift compares `(left − right)` vote shares across the explicit pair, using each election's classifications. Centre/unclassified votes remain in the denominator. Units missing either valid result produce no arrow or numeric change. Arrow length scales against all comparable mapped units, not just a search/threshold subset. A missing party within a fully recorded unit result counts as zero; a missing result does not. Aggregate shifts do not establish individual voter switching.

The v1 engine renders party/list vote totals on preprojected boundaries. Candidate/ranked-choice ballots, dynamic GeoJSON reprojection, crosswalk generation, demographic vintages and automatic source ingestion are importer/schema work if needed later; this refactor adds no elections or database polling.

Validation: `node --test scripts/check-election-geography.mjs scripts/check-municipal-comparison.mjs`, followed by the normal `pnpm test` and `pnpm build`. Tests reconcile all Dutch results and exercise an unrelated synthetic region dataset, mismatched boundaries/bases, missing results, election-specific metadata, standalone elections, comparisons, population circles and accessible rendering.
