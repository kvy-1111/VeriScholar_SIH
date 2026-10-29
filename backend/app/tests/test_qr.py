from app.services.qr import create_credential_payload, verify_signed_payload


def test_qr_signature_and_expiry():
    data = create_credential_payload("abc123", "Demo Student", "Demo College", expires_minutes=1)
    ok, message, payload = verify_signed_payload(data["signed_payload"])
    assert ok is True
    assert payload["credential_ref"] == "abc123"
