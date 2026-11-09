from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from app.schemas import UserCreate, UserRead

VALID = {"username": "alice", "email": "alice@example.com", "password": "ClassroomPass123!"}

def test_identity_normalization_and_secret_repr():
    data = UserCreate(**{**VALID, "username": " Alice ", "email": " Alice@Example.COM "})
    assert data.username == "alice"
    assert str(data.email) == "alice@example.com"
    assert VALID["password"] not in repr(data)
    assert VALID["password"] not in data.model_dump_json()

@pytest.mark.parametrize("field,value", [
    ("username", "ab"), ("username", "a" * 51), ("username", "has space"),
    ("username", "bad!"), ("username", ""), ("username", None),
    ("email", "not-an-email"), ("email", "alice@"), ("email", ""), ("email", None),
    ("password", "short"), ("password", "a" * 11), ("password", "a" * 129),
    ("password", ""), ("password", None),
])
def test_invalid_input_is_rejected(field, value):
    with pytest.raises(ValidationError):
        UserCreate(**{**VALID, field: value})

@pytest.mark.parametrize("field", ["username", "email", "password"])
def test_required_fields(field):
    data = VALID.copy()
    data.pop(field)
    with pytest.raises(ValidationError):
        UserCreate(**data)

@pytest.mark.parametrize("password", ["a" * 12, "a" * 128, "\u00e9" * 12])
def test_password_boundaries(password):
    assert UserCreate(**{**VALID, "password": password}).password.get_secret_value() == password

def test_cannot_submit_a_password_hash_or_id():
    for field in ["password_hash", "id", "created_at"]:
        with pytest.raises(ValidationError):
            UserCreate(**VALID, **{field: "not allowed"})

def test_public_schema_serializes_attributes_without_passwords():
    source = SimpleNamespace(id=1, username="alice", email="alice@example.com",
        created_at=datetime.now(timezone.utc), password="secret", password_hash="private-hash")
    public = UserRead.model_validate(source).model_dump(mode="json")
    assert set(public) == {"id", "username", "email", "created_at"}
    assert "secret" not in str(public)
    assert "private-hash" not in str(public)
