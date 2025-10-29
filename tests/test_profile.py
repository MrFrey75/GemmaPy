import pytest

def test_get_profile(client, auth_token):
    """Test getting user profile"""
    response = client.get('/api/profile', headers={
        'Authorization': f'Bearer {auth_token}'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'profile' in data
    assert data['profile']['username'] == 'testuser'
    assert 'id' in data['profile']
    assert 'created_at' in data['profile']

def test_get_profile_requires_auth(client):
    """Test that getting profile requires authentication"""
    response = client.get('/api/profile')
    assert response.status_code == 401

def test_update_profile_email(client, auth_token):
    """Test updating user email"""
    response = client.put('/api/profile',
        json={'email': 'test@example.com'},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == 'Profile updated successfully'
    assert data['profile']['email'] == 'test@example.com'

def test_update_profile_full_name(client, auth_token):
    """Test updating user full name"""
    response = client.put('/api/profile',
        json={'full_name': 'Test User'},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['profile']['full_name'] == 'Test User'

def test_update_profile_bio(client, auth_token):
    """Test updating user bio"""
    response = client.put('/api/profile',
        json={'bio': 'This is my bio'},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['profile']['bio'] == 'This is my bio'

def test_update_profile_multiple_fields(client, auth_token):
    """Test updating multiple profile fields at once"""
    response = client.put('/api/profile',
        json={
            'email': 'user@test.com',
            'full_name': 'John Doe',
            'bio': 'Software developer'
        },
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['profile']['email'] == 'user@test.com'
    assert data['profile']['full_name'] == 'John Doe'
    assert data['profile']['bio'] == 'Software developer'

def test_update_profile_no_fields(client, auth_token):
    """Test updating profile with no fields"""
    response = client.put('/api/profile',
        json={},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 400

def test_update_profile_requires_auth(client):
    """Test that updating profile requires authentication"""
    response = client.put('/api/profile',
        json={'email': 'test@example.com'}
    )
    assert response.status_code == 401

def test_change_password_success(client, auth_token):
    """Test successfully changing password"""
    response = client.put('/api/profile/password',
        json={
            'current_password': 'testpass',
            'new_password': 'newpass123'
        },
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == 'Password changed successfully'
    
    # Verify can login with new password
    login_response = client.post('/api/login', json={
        'username': 'testuser',
        'password': 'newpass123'
    })
    assert login_response.status_code == 200

def test_change_password_wrong_current(client, auth_token):
    """Test changing password with wrong current password"""
    response = client.put('/api/profile/password',
        json={
            'current_password': 'wrongpass',
            'new_password': 'newpass123'
        },
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 401
    data = response.get_json()
    assert 'incorrect' in data['error'].lower()

def test_change_password_too_short(client, auth_token):
    """Test changing password with too short new password"""
    response = client.put('/api/profile/password',
        json={
            'current_password': 'testpass',
            'new_password': '123'
        },
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 400
    data = response.get_json()
    assert '6 characters' in data['error']

def test_change_password_missing_fields(client, auth_token):
    """Test changing password with missing fields"""
    response = client.put('/api/profile/password',
        json={'current_password': 'testpass'},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 400

def test_change_password_requires_auth(client):
    """Test that changing password requires authentication"""
    response = client.put('/api/profile/password',
        json={
            'current_password': 'testpass',
            'new_password': 'newpass123'
        }
    )
    assert response.status_code == 401

def test_delete_profile_success(client):
    """Test successfully deleting user account"""
    # Create a new user for deletion
    from database import get_db_connection
    from auth import hash_password
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)',
            ('deleteuser', hash_password('deletepass'), 0)
        )
        conn.commit()
    
    # Login as the new user
    login_response = client.post('/api/login', json={
        'username': 'deleteuser',
        'password': 'deletepass'
    })
    token = login_response.get_json()['token']
    
    # Delete account
    response = client.delete('/api/profile',
        json={'password': 'deletepass'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == 'Account deleted successfully'
    
    # Verify cannot login anymore
    login_response = client.post('/api/login', json={
        'username': 'deleteuser',
        'password': 'deletepass'
    })
    assert login_response.status_code == 401

def test_delete_profile_wrong_password(client, auth_token):
    """Test deleting account with wrong password"""
    response = client.delete('/api/profile',
        json={'password': 'wrongpass'},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 401

def test_delete_profile_missing_password(client, auth_token):
    """Test deleting account without password"""
    response = client.delete('/api/profile',
        json={},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 400

def test_delete_profile_admin_blocked(client, admin_token):
    """Test that admin accounts cannot be deleted"""
    response = client.delete('/api/profile',
        json={'password': 'pass123'},
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    assert response.status_code == 403

def test_delete_profile_requires_auth(client):
    """Test that deleting profile requires authentication"""
    response = client.delete('/api/profile',
        json={'password': 'testpass'}
    )
    assert response.status_code == 401

def test_profile_persistence(client, auth_token):
    """Test that profile updates persist"""
    # Update profile
    client.put('/api/profile',
        json={
            'email': 'persist@test.com',
            'full_name': 'Persist Test',
            'bio': 'Testing persistence'
        },
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    # Get profile again
    response = client.get('/api/profile', headers={
        'Authorization': f'Bearer {auth_token}'
    })
    data = response.get_json()
    assert data['profile']['email'] == 'persist@test.com'
    assert data['profile']['full_name'] == 'Persist Test'
    assert data['profile']['bio'] == 'Testing persistence'

def test_update_profile_phone(client, auth_token):
    """Test updating user phone"""
    response = client.put('/api/profile',
        json={'phone': '+1-555-0123'},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['profile']['phone'] == '+1-555-0123'

def test_update_profile_address(client, auth_token):
    """Test updating user address"""
    response = client.put('/api/profile',
        json={'address': '123 Main Street'},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['profile']['address'] == '123 Main Street'

def test_update_profile_city_country(client, auth_token):
    """Test updating user city and country"""
    response = client.put('/api/profile',
        json={'city': 'New York', 'country': 'USA'},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['profile']['city'] == 'New York'
    assert data['profile']['country'] == 'USA'

def test_update_profile_date_of_birth(client, auth_token):
    """Test updating user date of birth"""
    response = client.put('/api/profile',
        json={'date_of_birth': '1990-01-15'},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['profile']['date_of_birth'] == '1990-01-15'

def test_update_profile_website(client, auth_token):
    """Test updating user website"""
    response = client.put('/api/profile',
        json={'website': 'https://example.com'},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['profile']['website'] == 'https://example.com'

def test_update_profile_company_job(client, auth_token):
    """Test updating user company and job title"""
    response = client.put('/api/profile',
        json={'company': 'Tech Corp', 'job_title': 'Software Engineer'},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['profile']['company'] == 'Tech Corp'
    assert data['profile']['job_title'] == 'Software Engineer'

def test_update_profile_all_personal_details(client, auth_token):
    """Test updating all personal details at once"""
    response = client.put('/api/profile',
        json={
            'email': 'complete@test.com',
            'full_name': 'John Complete Doe',
            'bio': 'Complete bio',
            'phone': '+1-555-9999',
            'address': '456 Oak Avenue',
            'city': 'San Francisco',
            'country': 'USA',
            'date_of_birth': '1985-06-20',
            'website': 'https://johndoe.com',
            'company': 'StartupXYZ',
            'job_title': 'CTO'
        },
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    data = response.get_json()
    profile = data['profile']
    assert profile['email'] == 'complete@test.com'
    assert profile['full_name'] == 'John Complete Doe'
    assert profile['bio'] == 'Complete bio'
    assert profile['phone'] == '+1-555-9999'
    assert profile['address'] == '456 Oak Avenue'
    assert profile['city'] == 'San Francisco'
    assert profile['country'] == 'USA'
    assert profile['date_of_birth'] == '1985-06-20'
    assert profile['website'] == 'https://johndoe.com'
    assert profile['company'] == 'StartupXYZ'
    assert profile['job_title'] == 'CTO'

def test_get_profile_includes_personal_details(client, auth_token):
    """Test that get profile includes all personal detail fields"""
    # First update some details
    client.put('/api/profile',
        json={
            'phone': '+1-555-1234',
            'city': 'Boston',
            'company': 'TestCo'
        },
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    # Get profile
    response = client.get('/api/profile', headers={
        'Authorization': f'Bearer {auth_token}'
    })
    assert response.status_code == 200
    data = response.get_json()
    profile = data['profile']
    
    # Check all fields are present
    assert 'phone' in profile
    assert 'address' in profile
    assert 'city' in profile
    assert 'country' in profile
    assert 'date_of_birth' in profile
    assert 'website' in profile
    assert 'company' in profile
    assert 'job_title' in profile
    
    # Check updated values
    assert profile['phone'] == '+1-555-1234'
    assert profile['city'] == 'Boston'
    assert profile['company'] == 'TestCo'

