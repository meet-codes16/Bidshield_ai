from app.models.entities import RiskLevel
def calculate_risk(compliance_score, missing_mandatory, authenticity_review, contradictions, low_confidence):
    score=0.0
    factors={}
    factors["compliance"]=max(0,100-compliance_score)*0.45
    factors["missing_mandatory"]=min(25,missing_mandatory*10)
    factors["authenticity"]=15 if authenticity_review else 0
    factors["contradictions"]=min(15,contradictions*7.5)
    factors["low_confidence"]=10 if low_confidence else 0
    score=min(100,sum(factors.values()))
    level=RiskLevel.LOW if score<25 else RiskLevel.MEDIUM if score<50 else RiskLevel.HIGH if score<75 else RiskLevel.CRITICAL
    return round(score,2),level,factors
