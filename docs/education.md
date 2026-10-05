# Education

Public routes: `/education/`, `/education/category/<category-id>/` and `/education/<educational-id>/`. The header has a dedicated Education tab. The five categories are defined in `lib/education.mjs`; the parties/ideology category and index link to the existing ideology library.

Moderators open **Private newsroom → Education newsroom** (`/editor/education/`). They can create an educational, choose a category, write a summary and lesson text, add/reorder sections, add HTTPS sources, preview, save a private draft, publish immediately or schedule publication in their browser time zone. Longer lessons generate a contents list and an estimated reading time. Drafts may have incomplete sections; publishing requires a summary and lesson text, and complete sections. Trash unpublishes a post and permits restoration as a private draft. Changing posts and leaving the page warn about unsaved changes.

Records use the existing `article` storage kind with `articleType: 'educational'`, a stable `educational-` ID, `educationCategory`, and structured text sections. No new table, RPC, policy, credential or database polling is introduced. News and ideology queries exclude educational records; educational queries select this subtype. Database RLS and the existing publication timestamp trigger protect drafts, scheduled releases and trashed posts. Only verified moderators can access or save through the newsroom.

The static public-page build generates the education directory, category pages, article pages, canonical metadata, breadcrumbs and `Article` structured data. Draft, future and trashed records never enter the static build. Empty category pages are accessible but remain out of the sitemap until they have a published educational. Scheduled articles become publicly readable at their release time; static pages and sitemap follow the site's existing build/deployment schedule.

The body and sections render as text paragraphs, not HTML. Structured sections keep authoring and reading independent so interactive lesson components can be added later. This update supplies the writing/publishing workflow and category introductions; it does not create example educationals or interactive lessons.

Checks: `node --test scripts/check-education.mjs scripts/check-seo.mjs`, `pnpm test`, `pnpm build`. `scripts/check-education-rls.sql` checks the actual database with anonymous, reader and moderator roles, using only temporary transactional fixtures which are rolled back.
