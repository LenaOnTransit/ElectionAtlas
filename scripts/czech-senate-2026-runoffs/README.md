# Czech Senate runoffs, 16–17 October 2026

22 new published district elections, 44 candidates; updates the existing second-round overview. Every district is enabled in Live Elections using the existing `live.enabled` flag. The overview remains a directory, not an additional duplicated live race.

The Interior Ministry's confirmed district list exactly matches the signed `ZVOLEN_1KOLO="2.KOLO"` advancement flags in the official Czech Statistical Office XML. The candidate register independently confirms each name and active registration. The new rows preserve saved party profiles, colours, registered membership/nomination distinctions and ideology attribution from the reviewed first-round records. No party membership or personal ideology is inferred.

Runoff districts: 3 Cheb; 6 Louny; 9 Plzeň-město; 15 Pelhřimov; 18 Příbram; 21 Praha 5; 24 Praha 9; 27 Praha 1; 30 Kladno; 36 Česká Lípa; 42 Kolín; 45 Hradec Králové; 51 Žďár nad Sázavou; 54 Znojmo; 60 Brno-město; 63 Přerov; 66 Litovel; 69 Frýdek-Místek; 72 Ostrava-město; 75 Karviná; 78 Zlín; 81 Uherské Hradiště.

Districts 12 Strakonice, 33 Děčín, 39 Trutnov, 48 Rychnov nad Kněžnou and 57 Vyškov already elected a senator and are excluded. Their first-round records are unchanged.

Polling: Friday 16 October 14:00–22:00 and Saturday 17 October 08:00–14:00, Europe/Prague (CEST). As verified in audit.json, the official XML publishes no counted runoff precincts. All second-round votes, shares, turnout and awarded seats therefore remain null, with no winner/advancement flags. First-round votes are not carried over. Every new election links its original first-round record and the national/second-round overview. Each district elects one senator; the overview counts the 22 contested runoff seats rather than the full 81-member Senate.

This change enables live-page selection and uses the site's existing refresh of saved records. It does not claim an automatic external-feed importer or predict a winner. Public bulletins explicitly say no runoff figures have been published. Polling an XML feed or posting future results is not scheduled by this import.

## Sources

- Ministry: https://mv.gov.cz/volby-referenda/informace-pro-volice-k-ii-kolu-voleb-do-senatu
- Official XML: https://volby.gov.cz/appdata/senat/20261009/odata/vysledky.xml
- Active candidate register: https://volby.gov.cz/opendata/se2026/json/serk.json

Official XML is retained in official-results.xml. Audit hashes identify all inputs; pre-import-backup.json preserves existing content. Reproduction: download the three inputs into `.cache/czech-runoffs` as `ministry.html`, `results.xml`, `candidates.json`; run `PYTHONPATH=.cache/python-libs python scripts/prepare-czech-senate-runoffs-2026.py` (BeautifulSoup required), then `python scripts/build-czech-senate-runoffs-sql.py`. The builder aborts if runoff counting has begun, requiring a current result import instead of overwriting newer figures.

Validate with `node scripts/check-czech-senate-runoffs-2026.mjs` and repository checks. import.sql performs one atomic additive DML transaction: new IDs must be absent or equal to the desired dataset, and the existing overview must match its exact saved baseline or desired data. No historical first-round figures, country assessments, parties, RLS, authentication or schema changes are made. Titles include Czechia, Senate, district, runoff and year. Public text is factual coverage only.
