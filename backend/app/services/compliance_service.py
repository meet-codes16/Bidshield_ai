from app.models.entities import ComplianceStatus
class ComplianceEngine:
    def evaluate(self, requirements, llm_results, evidence_by_req):
        results=[]
        for r in requirements:
            item=next((x for x in llm_results if x["requirement_id"]==str(r.id)),None)
            ev=evidence_by_req.get(str(r.id),[])
            if not ev: status=ComplianceStatus.REVIEW; conf=0.0; expl="Evidence unavailable; human review required."
            else:
                raw=(item or {}).get("status","REVIEW")
                status=ComplianceStatus(raw) if raw in ComplianceStatus._value2member_map_ else ComplianceStatus.REVIEW
                conf=float((item or {}).get("confidence",0))
                expl=(item or {}).get("explanation","Evidence retrieved for officer review.")
            results.append((r,status,conf,expl))
        mandatory=[x for x in results if x[0].mandatory]
        weighted=sum(r.weight for r,_,_,_ in results) or 1
        passed=sum(r.weight for r,s,_,_ in results if s==ComplianceStatus.PASS)
        mandatory_score=100*sum(r.weight for r,s,_,_ in mandatory if s==ComplianceStatus.PASS)/(sum(r.weight for r,_,_,_ in mandatory) or 1)
        return results, round(100*passed/weighted,2), round(mandatory_score,2)
