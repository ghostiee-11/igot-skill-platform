# Running the platform locally

This guide sets up the whole iGOT Karmayogi skill platform on your machine: the FastAPI backend, the Next.js frontend, the database, demo data, and the extra pieces each competency area needs (AI models, vector search, speech, labs and the cyber sandbox).

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000/api |
| API docs (Swagger) | http://localhost:8000/docs |
| Health check | http://localhost:8000/api/health |

---

## 1. Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | 3.12 | Tested on 3.12.5. Use a virtual environment (section 4). |
| Node.js | 20.9 or newer | Tested on Node 24.7 with npm 11.5. Required by Next.js 16. |
| Git | any recent | |
| Chrome or Edge | recent | Needed for the AI oral board interview (camera, microphone, face analysis). |
| Docker | optional | Isolates lab code execution. Without it, labs still run (section 9). |

You also need internet access: the database (Supabase), AI models (Groq), vector search (Pinecone), lesson videos (YouTube) and the interview's face model all run as online services.

---

## 2. Get the code

```bash
git clone https://github.com/arnavbisht141/iGotKarmayogi.git
cd iGotKarmayogi
git checkout final-shoot
```

---

## 3. Environment variables

There are two env files, and each app reads only its own:

| File | Read by | Committed? |
|---|---|---|
| `.env` (repository root) | Backend. `backend/.env` is also read and overrides it. | No, gitignored |
| `frontend/.env.local` | Frontend (Next.js does not read the root `.env`) | No, gitignored |

### 3.1 Backend: `.env` in the repository root

Copy the template and fill in the keys you have:

```bash
cp .env.example .env
```

| Variable | Needed for | Required? |
|---|---|---|
| `DATABASE_URL` | Supabase Postgres connection string. Leave unset to use a local SQLite file instead (section 5). | Recommended |
| `SECRET_KEY` | Signing login tokens. A development default is used if unset. | Set any long random string |
| `GROQ_API_KEY`, `GROQ_MODEL` | All AI features: interview board member and scoring, quiz generation, AI chatbot, recommendation reasons. Default model `openai/gpt-oss-120b`. | Yes, for AI features |
| `OPENAI_API_KEY`, `OPENAI_MODEL` | Fallback LLM if Groq fails. | Optional |
| `GOOGLE_API_KEY`, `GEMINI_MODEL` | Embeddings for recommendations (`gemini-embedding-001`), and last-resort LLM fallback. Use `GEMINI_MODEL=gemini-2.5-flash`. | Yes, for recommendations |
| `PINECONE_API_KEY`, `PINECONE_INDEX_NAME` | Vector search for personalised course recommendations. The index is created automatically. | Yes, for recommendations |
| `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_ROLE_KEY` | Supabase project details for the CLI and tools. | Optional |

The AI client tries Groq first, then OpenAI, then Gemini, so one working key is enough to start.

### 3.2 Frontend: `frontend/.env.local`

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

If you run the backend on a different port, change this value and restart `npm run dev`; Next.js only reads it at startup. If the file is missing, the frontend defaults to `http://localhost:8000/api`.

> Never commit `.env` or `.env.local`, and never paste keys into chats or issues. If a key is exposed, rotate it.

---

## 4. Backend setup

Name the virtual environment `venv` inside `backend/`. The cyber defense sandbox looks for the `marimo` command in `backend/venv`.

**macOS / Linux**

```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Windows (PowerShell)**

```powershell
cd backend
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Check that the packages every feature needs are installed:

```bash
python -c "import fastapi, sqlalchemy, psycopg2, langchain_groq, pinecone, pypdf, docx, pptx, marimo, pandas; print('backend dependencies OK')"
```

`requirements.txt` covers:

| Group | Packages | Used by |
|---|---|---|
| Web framework | fastapi, uvicorn, pydantic, pydantic-settings, python-dotenv, python-multipart, python-jose, httpx | API, logins, file uploads |
| Database | sqlalchemy, psycopg2-binary, supabase | Postgres and SQLite access |
| AI and retrieval | langchain, langchain-core, langgraph, langchain-groq, groq, langchain-google-genai, langchain-openai, pinecone | Agents, interview, quizzes, chatbot, recommendations |
| Quiz uploads | pypdf, python-docx, python-pptx | Reading PDF, Word and PowerPoint files |
| Data and labs | pandas, numpy, pyyaml, altair, jsonschema, marimo | Labs, cyber sandbox notebooks |
| Tests | pytest | Backend tests |

### Start the backend

Keep the virtual environment active and stay in `backend/`:

```bash
python run.py
```

This starts Uvicorn on port 8000 with auto-reload. The first start creates any missing tables and seeds the base data (competency taxonomy, courses, cyber challenges). On a hosted database this can take a minute.

Confirm it is up:

```bash
curl http://localhost:8000/api/health
```

> Always start the backend from inside `backend/`. Starting it elsewhere fails with `ModuleNotFoundError: No module named 'app'`.

---

## 5. Database

### Option A: Supabase Postgres (the team setup)

Set `DATABASE_URL` in the root `.env`:

```bash
DATABASE_URL=postgresql://postgres:<password>@db.<project-ref>.supabase.co:5432/postgres
```

- The backend creates missing tables on startup. The SQL migrations in `supabase/migrations/` describe the same schema if you manage the database with the Supabase CLI.
- Supabase's direct host is IPv6-only. If your network or host has no IPv6, or connections time out, use the **Session pooler** connection string from the Supabase dashboard (Project Settings, Database, Connection string).
- Each new database connection costs one to two seconds over the internet. The backend keeps connections warm, so the first page after starting it is the slowest.

### Option B: local SQLite (offline development)

Leave `DATABASE_URL` unset. The backend creates `backend/karmayogi.db` and seeds it on first start. Delete that file to reset. AI, recommendations and speech features still need their online keys.

---

## 6. Demo data

The base seed gives you a few accounts. To load the full demo (36 officials across ranks and divisions, 24 courses with lessons, videos and assessment banks, enrollments, 30 days of gap analysis history, recommendations and practice quizzes), run once with the backend's virtual environment active:

```bash
cd backend
python scripts/seed_demo.py            # uses the LLM for quizzes and indexes courses in Pinecone
python scripts/seed_demo.py --offline  # no LLM or Pinecone calls
```

The seed is idempotent: running it again does not duplicate data.

The final-assessment question bank is already committed in `backend/app/core/assessment_bank.json`. Regenerate it only if you change course content:

```bash
python scripts/build_assessment_bank.py                  # courses missing from the bank
python scripts/build_assessment_bank.py --provider gemini # use Gemini if Groq hits its daily limit
```

---

## 7. Frontend setup

In a second terminal:

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api" > .env.local
npm run dev
```

Open http://localhost:3000.

To check a production build, stop the dev server first (both use the `.next` folder), then run `npm run build`.

---

## 8. Sign-in accounts

| Role | Email | Password | Available after |
|---|---|---|---|
| Administrator | `admin@karmayogi.gov.in` | `Admin@123` | Backend first start |
| Learner (onboarded) | `rajesh.kumar@mospi.gov.in` | `Learner@123` | Backend first start |
| Learner (goes through onboarding) | `priya.sharma@mospi.gov.in` | `Learner@123` | Backend first start |
| Demo officials | `firstname.lastname@igot-demo.in`, for example `aarav.sharma@igot-demo.in` | `Demo@123` | `scripts/seed_demo.py` |

---

## 9. Making every competency area work

| Area | Where | Needs | Without it |
|---|---|---|---|
| Competency profile and gap analysis | `/competency`, `/competency/<domain>` | Database only | |
| Recommendations | `/recommendations`, home page | `PINECONE_API_KEY`, `GOOGLE_API_KEY` (embeddings), `GROQ_API_KEY` (reasons) | Reasons fall back to templates; vector ranking is skipped |
| Courses, lessons and assessments | `/courses`, `/learn/<id>`, `/assess/<id>` | Database; internet for YouTube videos | Each video shows a "Watch on YouTube" link if the embed is blocked |
| Statistical: adaptive exam | `/statistical` | Database only | |
| Technical: hands-on labs | `/labs`, `/labs/<id>` | `pandas` in the backend venv. Docker optional (pulls `python:3.10-slim` on first run). | Without Docker, lab code runs with the backend's Python. Fine locally, but it is not isolated. |
| Digital governance: cyber defense sandbox | `/digital-governance/sandbox` | `marimo` installed in `backend/venv` (from `requirements.txt`) | The page shows "The Marimo analyst console could not start" |
| Digital governance: crisis scenarios | `/digital-governance/scenarios` | Database only | |
| Behavioural: AI oral board interview | `/behavioural/interview` | `GROQ_API_KEY`; Chrome or Edge with camera and microphone allowed; internet access to `cdn.jsdelivr.net` and `storage.googleapis.com` for the face model | Template questions and estimated scores without an LLM; no video signals without a camera |
| Behavioural: case simulations | `/behavioural/cases` | Database; an LLM key to generate new cases | Existing cases still work |
| AI quiz from documents | `/quiz` | An LLM key; `pypdf`, `python-docx`, `python-pptx` | Fill-in-the-blank questions generated without AI |
| AI chatbot | Floating button on every page | An LLM key | |
| Admin console | `/admin` | Administrator account | |

The browser treats `localhost` as a secure origin, so the camera and microphone work without HTTPS locally. On any other host the site must be served over HTTPS.

---

## 10. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| "Failed to fetch" anywhere in the app | The backend is not running, is restarting, or `NEXT_PUBLIC_API_URL` points to the wrong port. Check `curl http://localhost:8000/api/health`, fix `frontend/.env.local`, and restart `npm run dev`. |
| `ModuleNotFoundError: No module named 'app'` | The backend was started outside `backend/`. `cd backend` and run `python run.py`. |
| `Address already in use` | Another process has the port. macOS/Linux: `lsof -ti tcp:8000` then `kill <pid>`. Windows: `netstat -ano \| findstr :8000` then `taskkill /PID <pid> /F`. |
| `connection to server ... timeout expired` on startup | The network to Supabase is slow or blocked. Retry, or switch `DATABASE_URL` to the Session pooler connection string. |
| Pages take many seconds to load | Each database query crosses the internet. Keep the backend running between page loads; use the pooler if connections are slow. |
| "The Marimo analyst console could not start" | Run `pip install -r requirements.txt` inside `backend/venv`, then restart the backend. |
| Groq error 429 "tokens per day" | The free daily token limit is used up. Add `GOOGLE_API_KEY` or `OPENAI_API_KEY` as a fallback, or wait for the limit to reset. |
| OpenAI error 429 `project_spend_limit_exceeded` | Raise the spend limit for that OpenAI project, or rely on Groq or Gemini. |
| Interview camera or microphone does not start | Allow camera and microphone for `localhost:3000` in the browser's site settings, and close other apps using the camera. |
| Interview face analysis says "unavailable" | The browser could not download the face model. Check access to `cdn.jsdelivr.net` and `storage.googleapis.com`. |
| A lesson video shows a connection error | Your network blocks the YouTube embed. Use the "Watch on YouTube" link under the video. |
| `pip` prints dependency conflict warnings | You installed into a shared system Python. Use the `backend/venv` virtual environment. |
| `npm install` fails with `ENOSPC` | The disk is full. Free space (for example `npm cache clean --force`) and retry. |

---

## 11. Everyday commands

```bash
# Terminal 1: backend
cd backend
source venv/bin/activate        # Windows: .\venv\Scripts\Activate.ps1
python run.py

# Terminal 2: frontend
cd frontend
npm run dev
```
