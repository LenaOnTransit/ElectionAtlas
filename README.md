# ElectionAtlas — The Election Desk

This repository contains the complete React/TypeScript application migrated from
https://election-desk-ltm.caitlynnesman.chatgpt.site/ (source version 5).
It preserves the publication design, article pages, Senate dashboards and editor,
world calendar and historical archive, election atlas, then-versus-now comparisons,
coalition builder, and election-night mode.

## Run locally

Requires Node.js 22.13+ and pnpm 11.25.0 (see `packageManager`).

```sh
corepack enable
corepack pnpm install --frozen-lockfile
corepack pnpm exec wrangler d1 migrations apply site-creator-d1 --local --config wrangler.jsonc
corepack pnpm dev
```

Open the local URL printed by the development server. On localhost, the development
sign-in uses a local test identity. Open `/editor` to initialize sample articles and
claim the local editorial identity. The Senate and world editors are linked there.

```sh
corepack pnpm test
corepack pnpm typecheck
corepack pnpm build
```

## Runtime and deployment

The application uses React 19, TypeScript, Tailwind CSS, Vinext (Next.js-compatible
routing on Vite), and Cloudflare D1. It is a server application, so GitHub Pages
cannot run its API routes or private editor.

The original Sites runtime provides trusted ChatGPT authentication headers and
D1 binding `DB`. Those integrations are retained. Deploying outside Sites requires
a trusted authentication gateway that strips client-supplied identity headers,
validates sessions and injects identity, plus a real Cloudflare D1 database with
both migrations applied. Do not expose the raw worker with header-based identity
or allow an untrusted account to become the first editor. Local mock sign-in is
restricted to localhost development.

`.openai/hosting.json` identifies the existing site; this migration does not
redeploy it. Database rows (including private drafts, editor identities, custom
articles and saved election records) are not in the Git source and have not been
copied. A new database starts with the source's seed/sample records. Back up and
transfer D1 separately if moving the production data.

## Original application notes

Vinext / React publication with D1 persistence. Public routes show published articles and election data; `/editor` is a protected newsroom. The first authenticated editor claims the editorial identity while the Site is owner-private. Subsequent users cannot edit. Open the newsroom as the owner before changing the Site audience. Drafts never enter public article queries.

## Maintenance
- UI: `app/page.tsx`, `app/components.tsx`, `app/globals.css`
- Editors: `app/editor/workspace.tsx`
- Auth / validation: `app/editor/page.tsx`, `app/api/content/route.ts`
- Data access and sample content: `db/content.ts`
- Schema: `db/schema.ts`; generate append-only migrations with `npm run db:generate`
- Build: `npm run build`

Sample articles and results are fictional. Initialize content by opening the newsroom, then replace samples with your reporting. Save articles as Draft to withdraw them from the publication. Election updates are published on save. No external election feed is connected. Candidate shares are calculated from stored vote totals.

## 2026 Senate
- `/senate`: state tile map, polling/results switch, candidate details, majority needles.
- `/editor/senate`: admin controls; saves the full Senate record to D1 through the existing authorized API.
- `lib/senate.ts`: defaults, palette, validation, and exact seat-distribution model.
- `db/senate.ts`: persistent record loader.
- `scripts/check-senate.mjs`: deterministic checks for probabilities, majority/tie rules, independents, calls, and flips.

2026 baseline: 35 races (33 Class II plus FL/OH specials), 32 D / 31 R / 2 I seats not up. The default independent baseline caucuses with Democrats. Seat holders' parties were checked against Senate.gov and the 2026 schedule; candidate names and polling/results values are intentionally blank for manual entry. Defaults are editable.

The needle is an independent-race editorial scenario, not a calibrated prediction. It uses per-mode manual party probabilities or configurable rating probabilities, or an optional numerical softmax heuristic from candidate poll percentages or vote shares. Results uncertainty shrinks as reporting rises; neither outstanding-precinct composition nor national error is modeled. Unconfigured tossups use D/R 50/50. Result calls supersede probabilities. Independent winners use a per-seat caucus assignment. All outcomes are enumerated by dynamic programming. No external feed is connected. Save validates all fields and a 100-seat chamber before writing.

## World calendar & archive
- `/calendar`: month grid plus upcoming list, country/region/type/date-status filters, approximate dates and schedule-change notices.
- `/archive`: searchable historical records and a country/entity directory.
- `/archive/country/:id`: country timeline and coverage note.
- `/world/election/:id`: sources, rounds, result table, notes, and article links.
- `/editor/world`: protected record/country editor, private drafts, staged JSON imports, and saved-revision restoration.
- `lib/world.ts`: types, validation, calendar/date logic.
- `lib/world-countries.ts`, `lib/world-seeds.ts`: curated initial directory and election records. Dates were reviewed on 2026-10-01. The calendar and archive are explicitly partial.
- `db/world.ts`: D1 records overlay seed IDs. A saved draft overrides a published seed and withdraws it. Saves use optimistic version checks and atomic revision logging. Country IDs are stable; historical entities can be added separately.

Sources are shown per record. No external API credentials or automatic feed is configured. Imports cannot overwrite existing IDs and always become drafts. Imported public data should include source attribution and comply with source reuse terms. Keep vote denominators explicit and do not treat blank figures as zero. Government formation is a separate narrative from party seat rankings. Rows may show a partial selection of parties; use coverage flags honestly. Mark an election Held to move it from the schedule to the historical view; passing its date does not fabricate results. Future larger archives can use the existing indexed record storage with server pagination rather than loading all entries into the browser.

## Reader election explorers
`/atlas` uses simplified Natural Earth public-domain country boundaries from datasets/geo-countries, with a searchable accessible country directory for small entities. `/compare` restricts comparisons to matching country/type/body/round and allows manual row matching; missing values never become zero. `/coalitions` uses saved seat allocations and a configurable majority threshold, with incomplete-data notices and editorial guidance. `/election-night` combines existing Senate calls with published world elections explicitly enabled by the editor. Optional refresh reads `/api/live`; only published world records are returned. World night reporting, bulletins, coalition notes, and thresholds use the existing authenticated, versioned save/revision flow. No new schema or external live-results feed is required.
