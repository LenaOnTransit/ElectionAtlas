# Austrian national election archive

Checked 13 October 2026. Uses the existing `WorldElection`, country-party and
`ea_records` models; no new schema or public/editor architecture.

## Scope

67 records, 1848–2024: 42 parliamentary records and 25 presidential records
(including separate popular rounds, indirect selections, the annulled May 2016
runoff, and the postponed October 2016 repeat). 308 source-era party, alliance or
group profiles carry consistent editorial display colours. Independent
candidates stay independent; endorsements do not establish membership.

Includes the Constituent Reichstag, Imperial Council, 1919 constituent assembly,
all republican National Council cycles, and presidential elections. Imperial
territories extended beyond present Austrian borders. The appointed/hereditary
House of Lords and rolling Landtag selections of the modern Bundesrat are not
invented as nationwide general elections. No confirmed future national polling
date through 31 December 2027 was identified; none is invented for the Calendar.

## Method and limitations

- The Interior Ministry's historical presidential tables supply every candidate
  vote count in all 19 popular rounds from 1951 to 2022. Each round has its own
  valid-ballot denominator. Party/support labels and older turnout are referenced
  separately; known independent candidacies are not assigned an endorsing party.
- Final Ministry parliamentary returns replace secondary reporting for every
  Second Republic election. Where a Ministry page contains votes without seats,
  the referenced final seat table supplies mandates. Minor lists individually
  named by the Ministry have zero seats only where the complete allocation
  already accounts for all seats and every winning list is matched.
- The 2024 result totals 4,882,888 valid votes and 183 seats. Turnout uses
  4,929,745 participating voters / 6,346,059 registered electors. The 2022
  presidential turnout uses 4,148,082 / 6,363,336.
- Shared coalition/aggregate cells are counted once. National-group qualifiers
  distinguish similarly named Imperial Council organisations. Before 1907,
  curial votes are omitted rather than presented as equal-franchise popular
  percentages. Modern democracy assessments are not projected backwards.
- The 1919 table is a 170-member assembly snapshot including subsequently
  appointed territorial representatives, not 170 directly elected mandates;
  initially 159 were elected. The 1920 183-seat allocation covers delayed polls
  through 18 June 1922, not the initial 174-member October result. The 1970 and
  1995 cycles include the final regional repeats in October 1970 and October 1996.
- The May 2016 runoff is annulled historical data with no winner/advancement.
  April's first round remains valid. December is the valid repeat runoff. The
  postponed October poll has no invented result.
- Month/year precision is intentional for uncertain historical dates. The
  internal first-day date is only a sorting anchor. The 1871 selection cycle
  extended into 1872; June–July 1911 is not reduced to a falsely exact day range.
- Eight historical elections have no verified comprehensive result allocation:
  1848, 1861, 1867, 1870, 1871–72, 1873, 1879 and 1891. The 1885 club allocation
  covers 174 of 353 seats; the remainder stays unassigned. The five indirect
  presidential selections in 1920, 1924, 1928, 1931 and 1945 record the known
  selected president, with ballot counts and shares null pending verification.

## Reproduction

`links.json` and both source audits record retrieval URLs, hashes and unsuccessful
historical page attempts. Cache retrieved HTML under `.cache/austria/<key>.html`;
Ministry parliamentary pages use `nationalratswahl_<year>` keys, including the
regional-repeat pages. The presidential history page is
`official-pres-history.html`. Python source extraction needs BeautifulSoup4.

```sh
python scripts/extract-austrian-election-sources.py
python scripts/extract-austrian-primary-sources.py
python scripts/import-austrian-elections.py
node scripts/check-austrian-elections.mjs
pnpm test
pnpm exec tsc --noEmit
pnpm build
```

The importer only writes local fixtures. The reviewed SQL publication workflow
stages drafts, compares every payload and profile, then publishes those exact
IDs. It does not overwrite pre-existing elections or alter country assessments.
`pre-import-backup.json` preserves the original Austrian country record.

## Verification

All 67 election models and 308 profiles validated. All stored draft election
payloads and party profiles matched the tested fixtures exactly before
publication; the country record remained unchanged. All 67 are public version 2,
none enabled for live reporting, and no party references or colours mismatch.
Full project tests, TypeScript checking and production page generation passed.

The existing protected integrity system reports zero errors, eight
`RESULTS_MISSING` warnings and six `FINAL_PARTIAL` informational findings.
These 14 known historical gaps remain Open for moderator review; no exception
was automatically accepted and no historical result was automatically repaired.
