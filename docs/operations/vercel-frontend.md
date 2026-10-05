# Vercel frontend deployment

Deployed and verified on 2026-10-05: [igotskill.vercel.app](https://igotskill.vercel.app). Vercel project: `igotskill`; team: `prathamesh-bhattas-projects`.

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

- Source commit: `6d23460`; 148 isolated frontend files uploaded (approximately 2.1 MB). Local `.env.local`, `.vercel`, dependencies and build caches were excluded; linking/authentication metadata remain ignored.
- Deployment: `dpl_CfvgJG697w8D6LAqcSt1Rnk1nDNi`; READY, production target.
- Immutable deployment URL: [igotskill-53oz3qexk-prathamesh-bhattas-projects.vercel.app](https://igotskill-53oz3qexk-prathamesh-bhattas-projects.vercel.app).
- [Vercel build inspection](https://vercel.com/prathamesh-bhattas-projects/igotskill/CfvgJG697w8D6LAqcSt1Rnk1nDNi).
- Actual remote build: Node 22.x, Next.js 16.3.4, webpack compilation, TypeScript and all 30 static pages passed on Vercel's standard 2-core/8-GB build machine.
- Anonymous HTTP verification: `/`, `/login`, `/about`, `/courses/1` returned 200 with application content, and a referenced CSS asset returned 200.
- `/api/health` returned 404, matching the intentionally deferred backend. Login, learner data and lab execution are not claimed operational online.
- Deployment was performed through authenticated CLI source upload. Automatic GitHub-to-Vercel deployments were not configured; future source changes require a CLI redeploy or an explicitly configured Git integration.

## Redeploy remotely

From the repository root, with Vercel CLI authentication available:

```powershell
npx --yes --package vercel@62.2.0 vercel link --cwd apps/frontend --project igotskill --yes
npx --yes --package vercel@62.2.0 vercel deploy --prod --yes --cwd apps/frontend --project igotskill --logs
```

The project's production/preview API variable is currently `/api`. Change it to the eventual public HTTPS gateway URL and redeploy when the user connects Render. These commands upload/build remotely; do not start local Docker or app servers.

Provider/signing/database credentials belong in backend secret configuration, not the public frontend bundle or Markdown. No Vercel token or sign-in device code belongs in committed docs.
