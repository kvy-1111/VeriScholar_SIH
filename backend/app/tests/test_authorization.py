from app.core.security import get_password_hash
from app.models.models import Role, User


def test_student_cannot_access_regulatory_dashboard(client, db_session):
    user = User(email="student@test.com", password_hash=get_password_hash("Pass@123"), role=Role.student, is_active=True)
    db_session.add(user)
    db_session.commit()

    login = client.post("/api/v1/auth/login", json={"email": "student@test.com", "password": "Pass@123"})
    token = login.json()["access_token"]

    resp = client.get("/api/v1/analytics/dashboard", headers={"Authorization": f"******"})
    assert resp.status_code == 403
