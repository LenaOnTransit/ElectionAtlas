# German national parliamentary archive

49 records: two North German Confederation precursor elections (1867), 13 German Empire Reichstag elections (1871–1912), the 1919 constituent National Assembly and eight Reichstag elections (1920–March 1933), three Nazi single-list ballots, one Sudeten territorial supplement, and all 21 Bundestag elections (1949–2025).

Germany retains country ID `de`. The Federal Republic is continuous: West German electoral territory through 1987; reunified territory from 2 December 1990. No GDR Volkskammer elections are included. There was no federal parliamentary election in 1945–1948. The 1868 Zollparlament election is outside the Reichstag/Bundestag series.

## Source conventions

* Bundestag votes and seats: Federal Returning Officer’s 2026 historical CSV, licensed under Datenlizenz Deutschland – Namensnennung – Version 2.0. National second votes from 1953; sole ballot in 1949. Seat composition includes indirectly selected West Berlin representatives. The 2021 results incorporate the 2024 Berlin repeat vote.
* Pre-1945 competitive results: Wahlen in Deutschland’s consistent national tables, calculated from historical official statistical publications listed in its source bibliography. Historical party-family aggregates remain aggregates; they are not fabricated individual-party results. The alternative GHDI and KAS tables were consulted but have different party allocations and rounding, so their figures are not mixed into this series.
* 1878: the historian table misprints the date as 30 June; the record uses the actual 30 July election date from the German Historical Museum’s dated election artefact.
* 1919: final 423 seats, including the two additional eastern-army SPD members, rather than initial 421. This distinction is confirmed by the Bundestag. Source turnout is approximate.
* 1920: completed nationwide results after territorial supplementary voting through November 1922, recorded under the general election’s June 1920 date. May 1924 similarly incorporates the September supplement. These supplements are not mislabeled as new nationwide elections.
* December 1924: published vote rows leave 779 valid votes unallocated. A clearly labeled discrepancy row preserves the denominator and avoids attributing votes to a party.
* Nazi-era figures are reported regime-era figures, not evidence of democratic consent. These records and March 1933 are marked uncompetitive. Single-list approval percentages are explicitly distinguished from competitive vote shares. November 1933 and March 1936 ballot totals follow the Nohlen/Stöver tables transcribed at the linked pages. April 1938 votes cover the German Reich excluding Austria (partial vote coverage); its 814 seats include Austria. The December territorial supplement adds 41 mandates, reaching 855. SUDD provides the separately scoped 1938 ballot totals.

Saved party/list labels retain source abbreviations; aggregated historical groups are not added as individual parties. Election-period ideology labels are limited to clear cases; saved party defaults are empty to avoid imposing contemporary classifications on historic results. Colours for unclassified minor lists are neutral, not asserted historical branding.

Rebuild with `python scripts/import-german-elections.py`; downloaded source caches are ignored. Validate with `node scripts/check-german-elections.mjs`. `source-audit.json` records consulted source hashes. This script only generates files and never writes to the database. Publishing must use an explicit database transaction with existing-record conflict protection. Rebuilding must not overwrite subsequent editorial changes.
