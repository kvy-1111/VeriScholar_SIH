from sqlalchemy import func
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.models import Institution, InvestigationCase, RiskAssessment, StudentRecord

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user=Depends(require_roles("regulatory_admin"))):
    total_institutions = db.query(func.count(Institution.id)).scalar() or 0
    total_records = db.query(func.count(StudentRecord.id)).scalar() or 0
    pending_cases = db.query(func.count(InvestigationCase.id)).filter(InvestigationCase.status.in_(["pending", "under_review"])).scalar() or 0
    potential_duplicates = db.query(func.count(StudentRecord.id)).filter(StudentRecord.verification_status == "potential_duplicate").scalar() or 0
    high_risk = db.query(func.count(RiskAssessment.id)).filter(RiskAssessment.category.in_(["High", "Critical"])).scalar() or 0

    return {
        "summary": {
            "total_institutions": total_institutions,
            "total_records": total_records,
            "pending_cases": pending_cases,
            "potential_duplicates": potential_duplicates,
            "high_risk_cases": high_risk,
        },
        "note": "All dashboard values are backend-computed using synthetic demo-safe data.",
    }
