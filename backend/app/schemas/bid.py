from pydantic import BaseModel
class BidCreate(BaseModel): bidder_id: str|None=None
class DecisionRequest(BaseModel): decision: str; reason: str
