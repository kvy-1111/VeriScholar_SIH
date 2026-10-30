# VeriScholar prototype

## Run (Python 3.10+)
    pip install -r requirements.txt
    uvicorn app:app --reload
Open http://127.0.0.1:8000  (API docs: /docs). First start creates verischolar.db, signing.key and sample_upload.csv. Logo files are in static/.
To reset the demo: stop the server and delete verischolar.db, then start again.

## Register
On the sign-in page choose Create an account. Public sign-up is for institution (pick your college) and verifier accounts; AICTE and reviewer accounts stay admin-created. Passwords are stored as salted PBKDF2 hashes in the users table. New accounts are active immediately in this prototype (a real deployment would add AICTE approval for institutions).

## Search
Every page has a search box in the nav bar (press / to focus). Dashboard, Review queue, Audit log, Upload history, rejected rows and Recent verifications filter instantly; Students searches name, APAAR ID, college and programme on the server.

## Logins
aicte / aicte123 | inst1..inst5 / inst123 | reviewer / rev123 | verifier / ver123

## Demo script (5 minutes)
1. Log in as aicte: dashboard shows colleges ranked by compliance score (I3 over intake, I2 supernumerary, I5 NRI cap, I4 inconsistent flags).
2. Review queue: see the cross-college duplicate (CROSS_DUP) and the fuzzy name+DOB match (FUZZY_DUP), each with a reason.
3. Log out, log in as inst1, Upload, choose sample_upload.csv: 8 rows: 5 rejected with exact reasons (bad check digit, short ID, missing name, duplicate in file, bad date) and 3 accepted. One accepted row is a student already enrolled at I3, so it creates a new CROSS_DUP flag.
4. Log in as aicte again: the Review queue now has the new cross-college flag for I1.
5. As reviewer: mark a flag Verified / Keep flagged / Reject with a note.
6. As inst1, Students: Issue record, copy token. As verifier, Verify tab: paste token, see the minimal result (no name, DOB or ID).
7. As aicte: Students, Tamper on that student, then verify again: fails. Or as inst1 revoke the record: fails.
8. As aicte, Audit log: Verify chain integrity (intact), click Demo tamper, chain breaks at entry 2.

## Mocked vs real
MOCKED: ABC/APAAR registry lookup (registry_lookup in app.py), AICTE portal sync (not connected), OAuth2 (simple token login).
DEMO RULE: the 12-digit Luhn check digit is NOT the official APAAR spec; switch off with RULES["demo_checkdigit"].
REAL: validation, duplicate/fuzzy/intake/cap/consistency rules (RULES dict), versioned history, hash-chained audit log, Ed25519 signed records with expiry, revocation and tamper check, consent check, minimal disclosure, role and college-level access control.

## Not built yet (honest list)
React/Tailwind (this uses plain HTML/JS, no build step), PostgreSQL swap, field-level AES encryption, 50k-row chunked upload with progress bar, web form entry, per-field consent, webhooks, PDF reports, year-on-year trends, certificate API, WebSocket live updates (polling instead).
