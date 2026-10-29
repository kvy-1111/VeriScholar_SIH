from app.core.security import get_password_hash
from app.models.models import Role, User


def test_login_and_me(client, db_session):
    user = User(email="admin@test.com", password_hash=get_password_hash("Pass@123"), role=Role.regulatory_admin, is_active=True)
    db_session.add(user)
    db_session.commit()

    resp = client.post("/api/v1/auth/login", json={"email": "admin@test.com", "password": "Pass@123"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"******"})
    assert me.status_code == 200
    assert me.json()["email"] == "admin@test.com"
