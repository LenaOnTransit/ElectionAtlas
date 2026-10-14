# Archive result gaps — 14 October 2026

100 existing published elections receive 994 result rows, reducing the known gap from 171 to 71. Every patch is explicitly partial. Unknown votes, shares, previous seats and ideologies stay null or unassigned. No dummy result rows are used.

`pre-import-backup.json` contains the public baseline; `records.json` the new records; `reconciliation.json` records scope and sources. `remaining-gaps.json` preserves unresolved records for further archival research. Those gaps lack a reliable chamber-specific allocation in the consulted sources; they must not be filled with another chamber’s results, approximate counts represented as exact, or participation-only placeholders.

Run `python scripts/import-archive-gap-tables.py` to reproduce records from the checked source transcriptions, then `node scripts/check-archive-gap-tables.mjs`. `apply.sql` is atomic and idempotent and rejects any baseline changed since preparation.

Swiss source transcriptions use Parliament’s historical PDF, seat-ballot pages 25–61 and elected-member chronology 74–78. Separate seat ballots retain their own counts and no shared vote denominator. Earlier accepted-member rosters are explicitly reconstructed and are not full ballot tallies. Scottish records use election/service intervals, with the 1868 tied final seat and the 1880 Gazette return overriding naive interval counts. Spanish deputy compositions come from Fundación BBVA historical statistics, table 14.3, printed page 1091; these are observed seat compositions, not vote shares. Each record retains its source URLs and public explanations of scope.
