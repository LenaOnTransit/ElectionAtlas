# Luxembourg national election archive

63 held records: 53 national legislative and constituent elections/regular renewals from 1845 through 2023, plus all ten Luxembourg European Parliament elections from 1979 through 2024. The 1848 Constituent Assembly and the separate 1918 constitutional-revision Assembly are retained as distinct elections. Initial appointed assemblies, individual by-elections, municipal contests and referendums are outside this legislative import. The hereditary head of state is not represented as an elected president.

The existing `linkedElectionIds` tool links parliamentary and European contests held on the same day. These are reciprocal links between separately browsable records, with separate national-legislature and European series. Reviewed national polling dates replace Europe-wide date intervals.

Historical restricted franchise, indirect elections, partial chamber renewals and multi-round votes are identified in each record. Seats in partial renewals mean seats elected, excluding continuing members. Early records transcribe only candidates explicitly marked elected, with one seat, no inferred party, and no national vote or share. Coverage stays partial; 1845 and April 1848 remain chronology-only. Unknown days use month/year precision, never an invented precise polling day.

Luxembourg uses multiple candidate votes per voter and panachage. Raw candidate/list totals are distinct from ballots cast and from voter-weighted theoretical electors. National percentages use a single raw-vote denominator. Joint source cells are counted once. Party seat rankings are not individual winner calls or government-formation claims.

## Certified recent results

The 2023 and 2024 result web pages retain unofficial election-night figures. The signed final recensement PDFs take precedence. `certified-extract.json` preserves reviewed values, exact source hashes and printed page references. Scanned 2023 reports were rendered, OCR-assisted and visually checked. East party totals sum the published candidate totals, which already include list votes; these are not added a second time. The four constituencies reconcile to 3,763,400 raw votes, 250,034 ballots cast, 231,343 valid ballots and 60 seats. National shares are calculated from these certified raw votes. Turnout uses the official national electoral-roll total and certified ballots cast. The 2024 nationwide report reconciles to 1,384,190 raw votes, 238,602 valid ballots and six seats.

## Rebuild and verify

Install Python `beautifulsoup4`. Download snapshots listed in `source-audit.json` into `.cache/luxembourg/` using their exact filenames and URLs; use `overview.html` for the chronology. Reviewed links, date corrections and certified extracts are included. Source hashes identify reviewed versions; changed PDFs require another review. Run `python scripts/import-luxembourg-elections.py`, `node scripts/check-luxembourg-elections.mjs`, and `pnpm test`.

The generator never publishes. Reject existing identifier conflicts; insert drafts, verify their content signatures, then publish only that reviewed set. Preserve concurrent edits to the country row. `pre-import-backup.json` records the existing country row and empty Luxembourg election set. Verify the public build and the deployed country page after publishing.
