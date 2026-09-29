from app.models.entities import VerificationStatus
def verify_integrity(expected_hash, actual_hash):
    return VerificationStatus.VERIFIED if expected_hash==actual_hash else VerificationStatus.FAILED
def overall_status(integrity,authority):
    if integrity==VerificationStatus.FAILED: return VerificationStatus.FAILED
    if authority==VerificationStatus.VERIFIED: return VerificationStatus.VERIFIED
    return VerificationStatus.REVIEW
