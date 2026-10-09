# Election Data Integrity Checker

The checker reads the existing `ea_records` rows of kind `world_election`, including private drafts, `WorldResult` rows, state contests, regional overview/child links, and embedded US House district tables. It does not introduce a replacement election model. The legacy newsroom's fictional live-results sample and its separate Senate forecasting configuration are not historical archive records and are outside this scan.

Only membership in `ea_editors` grants access, matching the existing moderator newsroom. The protected page is `/editor/integrity`. Anonymous visitors and signed-in readers cannot read findings, scan metadata, context or review notes, invoke operational RPC actions, or run the private worker. Public generation requests no checker tables, emits only a noindex loading shell for this route and excludes it from the sitemap. A static host cannot make JavaScript source secret; confidential data and operations are protected in Supabase, not by hiding a URL.

## Rules and limitations

| Rule | Meaning and safeguards |
| --- | --- |
| ELECTION_DUPLICATE | Matching country, election type, date interval/precision, chamber, method, round, geographic/component identity and compatible series IDs suggests a duplicate. Explicit geography and legacy district/constituency title identifiers distinguish separate bodies. Unknown dates are not treated as identical events. No merge is performed. |
| DATE_INVALID / DATE_ORDER / DATE_PRECISION | Check calendar validity, polling order and agreement with precision/confirmation. Year/month reference dates are not treated as exact days. Historical multi-week polling remains valid. |
| ROUND_ORDER / RESULT_DATE | Exact-day numbered rounds in a shared series or explicit link are compared within 180 days. Postponements and reruns may explain warnings. The model's `checked` field is a source-review date, never a result date. Optional checker context can record a source-backed announcement date; an announcement before polling triggers review. |
| COUNT_INVALID / SHARE_RANGE | Recorded vote, ballot, seat, previous-seat and electoral counts must be non-negative integers; percentages must be numeric and within 0–100. Explicit weighted-count context allows fractional vote weights. Multi-member candidate selections may exceed voter counts and are not rejected for that reason. |
| SHARE_TOTAL | Sum only complete tables with all shares and an explicitly confirmed or clearly labelled common denominator. Use tolerance `max(0.2, number of rows × 0.05)` percentage points. Skip weighted, mixed, component and separate-electorate bases unless explicitly confirmed. Blank-ballot conventions and rounding may explain warnings. Constituency tables are never combined. |
| SEAT_TOTAL | Compare a complete, fully allocated parliamentary table with that election's `totalSeats`, or a source-backed context override. Do not substitute today's chamber capacity. Partial coverage, partial renewals and missing allocations are not forced to equal a whole chamber. Embedded `HouseOverview` uses its existing 435-seat US House model. Appointed seats and elected components require correctly scoped input/context. |
| SOURCE_MISSING / RESULTS_MISSING | Missing source arrays or held-election/contest tables require review. A regional overview may correctly have no aggregate rows when results exist on child election records. Scheduled/cancelled elections do not require results. Missing historical tables remain gaps, not invented results. |
| FINAL_PARTIAL / FINAL_REQUIRED | Final partial coverage is informational: finality of entered results is distinct from archive completeness. Final complete tables with absent required allocation/value fields receive warnings, or missing-table errors. The current model supports final/provisional, not a separate certification field; future certified result status is also recognized by the rules without changing historical classifications. |
| ROW_DUPLICATE | Compare IDs and normalized candidate/party identities within each table. Same-party candidates with different names and identical names in different constituencies remain distinct. Repeated historical ballots may legitimately repeat a candidate, so flags require review. |
| CHANGE_ANOMALY | Compare complete records with the same country, body, scope, series, round, method and vote basis, 180 days–10 years apart. A ≥25% capacity change or ≥25-point share change for a stable saved party ID is informational. No party-name guesses or cross-denominator swings are calculated. Reforms and genuine swings are valid explanations. |

An unflagged record is not certified correct. The checker cannot assess source reliability, infer missing ballot denominators, identify every spelling variant, reconstruct historical results or distinguish every legacy sub-contest lacking structured identity. Moderators retain judgment.

## Persistent reviews and context

`ea_integrity_findings` stores deterministic keys by election/rule/table/subject and a fingerprint of evidence/explanation. Rescanning does not create repeat alerts. Findings that disappear become Fixed and inactive; recurrence reopens them. Accepted Exception requires a note and remains accepted only while the same active evidence persists. Changed evidence reopens review without deleting notes/history. Marking Fixed queues verification; the finding reopens if the condition persists. Reviews require the current evidence fingerprint, preventing stale review writes.

`ea_integrity_reviews` retains review history. `ea_integrity_scans` records full/incremental progress. `ea_integrity_context` stores validation-only metadata with a moderator rationale; it never edits the election payload. Examples:

```json
{
  "resultDate": "2024-07-10",
  "tables": {
    "national": {"commonDenominator": false, "seatScope": "not-comparable"},
    "contest:race-example": {"complete": true, "expectedSeats": 1},
    "district:example": {"countMode": "weighted"}
  }
}
```

Set these only with source evidence. A scope override is an explicit review choice, not automatic historical correction. Complete-table and integer checks can still detect contradictions; unsupported interpretations must be documented as accepted exceptions.

## Automation and operation

A trigger queues inserts, deletes and substantive election JSON edits, including direct SQL imports and existing `ea_save_record` calls. Version bumps and presentation-only fields do not force redundant scans. The queue coalesces repeated edits per ID and rechecks relevant family members/linked records, so duplicates and preceding-election comparisons are updated on both sides. Regional child edits also enqueue their overview.

The private SQL worker runs every minute and processes at most 100 records per scheduled invocation (hard maximum 200). A full archive scan is queued nightly at 02:20 UTC and on demand in the dashboard. No browser session, external notification or secret client key is needed. Family/overview indexes and trimmed peer payloads reduce work; there is no archive-sized request subject to Supabase's 1,000-row limit. The dashboard queries server-side filters and paginates 50 findings at a time.

The worker serializes scans, keeps edits committed after its snapshot queued, and resolves findings only after that record's successful validation. Individual failures remain queued with bounded retry delay and appear as a failure count in the dashboard. Private checked-record fingerprints report distinct records scanned. An in-progress full scan is reused rather than duplicated. The dashboard can process a batch immediately; scheduled execution completes scans even when no moderator is signed in.

The engine contains no writes to election results, country records, classifications, sources, publication or revisions. Only checker operational tables change. The migration creates RLS-protected tables, a non-exposed privileged implementation with a membership guard, and a public security-invoker RPC wrapper. Direct client writes to findings are not permitted even for moderators.

## Validation

Run `pnpm test`, `pnpm typecheck`, `pnpm build`, and execute `supabase/tests/data-integrity.sql` as database owner after both integrity migrations. SQL fixtures cover modern and historical capacities, partial coverage, scheduled records, weighted votes, presidential electoral votes, exact/coarse dates, multi-round timing, multiple constituencies, regional overviews, duplicate rows/events, stable-party informational swings, persistence, required exception notes, stale reviews, resolution/recurrence, and anonymous/reader/moderator RLS/RPC access. The SQL transaction rolls back every fixture and operational test change. Repository checks verify route gating, editor deep links, server-side filters and absence of private checker data in public rendering. Confirm the archive checksum before and after scans, and inspect cron run history and queued failure counts.
