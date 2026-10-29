import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

from app.core.config import settings


def _sign(payload: str) -> str:
    return hmac.new(settings.jwt_secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()


def create_credential_payload(credential_ref: str, student_name: str, institution: str, expires_minutes: int = 60 * 24):
    payload = {
        "credential_ref": credential_ref,
        "student_name": student_name,
        "institution": institution,
        "issuer": "VeriScholar (Demo Credential)",
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)).isoformat(),
    }
    payload_str = json.dumps(payload, sort_keys=True)
    signature = _sign(payload_str)
    return {"payload": payload, "signed_payload": f"{payload_str}.{signature}"}


def verify_signed_payload(signed_payload: str):
    try:
        payload_str, signature = signed_payload.rsplit(".", 1)
    except ValueError:
        return False, "Malformed payload", None

    expected = _sign(payload_str)
    if not hmac.compare_digest(signature, expected):
        return False, "Invalid signature", None

    payload = json.loads(payload_str)
    expires_at = datetime.fromisoformat(payload["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        return False, "Credential expired", payload

    return True, "Credential valid", payload
