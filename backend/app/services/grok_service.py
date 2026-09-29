from openai import OpenAI
from app.core.config import settings

client = OpenAI(
    api_key=settings.GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)


def analyze_compliance(requirement: str, document_text: str):

    prompt = f"""
You are an AI procurement compliance analyst.

Analyze the bidder document against the tender requirement.

Tender Requirement:
{requirement}

Bidder Document:
{document_text}

Return ONLY valid JSON:

{{
    "status": "PASS | FAIL | REVIEW",
    "reason": "short explanation",
    "evidence": "relevant evidence from the document",
    "confidence": 0.0
}}

Rules:
- PASS if the document clearly satisfies the requirement.
- FAIL if the document clearly does not satisfy it.
- REVIEW if evidence is missing or ambiguous.
- Do not invent information.
- Base the decision only on the provided document.
"""

    create_kwargs = {
        "model": settings.GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a procurement compliance AI."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    if "gpt-oss" in settings.GROQ_MODEL or "reason" in settings.GROQ_MODEL:
        create_kwargs["extra_body"] = {"include_reasoning": False}
    response = client.chat.completions.create(**create_kwargs)

    return response.choices[0].message.content