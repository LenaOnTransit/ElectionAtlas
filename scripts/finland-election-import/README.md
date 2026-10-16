# Finland national election archive

75 historical records, 719 result rows, 110 party/list profiles:

- All 39 elections to the unicameral Eduskunta, 1907–2023, including elections under the Grand Duchy.
- Presidential candidate selection from 1919–2024: direct popular rounds from 1994, the distinct 1988 popular ballot, and final decisive ballots in Parliament or the electoral college.
- Ten public elections of presidential electors, recorded separately with elector seats. Alliance component rows are counted once; alliance subtotals are excluded.

The 1944 appointment under special law and the 1973 extension of the incumbent’s term are not fabricated as candidate elections. Earlier estate-based Diet elections, European, municipal and Åland-only parliamentary elections are outside this import. The existing scheduled 2027 election is preserved and receives a descriptive title.

## Sources and checks

`source-extract.json` contains expanded historical result tables, source URLs and SHA-256 hashes of the 59 downloaded pages. `links.json` is the reproducible download manifest. The extractor handles row and column spans. `reconciliation.json` checks every included table’s reported total against its result rows: all 75 vote totals reconcile; all 39 parliamentary tables total 200 seats.

Raw official Statistics Finland JSON-stat snapshots are included for tables 13sw (national party votes, 1983–2023), 13t4 (elected MPs, 2003–2023), and 12i9 (resident-citizen turnout, 1908–2023). `primary-reconciliation.json` records 131 independently checked named major-party vote/seat values. Do not equate the modern table’s residual categories with an individual Åland alliance. Parliamentary turnout from 1908 is consistently the official resident-citizen measure; foreign residents are excluded from that denominator. Presidential tables retain the turnout denominator in the cited result table, and indirect parliamentary turnout is parliamentary participation.

Historical joint lists retain their reported aggregate votes and seats, without guessed component allocations or previous-seat comparisons. Saved party identities distinguish similarly named historical organisations; minor-party ideology is left unassessed. Modern major-party ideology is sourced as a party tradition rather than an individual candidate assessment. Colours are a display palette. Unknown prior seats remain null; comparisons use the immediately preceding Eduskunta election only. Before the Green League was founded, the green electoral movement is separate. Elector seats are never compared with parliamentary seats.

For indirect elections, `electoralVotes` stores candidate ballot votes and `votes` remains null. Only the final decisive internal ballot is shown; an exact selection date is not invented when the sources inspected establish only its year. Public polling dates and ranges use the cited date. The 1988 popular ballot has neither a winner nor a false top-two runoff qualification.

## Reproduce and publish

Download manifest URLs to `.cache/finland/<page>.html`. With BeautifulSoup available:

```
python scripts/extract-finland-sources.py
python scripts/import-finland-elections.py
python scripts/build-finland-import-sql.py
node scripts/check-finland-elections.mjs
```

The SQL is additive and guarded against conflicting record/party content and concurrent coverage-note changes. No schema, permissions, authentication or RLS changes. `pre-import-backup.json` preserves the country and scheduled-election baseline. Published text contains election context only; this file documents import implementation for maintainers.
