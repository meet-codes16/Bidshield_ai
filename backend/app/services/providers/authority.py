from abc import ABC, abstractmethod
from app.models.entities import VerificationStatus
class AuthorityVerificationProvider(ABC):
    @abstractmethod
    def verify(self, field_type: str, value: str): ...
class MockAuthorityProvider(AuthorityVerificationProvider):
    def verify(self, field_type,value):
        return {"status":VerificationStatus.UNAVAILABLE.value,"provider":"MOCK","reason":"No official authority was contacted."}
class RealAuthorityProvider(AuthorityVerificationProvider):
    def verify(self, field_type,value):
        raise NotImplementedError("Connect an authorized government API here; do not infer official verification.")
