# Montenegro parliamentary archive

Country: existing `me` (`world-country-me`). Checked 6 October 2026.

This assignment contains 59 parliamentary records from 1905 through 2023: 12 national multiparty elections and 47 historical assembly/council records. Eleven modern tables are complete. The 2006 table and all historical records are explicitly partial. No presidential, local or Yugoslav federal contests are included. The 1943 wartime convention and the 1947 conversion of the existing assembly are not treated as new parliamentary elections.

`records.json` is the exact version-1 publication payload. `parties.json` contains 20 reusable country profiles, all without inferred ideology. Coalition results retain election-specific labels rather than being split into component-party vote rows. Royal-era parties are not linked to present-day names. Colours are editorial display conventions. Existing country legitimacy data is not altered.

## Sources and reconciliation

The six available final commission tables (2006, 2009, 2012, 2016, 2020, 2023) were checked directly. The 1990–2002 figures use Boris Lipovina’s MNEE transcription of the cited electoral commission reports published in Pobjeda/the Official Gazette. `national-results.json` preserves the source cells and qualifications; `source-audit.json` retains precise archival references and denominator checks. MNEE’s party-name, election-date and electoral-system references were checked separately. All 19 linked source URLs returned HTTP 200.

For 1990/1992 the valid-vote denominator is reconstructed from the list totals; it was not independently reported in the cited commission return. All modern tables reconcile their seat totals. The 2006 final lists sum to 338,833 votes against 338,835 valid ballots: a two-vote gap remains explicitly documented and coverage is partial. Shares retain the 338,835 denominator. No fabricated Other row absorbs the gap.

The 2016 final return identifies the 693-vote list as Stranka srpskih radikala (SSR); the reused MNEE SRS label is corrected without linking it to the earlier Šešelj party. Final 2020 DPS votes are 143,515. Final 2023 results follow certification on 14 July, with the original 11 June general-election date retained. Rejected, missing, cancelled/replaced ballots and turnout denominators are explained in the records.

UNDP’s 2024 historical study and Montenegro’s parliamentary archives establish the socialist-era dates, selection rules and council sizes. Separate chambers keep separate records, electorates and cross-links. The 1965/1967 half-renewals list only newly filled seats; continuing incumbents are not reported as wins. Historical aggregate rows count representatives whose party affiliations are not tabulated: they are not Communist Party vote totals. Votes, percentages, turnout and previous party seats remain null. Historical “final” denotes the sourced seat outcome, not a recovered ballot certification.

Unresolved historical qualifications: realised chamber totals in 1905–1911; the binary direct/indirect method for the 1953/1958 Producers’ Council (optional flag omitted); the 3 July date printed for the 1963 Organisational and Political Council, versus 3 June for other councils; and absent original ballot/party returns. Royal-era grouping tables use explicitly labelled secondary election accounts alongside the parliamentary history. Their appointed/elected member differences and calendar-style uncertainty remain documented.

## Validation and publication

Rebuild the deterministic payload with `python scripts/import-montenegro-elections.py`; check it with `node scripts/check-montenegro-elections.mjs`. The checker imports the current `validateWorldElection` and `validateParty`, reconciles national votes/seats/shares/turnout, checks historical nulls, partial coverage, half-renewals, party links, unique IDs, cross-links, source-extract hashes and generated SEO.

The generator does not publish. Before publication, re-read all Montenegro country, election and party records; if any assigned record or matching party has appeared, reconcile and preserve its identity/version instead of overwriting. Initial publication uses a guarded transaction containing only new Montenegro rows at version 1 and these party profiles. No changes to RLS, schemas, credentials or other-country records are required. Initial owner imports do not impersonate an editor or fabricate authenticated revision entries; subsequent editor saves follow the normal revision RPC.

Repository tests and the production build passed before publication. After publication, regenerate the public pages and verify every assigned ID in the country archive, the generated election metadata, the anonymous public API and the successful Pages deployment.

## Assigned election IDs

| ID | Date / period | Chamber | Coverage |
|---|---|---|---|
| `world-montenegro-1905-11-27-constitutional-assembly` | 1905-11-27 | Constitutional Assembly | partial |
| `world-montenegro-1906-09-27-parliament` | 1906-09-27 | National Assembly | partial |
| `world-montenegro-1907-10-31-parliament` | 1907-10-31 | National Assembly | partial |
| `world-montenegro-1911-09-27-parliament` | 1911-09-27 | National Assembly | partial |
| `world-montenegro-1914-01-11-parliament` | 1914-01-11 | National Assembly | partial |
| `world-montenegro-1918-11-21-podgorica-assembly` | 1918-11-21 | Podgorica Assembly | partial |
| `world-montenegro-1946-11-03-constitutional-assembly` | 1946-11-03 | Constitutional Assembly | partial |
| `world-montenegro-1950-10-08-national-assembly` | 1950-10-08 | National Assembly | partial |
| `world-montenegro-1953-11-22-republican-council` | 1953-11-22 | Republican Council | partial |
| `world-montenegro-1953-11-26-producers-council` | 1953-11-26 | Council of Producers | partial |
| `world-montenegro-1958-03-23-republican-council` | 1958-03-23 | Republican Council | partial |
| `world-montenegro-1958-03-28-producers-council` | 1958-03-28 | Council of Producers | partial |
| `world-montenegro-1963-06-03-economic-council` | 1963-06-03 | Economic Council | partial |
| `world-montenegro-1963-06-03-education-cultural-council` | 1963-06-03 | Education and Cultural Council | partial |
| `world-montenegro-1963-06-03-social-health-council` | 1963-06-03 | Social and Health Council | partial |
| `world-montenegro-1963-06-16-republican-council` | 1963-06-16 | Republican Council | partial |
| `world-montenegro-1963-07-03-organisational-political-council` | 1963-07-03 | Organisational and Political Council | partial |
| `world-montenegro-1965-04-04-economic-council` | 1965-04-04 | Economic Council | partial |
| `world-montenegro-1965-04-04-education-cultural-council` | 1965-04-04 | Education and Cultural Council | partial |
| `world-montenegro-1965-04-04-organisational-political-council` | 1965-04-04 | Organisational and Political Council | partial |
| `world-montenegro-1965-04-04-social-health-council` | 1965-04-04 | Social and Health Council | partial |
| `world-montenegro-1965-04-18-republican-council` | 1965-04-18 | Republican Council | partial |
| `world-montenegro-1967-04-23-economic-council` | 1967-04-23 | Economic Council | partial |
| `world-montenegro-1967-04-23-education-cultural-council` | 1967-04-23 | Education and Cultural Council | partial |
| `world-montenegro-1967-04-23-organisational-political-council` | 1967-04-23 | Organisational and Political Council | partial |
| `world-montenegro-1967-04-23-republican-council` | 1967-04-23 | Republican Council | partial |
| `world-montenegro-1967-04-23-social-health-council` | 1967-04-23 | Social and Health Council | partial |
| `world-montenegro-1969-04-13-republican-council` | 1969-04-13 | Republican Council | partial |
| `world-montenegro-1969-04-23-communes-council` | 1969-04-23 | Council of Communes | partial |
| `world-montenegro-1969-04-23-economic-council` | 1969-04-23 | Economic Council | partial |
| `world-montenegro-1969-04-23-education-cultural-council` | 1969-04-23 | Education and Cultural Council | partial |
| `world-montenegro-1969-04-23-social-health-council` | 1969-04-23 | Social and Health Council | partial |
| `world-montenegro-1974-04-25-associated-labour-council` | 1974-04-25 | Council of Associated Labour | partial |
| `world-montenegro-1974-04-25-municipalities-council` | 1974-04-25 | Council of Municipalities | partial |
| `world-montenegro-1974-04-25-socio-political-council` | 1974-04-25 | Socio-Political Council | partial |
| `world-montenegro-1978-04-13-associated-labour-council` | 1978-04-13 | Council of Associated Labour | partial |
| `world-montenegro-1978-04-13-municipalities-council` | 1978-04-13 | Council of Municipalities | partial |
| `world-montenegro-1978-04-13-socio-political-council` | 1978-04-13 | Socio-Political Council | partial |
| `world-montenegro-1982-04-13-associated-labour-council` | 1982-04-13 | Council of Associated Labour | partial |
| `world-montenegro-1982-04-13-municipalities-council` | 1982-04-13 | Council of Municipalities | partial |
| `world-montenegro-1982-04-13-socio-political-council` | 1982-04-13 | Socio-Political Council | partial |
| `world-montenegro-1986-04-21-associated-labour-council` | 1986-04-21 | Council of Associated Labour | partial |
| `world-montenegro-1986-04-21-municipalities-council` | 1986-04-21 | Council of Municipalities | partial |
| `world-montenegro-1986-04-21-socio-political-council` | 1986-04-21 | Socio-Political Council | partial |
| `world-montenegro-1989-06-12-associated-labour-council` | 1989-06-12–1989-06-13 | Council of Associated Labour | partial |
| `world-montenegro-1989-06-18-municipalities-council` | 1989-06-18 | Council of Municipalities | partial |
| `world-montenegro-1989-06-18-socio-political-council` | 1989-06-18 | Socio-Political Council | partial |
| `world-montenegro-1990-12-09-parliament` | 1990-12-09 | Parliament of Montenegro | complete |
| `world-montenegro-1992-12-20-parliament` | 1992-12-20 | Parliament of Montenegro | complete |
| `world-montenegro-1996-11-03-parliament` | 1996-11-03 | Parliament of Montenegro | complete |
| `world-montenegro-1998-05-31-parliament` | 1998-05-31 | Parliament of Montenegro | complete |
| `world-montenegro-2001-04-22-parliament` | 2001-04-22 | Parliament of Montenegro | complete |
| `world-montenegro-2002-10-20-parliament` | 2002-10-20 | Parliament of Montenegro | complete |
| `world-montenegro-2006-09-10-parliament` | 2006-09-10 | Parliament of Montenegro | partial |
| `world-montenegro-2009-03-29-parliament` | 2009-03-29 | Parliament of Montenegro | complete |
| `world-montenegro-2012-10-14-parliament` | 2012-10-14 | Parliament of Montenegro | complete |
| `world-montenegro-2016-10-16-parliament` | 2016-10-16 | Parliament of Montenegro | complete |
| `world-montenegro-2020-08-30-parliament` | 2020-08-30 | Parliament of Montenegro | complete |
| `world-montenegro-2023-06-11-parliament` | 2023-06-11 | Parliament of Montenegro | complete |

## Saved party profiles

| Profile | Abbreviation | ID |
|---|---|---|
| League of Communists of Montenegro | SKCG | `494f9dd5-d152-5db2-b28f-224b035e33de` |
| Democratic Party of Socialists of Montenegro | DPS | `0512aafb-dbca-5707-9925-a1285b10f3fd` |
| People’s Party (founded 1990) | NSCG | `1f9ece23-aa66-509a-a8da-7af792ff2ae5` |
| Liberal Alliance of Montenegro | LSCG | `8443964c-efb7-5b1b-9b46-8bfb62bae4a2` |
| Social Democratic Party of Reformists | SDPR | `cf828abc-4b07-51a4-b21c-e9d39e5b712d` |
| Social Democratic Party of Montenegro | SDP | `c9b0a4c4-dd15-5624-bd4f-76ac58c37c21` |
| Socialist People’s Party of Montenegro | SNP | `c8665c8b-f3cb-56ac-8dbf-ebbaab8d3eac` |
| Serb People’s Party | SNS | `588f4152-91e1-5248-b5a3-cfef3f8a4d4f` |
| Democratic Union of Albanians | DUA | `a0e839b5-97a7-50ef-8d10-989345cb0b05` |
| Democratic Alliance in Montenegro | DSCG | `217fc2a9-79e9-5b38-b4ab-f12ba093ec05` |
| Party of Democratic Prosperity | PDP | `b00fe08d-00be-57e7-acc0-e1172016ba9f` |
| Movement for Changes | PZP | `0a412071-3dbb-5952-9d40-98d9ad264bce` |
| Bosniak Party | BS | `9fb91671-9184-594d-a873-059b7bc32e3a` |
| Croatian Civic Initiative | HGI | `e1dc6aa0-04ff-535e-948c-533a4d63d9b6` |
| New Democratic Power – FORCA | FORCA | `7b3738a7-2c12-5f89-a4df-e89b1f335989` |
| Albanian Alternative | AA | `265c7368-db25-595c-8a36-c43fec1ed73e` |
| Positive Montenegro | PCG | `66cc4ab9-a77e-5bf9-8089-0c7eae034318` |
| Democratic Montenegro | DCG | `412c5b05-45bf-5cbf-a494-48f4398fb6c2` |
| Social Democrats of Montenegro | SD | `17336f9e-3bf0-5cba-8e23-f1c630aab6a1` |
| Europe Now Movement | PES | `7ff11285-dc70-5871-b51e-33776d0c2de2` |
