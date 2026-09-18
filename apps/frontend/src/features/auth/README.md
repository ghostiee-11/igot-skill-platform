# Auth feature

Owns login, registration, and password-reset screens. It consumes the global auth context and the shared API client; route files in `app/(auth)` are intentionally thin adapters. Keep credential and session behavior in the existing auth provider unless it becomes reusable feature-specific logic.

Future folders: add `hooks/` or `api/` only for real auth-only flows.
