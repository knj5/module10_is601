from datetime import datetime, timezone
import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from app.models import User
from app.security import hash_password, verify_password

pytestmark = pytest.mark.integration
VALID = {"username": "alice", "email": "alice@example.com", "password": "ClassroomPass123!"}

def test_real_postgresql_is_used(db_session):
    assert "PostgreSQL" in db_session.execute(text("SELECT version()")).scalar_one()

def test_register_persists_hash_and_hides_secrets(user_client, db_session):
    before = datetime.now(timezone.utc)
    response = user_client.post("/users", json=VALID)
    assert response.status_code == 201
    public = response.json()
    assert set(public) == {"id", "username", "email", "created_at"}
    assert public["username"] == "alice"
    stored = db_session.get(User, public["id"])
    assert stored.password_hash.startswith("$argon2id$")
    assert verify_password(VALID["password"], stored.password_hash)
    assert stored.created_at.tzinfo is not None
    assert stored.created_at <= datetime.now(timezone.utc)
    assert stored.created_at >= before.replace(microsecond=0)
    assert stored.password_hash not in response.text
    assert VALID["password"] not in response.text

@pytest.mark.parametrize("field,value", [("username", "alice"), ("email", "alice@example.com")])
def test_api_rejects_duplicate_identity_and_session_recovers(user_client, db_session, field, value):
    assert user_client.post("/users", json=VALID).status_code == 201
    other = {**VALID, "username": "bob", "email": "bob@example.com", field: value}
    response = user_client.post("/users", json=other)
    assert response.status_code == 409
    assert "password" not in response.text
    assert db_session.scalar(select(func.count()).select_from(User)) == 1
    # Rollback after a uniqueness failure must leave the session usable.
    assert user_client.post("/users", json={**VALID, "username": "charlie", "email": "charlie@example.com"}).status_code == 201

@pytest.mark.parametrize("change", [
    {"username": " ALICE ", "email": "other@example.com"},
    {"username": "other", "email": "ALICE@EXAMPLE.COM"},
])
def test_normalized_duplicates_are_rejected(user_client, change):
    assert user_client.post("/users", json=VALID).status_code == 201
    assert user_client.post("/users", json={**VALID, **change}).status_code == 409

@pytest.mark.parametrize("email", ["not-an-email", "alice@", "", "@example.com"])
def test_invalid_email_never_reaches_database(user_client, db_session, email):
    response = user_client.post("/users", json={**VALID, "email": email})
    assert response.status_code == 422
    assert db_session.scalar(select(func.count()).select_from(User)) == 0
    assert VALID["password"] not in response.text

@pytest.mark.parametrize("change", [
    {"password": "short"}, {"password": "x" * 129}, {"password_hash": "injected"},
    {"username": "!"}, {"id": 99},
])
def test_invalid_registration_rejected_without_insertion(user_client, db_session, change):
    response = user_client.post("/users", json={**VALID, **change})
    assert response.status_code == 422
    assert db_session.scalar(select(func.count()).select_from(User)) == 0
    assert VALID["password"] not in response.text
    assert change.get("password", VALID["password"]) not in response.text

@pytest.mark.parametrize("field", ["username", "email"])
def test_database_uniqueness_cannot_be_bypassed(db_session, field):
    stored_hash = hash_password(VALID["password"])
    db_session.add(User(username="alice", email="alice@example.com", password_hash=stored_hash))
    db_session.commit()
    duplicate = {"username": "bob", "email": "bob@example.com", "password_hash": stored_hash}
    duplicate[field] = VALID[field]
    db_session.add(User(**duplicate))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
    assert db_session.scalar(select(func.count()).select_from(User)) == 1

@pytest.mark.parametrize("field", ["username", "email", "password_hash"])
def test_database_not_null_constraints(db_session, field):
    data = {"username": "alice", "email": "alice@example.com", "password_hash": "test-hash"}
    data[field] = None
    db_session.add(User(**data))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

def test_different_users_can_have_same_password(user_client, db_session):
    first = user_client.post("/users", json=VALID)
    second = user_client.post("/users", json={**VALID, "username": "bob", "email": "bob@example.com"})
    assert first.status_code == second.status_code == 201
    a = db_session.get(User, first.json()["id"])
    b = db_session.get(User, second.json()["id"])
    assert a.password_hash != b.password_hash

def test_health_checks_database(user_client):
    assert user_client.get("/health").json() == {"status": "ok", "database": "connected"}
