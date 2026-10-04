# World of Elections: data-rights operations

Account settings provide free JSON export and permanent account deletion. Both RPCs use the verified JWT user ID and a live Supabase session. Deletion additionally requires a session created within five minutes. The UI asks for a fresh password sign-in and explicit confirmation. Never accept a user ID from a request to decide whose account to export or erase.

Export contains account contact details, username and submitted election revisions. It excludes passwords, tokens, other accounts and other moderators' revisions. Deletion removes the auth account, profile, editorial membership, sessions and submitted revision snapshots. Published election records and articles are not automatically removed. Storage ownership blocks deletion until any files can be removed through the Storage API; the current site has no uploaded storage objects.

## Required controller decisions before claiming compliance

- Publish the controller's identity and a monitored privacy contact that people can use without creating an account. Cover account access problems, information in editorial coverage and direct portability transfers.
- Define and document retention for Supabase authentication/audit logs, infrastructure logs and backups. Account deletion does not promise instant deletion from all backups or third-party logs. Ensure restoration does not reintroduce erased personal data, and instruct relevant processors/recipients where required.
- Record the lawful bases for processing and any justified erasure exceptions. Public election coverage is not automatically exempt from a request; review the applicable national journalism rules and Article 17 exceptions case by case.

## Handling requests

Respond without undue delay, normally within one month of receipt. If a lawful extension is necessary, notify the person within the first month with the reason. Request only identity information that is necessary and proportionate. Do not require an account for a rights request.

For erasure, assess the requested data and applicable grounds/exceptions, remove data from active systems and notify recipients as Article 19 requires. Explain any refusal and available complaint/remedy routes. For Article 20, supply applicable data provided by the person in a structured machine-readable format; support direct transmission to a verified controller where technically feasible while protecting other people’s data. Do not treat an account JSON download as the answer to every possible portability request.

Review requests involving published editorial material separately. Preserve public election facts while assessing personal information, bylines and other identifying text. Account deletion cannot identify personal information manually entered into articles.

Reference: https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng (Articles 12, 17, 19 and 20).

Validation: `supabase/tests/account-data-rights.sql` tests anonymous denial, reader/editor isolation, confirmation, stale-session rejection and deletion using synthetic accounts in a rolled-back transaction.
