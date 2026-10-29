from app.services.verification import detect_duplicates


def test_detect_duplicates():
    rows = [
        {"apaar_ref": "APAAR-DEMO-001"},
        {"apaar_ref": "APAAR-DEMO-002"},
        {"apaar_ref": "APAAR-DEMO-001"},
    ]
    assert detect_duplicates(rows) == {"APAAR-DEMO-001"}
