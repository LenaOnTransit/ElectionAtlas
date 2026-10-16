# Ireland national-election import

80 elections, 504 result rows and 85 saved ballot organisations: 34 Dáil contests from 1918 to 2024, 31 Seanad elections from 1922 to 2025 and all 15 presidential elections from 1938 to 2025. Every record contains a result table. Six unopposed presidential records identify the elected candidate without numeric votes or turnout. All titles include Ireland, the institution and year; repeated elections in a year include a month.

## Scope and historical interpretation

The 1918 record is the all-Ireland Westminster result that preceded the First Dáil; it does not claim that every elected MP attended the Dáil. The 1921 record covers the 128 Southern Ireland returns, all unopposed at nominations on 13 May. It does not combine Northern Ireland's separate ballot with Southern Ireland or turn seat percentages into popular vote shares. Local, regional, European Parliament and by-elections are outside this national general-election import.

Dáil votes and shares are first preferences. The automatically returned outgoing Ceann Comhairle is included in the mandate allocation where applicable. Historical turnout can use the electorate in contested constituencies; no votes are invented for unopposed seats. In 1932 the delayed Leitrim–Sligo poll extends the record to 2 March.

Presidential STV counts are stages of one poll, not separate runoff elections. Result rows show first preferences; the winner marker reflects the final count and explanatory notes supply the decisive transferred totals. Mary Robinson therefore wins in 1990 despite having fewer first preferences than Brian Lenihan. Jim Gavin's 2025 votes remain included because his name remained on the ballot after he stopped campaigning. Six unopposed elections use year precision: scheduled polling days and inauguration dates are not treated as actual polls.

Seanad tables since 1938 show only the 49 elected mandates (43 vocational-panel and six university seats), derived from the initial composition's seven elected-constituency columns. All eleven Taoiseach nominees are excluded from seats won. The chamber capacity remains 60. National votes, shares and turnout remain null because the electorates differ and no national popular vote exists. The election method describes the dominant indirect panel process; the notes explain the separate graduate constituencies. Previous seats compare the preceding 49 elected mandates only. Year precision is used where exact election dates have not been established; first sittings and predecessor term-end dates are not substituted. The January 1983 election is dated to IPU's contemporary chronology, rather than the misleading December 1982 predecessor term-end.

Free State Seanad tables show the particular elected cohort, excluding continuing members and nominees: 30 elected by the Dáil in 1922, 19 elected by popular vote in 1925, 17 in 1928, 23 in 1931 and 23 in 1934. The Oireachtas centenary history confirms 23 seats filled in 1934, resolving a contradictory secondary lead. Cumann na nGaedheal supporters in 1922/1925 are retrospective groupings and are labelled accordingly. No seat changes are assigned across rotating cohorts.

## Source reconciliation

`source-extract.json` retains table transcriptions, citations and source HTML hashes. `reconciliation.json` records totals and the elected-only Seanad allocation. `primary-reconciliation.json` contains 86 vote checks against the Oireachtas national-total rows for 2016, 2020 and 2024, and the Presidential Returning Officer's complete 1938–2025 handbook for all contested presidential candidates.

The official 2016 Independent aggregate (334,814 votes, 19 seats) includes the Independent Alliance and the unregistered Identity Ireland candidate; these are not double-counted as separate parties. The 1997 Independent vote share is calculated from its votes and valid poll (6.88%), replacing the inconsistent 7.9% summary. The historical 1922, 1933 and 1948 component vote sums differ from their published aggregates by two, three and 450 respectively. Those unresolved discrepancies are described in the public notes and are not arbitrarily assigned to a party. Coverage remains partial rather than falsely marked complete.

Colours are a display palette. Ideology assignments describe broad party traditions, with source links; other organisations and independents remain unassessed. Historical Sinn Féin groups and differently founded National Parties use separate identities. Missing previous mandates remain null rather than an inferred zero for a new party.

## Reproduction and verification

Cache the pages from `links.json` under `.cache/ireland/<page>.html`, then run:

```sh
PYTHONPATH=.cache/python-libs python scripts/extract-ireland-sources.py
python scripts/import-ireland-elections.py
python scripts/reconcile-ireland-primary.py
python scripts/build-ireland-import-sql.py
node scripts/check-ireland-elections.mjs
pnpm test
pnpm build
```

The primary reconciliation expects `pdftotext -layout` exports named `dail-2016.txt`, `dail-2020.txt`, `dail-2024.txt` and `presidential-handbook.txt` in `.cache/ireland`. Exact official URLs are retained in the election citations.

The atomic import adds records and party profiles only if absent or identical, rejects conflicting content, and changes only the country's coverage note. Its pre-import backup contains the already-public country record. No schema, authorization, credentials or private content changes are included.
