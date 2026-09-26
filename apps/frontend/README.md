# iGOT Karmayogi frontend

Next.js 16 App Router frontend for the iGOT Karmayogi learning experience.

## Structure

- `src/app`: URL and layout ownership only. Pages are deliberately thin route entry points.
- `src/features`: domain UI and client-side orchestration. See its README and each feature README for boundaries.
- `src/components/ui`: reusable, domain-neutral interface primitives.
- `src/components/shared`: reusable application-wide presentation such as navigation.
- `src/components/certificate`: cross-feature certificate presentation shared by progress and assessments.
- `src/lib`: cross-cutting API client, providers, types, i18n, and utilities.

## Data and state flow

`src/app/layout.tsx` provides auth and i18n context. Feature components own local interactive state, consume those providers, and use `fetchApi` plus shared types for backend communication. Keep route parameters and URL navigation inside the feature that owns the screen. Do not import feature internals across domains; promote truly reusable code to `components` or `lib`.

## Commands

```bash
npm run dev
npm run lint
npx tsc --noEmit
npm run build
```

## Planned structure

Feature-level `api/`, `hooks/`, `types/`, or finer-grained component folders are added only when real implementation needs justify them. They are intentionally absent today.