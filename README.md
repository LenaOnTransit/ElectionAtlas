# ElectionAtlas — The Election Desk

Standalone React 19 / Next.js 16 / TypeScript election publication. No ChatGPT account, Sites runtime, Cloudflare binding, or external identity gateway is required. All internal links use this application's own origin.

## Run

Requires Node.js 22.13+ (Node 24 recommended) and pnpm 11.25.0.

```sh
corepack pnpm install --frozen-lockfile
cp .env.example .env.local
corepack pnpm dev
```

Open http://localhost:3000. SQLite tables initialize automatically at `DATABASE_PATH`, default `./data/electionatlas.sqlite`. Public articles and election tools need no sign-in. Sample coverage is fictional; the world directory/calendar/archive are curated, partial seed datasets.

## Your administrator account

1. Open `/account`, select **Create account**, and enter your email, username, and a password of at least 12 characters.
2. On the server, grant that registered username editorial access:

```sh
npm run admin -- your_username
```

3. Open `/editor`. Only administrator accounts can read drafts or save article, Senate, and world-election changes.

The command and web server must point to the same `DATABASE_PATH`. The admin command reads shell environment variables, so export `DATABASE_PATH` if you changed the default; it does not load `.env.local`. Registration always creates a reader, including the first account. Email addresses and usernames are case-insensitive. No public route promotes an account.

Passwords use salted scrypt (N=32768, r=8, p=1). Sessions use random tokens; only token hashes are stored. Cookies are HttpOnly, SameSite=Strict and Secure in production, expire after seven days, and are revoked on sign-out. Session roles are read from the database on every request. Account endpoints enforce origin checks, input bounds, and persistent rate limits. Email verification, outbound email, and self-service password reset are not included; entered email addresses are account identifiers, not verified ownership claims.

## Production

```sh
corepack pnpm test
corepack pnpm typecheck
corepack pnpm build
APP_ORIGIN=https://your-domain.example DATABASE_PATH=/persistent-volume/electionatlas.sqlite corepack pnpm start
```

Use a Node.js host with HTTPS and persistent storage. Set `APP_ORIGIN` to the exact public origin without a trailing slash; account writes fail closed if it is unset in production. SQLite is suitable for a single server with persistent disk; ephemeral serverless filesystems and GitHub Pages cannot host this application. Keep the database private and back up the SQLite database with its WAL files or an online SQLite backup. Do not commit database files, sessions, or environment secrets. For container deployment, mount a persistent volume at `DATABASE_PATH`.

## Data migration

Existing production articles, editor identities, private drafts, Senate edits, and saved world records were not part of the exported source. This standalone version starts with seed/sample records. Transfer the `records` table from an authorized database export to retain content and revisions. Legacy editor identities are intentionally not trusted: register a new account and grant it administrator access with the server command. Keep the existing live publication separate until its content has been transferred and the replacement has been verified.

## Features and maintenance

- `/`: publication; `/article/:id`: published articles.
- `/senate`: 2026 Senate tile map, candidates, polling/results, party rating shades, flips, and majority needles. No external results feed. The needle is an independent-race editorial scenario, not a calibrated forecast.
- `/calendar`, `/archive`, `/archive/country/:id`, `/world/election/:id`: country schedules, historical records, sources, rounds, and results.
- `/atlas`, `/compare`, `/coalitions`, `/election-night`: interactive maps, matching-election comparisons, seat coalitions, and optional refresh of published results.
- `/editor`, `/editor/senate`, `/editor/world`: protected editors, world record revisions, and staged draft imports.
- `db/storage.mjs`: SQLite initialization and transaction adapter; `db/content.ts`, `db/world.ts`, `db/senate.ts`: content access.
- `lib/auth-core.mjs`, `app/auth.ts`, `app/api/auth/[action]/route.ts`: accounts and sessions.
- `app/components.tsx`, `app/globals.css`: publication design.

Checks cover authentication, session revocation/expiry, account uniqueness, reader/admin separation, rate limits, transactional rollback, Senate seat/probability rules, and world record/date/privacy validation.
