from app.security import hash_password, verify_password

def test_hash_is_argon2id_and_not_plaintext():
    password = "A demonstration password"
    stored = hash_password(password)
    assert stored.startswith("$argon2id$")
    assert password not in stored
    assert verify_password(password, stored)

def test_wrong_password_is_rejected():
    assert not verify_password("wrong password", hash_password("correct password"))

def test_each_hash_uses_a_different_salt():
    first = hash_password("same password")
    second = hash_password("same password")
    assert first != second
    assert verify_password("same password", first)
    assert verify_password("same password", second)

def test_malformed_hash_is_rejected():
    assert not verify_password("password", "not-a-password-hash")

def test_long_unicode_password_is_not_silently_truncated():
    password = "\u00e9" * 100
    stored = hash_password(password)
    assert verify_password(password, stored)
    assert not verify_password(password[:72], stored)
