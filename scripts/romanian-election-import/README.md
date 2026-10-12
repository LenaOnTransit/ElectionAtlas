# Romania national archive

Reuses the existing `WorldElection` and `CountryParty` models and protected import/publication workflow. No new election schema or public moderation surface is introduced.

Scope: 116 national parliamentary chamber/event and presidential round records from 1864 through 2025. The event inventory includes early dissolutions, separate Senate renewals, the February and May 1914 elections, Communist-era assemblies, four indirect presidential selections, and the annulled 2024 process. Local, European Parliament and referendum ballots are separate subjects; this is not a complete inventory of constituency by-elections. No confirmed future Romanian national polling date through 31 December 2027 was established at the 12 October 2026 review, so none is invented for Calendar.

The 20 parliamentary chamber records from 1990 onward reconcile their own valid-vote denominators and final seat allocations. Minority representative seats are included. Historical capacities vary: 2012 has 412 deputies and 176 senators; 2024 has 331 deputies and 134 senators. Those figures must not be replaced by today's generic constitutional seat count.

## Sources and reproduction

`links.json` identifies the secondary result-table pages and their bibliographies. `source-tables.json` preserves extracted factual table cells and shared-cell identities; `source-audit.json` records retrieved HTML hashes. Modern tables often cite AEP/BEC, while older tables cite historical handbooks, contemporary press and official gazettes. This does not mean every secondary transcription has been independently verified against an original protocol. AEP/BEC endpoints encountered browser challenges/403 responses; the independently checked 2025 presidential totals come from CCR Decisions 39 and 43 published by the Ministry of Justice. `primary-reconciliation.json` records all 11 first-round candidate totals, both runoff totals, and the certified register/attendance denominators.

The primary Senate history establishes the bicameral chronology, the appointed early Senate, and the separate 1869 Senate dissolution election. Enciclopedia României's political portal supplies the early event inventory, including events whose linked articles remain unwritten. The February 1914 event is additionally supported by Ana Maria Rădulescu, *Studia Politica* 5(1), 2005, pp. 203–210 (SSOAR). Only numerical facts and source references are reproduced, not the paper's prose or local constituency results as invented nationwide totals.

To reproduce, retrieve each `links.json` URL to `.cache/romania/<key>.html`, then run:

```sh
PYTHONPATH=/path/to/beautifulsoup python scripts/extract-romanian-election-sources.py
python scripts/import-romanian-elections.py
node scripts/check-romanian-elections.mjs
pnpm test
pnpm build
```

The generator does not write to Supabase. `pre-import-backup.json` preserves the existing Romania country row; it had no election records or party profiles. Its country-level electoral assessment is not copied into historical elections.

## Methodology and limitations

- Duplicate coalition/front vote and seat cells are counted once using HTML cell identity. Constituent parties are grouped under the shared election list. Missing votes are never derived from rounded percentages or filled with a guessed residual.
- Presidential rounds remain separate, with separate denominators. First-round advancement and final winners are explicit. The 2024 first round and planned runoff have `status=cancelled`: the former retains clearly labelled annulled returns, the latter has no certified result. Neither has an elected or advancing candidate. The 2025 rerun is a distinct pair of records.
- The 1922 Chamber combines different ballot systems and vote-mark denominators. Only its reconciled 369-seat allocation is entered. The 1928 Senate table is internally inconsistent across electoral components; the record explicitly covers the verified 113 universal-college mandates, not an invented full chamber. Other prewar Senate capacities describe the source's elected mandates, excluding unspecified senators by right.
- Restricted suffrage, mixed direct/indirect colleges, institutional senators, royal dictatorship and noncompetitive Communist fronts are described in notes. No modern electoral legitimacy assessment or reconstructed genuine vote is inferred. Early selection methods are left unspecified where a single model value would misrepresent mixed colleges.
- Historical dates with uncertain Julian/Gregorian conversion use month/year precision. Their internal first-day anchors are for sorting only; they are not confirmed polling days. Some later ranges cover the parliamentary election cycle across chambers and territories.
- 32 early event/chamber records currently have no verified national result table (`not-entered`, partial). The 1911 Chamber table accounts for 182 of 183 mandates; one mandate remains unverified. The 1907 Senate table has two disputed mandates and is explicitly provisional. The four indirect presidential selections have known selected candidates but unverified ballot counts/attendance; numerical coverage stays partial. These are manual archival research tasks, not live contests.
- Party/front/support names remain source-era labels. Historical entities are distinguished from modern names. Profiles use no inferred ideologies; colours are an editorial display palette, not a verified official branding claim. The existing party loader is paginated with a stable name/id order so the expanded archive is not silently limited to 1,000 profiles.

`reconciliation.json` supplies a per-record numerical audit. Regression checks exercise modern and historical seat capacities, multi-round linking, cancelled/annulled events, mixed denominators, single-front cell deduplication, independent candidates, saved party references, and pagination beyond 1,000 profiles. Database publication must follow draft insertion, exact stored-payload comparison, and version-guarded publication of only the reviewed IDs. The existing protected integrity queue scans the imported records; accepted exceptions are not automatically set.

Import verification: all 116 stored draft payloads and all 418 saved party profiles matched the validated files exactly before version-guarded publication. All 116 records are public at version 2, with live reporting disabled. The full test suite and production build passed; the generated country archive contains all 116 links and all 116 result/event pages exist. The automatic integrity scan reported no errors, 32 missing-table warnings, and six informational findings (five final records with partial numerical coverage plus the 1919–1920 Chamber size change from 568 to 366). Findings remain open for manual review; no historical data or review status was automatically altered.
