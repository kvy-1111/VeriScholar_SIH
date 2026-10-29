import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.core.rate_limiter import rate_limit_public_verify
from app.models.models import QRCredential, StudentRecord
from app.services.qr import create_credential_payload, verify_signed_payload

router = APIRouter(prefix="/qr", tags=["qr"])


@router.post("/create")
def create_qr(payload: dict, db: Session = Depends(get_db), user=Depends(require_roles("college_admin", "regulatory_admin"))):
    student = db.query(StudentRecord).filter(StudentRecord.id == payload["student_record_id"]).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    credential_ref = secrets.token_hex(12)
    signed = create_credential_payload(credential_ref, student.student_name, str(student.institution_id), payload.get("expires_minutes", 1440))
    cred = QRCredential(
        credential_ref=credential_ref,
        student_record_id=student.id,
        signed_payload=signed["signed_payload"],
        expires_at=datetime.fromisoformat(signed["payload"]["expires_at"]),
    )
    db.add(cred)
    db.commit()
    return {
        "credential_ref": cred.credential_ref,
        "signed_payload": cred.signed_payload,
        "disclaimer": "VeriScholar-issued demonstration credential. Not an official APAAR credential.",
    }


@router.get("/verify/{credential_ref}", dependencies=[Depends(rate_limit_public_verify)])
def verify_qr(credential_ref: str, request: Request, db: Session = Depends(get_db)):
    cred = db.query(QRCredential).filter(QRCredential.credential_ref == credential_ref).first()
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")
    if cred.revoked:
        raise HTTPException(status_code=410, detail="Credential revoked")

    ok, message, payload = verify_signed_payload(cred.signed_payload)
    if not ok:
        raise HTTPException(status_code=400, detail=message)
    if datetime.now(timezone.utc) > cred.expires_at.replace(tzinfo=timezone.utc):
        raise HTTPException(status_code=400, detail="Credential expired")

    return {
        "credential_ref": payload["credential_ref"],
        "student_name": payload["student_name"],
        "institution": payload["institution"],
        "issuer": payload["issuer"],
        "status": "valid",
    }


@router.post("/revoke/{credential_ref}")
def revoke_credential(credential_ref: str, db: Session = Depends(get_db), user=Depends(require_roles("regulatory_admin"))):
    cred = db.query(QRCredential).filter(QRCredential.credential_ref == credential_ref).first()
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")
    cred.revoked = True
    db.commit()
    return {"detail": "Credential revoked"}
