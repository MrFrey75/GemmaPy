import sqlite3
import os
from contextlib import contextmanager

def get_database_path():
    return os.getenv('DATABASE_PATH', 'gemmapy.db')

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(get_database_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    from auth import hash_password
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT,
                full_name TEXT,
                bio TEXT,
                phone TEXT,
                address TEXT,
                city TEXT,
                country TEXT,
                date_of_birth TEXT,
                website TEXT,
                company TEXT,
                job_title TEXT,
                is_admin INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # LLM Metrics table (Phase 2)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS llm_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                model TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                prompt_tokens INTEGER,
                response_tokens INTEGER,
                total_tokens INTEGER,
                duration_ms INTEGER,
                tokens_per_second REAL,
                cached BOOLEAN DEFAULT 0,
                error BOOLEAN DEFAULT 0,
                error_message TEXT,
                user_rating INTEGER CHECK(user_rating IN (-1, 0, 1)),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Create indexes for metrics
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_metrics_model 
            ON llm_metrics(model)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_metrics_created 
            ON llm_metrics(created_at)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_metrics_user 
            ON llm_metrics(user_id)
        ''')
        
        # Conversations table (Phase 3)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT,
                model TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Conversation messages table (Phase 3)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('system', 'user', 'assistant')),
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
        ''')
        
        # Prompt templates table (Phase 3)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prompt_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT,
                template TEXT NOT NULL,
                variables TEXT,
                model TEXT,
                temperature REAL,
                is_public BOOLEAN DEFAULT 0,
                usage_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Create indexes for Phase 3 tables
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_conv_user 
            ON conversations(user_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_msg_conv 
            ON conversation_messages(conversation_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_template_user 
            ON prompt_templates(user_id)
        ''')
        
        # Check if admin user exists
        cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('admin',))
        admin_exists = cursor.fetchone()[0] > 0
        
        # Create default admin user if it doesn't exist
        if not admin_exists:
            hashed_password = hash_password('pass123')
            cursor.execute(
                'INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)',
                ('admin', hashed_password, 1)
            )
            print("Default admin user created (username: admin, password: pass123)")
        
        conn.commit()
        print("Database initialized successfully")

if __name__ == '__main__':
    init_db()
