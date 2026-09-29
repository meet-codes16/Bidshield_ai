from datetime import datetime
from pydantic import BaseModel
from app.models.entities import TenderStatus
class TenderCreate(BaseModel):
    tender_number: str; title: str; description: str|None=None; department: str|None=None; category: str|None=None
    estimated_value: float|None=None; publish_date: datetime|None=None; submission_deadline: datetime|None=None
class RequirementCreate(BaseModel):
    requirement_text: str; category: str="GENERAL"; mandatory: bool=True; weight: float=1.0; verification_type: str="DOCUMENT"
class TenderOut(BaseModel):
    id: str; tender_number: str; title: str; status: TenderStatus
