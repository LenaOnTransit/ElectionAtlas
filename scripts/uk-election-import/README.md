# UK general election results, 2010–2024

The five most recent general elections are recorded under the existing `gb` country record: 6 May 2010, 7 May 2015, 8 June 2017, 12 December 2019 and 4 July 2024. The existing 2024 election ID is retained and its partial five-party result is expanded to the full official result.

The source is the UK Parliament Election Results archive. All registered parties in each official party table are included, including parties with no seats. The official non-party candidate table separately identifies independent candidates and the Commons Speaker. To reconcile the archive to exactly 650 seats and the full valid-vote denominator, independent and other non-party candidates are aggregated into one row; the Speaker receives a separate row. The 650 seats include the Speaker and Sinn Féin members who do not take their seats.

Vote shares are recalculated from the exact official votes and valid-vote total, then stored to four decimal places. Turnout uses the UK Parliament dataset’s valid votes divided by electorate convention. Party profiles are saved for parties that won seats or reached at least 0.5% of votes in one of these elections; all minor parties remain present in results and use a neutral colour when they have no reusable profile. No ideology classifications are inferred.

Run `python scripts/import-uk-general-elections.py` to rebuild records from the source extract. It does not publish. Run `node scripts/check-uk-elections.mjs` to validate votes, seats, dates, country IDs and saved-party links.
