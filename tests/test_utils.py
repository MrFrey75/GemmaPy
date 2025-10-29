import pytest
from auth import hash_password, verify_password, generate_token, decode_token

def test_hash_password():
    password = 'testpassword'
    hashed = hash_password(password)
    assert hashed != password
    assert len(hashed) > 0

def test_verify_password_success():
    password = 'testpassword'
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True

def test_verify_password_failure():
    password = 'testpassword'
    hashed = hash_password(password)
    assert verify_password('wrongpassword', hashed) is False

def test_generate_token():
    token = generate_token(1, 'testuser', False)
    assert isinstance(token, str)
    assert len(token) > 0

def test_decode_token():
    token = generate_token(1, 'testuser', False)
    payload = decode_token(token)
    assert payload is not None
    assert payload['user_id'] == 1
    assert payload['username'] == 'testuser'
    assert payload['is_admin'] is False

def test_decode_invalid_token():
    payload = decode_token('invalid.token.here')
    assert payload is None

def test_admin_token():
    token = generate_token(2, 'admin', True)
    payload = decode_token(token)
    assert payload is not None
    assert payload['is_admin'] is True
