import pytest

def test_get_users_requires_admin(client, auth_token):
    response = client.get('/api/admin/users', headers={
        'Authorization': f'Bearer {auth_token}'
    })
    assert response.status_code == 403

def test_get_users_with_admin(client, admin_token):
    response = client.get('/api/admin/users', headers={
        'Authorization': f'Bearer {admin_token}'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'users' in data
    # Should have admin (preseeded) + testuser (from fixture)
    assert len(data['users']) >= 2

def test_create_user_requires_admin(client, auth_token):
    response = client.post('/api/admin/users',
        json={'username': 'newuser', 'password': 'newpass'},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 403

def test_create_user_with_admin(client, admin_token):
    response = client.post('/api/admin/users',
        json={'username': 'newuser', 'password': 'newpass'},
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data['username'] == 'newuser'
    assert 'id' in data

def test_create_user_duplicate(client, admin_token):
    client.post('/api/admin/users',
        json={'username': 'duplicate', 'password': 'pass'},
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    
    response = client.post('/api/admin/users',
        json={'username': 'duplicate', 'password': 'pass'},
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    assert response.status_code == 400

def test_create_admin_user(client, admin_token):
    response = client.post('/api/admin/users',
        json={'username': 'newadmin', 'password': 'adminpass', 'is_admin': True},
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    assert response.status_code == 201

def test_create_user_missing_fields(client, admin_token):
    response = client.post('/api/admin/users',
        json={'username': 'incomplete'},
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    assert response.status_code == 400
