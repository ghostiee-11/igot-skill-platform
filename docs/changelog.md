# 📜 Repository Changelog

## 2026-09-18 — Obsolete repository material removed

- Removed the superseded root `ai-service/` placeholder; the active implementation is `services/ai/`.
- Removed the empty local `Plan/` directory and obsolete `docs/superpowers/` implementation drafts.
- Removed regenerable dependency, virtual-environment, build and test-cache directories from the workspace.
- Replaced the monolith-era `LOCAL_SETUP.md` and root `.env.example` with Compose-first service architecture instructions and environment names.
- Preserved `restructure/` as requested.
- Preserved `backend/`, `content-pipeline/` and `supabase/` because they still serve as migration/parity references for specialist behavior not yet fully implemented in the new services. Remove them only after the remaining compatibility catalogue is closed.
- Restored the standard `rajesh.kumar@mospi.gov.in` / `Learner@123` quick login through an explicit local-demo identity mode with create-and-repair regression coverage.
- Added the missing behavioural course/corpus/case/session compatibility endpoints and made default Compose startup health-gated across every backend, labs, gateway and frontend.
- Moved live behavioural interview transcripts, turn telemetry and final reports into assessment-owned PostgreSQL sessions, so an assessment-service restart no longer invalidates an active interview.

## 2026-09-17 — Service architecture migration started

- Architecture/migration: baseline `final-final` (`7123bd3`) fast-forwarded into `main` and pushed. Implementation is on `rebuild/service-architecture`, pending user review before merge.
- Frontend screens are preserved during relocation; backend ownership is split into domain services.
- Data requires explicit migration to owned schemas; no live data migration was run.
- Decisions: [domain services](decisions/0003-domain-services.md), [lab runtime](decisions/0004-lab-runtime.md).
- Validation and remaining work: [migration status](migration/status.md). This entry does not claim full parity.
- Fresh frontend and cloud VM execution are deferred.

All notable changes to the **iGOT Karmayogi (MoSPI)** platform are documented in this file.

This changelog serves as the authoritative source of change history for **engineering team members** and **AI coding agents** to provide context for upcoming features, bug fixes, and architectural evolutions.

---

## 📌 Format Guide for New Entries

When contributing changes, append entries at the top of the appropriate version/date block following this convention:

```markdown
### [YYYY-MM-DD] - Short Title of Change

- **Author**: Name (@github-username)
- **Scope**: `[frontend]` | `[backend]` | `[ai-service]` | `[docs]` | `[devops]` | `[architecture]`
- **Description**: Concise explanation of what was changed and the rationale.
- **Affected Files / Routes**:
  - `path/to/file.tsx`
  - `POST /api/endpoint`
- **Agent Context / Rules**: Any architectural constraints or edge cases future agents must respect.
```

---

## 🔄 Change History

### [2026-09-11] - Technical Course Content Generation Pipeline Backend
- **Author**: Antigravity AI & Ravish Kansal (@ravishkansal22)
- **Scope**: `[backend]` `[ai-service]` `[architecture]` `[docs]`
- **Branch**: `technical-course-pipeline`
- **Description**:
  - Implemented the complete backend pipeline for Technical Course content generation in iGOT Karmayogi under `backend/app/modules/technical_courses/`.
  - **Transcript Ingestion & Chunking (`transcript_service.py`):** Cleaning WebVTT/SRT timestamps, audio cues, whitespace normalization, token estimation, and overlapping semantic chunking.
  - **Structured Learning Objective Extraction (`objective_extractor.py`):** Schema-driven extraction (skill, difficulty, action, mode) with Gemini/OpenAI support and deterministic testing fallbacks.
  - **Quiz vs. Lab Decision Layer (`decision_service.py`):** Extensible Bloom taxonomy classifier determining whether objectives require interactive sandbox labs or multiple-choice quizzes.
  - **Human-Controlled Lab Templates (`template_service.py`):** Enforces human instructional boundaries; templates define starter code structure, constraints, and unit test suites before LLM filling.
  - **Controlled Lab Generation (`lab_generator.py`):** Generates concrete labs conforming strictly to `GeneratedLabSchema`.
  - **Reference Solution Generation (`solution_generator.py`):** Synthesizes reference solutions marked untrusted until validated.
  - **Isolated Sandbox Validation (`sandbox_service.py`):** Primary Docker container execution (`--network none`, 128MB limit, timeout, non-root) with isolated subprocess fallback for development/testing.
  - **Full Pipeline Orchestrator (`pipeline_orchestrator.py`):** Coordinates transcript ingestion -> objectives -> lab decision -> template matching -> lab generation -> solution generation -> sandbox validation -> SQLite persistence.
  - **Database Models (`models.py`):** Added `TechnicalTranscript`, `TechnicalLearningObjective`, `TechnicalLabTemplate`, `TechnicalGeneratedLab`, `TechnicalLabSolution`, and `TechnicalLabValidationResult`.
  - **Automated Test Suite (`backend/tests/test_technical_pipeline.py`):** 22 unit & integration tests validating all pipeline components, sandbox isolation, error modes, and REST APIs.
- **Affected Files / Routes**:
  - `backend/app/modules/technical_courses/` [NEW]
  - `backend/app/models/models.py`
  - `backend/app/core/seed_data.py`
  - `backend/app/main.py`
  - `backend/tests/test_technical_pipeline.py` [NEW]
  - `docs/features/technical-course-pipeline.md` [NEW]
  - `POST /api/technical-courses/process`
  - `POST /api/technical-courses/objectives`
  - `POST /api/technical-courses/decide-mode`
  - `GET /api/technical-courses/templates`
  - `POST /api/technical-courses/match-template`
  - `POST /api/technical-courses/labs/generate`
  - `POST /api/technical-courses/labs/{id}/solution`
  - `POST /api/technical-courses/labs/{id}/validate`
  - `GET /api/technical-courses/labs/{id}`
  - `POST /api/technical-courses/pipeline/run-full`
- **Agent Context / Rules**:
  - Code generation must always be validated in Docker/isolated sandbox before marking a lab as deployable.
  - Keep domain modules strictly isolated so teammates working on Statistical, Governance, and Behavioural pipelines face zero merge conflicts.

---

### [2026-09-13] - Marimo App Run Mode, Code Hiding & Hint Session Resiliency

- **Author**: Diwakar Ujjwal (@diwakarujjwal)
- **Scope**: `[frontend]` `[backend]` `[sandbox]` `[marimo]` `[ctf]` `[docs]`
- **Branch**: `cgp/digital-governance`
- **Description**:
  - **Marimo App Run Mode & Code Hiding**:
    - Converted `sandbox_manager.py` Marimo runner from `marimo edit` to `marimo run` (`run <notebook_path> --host 127.0.0.1 --port <port> --no-token --headless --no-skew-protection --allow-origins *`).
    - Exposes notebooks exclusively in read-only App Mode (`mode="read"`), hiding raw Python code cells, editor gutters, and cell execution controls, leaving strictly the interactive analysis console (widgets, KPIs, telemetry tables, timeline viewers, deobfuscator sandboxes, and verification checklists).
    - Updated console iframe status badge in `CyberSandboxPage.tsx` to `"Interactive Analysis Console • Port [port]"`.
  - **Database Session Re-hydration & Resilient Hint Unlocking**:
    - Resolved root cause of `"Session not found"` errors occurring during hint unlocking when Uvicorn reloads or worker processes recycle.
    - Implemented `_restore_session_from_db(session_id, db)` in `SandboxManager` to lazily reconstruct `ActiveSession` objects and challenge templates directly from SQLite (`cyber_sandbox_sessions` and `cyber_sandbox_challenges`).
    - Updated `unlock_hint`, `submit_flag`, `get_session`, and `stop_session` to re-hydrate from database whenever in-memory `_sessions` is cold.
    - Updated `SandboxHintUnlockRequest` and `SandboxFlagSubmitRequest` schemas and router endpoints to accept `challenge_id` for deterministic fallback.
    - Added `CHALLENGE_HINTS_CATALOG` in `CyberSandboxPage.tsx` with tiered progressive hints for all active challenges, providing instant offline fallback and preventing `"Session not found."` from ever displaying in the UI.
  - **Testing**:
    - Added `test_08_hint_unlock_after_server_reload_and_fallback` to `backend/tests/test_sandbox.py` verifying DB re-hydration after clearing in-memory state.
    - All 16 backend unit tests pass (`PYTHONPATH=backend python3 -m unittest discover -s backend/tests -p "test_*.py"`).
    - Frontend Next.js Turbopack build succeeds with 0 errors across 20 routes.
- **Affected Files**:
  - `backend/app/modules/digital_governance/router.py`
  - `backend/app/modules/digital_governance/schemas.py`
  - `backend/app/modules/digital_governance/services/sandbox_manager.py`
  - `backend/tests/test_sandbox.py`
  - `frontend/src/features/digital_governance/components/CyberSandboxPage.tsx`
  - `docs/features/digital-governance-cybersecurity.md`
  - `docs/team/diwakar-ujjwal.md`
  - `docs/changelog.md`

### [2026-09-13] - Real-Life Elevation of All 8 CTF Templates, Marimo Sidebar Restoration & Auto-run Engine

- **Author**: Diwakar Ujjwal (@diwakarujjwal)
- **Scope**: `[backend]` `[sandbox]` `[marimo]` `[ctf]` `[security]` `[docs]`
- **Branch**: `cgp/digital-governance`
- **Description**:
  - **Elevated All 8 Procedural Challenge Templates to Real-Life DFIR/SOC Standards (600–800 lines each)**:
    1. **`01-soc-auth-investigation` (783 lines)**: 6 tabs, live Python scratchpad (`df_auth`, `pd`, `re`, `json`), `mo.download` auth log export, anomaly threshold slider, chronological attack timeline, LOLBin commands.
    2. **`02-phishing-dfir` (699 lines)**: 6 tabs, live Python scratchpad (`eml_content`, `dns_df`), RFC 822 `.eml` parser & download, attachment carving, VBA macro deobfuscator, Base64 decoder widget, DNS telemetry correlation.
    3. **`03-compromised-linux-server` (719 lines)**: 6 tabs, live Python scratchpad (`df_bash`, `df_auth`, `df_cron`), bash history & auth log `mo.download` exports, GTFOBins sudo escalation analysis, reverse shell inspection, SHA-256 verification.
    4. **`04-vulnerable-web-app` (716 lines)**: 6 tabs, live Python scratchpad (`df_employees`, `conn`), SQLite DB export, interactive SQLi workbench with presets, executed SQL inspector, parameterized defense diff.
    5. **`05-threat-hunting-lotl` (775 lines)**: 6 tabs, live Python scratchpad (`df_proc`, `df_dns`, `shannon_entropy`), Sysmon CSV exports, process masquerading hunt, entropy/length sliders, Base64 subdomain decoder.
    6. **`06-pki-token-dispute` (625 lines)**: 6 tabs, live Python scratchpad (`df_crl`, `sub_data`), GeM tender JSON export, CRL revocation list analyzer, Section 3A IT Act timeline, Section 65B Indian Evidence Act certificate generator.
    7. **`07-meghraj-cloud-audit` (785 lines)**: 6 tabs, live Python scratchpad (`df`), CloudTrail JSON export, cross-border data transfer analyzer, SCP geo-fencing policy diff, STQC cloud compliance verification.
    8. **`08-dpi-apisetu-replay` (567 lines)**: 6 tabs, live Python scratchpad (`df`, `hmac`, `hashlib`), API Setu gateway JSON export, OpenAPI spec export, nonce collision analyzer, hardened Envoy/Lua sliding-window cache diff, DPDP Act 2023 clearance.
  - **Restored Marimo Sidebar & Chrome Panels**:
    - Identified CSS rule `.marimo-cell:not(:has(.console-topbar)) { display: none !important; }` and `[data-testid="chrome-sidebar"] { display: none !important; }` that hid Marimo's native sidebar and non-root cells.
    - Updated CSS across all 8 templates to un-hide the sidebar and cell outputs while preserving clean layout.
    - Added dedicated `@app.cell def __(mo, sidebar_content): return (mo.sidebar(sidebar_content),)` to ensure Marimo mounts the sidebar custom element.
    - Added `"📌 Investigation / Audit Checklist"` as a first-class console tab in every challenge so users on any viewport size always have immediate checklist access.
  - **Resolved Cell Auto-Running on Session Startup**:
    - Discovered Marimo defaults `auto_instantiate = False` when running notebooks in read-only / app view.
    - Configured `sandbox_manager.py` to write `.marimo.toml` with `[runtime] auto_instantiate = true` and `on_cell_change = "autorun"` directly into each session directory.
    - Exported `_MARIMO_CONFIG_OVERLOAD_RUNTIME_AUTO_INSTANTIATE="true"` and configured `XDG_CONFIG_HOME` on the spawned Marimo subprocess.
  - **Database Persistence**:
    - Re-seeded both `backend/karmayogi.db` and root `karmayogi.db` with updated procedural definitions, slots, artifacts, and full notebook code.
    - Guaranteed zero writes to Supabase (100% read-only GET guardrail preserved).
  - **Testing**:
    - All 8 templates compile and synthesize artifacts without errors.
    - All 15 backend unit tests pass (`test_sandbox.py`, `test_digital_governance.py`, `test_scenarios.py`).
    - Frontend TypeScript typecheck (`tsc --noEmit`) passes with 0 errors.
- **Affected Files**:
  - `backend/app/modules/digital_governance/services/sandbox_manager.py`
  - `backend/app/modules/digital_governance/services/templates/*.py` (all 8 templates)
  - `backend/app/core/seed_data.py`
  - `docs/changelog.md`

- **Author**: Diwakar Ujjwal (@diwakarujjwal)
- **Scope**: `[backend]` `[sandbox]` `[marimo]` `[ctf]` `[sqlalchemy]` `[docs]`
- **Branch**: `cgp/digital-governance`
- **Description**:
  - Restored the complete, full-depth 400–760 line interactive Marimo challenge notebooks from the reference repository into procedural templates, replacing legacy stubs with full reactive analyst workbenches:
    1. **`01-soc-auth-investigation` (764 lines)**: Sidebar checklist (`mo.sidebar`), stat KPIs (`mo.stat`), filterable telemetry table with JSON export, reactive Python analytics scratchpad, anomaly failure threshold slider, chronological attack timeline, confirmed breach callout, and Living-off-the-Land (LOLBin) command cards.
    2. **`02-phishing-dfir` (679 lines)**: Sidebar checklist, RFC 822 `.eml` parser & download, attachment carving & MD5/SHA-256 metadata, decompiled VBA macro preview, live Python deobfuscator, manual Base64 decoder widget, and correlated host DNS telemetry table with C2 beacon alert.
    3. **`03-compromised-linux-server` (488 lines)**: Sidebar checklist, GTFOBins sudo find escalation pattern detector, `/var/log/auth.log` triage table, `/etc/cron.d/` scheduled persistence hunter, `.sync.sh` reverse shell reverse engineering, and IR remediation checklist.
    4. **`04-vulnerable-web-app` (415 lines)**: Sidebar checklist, OWASP A03 mapping, interactive SQL injection workbench with methodology presets and live SQLite execution, executed SQL display, query status badge, and parameterized remediation comparison.
    5. **`05-threat-hunting-lotl` (485 lines)**: Sidebar checklist, Sysmon process telemetry audit with rogue non-System32 `svchost.exe` detection, Shannon entropy ($H$) & query length sliders, high-entropy DNS hunt table, and Base64 subdomain chunk decoder widget.
  - Elevated the 3 Digital Governance domain challenges to matching Karmayogi Sandbox standard: 6. **`06-pki-token-dispute` (277 lines)**: High-Value GeM Tender Dispute with Sidebar checklist, GeM bid submission TSA metadata, CA CRL revocation list explorer, IT Act Section 3A legal non-repudiation timeline analysis, and Indian Evidence Act Section 65B Certificate unlock. 7. **`07-meghraj-cloud-audit` (278 lines)**: MeghRaj Sovereign Cloud Audit with Sidebar checklist, CloudTrail audit stream with region filter, cross-border data residency violation detector, S3 sovereign replication audit, and STQC Sovereign Cloud Clearance Report unlock. 8. **`08-dpi-apisetu-replay` (278 lines)**: API Setu Replay Defense with Sidebar checklist, India Stack access gateway log explorer, cryptographic nonce collision analyzer, botnet subnet cluster detection, WAF sliding TTL replay protection, and National DPI Hardening Certification unlock.
  - Re-seeded both `backend/karmayogi.db` and root `karmayogi.db` with full notebook code in `cyber_sandbox_challenges.notebook_code` and `cyber_sandbox_templates`.
  - Static validation: All 8 challenge notebooks passed `marimo check` with returncode 0.
  - Test suite: All 15 backend unit tests pass.
- **Affected Files / Routes**:
  - `backend/app/modules/digital_governance/services/templates/soc_auth_template.py`
  - `backend/app/modules/digital_governance/services/templates/phishing_dfir_template.py`
  - `backend/app/modules/digital_governance/services/templates/linux_forensics_template.py`
  - `backend/app/modules/digital_governance/services/templates/web_sqli_template.py`
  - `backend/app/modules/digital_governance/services/templates/threat_hunting_lotl_template.py`
  - `backend/app/modules/digital_governance/services/templates/pki_defense_template.py`
  - `backend/app/modules/digital_governance/services/templates/cloud_audit_template.py`
  - `backend/app/modules/digital_governance/services/templates/dpi_replay_template.py`
  - `backend/requirements.txt`
  - `docs/changelog.md`

### [2026-09-13] - Upgraded 8-Sandbox Suite, SQLAlchemy Persistence & Supabase Integration (Milestone 3)

- **Author**: Diwakar Ujjwal (@diwakarujjwal)
- **Scope**: `[backend]` `[frontend]` `[sandbox]` `[ctf]` `[sqlalchemy]` `[supabase]` `[marimo]` `[tests]` `[docs]`
- **Branch**: `cgp/digital-governance`
- **Description**:
  - Upgraded and restored all 5 original sandboxes plus 3 digital governance domain challenges into mature procedural templates:
    1. **`01-soc-auth-investigation`**: _Operation NightShift_ — Windows Security Event telemetry (4624, 4625, 4688) with brute-force triage and LOLBin staging.
    2. **`02-phishing-dfir`**: _Executive Spearphish & Invoice Fraud_ — Raw MIME `.eml` with SPF/DKIM spoofing and DNS C2 beacon correlation.
    3. **`03-compromised-linux-server`**: _Operation Shakti (Linux IR)_ — `auth.log`, `crontab.txt`, `backup_sync.sh`, and `bash_history` for privilege escalation and malicious cron persistence.
    4. **`04-vulnerable-web-app`**: _Operation Suraksha (Citizen DB)_ — `corp_directory.db` (SQLite citizen registry) with UNION SQL injection vulnerability and DPDP Act breach triage.
    5. **`05-threat-hunting-lotl`**: _Operation Garuda (Threat Hunting)_ — Sysmon process trees and high-entropy DNS tunneling exfiltration analysis.
    6. **`06-pki-token-dispute`**: _Operation Mudra (PKI Defense)_ — GeM e-tender submission timestamping vs. CA revocation lists (CRL/OCSP) under IT Act Section 3 & 3A.
    7. **`07-meghraj-cloud-audit`**: _Operation Megh (Sovereign Cloud)_ — Cloud audit logs detecting unauthorized cross-border container migrations violating MeitY data localization.
    8. **`08-dpi-apisetu-replay`**: _Operation Setu (API Setu Defense)_ — e-KYC gateway logs with duplicate cryptographic nonces and WAF rate-limiting mitigations.
  - **SQLAlchemy Database Persistence Architecture**:
    - Created models `CyberSandboxChallenge`, `CyberSandboxSession`, and `UserCyberCompetency` in `backend/app/models/models.py`.
    - Stored all challenge manifests, evidence telemetry (`artifacts_json`), and Marimo Python notebooks (`notebook_code`) directly in SQLite/Postgres.
    - Completely purged `backend/content/` from the repository, preventing git file sprawl.
    - Ephemeral materialization into `backend/scratch/sandboxes/<session_id>/` on session launch with automatic cleanup upon termination.
  - **Live Supabase Knowledge Base Integration (Strictly Read-Only GET)**:
    - Built `supabase_service.py` to query scraped Wikipedia articles and YouTube curricula from `https://tdcrpjlpvkqjptvsndnp.supabase.co` across the 5 official Digital Governance topics (`cybersecurity`, `data-privacy`, `digital-signatures`, `government-cloud`, `digital-public-infrastructure`).
    - Exposed `GET /api/digital-governance/sandbox/knowledge-base` and `POST /api/digital-governance/sandbox/generate-from-topic`.
  - **Client Console & Navigation**:
    - Enhanced `CyberSandboxPage.tsx` with a 3-tab generator modal (Live Supabase Knowledge Base, Lecture Presets, Custom Transcripts), 9-category filter pills, live Marimo console embed, and CTFd flag verification.
    - Added "Digital Governance" navigation link in `Navbar.tsx` (desktop and mobile) and bilingual English/Hindi translations in `frontend/src/lib/i18n/index.tsx`.
  - **Verification**:
    - Full backend test suite passing (15 tests total: 4 curriculum, 4 tabletop scenarios, 7 sandbox suite tests).
    - `npx tsc --noEmit` and `npm run build` compiled all 20 pages with 0 errors.
- **Affected Files / Routes**:
  - `backend/app/models/models.py`
  - `backend/app/core/seed_data.py`
  - `backend/app/modules/digital_governance/services/llm_provider.py`
  - `backend/app/modules/digital_governance/services/supabase_service.py`
  - `backend/app/modules/digital_governance/services/sandbox_manager.py`
  - `backend/app/modules/digital_governance/services/content_pipeline.py`
  - `backend/app/modules/digital_governance/services/templates/` (all 8 templates)
  - `backend/app/modules/digital_governance/schemas.py`
  - `backend/app/modules/digital_governance/router.py`
  - `backend/tests/test_sandbox.py`
  - `frontend/src/features/digital_governance/components/CyberSandboxPage.tsx`
  - `frontend/src/components/shared/Navbar.tsx`
  - `frontend/src/lib/i18n/index.tsx`
  - `GET /api/digital-governance/sandbox/challenges`
  - `GET /api/digital-governance/sandbox/knowledge-base`
  - `POST /api/digital-governance/sandbox/generate-from-topic`
  - `POST /api/digital-governance/sandbox/generate`
  - `POST /api/digital-governance/sandbox/session/start`
  - `GET /api/digital-governance/sandbox/session/{session_id}`
  - `POST /api/digital-governance/sandbox/session/{session_id}/stop`
  - `POST /api/digital-governance/sandbox/session/submit-flag`
  - `POST /api/digital-governance/sandbox/session/unlock-hint`
  - `GET /api/digital-governance/sandbox/competencies`
- **Agent Context / Rules**:
  - Zero git file clutter: all challenges and evidence files must reside in the SQLAlchemy database.
  - Ephemeral scratch runtime files must only be materialized in `backend/scratch/` (gitignored).
  - Supabase is strictly read-only: never perform POST/PUT/PATCH/DELETE against Supabase.

### [2026-09-12] - Multi-Stage Incident Response Tabletop Engine (Milestone 2)

- **Author**: Diwakar Ujjwal (@diwakarujjwal)
- **Scope**: `[backend]` `[frontend]` `[scenarios]` `[api]` `[tests]` `[docs]`
- **Branch**: `cgp/digital-governance`
- **Description**:
  - Implemented the Multi-Stage Incident Response Tabletop Engine in `backend/app/modules/digital_governance/` and mounted under `/api/v1/digital-governance/scenarios`.
  - Formulated 5 comprehensive civil-service case scenarios covering the 5 national digital governance pillars:
    1. **Cybersecurity**: _Operation Vajra_ — Ransomware outbreak on State Treasury Payment Gateway (PFMS), network segmentation vs. volatile memory destruction, CERT-In 6-hour reporting adherence under Section 70B, and Section 65B forensic chain of custody.
    2. **Data Privacy**: _Operation Raksha_ — Aadhaar-linked DBT citizen pension registry leak on public cloud, statutory notification to the Data Protection Board of India under Section 8(6) of DPDP Act 2023, Aadhaar masking, and Significant Data Fiduciary (SDF) appointment.
    3. **Digital Signatures & PKI**: _Operation Mudra_ — Disputed ₹45 crore e-procurement tender on GeM, Class 3 DSC token theft defense, OCSP/CRL timestamp inspection, and legal non-repudiation under IT Act Sections 3 & 3A.
    4. **Government Cloud (MeghRaj / GI Cloud)**: _Operation Megh_ — Unauthorized foreign region workload migration during peak traffic, STQC audit enforcement, sovereign data localization, and Government Community Cloud (GCC) isolation.
    5. **Digital Public Infrastructure (DPI / India Stack)**: _Operation Setu_ — 65,000 req/sec cryptographic replay attack on citizen e-KYC and API Setu highway, single-use nonce validation, adaptive rate-limiting, and NCCC threat sharing.
  - Built interactive client interface `CyberScenariosPage.tsx` at `/digital-governance/scenarios` matching the `dev` institutional design tokens (Navy `#1E3A8A`, Gold `#EAB308`, Slate `#F8FAFC`).
  - Added real-time compliance scoring ($0–100\%$), decision consequence summaries, and executive debrief certification.
  - Added unit test suite `backend/tests/test_scenarios.py` with 4 automated tests passing in 0.001s.
- **Affected Files**:
  - `backend/app/modules/digital_governance/schemas.py`
  - `backend/app/modules/digital_governance/services/scenario_service.py`
  - `backend/app/modules/digital_governance/router.py`
  - `backend/app/main.py`
  - `backend/tests/test_scenarios.py`
  - `frontend/src/app/digital-governance/scenarios/page.tsx`
  - `frontend/src/features/digital_governance/components/CyberScenariosPage.tsx`
  - `docs/team/diwakar-ujjwal.md`
  - `docs/features/digital-governance-cybersecurity.md`
  - `docs/changelog.md`

---

### [2026-09-12] - Digital Governance & Cyber Defense Curriculum Architecture (Milestone 1)

- **Author**: Diwakar Ujjwal (@diwakarujjwal)
- **Scope**: `[backend]` `[curriculum]` `[assessments]` `[tests]` `[docs]`
- **Branch**: `cgp/digital-governance`
- **Description**:
  - Seeded official Government of India curriculum: _"Digital Governance, Cyber Defense & Public Digital Architecture"_ accredited by NeGD and CERT-In (`backend/app/core/seed_data.py`).
  - Implemented 5 comprehensive modules covering the 5 core national pillars:
    1. **Cybersecurity**: CERT-In 6-hour reporting mandate (Section 70B IT Act 2000), Critical Information Infrastructure (NCIIPC), and live SOC telemetry triage.
    2. **Data Privacy**: Digital Personal Data Protection Act 2023 (DPDP Act), Data Fiduciary obligations, Consent Managers, and DPBI penalty structures.
    3. **Digital Signatures & PKI**: IT Act Sections 3 & 3A, Controller of Certifying Authorities (CCA), Class 3 DSC tokens, Aadhaar eSign in e-Office, and non-repudiation under Indian Evidence Act Section 65B.
    4. **Government Cloud (MeghRaj / GI Cloud)**: MeitY CSP empanelment, STQC security audits, sovereign data localization, and Government Community Cloud isolation.
    5. **Digital Public Infrastructure (DPI / India Stack)**: Aadhaar e-KYC protocols, DigiLocker Rule 9A legal parity, PFMS Direct Benefit Transfer (DBT), and API Setu interoperability.
  - Added in-lesson practice MCQs with detailed statutory explanations across all 10 lessons in `CourseLearningPlayerPage.tsx`.
  - Engineered 15-question end-of-course Certification Assessment with automated grading, 70% passing threshold, and credential certificate preview via `AssessmentTestPage.tsx`.
  - Added unit test suite `backend/tests/test_digital_governance.py` with 4 automated tests passing in 0.03s.
- **Affected Files**:
  - `backend/requirements.txt`
  - `backend/app/core/seed_data.py`
  - `backend/tests/test_digital_governance.py`
  - `docs/team/diwakar-ujjwal.md`
  - `docs/features/digital-governance-cybersecurity.md`
  - `docs/changelog.md`

---

### [2026-09-09] - Comprehensive Visual Design Overhaul (design branch)

- **Author**: Antigravity AI & Arnav Bisht (@arnavbisht141)
- **Scope**: `[frontend]` `[ui]` `[css]` `[design]`
- **Branch**: `design`
- **Description**:
  - **Design Foundation (`globals.css`):** Expanded the design token system with an extended palette — navy scale (`#070E20` → `#1E3A8A`), teal accents (`#0D9488`, `#14B8A6`), ochre (`#B45309`), sage (`#059669`). Added 8 CSS keyframe animations (`fadeInUp`, `pulseGlow`, `shimmer`, `floatDot`, `slideLine`, `cardHover`) and utility classes (`.hero-gradient`, `.navy-teal-gradient`, `.glass-light`, `.glass-card`, `.card-hover-lift`, `.hero-mesh`, `.animate-pulse-glow`, `.animate-float-dot*`).
  - **Landing Page (`EntryLandingPage.tsx`):** Transformed hero section to a dramatic `hero-gradient` (dark navy-to-teal) with CSS mesh-grid pattern overlay and two radial glow orbs. Stats bar moved into the hero as frosted glass cards. Carousel now uses full `object-cover` with gradient overlay and teal dot controls. About section: unique icon backgrounds per pillar (navy/teal/ochre) with left-border accent cards. How It Works: horizontal timeline with gradient connecting line and colored step circles (navy/teal/amber/ochre) — stacked mobile version. Resources: top-stripe colored cards per document category. Help: 3 gradient-accent support cards with distinct top stripes (navy/teal/ochre). Closing CTA banner reuses hero-gradient with mesh overlay.
  - **Home Page Dashboard (`HomePage.tsx`):** Welcome header becomes a full hero-gradient section with CSS mesh, two glow orbs, gradient avatar ring with online pulse, and glassmorphic secondary button. Teal left-border on "Continue Learning" card; gradient horizontal progress bars replacing flat navy; amber-gradient streak card when streak ≥ 3; difficulty-colored left-border course cards (green=beginner, blue=intermediate, amber=advanced). All card section icons upgraded to colored rounded-xl icon containers (navy/teal/amber/sage). Stats grid uses color-coded cells (slate/teal/blue).
  - **Discover Page (`DiscoverPage.tsx`):** Header becomes hero-gradient with glassmorphic search input (glass-light class), gradient send button, and glass trending topic pills. Category tabs use navy-teal-gradient for active state. Course cards get category-colored accent top stripe, colored difficulty dots, gradient "View Course" button, and card-hover-lift animation. Empty state and loading spinner upgraded.
  - **AI Assistant Widget (`AiAssistantWidget.tsx`):** Floating button uses navy-teal-gradient with `animate-pulse-glow`, ping online indicator, and hover tooltip. Chat panel: gradient header with mesh overlay, assistant messages with teal left-border, user messages with gradient bubble, animated typing indicator (3 bouncing dots using `animate-float-dot*`), gradient send button, auto-scroll to latest message.
  - **Navbar (`Navbar.tsx`):** Brand icon upgraded to rounded-xl navy-teal-gradient. Active nav link indicators changed from bg-blue-50 rectangle to bottom-bar gradient underline (`linear-gradient(navy→teal)`). Profile avatar upgraded to gradient ring with dark center. Profile dropdown upgraded to `rounded-2xl` with enhanced shadow. Register button upgraded to navy-teal gradient. Language switcher gets teal icon and rounded-full style.
- **Design Principles Enforced:**
  - No emojis, no colored pill boxes above headings
  - All animations use CSS-only keyframes (no JS animation libraries)
  - `prefers-reduced-motion` media query kills all animations for accessibility
  - Hindi/English i18n completely preserved — no translation keys changed
  - All routing logic untouched
- **Affected Files**:
  - `frontend/src/app/globals.css`
  - `frontend/src/features/landing/components/EntryLandingPage.tsx`
  - `frontend/src/features/dashboard/components/HomePage.tsx`
  - `frontend/src/features/catalog/components/DiscoverPage.tsx`
  - `frontend/src/features/assistant/components/AiAssistantWidget.tsx`
  - `frontend/src/components/shared/Navbar.tsx`
  - `docs/changelog.md`
  - `docs/team/arnav-bisht.md`
  - `docs/features/ui-design-system.md`

---

### [2026-09-09] - Dedicated Institutional Pages & Context-Aware Navbar Routing

- **Author**: Antigravity AI & Arnav Bisht (@arnavbisht141)
- **Scope**: `[frontend]` `[ui]` `[i18n]` `[routing]` `[docs]`
- **Branch**: `postlogin`
- **Description**:
  - Created 4 dedicated institutional pages (`/about`, `/how-it-works`, `/resources`, `/help`) as standalone routes with full-page components under `frontend/src/features/institutional/components/`.
  - **About Page (`/about`):** Institutional framework overview featuring 3 competency pillars (Statistical Methodology, Standardized Evaluation, Cadre AI Assistant), a paradigm shift comparison (Rule-Based vs. Role-Based learning), 6 institutional stakeholder cards (MoSPI, CBC, NSSTA, NSSO, CSO, ISTM), and a verifiable credentials banner.
  - **How It Works Page (`/how-it-works`):** Detailed 4-stage capacity building breakdown (Authenticate & Onboard, Study Accredited Curriculum, Standardized Assessment, Earn Verified Credential) with full explanations, key standard operations, process guarantee stats, and learning process FAQ section.
  - **Resources Page (`/resources`):** Searchable and filterable official statistical library with 6 cadre document cards (NSSO Field Manual, CPI Technical Manual, UN-NQAF Rubrics, CAPI Operations Manual, NAS Handbook, PFMS Guide), download modal with authentication badges, and category/search filtering.
  - **Help Page (`/help`):** 3-channel support grid (24/7 AI Assistant, Central Training Division Desk, Nodal Cadre Coordinators), collapsible FAQ accordion with 5 common queries, and full support ticket submission form with simulated tracking IDs.
  - **Context-Aware Navbar Routing:** Updated `Navbar.tsx` to differentiate between unauthenticated landing page users (smooth-scroll anchor links to `/#about`, `/#how-it-works`, etc.) and authenticated/inner-page users (dedicated page routes to `/about`, `/how-it-works`, etc.).
  - All 4 pages follow the institutional design standard: white header banner (`bg-white border-b border-slate-200`), continuous `#F8FAFC` slate canvas, Official Navy `#1E3A8A` branding, and Lucide SVG iconography.
  - Each page includes bilingual (Hindi/English) support via `useI18n()` for all translated keys.
- **Affected Files**:
  - `frontend/src/features/institutional/components/AboutPage.tsx` [NEW]
  - `frontend/src/features/institutional/components/HowItWorksPage.tsx` [NEW]
  - `frontend/src/features/institutional/components/ResourcesPage.tsx` [NEW]
  - `frontend/src/features/institutional/components/HelpPage.tsx` [NEW]
  - `frontend/src/app/about/page.tsx` [NEW]
  - `frontend/src/app/how-it-works/page.tsx` [NEW]
  - `frontend/src/app/resources/page.tsx` [NEW]
  - `frontend/src/app/help/page.tsx` [NEW]
  - `frontend/src/components/shared/Navbar.tsx`
  - `docs/changelog.md`
  - `docs/team/arnav-bisht.md`
  - `docs/features/ui-design-system.md`
  - `docs/features/homepage-portal.md`

---

### [2026-09-09] - Post-Login Homepage & Repository-Wide Non-AI Institutional Redesign

- **Author**: Antigravity AI & Arnav Bisht (@arnavbisht141)
- **Scope**: `[frontend]` `[ui]` `[i18n]` `[docs]`
- **Branch**: `postlogin`
- **Description**:
  - Extended the non-AI, white background institutional standard from Discover across the post-login homepage (`/home`), my learning (`/my-learning`), officer profile (`/profile`), and administration console (`/admin`).
  - Replaced isolated floating widget cards and dark gradients with seamless full-width white institutional headers (`bg-white border-b border-slate-200 py-8 sm:py-10`) and a continuous `#F8FAFC` slate canvas.
  - Stripped all remaining decorative unicode emojis (`🔥`, `✨`, `★`, `🎉`) and text checkmarks (`Completed ✓`) across all pages (`CourseLearningPlayerPage.tsx`, `AssessmentTestPage.tsx`, `OnboardingWizardPage.tsx`, `AdminDashboardPage.tsx`), replacing them with semantic Lucide SVG icons (`CheckCircle2`, `XCircle`, `Check`).
  - Eliminated artificial colored/saffron eyebrow pill boxes above headings; standardized on letter-spaced ministry headers with Lucide `Building2` iconography.
  - Standardized interactive buttons across the application on Official Navy Primary (`#1E3A8A` / hover `#172554`).
  - Implemented 100% full bilingual (Hindi/English) translation parity across `home.*`, `learning.*`, `profile.*`, and `admin.*` keys in `frontend/src/lib/i18n/index.tsx`.
  - Updated documentation across `docs/features/ui-design-system.md`, `docs/features/analytics-dashboard.md`, `docs/team/arnav-bisht.md`, and `docs/changelog.md`.
- **Affected Files**:
  - `frontend/src/features/dashboard/components/HomePage.tsx`
  - `frontend/src/features/progress/components/MyLearningPage.tsx`
  - `frontend/src/features/profile/components/ProfilePage.tsx`
  - `frontend/src/features/administration/components/AdminDashboardPage.tsx`
  - `frontend/src/features/learning/components/CourseLearningPlayerPage.tsx`
  - `frontend/src/features/assessments/components/AssessmentTestPage.tsx`
  - `frontend/src/features/onboarding/components/OnboardingWizardPage.tsx`
  - `frontend/src/features/auth/components/ForgotPasswordPage.tsx`
  - `frontend/src/lib/i18n/index.tsx`
  - `docs/features/ui-design-system.md`
  - `docs/features/analytics-dashboard.md`
  - `docs/team/arnav-bisht.md`
  - `docs/changelog.md`

---

### [2026-09-08] - Discover Page Overhaul, Background Fix & Full Hindi Localization

- **Author**: Antigravity AI & Arnav Bisht (@arnavbisht141)
- **Scope**: `[frontend]` `[ui]` `[i18n]` `[docs]`
- **Branch**: `discover`
- **Description**:
  - Solved the background color and container problem on `/discover`: replaced the nested, floating widget box layout with a seamless full-width institutional white header banner (`bg-white border-b border-slate-200`) and a unified `#F8FAFC` slate catalog canvas.
  - Eliminated all artificial "AI telltale" indicators: removed unicode emojis (`🔥`, `✨`, `★`) from category tabs, trending pills, and course cards, and replaced rectangular colored pill boxes above headings with clean, letter-spaced ministry eyebrow text and Lucide `Building2` iconography.
  - Implemented 100% full bilingual (Hindi/English) compatibility: expanded `frontend/src/lib/i18n/index.tsx` dictionary with translations for search inputs, search/clear buttons, trending topics (_National Sample Survey_, _CPI_, _PFMS_, etc.), discipline categories, filter options, sort order, and dynamic course card title/overview metadata.
  - Elevated course card presentation: integrated official MoSPI/ISTM badges, Lucide `Clock` duration counters, Lucide `Star` ratings with enrolled counts, structured metadata lists, and official Navy `#1E3A8A` primary buttons.
  - Added an institutional accreditation trust ribbon affirming MoSPI accreditation, CBC competency guidelines, and verifiable cryptographic credentials.
  - Harmonized `CourseDetailPage.tsx` with clean layout, Lucide `Star` rating icons, and bilingual string lookup.
  - Updated documentation across `docs/features/course-management.md`, `docs/features/ui-design-system.md`, `docs/team/arnav-bisht.md`, and `docs/changelog.md`.
- **Affected Files**:
  - `frontend/src/features/catalog/components/DiscoverPage.tsx`
  - `frontend/src/features/catalog/components/CourseDetailPage.tsx`
  - `frontend/src/lib/i18n/index.tsx`
  - `docs/features/course-management.md`
  - `docs/features/ui-design-system.md`
  - `docs/team/arnav-bisht.md`
  - `docs/changelog.md`

---

### [2026-09-08] - Homepage Streamlining, Sober Yellow Accents & Hindi Toggle Migration

- **Author**: Antigravity AI & Arnav Bisht (@arnavbisht141)
- **Scope**: `[frontend]` `[ui]` `[docs]`
- **Branch**: `homepage`
- **Description**:
  - Removed top ministry ribbon from `Navbar.tsx`; integrated language toggle button (`हिन्दी / English`) directly into main navbar action bar and mobile drawer.
  - Eliminated artificial "AI telltale" elements: stripped out multi-colored eyebrow pill boxes above section titles, removed fake progress meters, rainbow gradient lines, and synthetic query chips.
  - Transitioned from saturated amber-gold to sober warm yellow accents (`#EAB308` / `#CA8A04` / `#FEF9C3`), keeping it restrained, dignified, and authentic to Indian public-service standards.
  - Streamlined page architecture to a bare-bones, highly focused portal: clean hero with framed carousel, clean 4-metric statistics strip, grounded institutional overview card, direct 4-step milestone cards, uniform document cards, and solid deep navy closing banner.
  - Recalibrated section scroll offsets and viewports to `scroll-mt-16 sm:scroll-mt-[68px] min-h-[calc(100vh-68px)]`.
  - Implemented full bilingual internationalization (Hindi/English) across all homepage sections (`hero`, `about`, `howItWorks`, `resources`, `help`, `footer`, and carousel slides) via `useI18n()`.
  - Updated `docs/features/homepage-portal.md`, `docs/features/ui-design-system.md`, and `docs/team/arnav-bisht.md`.
- **Affected Files**:
  - `frontend/src/components/shared/Navbar.tsx`
  - `frontend/src/features/landing/components/EntryLandingPage.tsx`
  - `frontend/src/lib/i18n/index.tsx`
  - `frontend/src/app/globals.css`
  - `docs/features/homepage-portal.md`
  - `docs/features/ui-design-system.md`
  - `docs/team/arnav-bisht.md`
  - `docs/changelog.md`

---

### [2026-09-08] - Homepage Aesthetic Unification & Navy/Gold Design System

- **Author**: Antigravity AI & Arnav Bisht (@arnavbisht141)
- **Scope**: `[frontend]` `[ui]` `[docs]`
- **Branch**: `homepage`
- **Description**:
  - Completely unified the portal landing page (`EntryLandingPage.tsx`) under the official **Navy Blue (`#1E3A8A`) & Gold/Yellow (`#F59E0B`) Institutional Standard**, systematically replacing fragmented legacy rose/charcoal hues.
  - Introduced rich graphical elements: connected horizontal progression line with navy-to-gold gradient, competency progress meters, dual-tone icon containers, and ambient backdrop lighting.
  - Integrated comprehensive `lucide-react` iconography across metrics, milestones, resource cards, and interactive support channels.
  - Enhanced text readability with relaxed line-heights, high contrast WCAG AAA ratios, interactive AI Copilot sample prompt chips, and scannable cadre FAQ cards.
  - Preserved single-viewport layout physics (`scroll-mt-[120px] min-h-[calc(100vh-120px)]`) and zero-shift programmatic glide scrolling.
  - Added new feature specification `docs/features/homepage-portal.md`, updated `docs/features/ui-design-system.md`, and logged contributor activity in `docs/team/arnav-bisht.md`.
- **Affected Files**:
  - `frontend/src/features/landing/components/EntryLandingPage.tsx`
  - `frontend/src/app/globals.css`
  - `docs/features/homepage-portal.md`
  - `docs/features/ui-design-system.md`
  - `docs/features/README.md`
  - `docs/team/arnav-bisht.md`
  - `docs/changelog.md`
- **Agent Context / Rules**:
  - Maintain the Navy Blue & Gold color tokens (`--color-navy-primary`, `--color-gold-primary`) and avoid reintroducing legacy rose tones (`#965C66`).
  - Keep single-viewport section heights (`min-h-[calc(100vh-120px)]`) and ID anchors intact for smooth navbar gliding.

---

### [2026-09-08] - Documentation Hierarchy Revamp & Knowledge Decentralization

- **Author**: Antigravity AI & Arnav Bisht (@arnavbisht141)
- **Scope**: `[docs]`
- **Description**:
  - Decomposed redundant monolithic documentation (`PROJECT_CONTEXT_AND_PROGRESS.md`, `HOMEPAGE_UI_REFINEMENTS.md`, `UI_UX_CHANGES.md`) into a modular structure.
  - Established `docs/features/` with in-depth specifications for AI Copilot, Course Management, Assessments & Certificates, Auth/RBAC, Analytics & Dashboards, and the UI Design System.
  - Established `docs/team/` for recording visible and invisible (research, design, architecture) contributions by teammates.
  - Established unified `docs/changelog.md` for team and AI agent operational context.
  - Updated root `docs/README.md` as the centralized documentation hub.
- **Affected Files**:
  - `docs/changelog.md`
  - `docs/features/*`
  - `docs/team/*`
  - `docs/README.md`
  - Removed redundant legacy files.

---

### [2026-09-07] - Domain Boundary Reorganization & Modular Monolith Transition

- **Author**: Arnav Bisht (@arnavbisht141)
- **Scope**: `[backend]` `[architecture]`
- **Description**:
  - Reorganized backend into clean domain modules under `backend/app/modules/` (`auth`, `onboarding`, `profile`, `discover`, `courses`, `learning`, `assessments`, `dashboard`, `admin`).
  - Integrated latest landing page and layout features into the modular structure.
  - Created ADRs (`adr/0001-modular-monolith-and-ai-boundary.md` and `adr/0002-backend-owns-lms-data.md`) establishing boundaries between LMS data ownership and future AI services.
- **Affected Files**:
  - `backend/app/modules/*`
  - `backend/app/main.py`
  - `docs/domain-boundaries.md`
  - `docs/architecture.md`
  - `docs/adr/*`

---

### [2026-09-07] - Hero, Navbar Brand & Statistics Polish (Navy Aesthetic)

- **Author**: Diwakar Ujjwal (@diwakarujjwal)
- **Scope**: `[frontend]`
- **Description**:
  - Aligned hero headline and statistics section with the official dark navy (`#1E3A8A`) and slate aesthetic.
  - Refined top navbar brand container, Government of India ribbon, and active indicators.
  - Merged pull request #6 from branch `aarna` into `main`.
- **Affected Files**:
  - `frontend/src/app/page.tsx`
  - `frontend/src/components/shared/Navbar.tsx`

---

### [2026-09-06] - Viewport-Snap Navigation, Scroll-Spy Lock & Dynamic Footer Architecture

- **Author**: Diwakar Ujjwal (@diwakarujjwal)
- **Scope**: `[frontend]`
- **Description**:
  - **Single-Viewport Section Architecture**: Configured landing page sections (`#hero`, `#about`, `#how-it-works`, `#resources`, `#help`) with `scroll-mt-[120px] min-h-[calc(100vh-120px)] flex flex-col justify-center`.
  - **Trackpad Inertia Restoration**: Removed global `html { scroll-behavior: smooth; }` and eliminated duplicate `scroll-padding-top: 120px` in `globals.css` that was compounding with section offsets. Smooth scrolling is handled programmatically via `window.scrollTo({ behavior: "smooth" })`.
  - **Programmatic Scroll Lock**: Implemented `isProgrammaticScrollRef` lock during anchor scrolling to prevent intermediate tabs from cycling mid-flight.
  - **Zero-Blink Tabs**: Standardized 1px fixed borders (`border-transparent` vs `border-blue-200`) and constant `font-medium` to eliminate box-model layout shifts when toggling tabs. Added `scroll={false}` and `prefetch={false}` to anchor Links.
  - **Dynamic Footer**: Replaced static layout footer with context-aware client `<Footer />` component that is omitted on the landing page (to avoid duplicate white footers below `#help`) and auto-rendered on inner pages.
  - Cleaned untracked `.venv` directory from git tracking.
- **Affected Files**:
  - `frontend/src/app/globals.css`
  - `frontend/src/components/shared/Navbar.tsx`
  - `frontend/src/components/shared/Footer.tsx`
  - `frontend/src/app/layout.tsx`
  - `frontend/src/app/page.tsx`

---

### [2026-09-06] - Header & Landing Page Aesthetic Parity Refinements

- **Author**: Arnav Bisht (@arnavbisht141)
- **Scope**: `[frontend]` `[docs]`
- **Description**:
  - Removed top scrolling announcement marquee from `Navbar.tsx` to eliminate visual noise.
  - Removed redundant `[MoSPI]` pill badge in header logo and eyebrow badge in landing hero.
  - Unified typography across navigation links (`About`, `Resources`, `Help` match `Discover` at `text-sm font-medium`).
  - Enlarged authentication CTAs: `Sign In` (`h-10 px-4`) and `Register` (`h-10 px-5 bg-[#1E3A8A]`).
  - Elevated landing hero headline (`text-3xl sm:text-4xl lg:text-[36px] font-extrabold text-slate-900`) and enlarged CTA buttons (`h-11 px-7`).
  - Refined statistics section to `100% Accredited Curriculum` with `text-3xl sm:text-4xl font-extrabold text-[#1E3A8A]`.
  - Merged PR #4 (`arnav` branch).
- **Affected Files**:
  - `frontend/src/components/shared/Navbar.tsx`
  - `frontend/src/app/page.tsx`

---

### [2026-09-06] - Official iGOT Karmayogi Navy & Slate Aesthetic Refinement

- **Author**: Arnav Bisht (@arnavbisht141)
- **Scope**: `[frontend]`
- **Description**:
  - Aligned the application with official Government of India iGOT Karmayogi standards, transitioning primary accents to `#1E3A8A` / `#1D3557` and layout neutrals to slate.
  - Removed excessive AI branding and overbearing neon elements in favor of dignified institutional aesthetics.
- **Affected Files**:
  - `frontend/src/app/globals.css`
  - `frontend/src/components/shared/*`
  - `frontend/src/app/(auth)/*`

---

### [2026-09-06] - Muted Rose Design System & Floating AI Assistant Redesign

- **Author**: Aarna (@aarna605-dot), Ravish Kansal (@RavishKansal), Arnav Bisht (@arnavbisht141)
- **Scope**: `[frontend]`
- **Description**:
  - Implemented the **Muted Rose Design System** palette tokens (`#965C66` primary, `#C8A8A9` secondary, `#EEE8E9` warm background, `#241E20` charcoal text).
  - Redesigned landing page hero layout and statistics bar with aspect-ratio-preserved official photographs (`/karmayogi.jpg`, `/government-meeting.jpg`, `/ai-daksh.jpg`).
  - Redesigned floating AI assistant widget (`AiAssistantWidget.tsx`) into a sleek circular launcher (`h-14 w-14 rounded-full bg-[#965C66]`), removed LangGraph vendor branding, and established civil-service identity: _"Karmayogi AI - Civil Service Intelligence Assistant"_.
  - Merged PR #2 (`Aarna` branch).
- **Affected Files**:
  - `frontend/src/app/page.tsx`
  - `frontend/src/components/shared/AiAssistantWidget.tsx`
  - `frontend/src/app/(auth)/login/page.tsx`
  - `frontend/src/app/(auth)/register/page.tsx`

---

### [2026-09-06] - Dockerization & Multi-Stage Deployment Architecture

- **Author**: Arnav Bisht (@arnavbisht141)
- **Scope**: `[devops]` `[infra]`
- **Description**:
  - Production-grade multi-stage Docker build for Next.js 16 (`base` ➔ `deps` ➔ `builder` ➔ `runner`) generating an unprivileged ~150MB standalone container.
  - FastAPI Python 3.12 Docker container with automated health check probes.
  - Dual Compose configurations:
    - `docker-compose.yml`: Standalone production profiles with persistent SQLite volume (`backend-data:/app/data`).
    - `docker-compose.dev.yml`: Live-reload development setup with host volume binds (`./frontend:/app`, `./backend:/app`).
- **Affected Files**:
  - `frontend/Dockerfile`, `frontend/Dockerfile.dev`, `frontend/.dockerignore`
  - `backend/Dockerfile`, `backend/.dockerignore`
  - `docker-compose.yml`, `docker-compose.dev.yml`
  - `README.md`

---

### [2026-09-06] - Initial Codebase & LMS Domain Implementation

- **Author**: Arnav Bisht (@arnavbisht141)
- **Scope**: `[frontend]` `[backend]`
- **Description**:
  - Initial repository creation implementing the full Miro LMS user flow for Smart India Hackathon SIH '26 (MoSPI).
  - 17 normalized SQLAlchemy models covering users, roles, courses, modules, lessons, skills, enrollments, progress, assessments, questions, attempts, and learning histories.
  - NIST-standard PBKDF2-HMAC-SHA256 authentication replacing problematic `passlib` bcrypt dependencies.
  - LangGraph StateGraph assistant workflow with Google Gemini, OpenAI, and deterministic MoSPI domain fallback.
  - Coursera-style split learning player, timed MCQ assessment engine, verifiable PDF/printable certificate modal, and 5-step onboarding wizard.
