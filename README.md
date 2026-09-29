# BidShield AI 

AI-assisted procurement / tender compliance platform. Officers publish tenders with
requirements; bidders upload evidence PDFs; the backend extracts, retrieves and analyzes
that evidence with Groq (LLM) combined with deterministic Python rules, produces a
compliance score + risk level, and every material action is recorded in a SHA-256
hash-chained audit log. The AI never makes the final call -- a human officer always
approves, rejects, or sends a bid for clarification.

> **Prototype / demo status.** Authenticity checks return `VERIFIED` / `UNVERIFIED` /
> `REVIEW`, never a false claim of "fake" or "genuine" -- there is no live government
> verification API wired in (`AUTHORITY_MODE=mock`). Compliance scores and risk levels
> are a prototype decision-support signal, not a legally validated procurement decision.

---

## Architecture

```
React (Vite)  ---HTTP/JSON--->  FastAPI backend  --->  SQLite (demo) / Postgres (optional)
                                     |
                                     |--> PyMuPDF (+ Tesseract OCR fallback) - PDF text extraction
                                     |--> TF-IDF retrieval (scikit-learn) - lightweight RAG
                                     |--> Groq API (OpenAI-compatible) - evidence interpretation
                                     |--> Deterministic Python rules - final PASS/FAIL/REVIEW
                                     +--> SHA-256 hash chain - audit log
```

| Layer | Tech |
|---|---|
| Frontend | React 18 + Vite (single file: `frontend/src/main.jsx`) |
| Backend | FastAPI + Pydantic + SQLAlchemy 2.0 |
| Database | SQLite by default (`backend/iprocurement_demo.db`); Postgres optional via `docker-compose.yml` |
| AI | Groq API (`openai` Python SDK pointed at `https://api.groq.com/openai/v1`) |
| PDF | PyMuPDF (`fitz`), with `pytesseract` OCR fallback for scanned PDFs |
| Retrieval | TF-IDF + cosine similarity (`scikit-learn`) -- no external vector DB needed |
| Auth | JWT (`python-jose`) + Argon2 password hashing (`passlib`) |
| Integrity | SHA-256 file hashing + hash-chained audit log |

**Important:** the Groq API key only ever lives on the backend, read from `backend/.env`.
It is never sent to or embedded in the frontend.

Frontend

React 18 — poora UI ek hi file (frontend/src/main.jsx) mein likha hai
Vite — dev server + build tool
Plain CSS (styles.css) — koi UI library (Tailwind/MUI) nahi use hui, hand-written CSS hai

Backend

Python + FastAPI — saare API routes
Pydantic / pydantic-settings — request validation aur .env config
SQLAlchemy 2.0 — database ORM
SQLite — demo database (default), Postgres optional hai (docker-compose ke through, use nahi kiya jaa raha)
Alembic — DB migrations (though startup par auto-create bhi ho jaata hai)

AI / LLM

Groq API (OpenAI-compatible endpoint) — model: llama-3.3-70b-versatile
openai Python SDK use hota hai Groq se baat karne ke liye (base_url Groq ka hai)
Mock LLM mode bhi hai (MOCK_LLM=true) offline testing ke liye — keyword-matching se fake result deta hai

Document Processing

PyMuPDF (fitz) — PDF se text extract karna
Tesseract OCR (pytesseract) — agar PDF scanned ho (text nahi milta) to fallback

Retrieval (RAG)

scikit-learn (TF-IDF + cosine similarity) — koi heavy vector database nahi, halka-fulka local retrieval — requirement ke liye sabse relevant document chunks nikalta hai

Security / Auth

JWT (python-jose) — login tokens
Argon2 (passlib) — password hashing
SHA-256 — file integrity hash + hash-chained audit log

Auth flow / storage

Local file storage (STORAGE_MODE=local) — uploaded PDFs disk par save hote hain, koi cloud/S3/MinIO use nahi ho raha (though config option maujood hai)
---

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** and npm
- A **Groq API key** -- get one at [console.groq.com](https://console.groq.com/keys)
  (or set `MOCK_LLM=true` to run without one, see below)

---

## Quick start

### 1. Backend

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

Create `backend/.env` (copy `backend/.env.example` if it's missing) and set:

```env
GROQ_API_KEY=your_groq_key_here
GROQ_MODEL=llama-3.3-70b-versatile
MOCK_LLM=false
```

Then start the API:

```bash
uvicorn app.main:app --reload --port 8000
```

- API: http://127.0.0.1:8000
- Swagger docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

The SQLite database and demo accounts/tenders are seeded automatically on first startup.

### 2. Frontend

In a **second terminal**:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The login page contains a **Demo Account Preset** dropdown for one-click access across 5 states and 10 vendor companies.

---

## Demo credentials & Multi-Role Setup

The platform is seeded with realistic synthetic government and vendor accounts. See [`DEMO_CREDENTIALS.md`](DEMO_CREDENTIALS.md) for the full directory.

| Role | Preset Accounts | Example Sign-in | Demo Password |
|---|---|---|---|
| **Ministry / Procurement Officer** | 5 States: MP, Rajasthan, Maharashtra, Gujarat, UP | `officer.maharashtra@bidshield.demo` | `Demo@MH2026` |
| **Registered Bidder** | 10 Vendors: Infra, AI, Telemetry, Healthcare, Solar, etc. | `bidder01@bidshield.demo` | `Bidder@01` |

*All passwords are encrypted in the database with Argon2 password hashing.*

---

## Core Enterprise Features

1. **One Bid Per Bidder Per Tender**:
   - Strictly enforced via database `UNIQUE(tender_id, bidder_id)` constraint.
   - API returns `409 Conflict` on duplicate attempts.
   - Frontend UI automatically detects submitted bids and locks the submission button, displaying `Bid Submitted (Locked)`.
2. **Hybrid Deterministic + LLM Compliance Engine**:
   - PyMuPDF text extraction with Tesseract OCR fallback.
   - Scikit-learn TF-IDF semantic chunk retrieval (RAG) mapped per requirement.
   - Groq API (`llama-3.3-70b-versatile`) generates executive summary, strengths, concerns, and clarification notices.
   - Deterministic rule scoring computes compliance percentage (0–100%) and multi-factor risk categorization (LOW, MEDIUM, HIGH, CRITICAL).
   - Analysis results are cached in the `ai_analyses` table for instant render and historical auditing.
3. **Cryptographic SHA-256 Audit Trail**:
   - Hash-linked ledger recording every critical event (`previous_hash -> current_hash`).
   - Exportable JSON audit trail for regulatory compliance.
4. **Document Vault & Verified Profiles**:
   - Central evidence repository tracking file sizes, processing status, SHA-256 hashes, and document authenticity.
   - Company profiles with verified GSTIN, PAN, and registration numbers.

---

## Demo flow (end to end)

1. **Sign in as bidder** -> *My bids* -> open a bid (or *Browse tenders* -> *Start bid* on
   any published tender).
2. **Upload a PDF** with *+ Add PDF* -- it's hashed (SHA-256), stored, and text-extracted
   automatically.
3. **Submit the bid.**
4. **Sign out, sign in as officer** -> *Review queue* -> select the bid.
5. Click **Run analysis** -- PyMuPDF extracts text -> TF-IDF retrieves the most relevant
   chunks per requirement -> Groq interprets the evidence -> Python rules compute the
   final compliance score, mandatory-requirement check, and risk level.
6. Review the per-requirement evidence, then **Approve** / **Request clarification** --
   this is the human decision that actually changes the bid's status.
7. Open **Audit trail** to see the hash-chained log of every action taken above.
8. Optionally, use **Verify authenticity** on an uploaded document (officer role) to run
   the integrity + mock-authority verification check.

---

## Environment variables (`backend/.env`)

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | `sqlite:///./iprocurement_demo.db` by default. Only change if you're running the Postgres docker-compose stack. |
| `GROQ_API_KEY` | Your Groq API key. Required unless `MOCK_LLM=true`. **Never commit this.** |
| `GROQ_MODEL` | Groq-hosted model id, e.g. `openai/gpt-oss-20b`. |
| `MOCK_LLM` | `true` runs a deterministic keyword-overlap mock instead of calling Groq -- useful for offline development/demos without an API key. |
| `JWT_SECRET` | Secret used to sign auth tokens. Change this for anything beyond local demo use. |
| `CORS_ORIGINS` | JSON array of allowed frontend origins, e.g. `["http://localhost:5173"]`. |
| `AUTHORITY_MODE` | `mock` (default) -- no real government verification API is wired in; returns `UNAVAILABLE` rather than fabricating a result. |
| `STORAGE_MODE` | `local` -- files are stored under `backend/data/`. |
| `MAX_UPLOAD_SIZE` | Max PDF upload size in bytes (default 25 MB). |

See `backend/.env.example` for the full list with defaults.

**Security notes**
- `backend/.env` and `frontend/.env` are both git-ignored -- never commit real secrets.
- If a real Groq key is ever accidentally committed or shared, **rotate it immediately**
  in the Groq console; treat it as compromised.

---

## Project structure

```
backend/
  app/
    api/            # FastAPI routers (auth, tenders, bids, documents, compliance, verification, audit, dashboard, jobs)
    core/           # config, database, security, dependencies
    models/         # SQLAlchemy entities + Pydantic schemas
    schemas/        # request/response Pydantic models
    services/       # document extraction, RAG, compliance engine, risk engine, audit hashing, Groq provider
  alembic/          # DB migrations (SQLAlchemy metadata is also created automatically on startup)
  requirements.txt
  .env.example
frontend/
  src/main.jsx      # entire React app (single file)
  index.html
  package.json
docker-compose.yml  # optional Postgres/Redis/MinIO stack -- not required for the SQLite demo
```

---

## Running with Docker (optional -- Postgres/Redis/MinIO stack)

The SQLite quick-start above is the recommended path for a demo. If you specifically
need the Postgres-backed stack:

```bash
GROQ_API_KEY=your_key_here docker compose up --build
```

This is **not required** for local development or demoing the SQLite version.

---

## Known limitations

- This is a hackathon/demo-grade prototype: authenticity/fraud checks are heuristic and
  explicitly labeled `UNVERIFIED`/`REVIEW` rather than a guarantee -- there is no live
  connection to an issuing authority.
- Risk thresholds (PASS >=80%, REVIEW 60-79%, FAIL <60%) are configurable constants, not
  a legally validated scoring model.
- The audit trail is a SHA-256 hash chain ("blockchain-ready cryptographic audit
  architecture"), not an actual blockchain network.
- RAG retrieval uses TF-IDF for simplicity/offline reliability, not a vector database --
  fine for the demo's document volume, not intended to scale to large corpora as-is.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `CORS policy` error in browser console | Frontend origin isn't in the backend's allowed list. The backend already allows any `localhost`/`127.0.0.1` port by regex -- restart the backend after pulling latest changes. |
| `405 Method Not Allowed` | Frontend/backend method mismatch -- make sure you're on the latest `main.jsx`. |
| `Document processing failed: ...` | Check the backend terminal for the full traceback; make sure the PDF actually contains extractable text (or install Tesseract for OCR fallback on scanned PDFs). |
| `No bidder documents available` when running analysis | Expected -- upload and submit at least one PDF against that bid first. |
| Groq call fails / times out | Confirm `GROQ_API_KEY` is set and valid, `MOCK_LLM=false`, and you have network access from the backend machine. Set `MOCK_LLM=true` to develop offline. |