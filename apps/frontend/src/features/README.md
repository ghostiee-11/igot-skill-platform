# Feature ownership

`features/` owns domain-specific UI and client-side orchestration. App Router files under `src/app` expose URLs only and delegate to these components.

Features may import shared primitives from `@/components/ui`, cross-cutting UI from `@/components/shared`, and stable services/types from `@/lib`. They should not import another feature's internals. Route parameters, search parameters, and navigation remain inside the owning feature component because the existing routes are client-rendered.

The root layout supplies authentication and i18n context; feature components call the existing `fetchApi` client and consume those providers. Add `api/`, `hooks/`, or `types/` inside a feature only when it contains real feature-specific code; do not pre-create them.

Current domains: `auth`, `onboarding`, `dashboard`, `catalog`, `learning`, `assessments`, `profile`, `progress`, `administration`, `assistant`, and `landing`.
