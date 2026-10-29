from app.services.csv_utils import parse_csv_with_validation


def test_csv_invalid_rows():
    content = b"internal_record_id,apaar_ref,student_name,date_of_birth,institution_id,course_id,academic_year,admission_date\n1,,X,2000-01-01,1,1,2026-27,2026-06-01\n"
    valid_rows, errors = parse_csv_with_validation(content)
    assert valid_rows == []
    assert any(e["field"] == "apaar_ref" for e in errors)
