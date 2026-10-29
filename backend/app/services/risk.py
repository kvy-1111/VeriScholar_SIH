from app.models.models import VerificationStatus

DEFAULT_WEIGHTS = {
    "potential_duplicate": 30,
    "above_intake": 30,
    "missing_fields": 20,
    "identity_mismatch": 25,
    "repeated_quality_issues": 15,
    "cross_institution_unusual": 10,
}


def category_for_score(score: int) -> str:
    if score >= 80:
        return "Critical"
    if score >= 60:
        return "High"
    if score >= 35:
        return "Medium"
    return "Low"


def calculate_risk_score(
    verification_status: str,
    is_above_intake: bool,
    has_missing_fields: bool,
    repeated_quality_issues: int,
    cross_institution_unusual: bool,
    weights: dict[str, int] | None = None,
):
    weights = weights or DEFAULT_WEIGHTS
    score = 0
    reasons: list[str] = []

    if verification_status == VerificationStatus.potential_duplicate.value:
        score += weights["potential_duplicate"]
        reasons.append("Potential duplicate admissions")
    if verification_status == VerificationStatus.identity_mismatch.value:
        score += weights["identity_mismatch"]
        reasons.append("Conflicting student details")
    if is_above_intake:
        score += weights["above_intake"]
        reasons.append("Admissions above approved intake")
    if has_missing_fields:
        score += weights["missing_fields"]
        reasons.append("Missing mandatory fields")
    if repeated_quality_issues > 1:
        score += weights["repeated_quality_issues"]
        reasons.append("Repeated data-quality problems")
    if cross_institution_unusual:
        score += weights["cross_institution_unusual"]
        reasons.append("Unusual cross-institution pattern")

    score = min(score, 100)
    return {"score": score, "category": category_for_score(score), "reasons": reasons}
