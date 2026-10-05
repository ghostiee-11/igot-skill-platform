# Vercel frontend deployment

Requested project/domain: `igotskill` / `igotskill.vercel.app`. Availability and successful deployment must be verified; this document does not claim the alias is deployed yet.

User scope: deploy the frontend first and connect the public backend later. Local Docker/application services must remain stopped. Vercel runs the build remotely.

Backend preference: temporary Render hosting later, using available account credits. Backend provisioning is deferred; evaluate core APIs, background workers, PostgreSQL/broker and the current Docker-socket lab execution requirement separately when requested.

## Build configuration

- Source app: `apps/frontend/`.
- Framework: Next.js; Node.js project version: 22.x.
- Build command: `npm run build -- --webpack`.
- Install command: `npm ci --no-audit --no-fund`.
- `apps/frontend/vercel.json` stores reproducible app settings; `.vercelignore` excludes local environment files, dependencies and build artifacts from source upload. Local `.vercel/` linking metadata is ignored by Git.
- An isolated app-directory CLI upload needs no backend/service source or root `.env`. If linking the entire Git monorepo later, configure the Vercel project's Root Directory as `apps/frontend`; use [Vercel's monorepo instructions](https://vercel.com/docs/monorepos).

For the frontend-only deployment, set public build variable `NEXT_PUBLIC_API_URL=/api` rather than publishing a localhost API URL. The same-origin API path will remain unavailable until a backend/proxy is configured; do not present login, live learner data or labs as connected. Configure the eventual public HTTPS gateway URL and its allowed frontend origin, then redeploy because public Next.js environment values are bundled at build time.

## Verification and continuity

Record the actual Vercel team/project, deployment URL, alias, source commit and build outcome after deployment. Check the public landing/login routes and static assets remotely. A deployed frontend is not proof that backend authentication or LMS journeys work.

Provider/signing/database credentials belong in backend secret configuration, not the public frontend bundle or Markdown. No Vercel token or sign-in device code belongs in committed docs.
