# iProcurement 2.0

AI-assisted procurement/tender compliance backend for the BidShield demo.

## Run with Docker

From the project root:

```powershell
$env:GROQ_API_KEY="your-key"
docker compose up --build
```

Backend: http://127.0.0.1:8000
Swagger: http://127.0.0.1:8000/docs

## Run locally (no Docker required)

The default local database is SQLite, so you can start the API without PostgreSQL. Docker Compose still overrides it with PostgreSQL.

```powershell
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API: http://127.0.0.1:8000
Swagger: http://127.0.0.1:8000/docs

## Environment

- `GROQ_API_KEY` is required when `MOCK_LLM=false`.
- `GROQ_MODEL` is configurable; the example uses `openai/gpt-oss-20b`. If Groq changes model availability, list models from the API and update this value.
- `AUTHORITY_MODE=mock` deliberately returns `UNAVAILABLE`; it does not claim government verification.
- `STORAGE_MODE=local` stores demo files under `data/object_store` and processing copies under `data/uploads`.
- `WORKER_MODE=inline` means document processing is triggered explicitly through `POST /api/documents/{document_id}/process`; Redis/Celery are reserved for a later async worker.

## Main flow

Register/Login -> Create Tender -> Add Requirements -> Publish -> Create Bid -> Upload PDF -> Process PDF -> Verify Integrity -> AI Compliance Analysis -> Risk Score -> Officer Decision -> Audit Log.

## LLM

The backend uses the OpenAI-compatible Groq endpoint. `app/services/providers/llm.py` is the single provider path used by the compliance engine, while `app/services/grok_service.py` powers the isolated `/api/test-grok` smoke endpoint.

## Notes

The first Alembic revision creates the SQLAlchemy metadata schema for the demo. `Base.metadata.create_all()` remains as a startup fallback so the prototype is easy to run.
