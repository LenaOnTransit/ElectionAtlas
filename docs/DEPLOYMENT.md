# ElectionAtlas: GitHub Pages + Supabase

The publication is a static React/Vite application. Supabase provides Postgres, email/password accounts, profile usernames, and database-enforced editorial permissions. There is no Node.js server or SQLite database to host. Hash routes (`/ElectionAtlas/#/senate`) support direct links and refreshes on GitHub Pages, including newly created articles and countries without a rebuild.

## Deployment

1. Merge the GitHub Pages/Supabase pull request.
2. In GitHub **Settings → Pages**, set **Source → GitHub Actions**. The included `pages.yml` workflow installs the locked dependencies, checks election rules, builds `dist`, and publishes it after pushes to `main` or a manual workflow dispatch.
3. GitHub Pages must be available for the repository's visibility and your plan. A private repository needs an eligible paid GitHub plan. This change does not change repository visibility. Alternatively deploy `dist` to another static host.
4. The default repository prefix is `/ElectionAtlas/`. For a custom domain at its root, set `VITE_BASE_PATH=/` in the workflow and configure the domain in GitHub Pages settings.

## Supabase authentication setup

The connected project is `qurdolyenxynuqdmcxbr`. The browser uses only its publishable key and project URL, which are intentionally public. Set `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY` at build time if using a different project. Never use a secret or service-role key in these variables.

In Supabase **Authentication → URL Configuration**, set the Site URL to your actual deployed Pages root, including `/ElectionAtlas/`, and add that exact root to Redirect URLs. For local development, also allow `http://localhost:5173/ElectionAtlas/`. Registration uses PKCE email confirmation and returns to the static root before opening the account screen. Keep email confirmations enabled.

Supabase's built-in mail service is restricted and intended for testing. Configure **Authentication → Email → SMTP Settings** with your own SMTP provider for public signups and reliable delivery. If signup reports that the email address is not authorized, configure SMTP; don't bypass email verification. Email/password registration always creates a reader profile, never editor membership. Username uniqueness is enforced by Postgres. Account passwords and email confirmation sessions are managed by Supabase Auth. The current UI supports signup/sign-in/sign-out; self-service password reset is not implemented.

## Your editor account

Create and confirm your own account using the site's **Account / sign in** page. Supabase dashboard membership is separate from a website account. After confirming the exact account email, run this in the Supabase SQL editor:

```sql
insert into public.ea_editors (user_id)
select id from auth.users where lower(email) = lower('YOUR_CONFIRMED_ACCOUNT_EMAIL')
on conflict (user_id) do nothing;
```

The grant requires database-owner access. No browser endpoint can grant it. Public users cannot change editorial membership. The first signup receives reader access just like all later signups. Do not grant membership based on user-editable metadata. Once granted, reopen `/ElectionAtlas/#/editor`.

## Database and content

The migration creates `ea_records`, `ea_revisions`, `ea_profiles`, and `ea_editors`, all with RLS. Public requests can select published articles/world elections and public country/Senate/results records. Drafts and revision history are editor-only. Editor saves run through the authenticated `ea_save_record` function; world saves enforce version checks, use transaction-level record locking, and insert revisions atomically. Public APIs cannot alter accounts or grant roles. The private signup trigger creates display profiles only.

`supabase/seed.sql` supplies the original fictional sample publication and curated election seeds. Run it once on a new project after migrations. Inserts use `ON CONFLICT DO NOTHING` so they cannot overwrite saved edits. Seed files contain no private production content. A withdrawn seeded article/election stays withdrawn because public pages use database rows rather than reintroducing missing seeds.

The original Sites production records are not available in the exported source and have not been transferred. The prior SQLite accounts are not Supabase accounts; users must register with Supabase. Keep private database exports outside the repository. `supabase/tests/access.sql` tests access rules and world revision/concurrency behavior in rolled-back transactions.

Supabase Free projects can pause for low activity over a week. Resume them from Supabase if necessary. The static frontend still opens during a pause, but database content, authentication, and saves will be unavailable. Export backups separately.

## Local maintenance

```sh
corepack pnpm install --frozen-lockfile
corepack pnpm dev
# Open http://localhost:5173/ElectionAtlas/
corepack pnpm test
corepack pnpm typecheck
corepack pnpm build
corepack pnpm preview
```

Read-only requests use the connected Supabase project by default. Use environment overrides for a separate development project before editing real data. UI and route loaders are in `app`; static route loading and navigation are in `src`. Supabase data access is in `db`, and browser auth is in `app/auth.ts` and `app/account`. All permissions are enforced by Supabase, regardless of hidden UI. Supabase package versions and the pnpm lockfile are committed.
