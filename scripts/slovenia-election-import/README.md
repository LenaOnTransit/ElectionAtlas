# Slovenia integration package — partial assignment

This package proposes 32 draft WorldElection records under the existing `si` country: ten National Assembly elections (1992–2026), twelve presidential rounds (1992–2022), and ten National Council replacement contests (1997–2024). It does not complete the all-elections assignment. No live records or party profiles were written; merging this PR does not import the JSON. Drafts must not appear in the public country archive.

## Sources and reconciliation

DVK archive landing pages, national result HTML/JSON, certified DVK reports and Official Gazette reports are linked in each record. `source-extract.json` and `council-extract.json` are the reproducible numeric inputs. `source-audit.json` records hashes of downloaded original sources; originals remain available at the labeled source URLs. `reconciliation.json` states each distinct denominator and its gap. Votes and six-decimal percentages are never combined between separate rounds or elector bodies. Missing seats, previous seats and electoral figures remain null. Every presidential round and Council replacement contest reconciles exactly to its valid-vote denominator.

The 1996 Assembly national table contains only 1,061,806 of 1,069,204 valid votes: a 7,398-vote gap remains. Local independent lists are described by the source diagram legend but cannot be allocated from the national table; no invented residual row is added. The 2000 detailed archive explicitly reports unofficial figures and 99.93% ballot counting; it remains provisional. Assembly records contain general-list ballots only; minority elections are not pooled into the percentage denominator and coverage remains partial. Seven major-party allocations in 2004 are taken from DVK's official composition table; 1992 and provisional 2000 general-list seats are transcribed from the DVK composition diagrams.

Material source corrections: the retrospective presidential overview swaps Türk and Zver totals in 2012; the certified results are used. The certified 1997 report supersedes the overview's incorrect voter and valid-ballot totals. The contemporary DVK 2002 runoff report supplies 1,052,795 voters instead of the overview's 1,052,759. The certified 1992 eligible total includes 940 voters admitted by certificate. The certified 2018 Assembly report supplies 901,512 participants. Council replacement election of 20 April 1997 was a direct public vote; current indirect rules must not be applied retrospectively. The 17 December 2018 Council report says Monday; the landing page wrongly says Thursday.

## Remaining assigned scope

- National Assembly minority candidates, separate ballot denominators and two seats for every general election; historical party seat allocations for 1996.
- Reconcile 1996 independent-list votes and replace the 2000 provisional source with a certified final table.
- National Council general elections in 1992, 1997, 2002, 2007, 2012, 2017 and 2022; all functional-interest and territorial electoral bodies, ties, repeat ballots and later annulments. The modern DVK archive begins its general Council listing in 2002; the earlier contests require additional authoritative research.
- Council replacement/repeat contests omitted from this package, including August 2026 districts 9 and 12 and the March 2018 culture/sport vote. The DVK archive identifies Vesna Humar and Marko Gasser as the 2026 winners, but their complete ballots have not been transcribed.
- The 1990 pre-independence Assembly and collective Presidency elections and their rounds require the historical chamber model and authoritative source tables; they have not been represented as modern 90-seat Assembly or single-president elections.

## Party and ideology handling

Six reusable party profiles are proposed, with deterministic UUIDs and DVK presentation colours. Exact organization-name matches link eligible modern Assembly rows; historical coalitions and merged organizations are not assigned present-day names. No ideology guide links or axis ratings are invented. Presidential ideology remains explicitly unassessed; proposer labels preserve support without asserting membership. All profiles remain proposed, not saved.

## Integration and concurrency

Read-only live checks on 6 October 2026 found country record `world-country-si`, data ID `si`, updated 2026-10-05 00:11:23.101201+00. No Slovenia election records or saved country parties existed at either initial or final pre-PR check. No other agent was active in this thread. These are snapshots, not locks.

Immediately before import, re-read ALL Slovenia elections (including drafts), saved parties (including archived parties), and record revisions through the authorized editor workflow. Match by date/body/round; preserve any election ID already created and replace proposed party UUIDs with matching saved profile IDs. Do not insert duplicate parties. Preserve source grouping and election-era names. Import only assigned `si` records with the current optimistic version via `ea_save_record`; stop on conflicts, never retry with a rewritten version. Published records require editorial review and sourced completion/qualification. Existing country legitimacy and coverage note must not be overwritten.

Use `python scripts/import-slovenia-elections.py`, `node scripts/check-slovenia-elections.mjs`, `corepack pnpm test`, and `corepack pnpm build`. The importer never writes to the database. Repository tests and production build passed on the inspected main checkout. The static build excludes these draft templates; generated SEO is checked using `electionMetadata` for every proposed record. After an authorized import/publish, verify each assigned ID through the public archive and inspect the matching GitHub Pages workflow deployment. No deployment verification is claimed by this data-only draft PR.

## Proposed election IDs

| ID | Coverage | Results |
| --- | --- | --- |
| world-slovenia-1992-12-06-assembly | partial | final |
| world-slovenia-1996-11-10-assembly | partial | final |
| world-slovenia-2000-10-15-assembly | partial | provisional |
| world-slovenia-2004-10-03-assembly | partial | final |
| world-slovenia-2008-09-21-assembly | partial | final |
| world-slovenia-2011-12-04-assembly | partial | final |
| world-slovenia-2014-07-13-assembly | partial | final |
| world-slovenia-2018-06-03-assembly | partial | final |
| world-slovenia-2022-04-24-assembly | partial | final |
| world-slovenia-2026-03-22-assembly | partial | final |
| world-slovenia-1992-12-06-president-round-1 | complete | final |
| world-slovenia-1997-11-23-president-round-1 | complete | final |
| world-slovenia-2002-11-10-president-round-1 | complete | final |
| world-slovenia-2002-12-01-president-round-2 | complete | final |
| world-slovenia-2007-10-21-president-round-1 | complete | final |
| world-slovenia-2007-11-11-president-round-2 | complete | final |
| world-slovenia-2012-11-11-president-round-1 | complete | final |
| world-slovenia-2012-12-02-president-round-2 | complete | final |
| world-slovenia-2017-10-22-president-round-1 | complete | final |
| world-slovenia-2017-11-12-president-round-2 | complete | final |
| world-slovenia-2022-10-23-president-round-1 | complete | final |
| world-slovenia-2022-11-13-president-round-2 | complete | final |
| world-slovenia-1997-04-20-council-local-interests-electoral-district-8 | complete | final |
| world-slovenia-2008-03-12-council-independent-professions | complete | final |
| world-slovenia-2008-04-09-council-local-interests-electoral-district-18 | complete | final |
| world-slovenia-2014-05-29-council-local-interests-electoral-district-3 | complete | final |
| world-slovenia-2014-05-29-council-local-interests-electoral-district-6 | complete | final |
| world-slovenia-2018-12-17-council-social-welfare | complete | final |
| world-slovenia-2020-06-18-council-local-interests-electoral-district-3 | complete | final |
| world-slovenia-2020-10-15-council-local-interests-electoral-district-6 | complete | final |
| world-slovenia-2023-05-31-council-culture-and-sport | complete | final |
| world-slovenia-2024-11-14-council-local-interests-electoral-district-13 | complete | final |
