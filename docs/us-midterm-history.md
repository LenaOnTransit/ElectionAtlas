# U.S. historical House, Senate and governor elections

The archive covers the 119 completed federal cycles from 1788–89 through 2024, including 59 midterms and 60 presidential-year cycles. Each cycle has three entries: House, Senate, and governors. Governor entries cover elections held in that election year, not off-year elections or every sitting governor.

## Representation

House entries use the House historian’s initial election party divisions for the following Congress. Nonvoting delegates and resident commissioners are excluded. Unallocated seats in that source remain a separate gray group. District results and nationwide popular-vote percentages are not inferred from seats.

Senate and governor entries store independently sourced state contests in `contests`. Each race has its own percentages, selection method, special-election flag, notes, and sources. The Senate diagram contains elected candidates from regular races in the cycle. Continuing senators, special mandates, and earlier rounds marked `diagramExcluded` are excluded; the diagram is not the full Senate. Early Senate cycles extend into the following year and generally use legislative selection. Legislative vote counts are left blank when ballots, multiple legislative chambers, or placeholders are not comparable.

Candidate rows retain calls and colors. Fusion ballot lines are consolidated by candidate; a source’s candidate subtotal is used once. Blank, void, overvote, and undervote rows are excluded from candidate totals. Historical governor selection can differ from the popular plurality, as in Massachusetts in 1850.

## Ideology

`ideologyBasis` describes candidate-specific assessments, election-era party fallback, or unassessed cases. Its sources and explanation are public. These mappings are editorial interpretations, not numeric measurements by the cited sources. References use existing ideology guides and protected nine-axis ratings. No exact numeric ratings are published.

The broad fallback distinguishes early factions, anti-slavery/Reconstruction Republicans, industrial-era Republicans, mid-century Republicans, the Reagan coalition and contemporary Republicans. Democratic traditions likewise distinguish nineteenth-century limited-government platforms, Progressive-era/agrarian platforms, New Deal liberalism and the post-civil-rights coalition. These broad traditions do not imply ideological unanimity within a party. Independent or miscellaneous labels alone do not establish an ideology. Sourced progressives and other candidate assessments override the party fallback.

## Sources and reproduction

- U.S. House History: initial party divisions, https://history.house.gov/Institution/Party-Divisions/Party-Divisions/
- U.S. Senate History: party divisions, https://www.senate.gov/history/partydiv.htm
- MIT Election Data and Science Lab: statewide Senate returns, https://doi.org/10.7910/DVN/PEJ5QU
- FiveThirtyEight historical gubernatorial returns, with per-result official sources: https://github.com/fivethirtyeight/election-results/blob/main/election_results_gubernatorial.csv
- Historical election/state summaries and the records cited on those pages, linked separately per race.
- First-party platforms preserved by the American Presidency Project at UCSB; Senate History, NGA and state historical societies for candidate assessments.

ICPSR historical files required an account and were not imported. Algara/Amlani’s county dataset was researched but was not substituted for certified statewide candidate results. Source coverage varies: missing counts and omitted minor candidates are disclosed, rather than presented as a complete certified series.

Cache public sources with `python3 scripts/fetch-us-midterms.py` and `python3 scripts/fetch-us-governor-gaps.py`. The cache also needs `house.html`, `platforms.html`, MIT’s Senate CSV saved as `senate.tab`, and FiveThirtyEight’s `governors-538.csv`. Run `python3 scripts/import-us-midterms.py`; it builds source-linked templates and a source hash audit, never writes the database. Run `node --test scripts/check-us-midterms.mjs` before importing.

## Reads and security

`ea_world_summaries()` omits nested candidate tables from the atlas, archive list, and calendar. `ea_public_election(id)` loads exactly one published detail record. Both are security-invoker functions retaining RLS and explicit publication filters, including for editor sessions. Editor reads retain the full records so races can be edited. Static SEO generation includes separate state result tables from anonymous public records.

The internal `us-*-midterms` series IDs and template filenames are retained for continuity. Both midterm and presidential-year cycles appear in each office’s year selector. Existing archive entries are preserved when adding the missing presidential-year records.
