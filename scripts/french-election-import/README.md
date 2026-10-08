# French national archive

110 held records: 68 lower-house elections/renewals from the 1789 Estates-General precursor through 2024, and 42 presidential rounds/designations from 1848 through 2022. Existing scheduled 2027 records are outside this import.

The Directory records describe historical legislature renewals, not a modern full lower-house composition. The 1871 presidential designation is a constitutional law, not a candidate election. Indirect presidential records show the decisive constitutional ballot, not every unsuccessful ballot or preliminary party meeting. Direct presidential elections include both rounds.

Each record carries sources, source scope and limitations. Older territorial totals and retrospective political groups are marked partial. 1789, 1817 and 1818 remain chronology-only where reconciled results are unavailable. No missing votes or modern party identities are invented. Parliamentary popular votes normally represent the first round; seats represent the final distribution. Shared table cells are counted once. See record notes for corrected dates, totals and denominators.

## Rebuild

Install Python `beautifulsoup4`. Download the HTML sources named in `source-audit.json` into `.cache/france/`: filenames map to `https://en.wikipedia.org/wiki/<filename without .html>`, except `indirect.html` maps to `List_of_indirect_presidential_elections_in_France` and `overview.html` maps to `Legislative_elections_in_France`. The audit records SHA-256 hashes of the exact reviewed snapshots. Later source edits must be reviewed; fetching a newer page is not proof of identical input.

Run `python scripts/import-french-elections.py` and `node scripts/check-french-elections.mjs`. The generator only writes local JSON; it never publishes. Publishing requires checking identifier conflicts and protecting existing edited records. The two 2022 identifiers are retained; their previous payloads are saved in `pre-import-backup.json`.
