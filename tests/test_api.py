import pytest

def test_get_data_requires_auth(client):
    response = client.get('/api/data')
    assert response.status_code == 401

def test_get_data_with_auth(client, auth_token):
    response = client.get('/api/data', headers={
        'Authorization': f'Bearer {auth_token}'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'data' in data
    assert isinstance(data['data'], list)

def test_post_data_requires_auth(client):
    response = client.post('/api/data', json={'content': 'test'})
    assert response.status_code == 401

def test_post_data_with_auth(client, auth_token):
    response = client.post('/api/data', 
        json={'content': 'Test content'},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 201
    data = response.get_json()
    assert 'id' in data
    assert data['message'] == 'Data created successfully'

def test_post_data_missing_content(client, auth_token):
    response = client.post('/api/data', 
        json={},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 400

def test_get_data_after_post(client, auth_token):
    # Create data
    client.post('/api/data', 
        json={'content': 'Test content'},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    # Retrieve data
    response = client.get('/api/data', headers={
        'Authorization': f'Bearer {auth_token}'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['data']) == 1
    assert data['data'][0]['content'] == 'Test content'
