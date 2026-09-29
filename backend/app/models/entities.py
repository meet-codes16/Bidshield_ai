import enum, uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Boolean, DateTime, Float, Integer, ForeignKey, Index, JSON, TypeDecorator, CHAR, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None

class GUID(TypeDecorator):
    """UUID type that uses native UUID on PostgreSQL and CHAR(36) on SQLite."""
    impl = CHAR
    cache_ok = True
    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            # NOTE: was `PG_GUID()` -- undefined name (only PG_UUID is imported above),
            # which raised NameError the moment this branch ran on Postgres.
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))
    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        return str(value)
    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))

class EmbeddingType(TypeDecorator):
    """pgvector on PostgreSQL, JSON list on SQLite demo mode."""
    impl = JSON
    cache_ok = True
    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and Vector is not None:
            return dialect.type_descriptor(Vector(384))
        return dialect.type_descriptor(JSON)
from app.core.database import Base

def utcnow(): return datetime.now(timezone.utc)

class Role(str, enum.Enum):
    ADMIN="ADMIN"; OFFICER="OFFICER"; MINISTRY_OFFICER="MINISTRY_OFFICER"; BIDDER="BIDDER"; AUDITOR="AUDITOR"
class TenderStatus(str, enum.Enum):
    DRAFT="DRAFT"; PUBLISHED="PUBLISHED"; CLOSED="CLOSED"; UNDER_EVALUATION="UNDER_EVALUATION"; AWARDED="AWARDED"; CANCELLED="CANCELLED"
class BidStatus(str, enum.Enum):
    DRAFT="DRAFT"; SUBMITTED="SUBMITTED"; UNDER_REVIEW="UNDER_REVIEW"; COMPLIANT="COMPLIANT"; NON_COMPLIANT="NON_COMPLIANT"; CLARIFICATION_REQUIRED="CLARIFICATION_REQUIRED"; ACCEPTED="ACCEPTED"; REJECTED="REJECTED"
class VerificationStatus(str, enum.Enum):
    VERIFIED="VERIFIED"; UNVERIFIED="UNVERIFIED"; FAILED="FAILED"; REVIEW="REVIEW"; UNAVAILABLE="UNAVAILABLE"
class ProcessingStatus(str, enum.Enum):
    QUEUED="QUEUED"; PROCESSING="PROCESSING"; COMPLETED="COMPLETED"; FAILED="FAILED"
class ComplianceStatus(str, enum.Enum):
    PASS="PASS"; FAIL="FAIL"; REVIEW="REVIEW"
class RiskLevel(str, enum.Enum):
    LOW="LOW"; MEDIUM="MEDIUM"; HIGH="HIGH"; CRITICAL="CRITICAL"

class User(Base):
    __tablename__="users"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(default=Role.BIDDER, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    organization_id: Mapped[uuid.UUID|None] = mapped_column(GUID(), ForeignKey("organizations.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class Organization(Base):
    __tablename__="organizations"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class Bidder(Base):
    __tablename__="bidders"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    organization_name: Mapped[str] = mapped_column(String(255))
    gstin: Mapped[str|None] = mapped_column(String(32))
    pan: Mapped[str|None] = mapped_column(String(32))
    registration_number: Mapped[str|None] = mapped_column(String(64))
    address: Mapped[str|None] = mapped_column(Text)
    contact_information: Mapped[str|None] = mapped_column(String(255))
    verification_status: Mapped[VerificationStatus] = mapped_column(default=VerificationStatus.UNVERIFIED)

class Tender(Base):
    __tablename__="tenders"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    tender_number: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str|None] = mapped_column(Text)
    department: Mapped[str|None] = mapped_column(String(255))
    category: Mapped[str|None] = mapped_column(String(100))
    estimated_value: Mapped[float|None] = mapped_column(Float)
    publish_date: Mapped[datetime|None] = mapped_column(DateTime(timezone=True))
    submission_deadline: Mapped[datetime|None] = mapped_column(DateTime(timezone=True))
    status: Mapped[TenderStatus] = mapped_column(default=TenderStatus.DRAFT, index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class Requirement(Base):
    __tablename__="requirements"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    tender_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("tenders.id", ondelete="CASCADE"), index=True)
    requirement_text: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100), default="GENERAL")
    mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    verification_type: Mapped[str] = mapped_column(String(100), default="DOCUMENT")

class Bid(Base):
    __tablename__="bids"
    __table_args__ = (
        UniqueConstraint("tender_id", "bidder_id", name="uq_bids_tender_bidder"),
    )
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    tender_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("tenders.id"), index=True)
    bidder_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("bidders.id"), index=True)
    status: Mapped[BidStatus] = mapped_column(default=BidStatus.DRAFT, index=True)
    submitted_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True))
    ai_recommendation: Mapped[str|None] = mapped_column(String(50))
    officer_decision: Mapped[str|None] = mapped_column(String(50))
    officer_reason: Mapped[str|None] = mapped_column(Text)

class Document(Base):
    __tablename__="documents"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    bid_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("bids.id"), index=True)
    document_type: Mapped[str] = mapped_column(String(100), default="OTHER")
    original_filename: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(50), default="UPLOADED", index=True)
    storage_key: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class DocumentVersion(Base):
    __tablename__="document_versions"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    storage_key: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class DocumentChunk(Base):
    __tablename__="document_chunks"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    bidder_id: Mapped[uuid.UUID] = mapped_column(GUID(), index=True)
    tender_id: Mapped[uuid.UUID] = mapped_column(GUID(), index=True)
    page_number: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    embedding: Mapped[list|None] = mapped_column(EmbeddingType())

class Evidence(Base):
    __tablename__="evidence"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    compliance_result_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("compliance_results.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(GUID(), index=True)
    page_number: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)

class ComplianceResult(Base):
    __tablename__="compliance_results"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    bid_id: Mapped[uuid.UUID] = mapped_column(GUID(), index=True)
    requirement_id: Mapped[uuid.UUID] = mapped_column(GUID(), index=True)
    status: Mapped[ComplianceStatus] = mapped_column(default=ComplianceStatus.REVIEW, index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    explanation: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(50), default="RULE+RAG+LLM")
    ai_recommendation: Mapped[str] = mapped_column(String(50), default="REVIEW")

class RiskAssessment(Base):
    __tablename__="risk_assessments"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    bid_id: Mapped[uuid.UUID] = mapped_column(GUID(), unique=True, index=True)
    risk_score: Mapped[float] = mapped_column(Float)
    risk_level: Mapped[RiskLevel] = mapped_column(index=True)
    factors: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class VerificationRecord(Base):
    __tablename__="verification_records"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(GUID(), index=True)
    integrity_status: Mapped[VerificationStatus] = mapped_column(default=VerificationStatus.VERIFIED)
    digital_signature_status: Mapped[VerificationStatus] = mapped_column(default=VerificationStatus.UNAVAILABLE)
    certificate_status: Mapped[VerificationStatus] = mapped_column(default=VerificationStatus.UNAVAILABLE)
    issuer_status: Mapped[VerificationStatus] = mapped_column(default=VerificationStatus.UNAVAILABLE)
    authority_status: Mapped[VerificationStatus] = mapped_column(default=VerificationStatus.UNAVAILABLE)
    cross_field_status: Mapped[VerificationStatus] = mapped_column(default=VerificationStatus.REVIEW)
    overall_status: Mapped[VerificationStatus] = mapped_column(default=VerificationStatus.REVIEW)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class AuditLog(Base):
    __tablename__="audit_logs"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    actor_id: Mapped[uuid.UUID|None] = mapped_column(GUID(), index=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    entity_type: Mapped[str] = mapped_column(String(100))
    entity_id: Mapped[str] = mapped_column(String(100), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    ip_address: Mapped[str|None] = mapped_column(String(64))
    previous_hash: Mapped[str|None] = mapped_column(String(64))
    current_hash: Mapped[str] = mapped_column(String(64), index=True)

class AIAnalysis(Base):
    __tablename__ = "ai_analyses"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    bid_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("bids.id", ondelete="CASCADE"), unique=True, index=True)
    overall_assessment: Mapped[str] = mapped_column(Text)
    key_strengths: Mapped[list] = mapped_column(JSON, default=list)
    key_concerns: Mapped[list] = mapped_column(JSON, default=list)
    clarifications_required: Mapped[list] = mapped_column(JSON, default=list)
    recommendation_context: Mapped[str|None] = mapped_column(Text)
    raw_response: Mapped[dict] = mapped_column(JSON, default=dict)
    model_name: Mapped[str] = mapped_column(String(100), default="llama-3.3-70b-versatile")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class ProcessingJob(Base):
    __tablename__="processing_jobs"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    job_type: Mapped[str] = mapped_column(String(100), index=True)
    entity_id: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[ProcessingStatus] = mapped_column(default=ProcessingStatus.QUEUED, index=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str|None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

Index("ix_bids_tender_bidder", Bid.tender_id, Bid.bidder_id)
Index("ix_chunks_scope", DocumentChunk.tender_id, DocumentChunk.bidder_id, DocumentChunk.document_id)
