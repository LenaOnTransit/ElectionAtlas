# Article publishing

In the private newsroom, choose **Draft**, **Publish now**, or **Schedule publication**. Scheduling requires an exact date and time, shown in the browser's local time zone. Press **Save schedule** to activate it. The article date is the byline date and does not control release.

To reschedule, change **Publish at** and save. To cancel, choose **Draft** and save. Removing a post also cancels publication; restoring it returns it as a private draft. A previously scheduled article can be edited after release without changing its original release time.

The existing `published` article status represents approval for publication. Optional `publishAt` stores the release instant in ISO format with a time zone. A database trigger synchronizes the `publication_at` timestamp; public RLS and `ea_public_records` allow reads only at or after that time. Public pages use this RPC even for signed-in editors, so future articles only appear in the private newsroom. Drafts and trashed articles remain private. The schedule uses the database clock and requires no cron job, background browser, or GitHub Pages rebuild. Visitors see new releases when they load or refresh the page. If the Supabase project is paused, publishing becomes visible when it resumes.

Apply `supabase/migrations/20261002162446_article_scheduling.sql` when configuring another database. Run `supabase/tests/publication.sql` and `supabase/tests/access.sql` as the database owner; both roll back their fixtures. `npm test` verifies local-time conversion, daylight-saving changes and release-boundary labels.
