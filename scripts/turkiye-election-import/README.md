# Türkiye national election archive

42 held elections from 1950–2023: 20 Grand National Assembly elections, eight Senate elections/renewals, four direct presidential ballots (including the 2023 runoff), and ten decisive parliamentary presidential selections.

This series excludes earlier elections, referendums, local elections, the failed 1980 presidential process and the invalidated April 2007 process. It includes the successful August 2007 selection. No future election date is inferred.

## Sources and scope

- `historical-primary-extract.json`: all party votes and election seats in YSK’s 1950–1977 and 1983–2007 national tables, extracted with Poppler coordinates to preserve empty columns. The early tables differ from the older TBMM statistical compilation; the YSK series is retained consistently.
- `source-tables.json`: cell-preserving detailed secondary result tables and their source references. Coalition subtotal cells are not counted as additional votes. Senate tables cite Nohlen et al., *Elections in Asia and the Pacific*, vol. I. TBMM parliamentary history independently supports renewal scope and major allocations; there is no claim of a district-level Senate recount.
- `primary-reconciliation.json`: vote-row cross-checks against the downloaded 2011–2023 YSK PDFs. The 2014 presidential scan was visually checked: 40,545,911 valid votes, 41,283,627 voters and 55,692,841 electors; candidate totals 21,000,143 / 15,587,720 / 3,958,048. YSK’s 2023 bulletin, pp.35–37, supplies all 25 party/independent rows and 600 list seats, replacing inconsistent secondary totals.
- Parliamentary presidential votes use TBMM minutes or TBMM’s published parliamentary history. Only the decisive ballot is recorded. Shares use all legislators’ ballots cast, including blank/invalid ballots, and public turnout is null. The 1950/1954 candidate errors in the secondary tables are replaced with the parliamentary history’s counts.
- `reconciliation.json`: denominator, seat and electorate controls for every election. Known YSK historical differences are preserved: 1950 party rows exceed voters by 309; 1961 party rows exceed printed valid votes by 3,208; 1969 by 3,570. Those records are partial. The 1954/1957 vote denominator is not separately certified as valid ballots. In 1983 399 members were elected to 400 positions; no fictitious party receives the vacant seat.
- Senate seats describe the renewal and any included vacancies, not the full chamber. Senate previous-seat comparisons are null because exact outgoing-cohort allocations were not established. The 1968 turnout discrepancy between the detailed table and TBMM narrative is explained in the record.
- Election seats remain with the ballot list. The 2002 general allocation precedes the 2003 Siirt repeat poll; the 2011 allocation follows Hatip Dicle’s disqualification. 2018/2023 AKP and CHP list seats include allied candidates, rather than later party membership. HDP and the 2023 Green Left ballot are not silently equated.
- Party colours are editorial display conventions. Sourced broad party traditions are attached where assessed; minor labels and independent candidates remain unassessed. Historical organisations with the same name remain distinct. CHP’s pre-1965 snapshots do not receive a retroactive social-democratic label.

## Rebuild and verify

Cache public HTML/PDF inputs under `.cache/turkiye` using `links.json`, `extra-primary-links.json` and `download-manifest.json`. Source checksums are recorded in `source-audit.json`. No original PDF/HTML or private records are shipped in the static build.

```sh
PYTHONPATH=.cache/python-libs python scripts/extract-turkiye-election-sources.py
python scripts/import-turkiye-elections.py
node scripts/check-turkiye-elections.mjs
corepack pnpm test
corepack pnpm build
```

`import.sql` is an additive, guarded transaction. It rejects a differing existing target record or party profile and changes only the country coverage text, preserving its electoral assessment. No schema, credentials, permissions or RLS changes are involved. Publication requires an explicit separate execution of that reviewed transaction; the generator never connects to the database.

The final label audit preserves the pre-2015 Workers’ Party name (İşçi Partisi), with its explicit continuity to the later Patriotic Party profile. İnce’s 2023 affiliation is the Memleket Party founded in 2021. `label-corrections.json` / `.sql` record the guarded correction to five version-2 records; the unused misleading profile is archived. Counts remain unchanged.
