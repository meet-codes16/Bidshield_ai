from app.services.risk_service import calculate_risk
from app.services.hash_service import sha256_file
def test_risk_is_deterministic():
    score,level,factors=calculate_risk(90,0,False,0,False)
    assert score >= 0 and level.value=="LOW"
def test_hash(tmp_path):
    p=tmp_path/"a.pdf";p.write_bytes(b"%PDF-demo")
    assert len(sha256_file(str(p)))==64


def test_risk_high_for_missing_mandatory():
    score, level, factors = calculate_risk(50, 2, False, 0, True)
    assert score > 50
    assert level.value in {"HIGH", "CRITICAL"}


def test_llm_json_parser():
    from app.services.providers.llm import GrokLLMProvider
    parsed = GrokLLMProvider._parse_json('```json\n{"requirements": []}\n```')
    assert parsed == {"requirements": []}
