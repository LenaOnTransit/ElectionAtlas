# Czech Senate first-round live snapshot

The timestamp and official counting totals are recorded in `audit.json`; the corresponding official CSO XML is preserved in `results.xml`. `records.json` uses the existing WorldElection model and contains the overview, conditional runoff and 27 linked district results. `baseline.json` preserves the two existing records for optimistic concurrency and an audit trail.

The overview retains the **81-seat whole Senate**, as requested. Only **27 seats** are contested in 2026. Its existing party rows, previous-seat metadata and legitimacy assessment are preserved; no unverified full-chamber party allocation is introduced. Each district has one contested seat and its own candidate-vote denominator. Whole-chamber composition and district wins must not be conflated.

Winner and advancement flags require the official XML outcome field after a signed district protocol; partial leads never receive seats. Unreported districts have null vote counts and shares. National turnout remains omitted while the electorate is incomplete. This is a timestamped manual update, not an automatic refresh service.

To reproduce, download the three official datasets into `.cache/czech-2026`: `https://volby.gov.cz/appdata/senat/20261009/odata/vysledky.xml`, `https://volby.gov.cz/opendata/se2026/json/serk.json`, and `https://volby.gov.cz/opendata/se2026/json/cvs.json`; provide the current database baseline as `baseline.json`. Run `python scripts/update-czech-senate-2026.py`, then `node scripts/check-czech-senate-2026.mjs`. Database application is separate and must reject changed baselines rather than overwrite concurrent edits.
