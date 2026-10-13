# Archive result coverage — 13 October 2026

The baseline has 2,298 public held elections in 42 countries. The old counter
recognised 1,989 national tables and ignored 119 US gubernatorial records with
state contest tables, plus two Dutch electoral-college overviews with child
tables. The shared coverage helper counts these records once, without summing
different electorates or borrowing a linked runoff’s results. Drafts, future
elections and cancelled elections do not count. Presence means a table exists,
not that every vote or candidate has been transcribed.

Seventeen empty records now have 303 sourced result rows: five South African
National Assembly elections (1999–2019), India’s 2024 Lok Sabha allocation,
Brazil’s 2022 presidential first round, Sweden/Denmark/Morocco in 2026, two Tunisian presidential first rounds (2014/2019), and
Nepal’s five National Assembly renewals (2018–2026). National-table coverage is
now 2,006; including existing nested tables, coverage is **2,127 of 2,298**.
The remaining **171** genuine gaps are enumerated in `remaining-gaps.json`.

## Source handling and limits

- South Africa: all 140 party vote/share rows match IEC national PDF reports;
  each allocation reconciles to 400 seats. The 2004 report distinguishes
  allocated seats from assigned office-holders; the table uses allocation.
  The 1999 seat-report URL was unavailable; its reviewed historical allocation
  is retained with IFES and historical bibliography identified explicitly.
- India: 42 seat-winning groups account for 543 seats. The two Shiv Sena
  factions and Kerala Congress are reconciled against the detailed election
  table; IPU’s abbreviated labels contain ambiguities. Popular-vote figures
  are untranscribed and coverage remains partial.
- Brazil: all eleven first-round candidates sum to 118,229,719 valid votes.
  TSE’s completed count supersedes election-night counts. Two candidates
  advanced, and neither is marked elected in the first round.
- Sweden: the official final summary covers all 349 seats and all vote-share
  categories, including the source’s other-party aggregate. Raw counts are
  not reconstructed from rounded percentages.
- Denmark: Statistics Denmark covers the 175 mainland seats. The 179-seat
  chamber capacity is retained; four Greenland/Faroe Islands seats are still
  untranscribed. Mainland turnout is not represented as realm-wide turnout.
- Morocco: all 395 seats reconcile to the government’s preliminary allocation.
  Certification is not inferred: status remains provisional, with unentered
  votes and no invented combined local/regional percentage.
- Nepal: the five elected cohorts contain 56, 18, 19, 19 and 18 seats. The
  chamber capacity is 59; continuing and appointed members are excluded from
  the election tally. No candidate or weighted-elector vote totals are inferred.
  The 2026 JSP-N label follows the documented pre-election LSP-N merger and
  Radio Nepal’s results, rather than carrying forward an obsolete affiliation.

- Tunisia: all 53 first-round candidate counts and percentages reconcile to
  the Carter Center’s reproduced ISIE table (2014) and final ISIE decision
  2019-27 as transcribed from JORT (2019). The final 2019 valid-vote total
  supersedes earlier preliminary news reports. Runoff qualifiers are marked
  advancing, not elected.

The remaining gaps include historical peer selections, executive renewals,
early legislatures and constituent/designation events. Modern party labels,
candidate vote counts, results derived from later membership, and dummy
“unknown” rows must not be inserted merely to increase the counter.

## Reproduce and verify

`pre-import-backup.json` preserves the records read before the guarded patch,
including unchanged comparison records. `primary-links.json` lists IEC source
downloads and retrieval outcomes; cache PDFs and run `pdftotext -layout` beside
their HTML sources under `.cache/result-coverage`. Reviewed source extracts
retain the other primary and contemporary controls. Run
`python scripts/import-result-coverage.py` to generate the 17 patches; it has no
database write capability. `reconciliation.json` records totals and source hashes.

Run `node --test scripts/check-archive-coverage.mjs`,
`node scripts/check-result-coverage-import.mjs`, `pnpm test`, `pnpm typecheck`,
and `pnpm build`. The checks preserve dates, IDs, publication, classifications,
existing sources and unrelated fields, test private/future/nested-table cases,
reconcile allocations, and distinguish partial coverage and provisional results.
Database publication compares complete baseline payloads before each atomic
batch: 15 records first, followed by two Tunisian records. Existing integrity triggers handle rescanning and resolve
missing-table findings; review access stays in the protected moderator dashboard.
