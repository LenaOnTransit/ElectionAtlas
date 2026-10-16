# Norway national elections, 1814–2025

65 elections with 526 result rows: both constituent assemblies in 1814 and 63 Storting elections from 1815 through 2025. Every election has a result table. No presidential election is invented for this constitutional monarchy. The Odelsting and Lagting were internal divisions selected from the elected Storting, not separate public national elections. Regional, municipal and Sámi Parliament elections are outside this national parliamentary import.

## Sources and interpretation

The 21 elections from 1945 through 2025 use Statistics Norway's national JSON-stat data directly: table 08092 (valid party/list votes), 08219 (elected representatives by sex and party/list), and 08243 (turnout). Region 0 is selected once. Sex categories are summed once; deputy representatives are not included. Raw official data, metadata provenance and an exact independent reconciliation are retained. Shares are calculated from exact valid votes and rounded to two decimals, avoiding accumulation errors in the coarser published percentage series. Blank and rejected ballots are excluded from those shares. Turnout retains official source precision.

Joint-list votes are separate disjoint source categories. These allocation rows do not receive invented party identities or standalone seats; elected representatives stay with their party categories as Statistics Norway attributes them. For example, in 1965 Centre has 18 representatives, Christian Democrats 13 and Conservatives 31, including joint-list seats. Treating only the separately elected party-list mandates as their entire seat count would understate those totals.

Older results use the cited historical tables with expanded row/column spans. In 14 elections from 1891–1933, shared vote cells span two or three organisations. Votes appear once in an electoral-cooperation row; the separate organisations retain seat counts and have null vote/share values. Each election's vote sum and representative count reconcile. Polling/runoff dates under the 1906–1918 two-round system vary by constituency: the national election is recorded once with final mandates and first-ballot totals, with year precision. Later established two-day polling ranges are preserved.

Before parties emerged, source tables identify the representatives as independent. These are published as non-partisan seat totals, not as a fictional single party with 100% of votes. Votes and shares remain null. The Eidsvoll Constituent Assembly's 112 delegates are confirmed in the Storting's own constitutional anniversary publication; its 33 military representatives are included. Northern elections occurred after the Eidsvoll assembly had finished. Separate autumn 1814 results cover 81 representatives. Historical franchise restrictions, indirect voting and incomplete vote information are stated publicly. Occupational counts in secondary prose are not substituted for parliamentary results.

Saved party profiles and previous seats follow identifiable organisations. The pre-1884 Liberal/Conservative movements are separate from the formal parties. Socialist splinters and electoral alliances are not silently merged. Unknown previous seats and ideology remain null/unassessed. Ideology is a sourced broad party-era tradition; colour is a display palette. Historical datasets remain marked partial where classification/detail is limited.

All titles include Norway, the institution and election year. Public text contains factual historical/source context only.

## Reproduction

- Download links.json pages to `.cache/norway/<key>.html`.
- GET metadata from `https://data.ssb.no/api/v0/en/table/<table>` for 08092, 08219 and 08243. POST a query selecting Region `0`, every party/sex/time/content value, with response format `json-stat2`. Save `.cache/norway/ssb-<table>.json`. The raw responses are also retained alongside this README.
- `PYTHONPATH=.cache/python-libs python scripts/extract-norway-sources.py` (BeautifulSoup required).
- `python scripts/import-norway-elections.py`.
- `python scripts/reconcile-norway-primary.py`.
- `python scripts/build-norway-import-sql.py`.
- `node scripts/check-norway-elections.mjs`, then repository tests/typecheck/build.

The application model and SEO checks validate every record and party, modern totals and seat changes, shared historical ballots, non-party results and polling ranges. The primary reconciliation independently checks every modern row's raw votes, elected representatives and calculated share, plus each national turnout.

## Publication

import.sql is atomic, additive DML. Existing IDs must be absent or exactly match the reviewed import; party profiles must match exactly. Only the country's coverageNote is updated; the country assessment and its sources are preserved. No schema, auth, RLS or secret changes. Verify the published JSON exactly, anonymous live rendering and static SEO pages after deployment.
