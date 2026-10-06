# Timor-Leste archive publication

Scope: all national assembly / parliament elections and all presidential rounds held through 6 October 2026. Existing country ID: `tl`. No referendum, local or subnational election has been added. The 2001 Constituent Assembly is included as the elected predecessor that became the first National Parliament in 2002.

The initial scope check found the existing `world-country-tl` row, no Timor-Leste election rows and no saved Timor-Leste party profiles. The same checks were repeated immediately before publication. The country row was preserved. No other agent was active in this session. The initial publication transaction only inserts new records, rejects an existing Timor-Leste election or party scope, and uses serializable isolation. It does not overwrite a stale record or impersonate an editor. New elections are stored at version 1. The SQL connector publication does not create user-attributed `ea_revisions` entries; the reviewed generator, JSON and audit files provide the initial import trail.

| Election ID | Date | Office / round | Valid votes | Seats | Coverage |
| --- | --- | --- | ---: | ---: | --- |
| world-tl-2001-08-30-assembly | 2001-08-30 | Constituent Assembly | 363,501 | 88 | Partial |
| world-tl-2002-04-14-president-r1 | 2002-04-14 | President, first round | 364,780 | — | Complete |
| world-tl-2007-04-09-president-r1 | 2007-04-09 | President, first round | 403,941 | — | Complete |
| world-tl-2007-05-09-president-r2 | 2007-05-09 | President, runoff | 413,177 | — | Complete |
| world-tl-2007-06-30-parliament | 2007-06-30 | National Parliament | 415,604 | 65 | Complete |
| world-tl-2012-03-17-president-r1 | 2012-03-17 | President, first round | 464,661 | — | Complete |
| world-tl-2012-04-16-president-r2 | 2012-04-16 | President, runoff | 449,879 | — | Partial |
| world-tl-2012-07-07-parliament | 2012-07-07 | National Parliament | 471,389 | 65 | Complete |
| world-tl-2017-03-20-president-r1 | 2017-03-20 | President, first round | 516,881 | — | Complete |
| world-tl-2017-07-22-parliament | 2017-07-22 | National Parliament | 568,070 | 65 | Complete |
| world-tl-2018-05-12-parliament | 2018-05-12 | Early National Parliament election | 624,525 | 65 | Complete |
| world-tl-2022-03-19-president-r1 | 2022-03-19 | President, first round | 651,859 | — | Complete |
| world-tl-2022-04-19-president-r2 | 2022-04-19 | President, runoff | 640,967 | — | Complete |
| world-tl-2023-05-21-parliament | 2023-05-21 | National Parliament | 692,521 | 65 | Partial |

All 151 result rows have unique election-local IDs, six-digit colours, exact vote totals when verified, shares computed without rounding from the record's own valid-vote denominator, and nulls for unknown or inapplicable values. Every recorded national valid-vote total and all six chamber totals reconcile exactly. First-round advances and elected candidates are mutually exclusive. Related presidential rounds link reciprocally through `linkedElectionIds` and share a year-specific `seriesId`.

## Sources and qualifications

Each record contains labelled HTTPS sources and a checked date of 2026-10-06. Sources include CNE, the Official Gazette's Court of Appeal judgment, UNTAET / UNMIT archives, EU and ANFREL observation reports, IPU, IFES and Tatoli's reports of CNE verification and court certification. Full secondary transcriptions are explicitly labelled when used for smaller parties or candidates unavailable in the accessible primary table. The JSON records contain the precise URLs used for each election.

- **2001:** National-list votes and combined elected seats are clearly distinguished. FRETILIN won 43 national and 12 district seats. National-list independents won no seats; António da Costa Lelan's district seat is a separate seats-only row. Unverified district candidate votes remain null. Conflicting transcriptions differ by one ballot (PARENTIL 1,970 versus 1,971); IFES's UDT count differs by three. The 363,501-valid-vote series is retained and reconciles. Registration / turnout estimates have not been resolved; turnout is null. Coverage is partial.
- **2007:** The chamber changed from 88 mixed-election seats in 2001 to 65 nationwide PR seats. Previous seats are null across that boundary. EU final annexes preserve both presidential rounds and the parliamentary outcome.
- **2012 first presidential round:** UNMIT's court-certified table gives 626,503 eligible voters, unlike IFES's reused second-round denominator of 627,295. The record follows 626,503. The cancelled candidacy of Francisco Xavier do Amaral is documented without inventing a zero-vote result.
- **2012 runoff:** The UNMIT summary gives 275,441 / 174,386, while its national total beneath the district table and IFES give 275,471 / 174,408. The latter total of 449,879 is entered. The 52-vote internal-source discrepancy is documented; coverage is partial.
- **2017:** The parliamentary threshold rose from 3% to 4%. The presidential table includes all eight candidates, including those below IFES's 2% reporting cutoff. Luís Alves Tilman is not conflated with Manuel Tilman. Old CNE live links now serve 2022 results and are not cited as live 2017 or 2018 data.
- **2018:** All eight joint or standalone lists remain grouped as on the ballot. AMP, FDD, MDN and MSD votes are not divided among component parties. The AMP electoral alliance is not the similarly abbreviated 2007 governing coalition.
- **2022:** Each round retains its own registration and valid-vote denominators. CNE pages still say provisional, so final status is separately grounded in court certification. The runoff includes CNE's revised totals, rather than STAE's earlier 397,145 / 242,440 count. Blank, null, rejected and abandoned ballots reconcile to participation in both rounds.
- **2023:** All 17 parties and 65 seats reconcile. The turnout series uses 705,692 cast votes / 890,145 registered voters. Tatoli's CNE categories instead reconcile to 705,693 participants, one higher; coverage is partial. The court validation date is 5 June 2023. Government formation is sourced to IPU; CNRT and PD together held 37 seats.

## Party profiles and ideology

46 reusable historical party/list profiles were added. Their exact UUIDs, names, abbreviations, colours and source references are in `scripts/timor-leste-party-profiles.json`. Source grouping is retained for coalitions. CASDT and ASDT, the two Democratic Alliances with different component parties, and unresolved historical Liberal identities are distinct. Profiles carry no automatic ideology links.

The existing published `ideology-marxism-leninism` guide is linked only to PST's 2007 parliamentary row and Avelino Coelho da Silva's 2007 presidential row, using ANFREL's election-era description. Both have `ideologyBasis.kind = 'party-era'`, year 2007, an explanation and the source. The candidate row explicitly identifies this as a party fallback, not a candidate-specific personal assessment. Other candidate assessments remain unassessed. No nine-axis scores were invented.

## Validation and integration

```sh
python scripts/import-timor-leste-elections.py
node scripts/check-timor-leste-elections.mjs
pnpm test
pnpm build
node scripts/verify-timor-leste-publication.mjs
```

The model check validates every record using the current `validateWorldElection` and every profile using `validateParty`. It checks exact dates, IDs, source URL schemes, party links, vote and seat totals, turnout denominators, comparable previous seats, publication, round links, winners / advances, election-era attribution and generated SEO metadata. `verify-timor-leste-publication.mjs` is read-only and uses anonymous public endpoints to compare all stored version-1 records and saved profiles against the reviewed files, then checks archive links and every generated page heading, canonical URL and title.

The full repository tests and production build passed before publication. After publication, regenerate the build from Vite's clean output before checking generated pages. `scripts/timor-leste-publish.sql` documents the guarded initial data publication; it must not be replayed over the existing country scope. For later corrections, re-read current IDs and versions and use the established save workflow with conflict checks.

Post-publication checks passed: all 14 records were publicly readable at version 1; all 46 saved profiles matched the reviewed file; the full production build generated 936 indexable public pages including all 14 assigned elections; the read-only verification confirmed every country archive link and every election heading, canonical URL and SEO title. The existing country record was unchanged.

The first Pages rerun built and tested successfully but could not publish because its workflow run contained duplicate `github-pages` artifacts. A fresh Pages run was triggered with a source-preserving publication commit (`32f4d5b705400477eb35febd001d260d675b4009`) on the current `main` head. No application or unrelated archive source was changed for that refresh. The integrator PR adds only this scope's import/audit assets and checks.
