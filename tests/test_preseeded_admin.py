import pytest

def test_default_admin_login(client):
    response = client.post('/api/login', json={
        'username': 'admin',
        'password': 'pass123'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'token' in data
    assert data['user']['username'] == 'admin'
    assert data['user']['is_admin'] is True

def test_default_admin_has_privileges(client, admin_token):
    response = client.get('/api/admin/users', headers={
        'Authorization': f'Bearer {admin_token}'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'users' in data
    
    # Check admin user is in the list
    admin_users = [u for u in data['users'] if u['username'] == 'admin']
    assert len(admin_users) == 1
    assert admin_users[0]['is_admin'] == 1

def test_default_admin_can_create_users(client, admin_token):
    response = client.post('/api/admin/users',
        json={'username': 'newuser', 'password': 'newpass123'},
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data['username'] == 'newuser'

def test_wrong_default_admin_password(client):
    response = client.post('/api/login', json={
        'username': 'admin',
        'password': 'wrongpassword'
    })
    assert response.status_code == 401
