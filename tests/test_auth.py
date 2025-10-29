import pytest

def test_login_success(client):
    response = client.post('/api/login', json={
        'username': 'testuser',
        'password': 'testpass'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'token' in data
    assert data['user']['username'] == 'testuser'
    assert data['user']['is_admin'] is False

def test_login_invalid_credentials(client):
    response = client.post('/api/login', json={
        'username': 'testuser',
        'password': 'wrongpass'
    })
    assert response.status_code == 401
    data = response.get_json()
    assert 'error' in data

def test_login_missing_username(client):
    response = client.post('/api/login', json={
        'password': 'testpass'
    })
    assert response.status_code == 400

def test_login_missing_password(client):
    response = client.post('/api/login', json={
        'username': 'testuser'
    })
    assert response.status_code == 400

def test_login_nonexistent_user(client):
    response = client.post('/api/login', json={
        'username': 'nonexistent',
        'password': 'testpass'
    })
    assert response.status_code == 401
