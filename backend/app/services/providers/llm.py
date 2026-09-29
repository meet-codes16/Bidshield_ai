from abc import ABC, abstractmethod
import json
import re
from app.core.config import settings


class LLMProvider(ABC):
    @abstractmethod
    def analyze(self, requirements, evidence_by_req):
        ...


class MockLLMProvider(LLMProvider):
    def analyze(self, requirements, evidence_by_req):
        out = []
        for r in requirements:
            evidence = evidence_by_req.get(str(r.id), [])
            joined = " ".join(e["text"] for e in evidence).lower()
            terms = [x.lower().strip(".,:;()") for x in r.requirement_text.split() if len(x) > 3]
            hit = sum(t in joined for t in terms) / max(1, len(terms))
            status = "PASS" if hit >= 0.5 and evidence else "REVIEW"
            out.append({
                "requirement_id": str(r.id),
                "status": status,
                "confidence": round(min(0.99, hit), 2),
                "evidence": evidence[:2],
                "explanation": "Mock LLM interpretation; evidence is limited to bidder-scoped chunks."
            })
        return {
            "overall_assessment": "Deterministic keyword and evidence alignment check completed.",
            "key_strengths": ["Document chunks extracted and mapped to requirements."],
            "key_concerns": ["Human procurement officer review required."],
            "clarifications_required": [],
            "requirements": out,
        }


class GrokLLMProvider(LLMProvider):
    def __init__(self):
        from openai import OpenAI
        if not settings.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not configured")
        self.client = OpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )

    @staticmethod
    def _parse_json(text: str):
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
            text = re.sub(r"\s*```$", "", text)
        return json.loads(text)

    def analyze(self, requirements, evidence_by_req):
        payload = {
            "requirements": [{"id": str(r.id), "text": r.requirement_text} for r in requirements],
            "evidence": {
                rid: [{"document_id": e.get("document_id"), "page": e["page"], "text": e["text"], "score": e.get("score", 0)}
                       for e in evidence]
                for rid, evidence in evidence_by_req.items()
            },
        }
        prompt = (
            'Return strict JSON only with this shape: '
            '{"overall_assessment":"summary of bidder compliance", '
            '"key_strengths":["..."], "key_concerns":["..."], "clarifications_required":["..."], '
            '"requirements":[{"requirement_id":"...","status":"PASS|FAIL|REVIEW","confidence":0.0,"evidence":[],"explanation":"..."}]}. '
            'Never invent evidence. Evidence must come only from the supplied evidence for that requirement. '
            'If evidence is missing or ambiguous, return REVIEW. '
            'A requirement should be PASS only when the supplied evidence clearly satisfies it. '
            'DATA:\n' + json.dumps(payload, ensure_ascii=False)
        )
        try:
            create_kwargs = {
                "model": settings.GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a procurement evidence analyst. Always return a valid JSON object matching the requested schema."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0,
                "max_tokens": 2048,
                "response_format": {"type": "json_object"},
            }
            if "gpt-oss" in settings.GROQ_MODEL or "reason" in settings.GROQ_MODEL:
                create_kwargs["extra_body"] = {"include_reasoning": False}
            resp = self.client.chat.completions.create(**create_kwargs)
        except Exception as exc:
            raise RuntimeError(f"Groq API request failed: {exc}") from exc
        parsed = self._parse_json(resp.choices[0].message.content or "{}")
        if not isinstance(parsed, dict) or not isinstance(parsed.get("requirements"), list):
            raise RuntimeError("LLM returned invalid compliance JSON")
        parsed.setdefault("overall_assessment", "AI compliance analysis completed.")
        parsed.setdefault("key_strengths", [])
        parsed.setdefault("key_concerns", [])
        parsed.setdefault("clarifications_required", [])
        return parsed


def get_llm_provider():
    return MockLLMProvider() if settings.MOCK_LLM else GrokLLMProvider()
