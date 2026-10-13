# Swiss national election archive

Checked 13 October 2026. Uses the existing `WorldElection`, country-party,
overview/related-election links and `ea_records` infrastructure. No schema,
authorization, newsroom or public UI changes.

## Scope

395 records: 52 National Council elections (1848–2023), 44 documented Council of
States election-year compositions, 180 historical presidential selections,
52 historical Federal Council general renewals, the 2025 replacement election,
60 separate executive-seat ballots, and six upcoming records. Of these, 392 are
new; the three pre-existing Calendar records remain byte-for-byte unchanged.
83 party/group profiles provide consistent editorial display colours.

The public country timeline has 335 overview entries; the 60 individual seat
ballots appear through the existing overview/related-election links. All 395
records have public detail pages. This covers national general cycles and the
annual presidency; it is not a claim to enumerate every historical parliamentary
by-election or every mid-term Federal Council replacement.

The existing 9 December 2026 presidential selection and 24 October 2027
parliamentary overviews are retained. New confirmed entries cover the full
Federal Council renewal and presidency selection on 15 December 2027. The
president selected then serves in 2028, but the election falls within 2027.
Parmelin's replacement is separately recorded as expected on 9 December 2026,
following the party's stated current plan; it is not promoted to a confirmed
official date and has no invented successor or results.

## Method and limitations

- National Council dates come from Parliament's historical chronology. The
  1848 election had no uniform national polling day; October precision is used.
  Every election uses its historical capacity, from 111 seats in 1848 to 200
  in modern elections.
- Before 1919, majority systems, multiple votes and repeated candidate ballots
  make a naïve nationwide party-vote total inappropriate. Only reported party
  or group seats are entered. For proportional elections, national party
  strength is based on canton-size-normalised voter equivalents. Rounded proxy
  counts are not recorded as exact ballots. Shared coalition/percentage cells
  are counted once; their seat allocations are grouped under the shared list.
- The FSO's final PX-Web series independently supplies all party percentages
  and mandates for all 14 National Council elections from 1971 to 2023. In 2023
  the SVP has 62 seats and 27.93% normalised party strength; SP has 41 seats.
- The Council of States has no uniform nationwide general renewal. Its
  historical cantonal systems included legislatures, Landsgemeinde assemblies,
  differing terms and later direct ballots with varying runoff dates. These
  records are source-scoped election-year composition snapshots. They do not
  assert that all seats were contested on one date. National vote/share/turnout
  fields stay null. Capacity is 44 before Jura and 46 thereafter. The 2023
  composition reconciles at 46, including 15 Centre and 11 FDP seats.
- Eight early Council of States snapshots are not invented where no allocation
  was found: 1887, 1896, 1899, 1902, 1905, 1908, 1911 and 1917. The source for
  1939 accounts for 43 of 44 mandates; the unaccounted mandate stays unassigned.
- The president is annually elected by the United Federal Assembly to chair
  the seven-member Federal Council; the Council collectively performs
  head-of-state functions. The presidency is not a popular election of a
  separate head of state. Parliament's published historical table supplies
  172 term entries through 2020 (1848/49 is one selection), supplemented by its
  modern table through 2026. An independently published parliamentary XLS
  cross-checks the overlapping counts. Only the elected candidate's count is
  entered; remaining ballots and their denominator remain incomplete. The
  scholarly percentage of total assembly membership is deliberately not
  substituted for a share of valid ballots.
- Early scholarly affiliation labels describe a member's initial Federal
  Council affiliation rather than necessarily the later presidential-election
  affiliation. This scope is explicit in the label and notes. It is not mapped
  to today's party organisations. No ideology or legal continuity is inferred.
- Victor Ruffy and Fridolin Anderwert were elected for 1870 and 1881 but died
  before taking office. Their original selections are separate from the Dubs
  and Droz replacements. The replacement polling dates remain Unknown rather
  than being guessed from the upcoming term. Other unverified days use year
  precision; January 1 is only a sorting anchor for the selection year.
- Federal Council general renewals are indirect selections of seven separate
  seats. Modern renewal summaries retain the elected members and their winning
  counts, with partial numerical coverage because the counts have different
  denominators. Every source ballot is linked separately, with its own valid
  total and an absolute-majority test. Earlier unsuccessful rounds have no
  elected candidate. Unspecified other votes are an aggregate, never a winner.
  Candidate affiliation remains explicitly unverified where the source does
  not identify it; this is not silently reclassified as Independent.
- Seven renewal events from 1999 to 2023 provide 58 separate ballots; the 2025
  replacement provides another two. Modern winning counts are checked against
  parliamentary tables wherever retrieved. The French official 2019 page is
  used because the German page contains later-member labels. The 2023 secondary
  Keller-Sutter majority typo is not used: the threshold follows the 224 valid
  ballots. Her winning 176 votes exceed the correct 113-vote threshold.
- Forty-five historical Federal Council renewals retain event metadata but no
  invented full ballot table or seven-member outcome.

## Reproduction

Source audits preserve exact URLs, hashes and failed retrievals. Retrieve the
linked HTML into `.cache/switzerland/<key>.html`; the primary audit identifies
the PDF, XLS and PX-Web response cache names. PX-Web requests select Switzerland,
all years/parties, normalised party strength, and elected mandates for all sexes.
Do not substitute raw canton vote marks for national party strength. The PDF
text cache is produced with `pdftotext -layout`. Extraction needs BeautifulSoup4
and xlrd; these are source-reading tools, not website dependencies.

```sh
python scripts/extract-swiss-election-sources.py
python scripts/extract-swiss-primary-sources.py
python scripts/extract-swiss-council-sources.py
python scripts/import-swiss-elections.py
node scripts/check-swiss-elections.mjs
pnpm test
pnpm exec tsc --noEmit
pnpm build
```

The importer writes fixtures only. Publication stages the 392 new records as
drafts, verifies exact stored payloads and all 83 profiles, then publishes only
those IDs. No pre-existing election, country assessment or historical result is
overwritten. `pre-import-backup.json` preserves the original country and three
Calendar records.

## Verification and review

All 395 models and 83 profiles validated; full project tests and TypeScript
checks passed. All 392 stored draft payloads and 83 party profiles exactly
matched the tested fixtures. The country row and all three existing elections
remained unchanged. All 395 are public, none enabled for live reporting, and
no saved party references or colours mismatch. Production generation produced
all detail pages, 335 country timeline links and 60 linked ballot pages.

The existing protected integrity worker completed its queue with zero errors,
45 missing-result warnings and 189 partial-result informational findings.
These known gaps remain Open for moderator review: historical Council ballot
tables, presidency tables limited to the elected candidate, executive overview
summaries across separate ballots, and the incomplete 1939 States allocation.
No findings were automatically accepted and no results automatically repaired.
