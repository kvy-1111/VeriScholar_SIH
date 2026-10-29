from app.services.risk import calculate_risk_score


def test_risk_score_thresholds():
    r = calculate_risk_score("potential_duplicate", True, True, 2, True)
    assert r["score"] >= 80
    assert r["category"] == "Critical"


def test_risk_score_low():
    r = calculate_risk_score("valid_format", False, False, 0, False)
    assert r == {"score": 0, "category": "Low", "reasons": []}
