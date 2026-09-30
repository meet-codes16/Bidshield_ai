import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import Base, engine
from app.api import (
    auth,
    tenders,
    bids,
    documents,
    verification,
    compliance,
    audit,
    dashboard,
    jobs,
)
from app.services.grok_service import analyze_compliance


app = FastAPI(
    title=settings.APP_NAME,
    version="2.0.0",
    description="AI-assisted procurement compliance platform.",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4())

    response = await call_next(request)

    response.headers["X-Request-ID"] = request.state.request_id

    return response


@app.exception_handler(Exception)
async def generic_error(request: Request, exc):
    print("ACTUAL ERROR:", repr(exc))

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(exc),
            },
            "request_id": getattr(request.state, "request_id", ""),
        },
    )

# ============================================================
# API ROUTERS
# ============================================================

app.include_router(auth.router, prefix="/api")
app.include_router(tenders.router, prefix="/api")
app.include_router(bids.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(verification.router, prefix="/api")
app.include_router(compliance.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "iprocurement",
        "mock_llm": settings.MOCK_LLM,
        "authority_mode": settings.AUTHORITY_MODE,
    }


# ============================================================
# GROK COMPLIANCE TEST
# ============================================================

class ComplianceTestRequest(BaseModel):
    requirement: str
    document_text: str


@app.post("/api/test-grok")
def test_grok(data: ComplianceTestRequest):
    try:
        result = analyze_compliance(data.requirement, data.document_text)
    except Exception as exc:
        raise __import__('fastapi', fromlist=['HTTPException']).HTTPException(502, f"Groq analysis failed: {exc}")

    return {
        "success": True,
        "result": result,
    }




def _ensure_demo_data():
    """Ensure baseline demo officers, bidders, and tenders are present."""
    try:
        from seed_demo_data import seed_database
        seed_database(force=False)
    except Exception as exc:
        print(f"Warning: Demo database initialization notice: {exc}")

# ============================================================
# DATABASE STARTUP
# ============================================================

@app.on_event("startup")
def startup():
    # Alembic is the source of truth in deployed environments.
    # This fallback makes the demo usable if migrations have not yet been run.
    Base.metadata.create_all(bind=engine)
    _ensure_demo_data()

