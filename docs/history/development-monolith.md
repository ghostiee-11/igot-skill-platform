# Historical monolith development guide

This is preserved historical documentation for the older backend/SQLite startup. It is not the active runtime on `rebuild/lms` or after its merge into `main`. Historical demo scores and auto-seeding claims below are not claims about today's local service data. Use [current setup](../../LOCAL_SETUP.md) and [Docker runtime operations](../operations/docker-local.md).

# 🛠️ Development & Operations Guide

> **Platform:** iGOT Karmayogi (MoSPI)
> **Target Audience:** Developers, DevOps Engineers & AI Coding Agents

---

## 1. Quick Start Guide (Local Development)

> The full, current setup guide, including environment variables, demo data and the requirements of every competency area, is [LOCAL_SETUP.md](../../LOCAL_SETUP.md).

The application runs natively on your machine using Python 3.12 (FastAPI) for the backend and Node.js (Next.js 16) for the frontend.

### 1.1 Backend Setup (FastAPI & Python 3.12)

Open your first terminal:

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment (specify Python 3.12)
py -3.12 -m venv venv
# Or on macOS/Linux: python3 -m venv venv

# 3. Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows CMD:
# .\venv\Scripts\activate.bat
# Linux / macOS:
# source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Start the backend server
python run.py
```

- **Backend API:** `http://localhost:8000/api` (FastAPI with Uvicorn live reload)
- **Interactive Swagger Docs:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **Health Check Probe:** `http://localhost:8000/api/health`

> [!CAUTION]
> Do NOT install `passlib[bcrypt]` due to known upstream Python 3.12 compatibility bugs. The repository uses native NIST PBKDF2 in `backend/app/core/security.py`.

---

### 1.2 Frontend Setup (Next.js 16 & React 19)

Open your second terminal:

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Start development server with hot-reloading
npm run dev
```

- **Frontend Application:** `http://localhost:3000` (Next.js 16 with Turbopack / Fast Refresh)

---

## 2. Database Management & Resetting

The database is an SQLite instance at `backend/karmayogi.db` and is automatically created and pre-seeded on initial backend launch via `backend/app/core/seed_data.py`.

### Reset Database to Fresh State
To reset all data (users, courses, enrollments, analytics) back to fresh pre-seeded demonstration defaults:

```powershell
# Windows PowerShell:
Remove-Item backend\karmayogi.db

# macOS / Linux:
# rm backend/karmayogi.db
```

Restart the backend (`python run.py`), and a new database with seed data will automatically be created.

---

## 3. Pre-Seeded Accounts & Live Evaluation Personas

The database is automatically populated upon initial startup by `backend/app/core/seed_data.py`.
You can switch between these personas on `/login` using the **1-click demo buttons**:

| Role | Email | Password | Pre-Configured State & Key Demonstration Flow |
|---|---|---|---|
| **Administrator** | `admin@karmayogi.gov.in` | `Admin@123` | Full access to `/admin` console. Inspect officer roster, monitor cadre completion rates, assign mandatory courses, and review question difficulty metrics. |
| **Senior Statistical Officer** | `rajesh.kumar@mospi.gov.in` | `Learner@123` | Fully onboarded officer. Has active 66% progress in *National Sample Survey Methodologies*, a 6-day learning streak, today's goals, and acquired competency badges. |
| **New Civil Servant** | `priya.sharma@mospi.gov.in` | `Learner@123` | Brand new officer with `is_onboarded = False`. Logging in immediately routes into the **5-step Onboarding Wizard**. |

---

## 4. Verification & Testing Commands

```bash
# Verify backend code compiles cleanly
cd backend
python -m compileall app

# Verify backend health check endpoint (while backend is running)
curl http://localhost:8000/api/health

# Verify frontend production build
cd frontend
npm run build
```

---

## 5. Architectural Boundaries

For domain modules, see [domain-boundaries.md](../domain-boundaries.md).
For runtime boundaries and AI extraction plans, see [architecture.md](../architecture.md).
For ADRs, inspect the [adr/](../adr/) directory.
