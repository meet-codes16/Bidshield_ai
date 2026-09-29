from pydantic import BaseModel, Field
from typing import Any

class TenderCreate(BaseModel):
    title: str
    reference_no: str
    issuing_authority: str

class RequirementCreate(BaseModel):
    requirements: list[str] = Field(min_length=1)

class VerificationResult(BaseModel):
    document_id: str
    sha256: str
    digital_signature_status: str
    authority_status: str
    authenticity_status: str
    authenticity_score: float
    flags: list[str]

class AnalysisRequest(BaseModel):
    tender_id: str
    document_id: str

class AnalysisResult(BaseModel):
    tender_id: str
    document_id: str
    compliance_score: float
    authenticity_score: float
    confidence_score: float
    decision: str
    risk_flags: list[str]
    evidence: list[dict[str, Any]]
