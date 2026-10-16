# Portugal national-election import

135 public election/chamber/round records, 1820–2026: 134 additions and enrichment of the existing 2025 Assembly record. 676 result rows and 127 saved ballot organisations. Each title includes Portugal, the contest, year and a month/round distinction where needed.

## Scope

All 18 Assembly of the Republic elections (1976–2025), both constituent-assembly elections (1911 and 1975), the historical lower-house series from 1820, nine Senate elections/constitutions, the four general renewals of elective peers, and all presidential elections including indirect ballots and separately recorded rounds. European Parliament, local/regional elections, referendums, by-elections and royal appointments are outside this national general-election import. No legislative general election is added for 1926–1933 when none occurred.

## Evidence and limitations

`source-extract.json` retains transcribed historical tables, source URLs and downloaded-document SHA-256 hashes. `indirect-presidential.json` contains manual parliamentary-ballot transcriptions, with primary archival date controls. `reconciliation.json` checks every transcribed numeric total. `primary-reconciliation.json` checks 34 result rows against the CNE's certified 2025 legislative and both 2026 presidential national maps. The 2025 certification supersedes the earlier totals in the existing record. The July correction changes a deputy's name, not national party totals.

Published legislative shares are retained with their original denominator; they often include blank/invalid ballots, while current presidential shares use valid candidate votes. Coalition subtotal rows are excluded. Lists standing alone are not silently merged into their allies. Colours are a display palette; ideology is assigned only to identified broad party traditions, otherwise left unassessed. Previous seats require an identical saved organisation in the preceding comparable chamber ballot; no zero is inferred for an absent organisation.

The 1913 lower-house result covers 37 contested mandates, not the complete 153-seat chamber. The 1919 Senate's Evolutionist/Unionist grouping is retained jointly. The 1892 Regenerator/other grouping is retained jointly. The 1925 Senate lists 65 of 70 mandates; the missing five are unassigned. Some nineteenth-century tables omit overseas returns; seat totals describe the source scope, rather than a reconstructed full chamber. Historical restrictions, uncontested elections and authoritarian conditions are described in public-facing historical notes.

Primary archival dates replace erroneous secondary dates for 1822 (18 August), 1905 (12 February), and the 1919 presidency (6 August). 1828 is month precision; it concerns the People's Estate of the restored Three Estates, rather than an election under the suspended Charter. The November 1836 election constituted the 1837–1838 Constituent Cortes. Elective-peer general renewals are month precision, avoiding an invented common polling date. The 2026 runoff includes delayed voting through 15 February. Its certification flags omissions in the underlying tabulation; certified totals are retained with an explanatory public note.

119 records contain result tables; 117 contain numeric results and two identify the unopposed elected president without an invented tally. Sixteen early/historical entries remain date/history records without a verified party breakdown:

- 1820-12-10 Constituent Cortes
- 1822-08-18 Chamber of Deputies
- 1826-10-08 Chamber of Deputies
- 1828-05-01 People's Estate
- 1838-08-12 Chamber of Deputies
- 1838-08-12 Senate
- 1840-03-22 Chamber of Deputies
- 1840-03-22 Senate
- 1845-08-03 Chamber of Deputies
- 1847-11-28 Chamber of Deputies
- 1867-02-04 Chamber of Deputies
- 1885-12-01 Chamber of Peers
- 1887-03-01 Chamber of Peers
- 1890-04-01 Chamber of Peers
- 1894-04-01 Chamber of Peers
- 1911-08-25 Senate

## Reproduce and verify

1. Cache the pages listed in `links.json` under `.cache/portugal/<page>.html`.
2. `PYTHONPATH=.cache/python-libs python scripts/extract-portugal-sources.py`
3. `python scripts/import-portugal-elections.py`
4. Extract the three cited CNE PDF maps with `pdftotext -layout` into `2025-map.txt`, `2026-round1.txt`, `2026-round2.txt` in `.cache/portugal`.
5. `python scripts/reconcile-portugal-primary.py`
6. `python scripts/build-portugal-import-sql.py`
7. `node scripts/check-portugal-elections.mjs`, `pnpm test`, `pnpm build`.

The atomic SQL import rejects content that differs from the exact baseline or desired state, preserves the country assessment and existing record identity, and writes no schema or authorization changes. `pre-import-backup.json` contains only previously public Portugal data. No credentials or private content are included.
