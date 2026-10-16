# Sweden national election archive

137 published election records and 953 result rows: 35 Second Chamber elections (1866–1968), 17 unicameral Riksdag elections (1970–2026), and 85 First Chamber elections/renewals (1887–1969). The existing `world-sweden-2026` ID and official shares, seats and turnout are preserved. This adds 136 records and improves that existing record's title, series and previous-seat comparisons.

Every imported election has a result table. No regional, municipal, European Parliament or referendum records are added. Early First Chamber entries before 1887 lack a verified national party-result table and are not published as empty placeholders; see research-gaps.json. Several early entries are by-elections rather than regular chamber renewals.

## Interpretation

- Before 1970, lower-house results refer to Andra kammaren, not both chambers combined. The 1970 election elected the new unicameral Riksdag which took office in 1971.
- First Chamber rows count only the seats selected in that election. They exclude continuing members. Chamber capacity is separately recorded where available. The 1911 November, 1919 June–July and 1921 elections renewed the whole chamber.
- First Chamber votes, when shown, are electoral-college ballots, not popular votes. Shares are calculated from a reconciling published valid-ballot total. Historical multi-vote tallies, council membership totals and non-additive shared ballot counts are not substituted for popular votes. General-electorate turnout is null.
- Recent upper-house previous seats compare the corresponding outgoing cohort explicitly identified by the source. They do not compare this year's cohort to last year's different cohort. Early previous seats remain null.
- Lower-house previous seats use the immediately preceding election and a verified matching organisation. Historical Centre parties, left-wing splits and similarly named communist organisations have separate identities. Unknown previous results remain null.
- In 1893, 1896 and 1899, a common Liberal–Social Democratic vote total is counted once in a joint electoral-cooperation row. Individual party rows retain their separate seats but no duplicated votes.
- The original SCB 1985 report (printed pp. 8, 12) gives Centern (Centre–KDS) 691,258 votes and 44 seats, including one KDS member; KDS's own label received 5,000 votes and no seats. Secondary component tables incorrectly place those 5,000 within the joint list. The official joint-list total is used, and component ballots are not counted again.
- The Swedish 1887 tables are used in preference to inconsistent international-handbook classifications. The autumn table reports the settled mandates after Stockholm's list disqualification and uses retrospective parliamentary groups. The distinction is stated publicly. Pre-1911 direct/indirect voting and restricted franchise are identified.
- The SCB long-run series aggregates farmers' organisations in 1917/1920 and certain communist/socialist splits in 1924/1932/1936/1940. Detailed rows remain separate. The 1944 detailed Social Democratic share (46.55%) differs from the current long-run summary (46.7%); both figures are identified in the public note.
- Year/month precision is used when the selected evidence does not establish an exact polling day. A January 1 date with year precision is a storage convention, not a claimed polling date. The June–July 1919 upper-house election is explained in text because the model only permits exact-day date ranges.
- Broad party-era ideology is sourced for established parties. Historical splinters, electoral groups and minor lists are unassessed when evidence is insufficient. Colours are a display palette. Other-party aggregates and informal write-in categories do not receive invented party profiles.
- `resultCoverage=partial` is retained for the historical imports, reflecting classification and completeness limitations. The existing 2026 complete official summary remains complete on its stated aggregate basis. Raw 2026 party votes are not reverse-calculated from rounded percentages.

## Sources and validation

links.json identifies cached source pages; source-extract.json contains expanded result tables and source hashes. The primary source cross-check in primary-reconciliation.json independently checks 232 national turnout/share/seat entries against Statistics Sweden's 1910–2022 historical series and Valmyndigheten's final 2026 summary. Seven explicitly documented older classification/summary differences are retained. Original SCB reports for 1911, 1921, 1965–1969 First Chamber elections and 1985 were downloaded; the 1985 national summary and joint-list table were visually reviewed.

The importer checks every available national vote and elected-seat aggregate. Shared figures are not added twice. Tests also validate every record and party against the application model, each title's SEO metadata, preservation of 2026, modern seat counts, rotating cohorts and distinct historical organisations. No moderator instructions are published.

## Reproduction

1. Download links.json URLs into `.cache/sweden/<key>.html` (UTF-8 filenames). Download SCB's historical summary as `.cache/sweden/scb-history.html` and the official 2026 summary as `.cache/sweden/2026-official.html`; URLs are in primary-reconciliation.json.
2. `PYTHONPATH=.cache/python-libs python scripts/extract-sweden-sources.py` (BeautifulSoup required).
3. `python scripts/import-sweden-elections.py`.
4. `PYTHONPATH=.cache/python-libs python scripts/reconcile-sweden-primary.py`.
5. `python scripts/build-sweden-import-sql.py`.
6. `node scripts/check-sweden-elections.mjs`, then normal repository tests/typecheck/build.

## Publication

import.sql is an atomic, additive DML transaction. Existing party profiles must match exactly. New election IDs must be absent or equal to the reviewed dataset. The existing 2026 record can only change from the saved pre-import baseline or already-desired data. The country update changes coverageNote only, preserving its assessment and sources. No RLS, authentication, schema or secret changes are needed. Confirm exact published JSON and anonymous public rendering after import.
