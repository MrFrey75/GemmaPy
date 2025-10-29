import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import pytest
import uuid

@pytest.fixture
def client():
    # Use unique database path for each test
    db_path = f'/tmp/test_{uuid.uuid4().hex}.db'
    os.environ['DATABASE_PATH'] = db_path
    
    # Import after setting environment
    from app import app
    from database import init_db, get_db_connection
    from auth import hash_password
    
    app.config['TESTING'] = True
    
    with app.test_client() as test_client:
        with app.app_context():
            init_db()  # This will create the default admin user (admin/pass123)
            # Create additional test user
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)',
                    ('testuser', hash_password('testpass'), 0)
                )
                conn.commit()
        yield test_client
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)

@pytest.fixture
def auth_token(client):
    response = client.post('/api/login', json={
        'username': 'testuser',
        'password': 'testpass'
    })
    return response.get_json()['token']

@pytest.fixture
def admin_token(client):
    response = client.post('/api/login', json={
        'username': 'admin',
        'password': 'pass123'
    })
    return response.get_json()['token']
