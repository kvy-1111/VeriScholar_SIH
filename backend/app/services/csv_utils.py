from io import StringIO

import pandas as pd

REQUIRED_COLUMNS = [
    "internal_record_id",
    "apaar_ref",
    "student_name",
    "date_of_birth",
    "institution_id",
    "course_id",
    "academic_year",
    "admission_date",
]


def parse_csv_with_validation(content: bytes):
    df = pd.read_csv(StringIO(content.decode("utf-8")))
    errors: list[dict] = []
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            errors.append({"row": 0, "field": col, "error": "Missing required column"})

    if errors:
        return [], errors

    valid_rows = []
    for idx, row in df.iterrows():
        row_errors = []
        for col in REQUIRED_COLUMNS:
            if pd.isna(row[col]) or str(row[col]).strip() == "":
                row_errors.append({"row": int(idx + 2), "field": col, "error": "Missing value"})
        if row_errors:
            errors.extend(row_errors)
        else:
            valid_rows.append({k: str(row[k]) if k in ["internal_record_id", "apaar_ref", "student_name", "academic_year"] else row[k] for k in REQUIRED_COLUMNS})

    return valid_rows, errors
