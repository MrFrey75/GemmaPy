import pytest
import os
import sys
import uuid
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from auth import verify_password

def test_init_db_creates_tables():
    db_path = f'/tmp/test_{uuid.uuid4().hex}.db'
    os.environ['DATABASE_PATH'] = db_path
    
    from database import init_db, get_db_connection
    
    init_db()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        assert cursor.fetchone() is not None
        
        # Check data table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='data'")
        assert cursor.fetchone() is not None
    
    if os.path.exists(db_path):
        os.unlink(db_path)

def test_init_db_creates_default_admin():
    db_path = f'/tmp/test_{uuid.uuid4().hex}.db'
    os.environ['DATABASE_PATH'] = db_path
    
    from database import init_db, get_db_connection
    
    init_db()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
        admin_user = cursor.fetchone()
        
        assert admin_user is not None
        assert admin_user['username'] == 'admin'
        assert admin_user['is_admin'] == 1
        assert verify_password('pass123', admin_user['password'])
    
    if os.path.exists(db_path):
        os.unlink(db_path)

def test_init_db_does_not_duplicate_admin():
    db_path = f'/tmp/test_{uuid.uuid4().hex}.db'
    os.environ['DATABASE_PATH'] = db_path
    
    from database import init_db, get_db_connection
    
    # Initialize database twice
    init_db()
    init_db()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('admin',))
        count = cursor.fetchone()[0]
        
        # Should only have one admin user
        assert count == 1
    
    if os.path.exists(db_path):
        os.unlink(db_path)
