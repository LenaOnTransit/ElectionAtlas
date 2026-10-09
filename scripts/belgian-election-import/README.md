# Belgian parliamentary archive

174 held records, covering 76 Chamber elections/renewals from 1831 through 2024, 52 direct Senate elections/renewals through 2010, the 1830 constituent National Congress precursor, 7 Flemish, 7 Walloon, 8 Brussels and 13 German-speaking Community elections, and 10 European Parliament elections in Belgium.

This is a chronology of general elections and regular historical renewals. Individual by-elections, municipal and provincial council contests are outside this import. The French Community Parliament is constituted from regional representatives rather than a separate direct ballot. Direct Senate elections ceased in 2014; later Senate appointments are not labelled as direct elections.

Related contests use the existing `linkedElectionIds` field. Separate institutional `seriesId` values preserve each legislature's own history. No provincial overview or US state-contest schema is applied to Belgian legislatures. Same-day links are reciprocal, and all contests remain independently visible in the archive.

Brussels language groups and European electoral colleges retain their own row labels and seat allocations. For combined results, shares are calculated from the full valid-vote denominator; separate percentages summing to 200% or 300% are never presented as national percentages. Flemish seat totals include the Brussels members. Starting in 1995, Senate tables use the 40 directly elected seats, excluding community and co-opted members.

Historical partial renewals distinguish seats won from post-renewal composition. National popular votes must not be inferred from the votes recorded for only the contested provinces. Plural voting in 1894–1914 is flagged. Shared vote cells are counted once. All result rows have `winner: false`: a party's seat ranking is not an individual candidate call or a government-formation claim.

Ten early records remain chronology-only. Historical discrepancies and incomplete results stay explicitly partial. The German-speaking Parliament's primary table identifies blank/invalid ballots separately; these are not entered as an additional party, correcting a secondary-table problem in the earliest community elections. The 1904 and 1971 Senate source totals remain unreconciled and partial. No missing figures are invented.

## Rebuild and verify

Install Python `beautifulsoup4`. Download the snapshots in `source-audit.json` into `.cache/belgium/`, using the listed URLs and filenames. Download `List_of_elections_in_Belgium` as `overview.html`. The generator also reads `links.json`, generated from exact-date chronology links in that overview; the reviewed mapping is included here. Source hashes identify the exact reviewed versions; later source edits require a fresh review.

Run `python scripts/import-belgian-elections.py`, `node scripts/check-belgian-elections.mjs`, and `pnpm test`. The generator never publishes. Imports must reject identifier conflicts, preserve existing edits, and verify the anonymous public result before deployment. The pre-import backup contains Belgium's existing country record and the empty election set.
