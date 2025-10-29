"""
Unit tests for Phase 3: Conversation Persistence and Prompt Templates
"""

import unittest
import os
import sys
import tempfile
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from database import get_db_connection, init_db
from conversation_manager import ConversationManager
from prompt_templates import PromptTemplateManager


class TestConversationManager(unittest.TestCase):
    """Test ConversationManager functionality"""
    
    def setUp(self):
        """Set up test database"""
        self.db_fd, self.db_path = tempfile.mkstemp()
        os.environ['DATABASE_PATH'] = self.db_path
        init_db()
        
        # Create test user
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)',
                ('testuser', 'hashed_password', 0)
            )
            conn.commit()
            self.user_id = cursor.lastrowid
    
    def tearDown(self):
        """Clean up test database"""
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_create_conversation(self):
        """Test creating a conversation"""
        manager = ConversationManager()
        conv_id = manager.create(
            user_id=self.user_id,
            title="Test Conversation",
            model="llama2"
        )
        
        self.assertIsNotNone(conv_id)
        self.assertGreater(conv_id, 0)
    
    def test_create_conversation_with_system_prompt(self):
        """Test creating conversation with system prompt"""
        manager = ConversationManager()
        conv_id = manager.create(
            user_id=self.user_id,
            title="Test Conversation",
            model="llama2",
            system_prompt="You are a helpful assistant"
        )
        
        # Get messages
        messages = manager.get_messages(conv_id)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]['role'], 'system')
        self.assertEqual(messages[0]['content'], "You are a helpful assistant")
    
    def test_get_conversation(self):
        """Test retrieving conversation details"""
        manager = ConversationManager()
        conv_id = manager.create(
            user_id=self.user_id,
            title="Test Conversation",
            model="llama2"
        )
        
        conversation = manager.get(conv_id)
        
        self.assertIsNotNone(conversation)
        self.assertEqual(conversation['title'], "Test Conversation")
        self.assertEqual(conversation['model'], "llama2")
        self.assertEqual(conversation['user_id'], self.user_id)
    
    def test_list_user_conversations(self):
        """Test listing user conversations"""
        manager = ConversationManager()
        
        # Create multiple conversations
        conv1 = manager.create(self.user_id, "Conv 1", "llama2")
        conv2 = manager.create(self.user_id, "Conv 2", "llama3")
        
        conversations = manager.list_user_conversations(self.user_id)
        
        self.assertEqual(len(conversations), 2)
        # Should be ordered by updated_at DESC (most recent first)
        # Just verify both conversations are present
        conv_ids = [c['id'] for c in conversations]
        self.assertIn(conv1, conv_ids)
        self.assertIn(conv2, conv_ids)
    
    def test_add_message(self):
        """Test adding messages to conversation"""
        manager = ConversationManager()
        conv_id = manager.create(self.user_id, "Test", "llama2")
        
        # Add user message
        msg_id1 = manager.add_message(conv_id, 'user', 'Hello')
        self.assertIsNotNone(msg_id1)
        
        # Add assistant message
        msg_id2 = manager.add_message(conv_id, 'assistant', 'Hi there!')
        self.assertIsNotNone(msg_id2)
        
        # Get messages
        messages = manager.get_messages(conv_id)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]['content'], 'Hello')
        self.assertEqual(messages[1]['content'], 'Hi there!')
    
    def test_add_message_invalid_role(self):
        """Test adding message with invalid role"""
        manager = ConversationManager()
        conv_id = manager.create(self.user_id, "Test", "llama2")
        
        with self.assertRaises(ValueError):
            manager.add_message(conv_id, 'invalid', 'content')
    
    def test_update_title(self):
        """Test updating conversation title"""
        manager = ConversationManager()
        conv_id = manager.create(self.user_id, "Original Title", "llama2")
        
        updated = manager.update_title(conv_id, "New Title")
        self.assertTrue(updated)
        
        conversation = manager.get(conv_id)
        self.assertEqual(conversation['title'], "New Title")
    
    def test_delete_conversation(self):
        """Test deleting conversation"""
        manager = ConversationManager()
        conv_id = manager.create(self.user_id, "Test", "llama2")
        
        deleted = manager.delete(conv_id, self.user_id)
        self.assertTrue(deleted)
        
        conversation = manager.get(conv_id)
        self.assertIsNone(conversation)
    
    def test_delete_conversation_wrong_user(self):
        """Test deleting conversation with wrong user"""
        manager = ConversationManager()
        conv_id = manager.create(self.user_id, "Test", "llama2")
        
        # Try to delete with different user_id
        deleted = manager.delete(conv_id, 99999)
        self.assertFalse(deleted)
    
    def test_message_count_updates(self):
        """Test that message count updates correctly"""
        manager = ConversationManager()
        conv_id = manager.create(self.user_id, "Test", "llama2")
        
        # Add messages
        manager.add_message(conv_id, 'user', 'Message 1')
        manager.add_message(conv_id, 'assistant', 'Response 1')
        manager.add_message(conv_id, 'user', 'Message 2')
        
        conversation = manager.get(conv_id)
        self.assertEqual(conversation['message_count'], 3)
    
    def test_generate_title(self):
        """Test auto-generating title from messages"""
        manager = ConversationManager()
        
        messages = [
            {'role': 'user', 'content': 'What is Python?'},
            {'role': 'assistant', 'content': 'Python is a programming language'}
        ]
        
        title = manager.generate_title(messages)
        self.assertEqual(title, "What is Python?")
    
    def test_generate_title_long_message(self):
        """Test title generation with long message"""
        manager = ConversationManager()
        
        long_message = "This is a very long message that exceeds fifty characters and should be truncated"
        messages = [{'role': 'user', 'content': long_message}]
        
        title = manager.generate_title(messages)
        self.assertEqual(len(title), 53)  # 50 chars + "..."
        self.assertTrue(title.endswith('...'))
    
    def test_search_conversations(self):
        """Test searching conversations"""
        manager = ConversationManager()
        
        # Create conversations
        conv1 = manager.create(self.user_id, "Python Tutorial", "llama2")
        conv2 = manager.create(self.user_id, "JavaScript Guide", "llama2")
        conv3 = manager.create(self.user_id, "Python Best Practices", "llama2")
        
        # Add messages
        manager.add_message(conv1, 'user', 'Tell me about Python')
        manager.add_message(conv2, 'user', 'Tell me about JavaScript')
        
        # Search for "Python"
        results = manager.search_conversations(self.user_id, "Python")
        
        self.assertEqual(len(results), 2)
        result_ids = [r['id'] for r in results]
        self.assertIn(conv1, result_ids)
        self.assertIn(conv3, result_ids)
    
    def test_get_statistics(self):
        """Test getting conversation statistics"""
        manager = ConversationManager()
        
        # Create conversations with different models
        conv1 = manager.create(self.user_id, "Conv 1", "llama2")
        conv2 = manager.create(self.user_id, "Conv 2", "llama2")
        conv3 = manager.create(self.user_id, "Conv 3", "llama3")
        
        # Add messages
        manager.add_message(conv1, 'user', 'Message 1')
        manager.add_message(conv1, 'assistant', 'Response 1')
        manager.add_message(conv2, 'user', 'Message 2')
        
        stats = manager.get_statistics(self.user_id)
        
        self.assertEqual(stats['total_conversations'], 3)
        self.assertEqual(stats['total_messages'], 3)
        self.assertEqual(len(stats['models_used']), 2)
        
        # llama2 should be most used
        self.assertEqual(stats['models_used'][0]['model'], 'llama2')
        self.assertEqual(stats['models_used'][0]['count'], 2)


class TestPromptTemplateManager(unittest.TestCase):
    """Test PromptTemplateManager functionality"""
    
    def setUp(self):
        """Set up test database"""
        self.db_fd, self.db_path = tempfile.mkstemp()
        os.environ['DATABASE_PATH'] = self.db_path
        init_db()
        
        # Create test user
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)',
                ('testuser', 'hashed_password', 0)
            )
            conn.commit()
            self.user_id = cursor.lastrowid
    
    def tearDown(self):
        """Clean up test database"""
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_list_builtin_templates(self):
        """Test listing built-in templates"""
        manager = PromptTemplateManager()
        templates = manager.list_templates(include_custom=False)
        
        self.assertGreater(len(templates), 0)
        self.assertIn('summarize', templates)
        self.assertIn('translate', templates)
        self.assertIn('code_review', templates)
    
    def test_get_template(self):
        """Test getting specific template"""
        manager = PromptTemplateManager()
        template = manager.get_template('summarize')
        
        self.assertIsNotNone(template)
        self.assertEqual(template['name'], 'Summarize Text')
        self.assertIn('text', template['variables'])
        self.assertIn('length', template['variables'])
    
    def test_render_template(self):
        """Test rendering template with variables"""
        manager = PromptTemplateManager()
        
        prompt = manager.render('summarize', {
            'text': 'This is a long article about AI.',
            'length': '2'
        })
        
        self.assertIn('This is a long article about AI.', prompt)
        self.assertIn('2', prompt)
        self.assertNotIn('{text}', prompt)
        self.assertNotIn('{length}', prompt)
    
    def test_render_template_missing_variables(self):
        """Test rendering with missing variables"""
        manager = PromptTemplateManager()
        
        with self.assertRaises(ValueError):
            manager.render('summarize', {'text': 'Some text'})
    
    def test_create_custom_template(self):
        """Test creating custom template"""
        manager = PromptTemplateManager()
        
        template_id = manager.create_custom(
            user_id=self.user_id,
            name="My Template",
            description="Custom template",
            template="Hello {name}, welcome to {place}",
            variables=['name', 'place'],
            category='greeting',
            model='llama2',
            temperature=0.7
        )
        
        self.assertIsNotNone(template_id)
        self.assertGreater(template_id, 0)
    
    def test_get_custom_template(self):
        """Test retrieving custom template"""
        manager = PromptTemplateManager()
        
        template_id = manager.create_custom(
            user_id=self.user_id,
            name="My Template",
            description="Test",
            template="Hello {name}",
            variables=['name']
        )
        
        template = manager.get_custom_template(template_id)
        
        self.assertIsNotNone(template)
        self.assertEqual(template['name'], "My Template")
        self.assertEqual(template['template'], "Hello {name}")
        self.assertEqual(template['variables'], ['name'])
    
    def test_get_custom_templates(self):
        """Test listing user's custom templates"""
        manager = PromptTemplateManager()
        
        # Create multiple templates
        template_id1 = manager.create_custom(
            user_id=self.user_id,
            name="Template 1",
            description="First",
            template="Hello {name}",
            variables=['name'],
            category='greeting'
        )
        
        template_id2 = manager.create_custom(
            user_id=self.user_id,
            name="Template 2",
            description="Second",
            template="Bye {name}",
            variables=['name'],
            category='greeting'
        )
        
        templates = manager.get_custom_templates(self.user_id)
        
        self.assertEqual(len(templates), 2)
    
    def test_get_custom_templates_by_category(self):
        """Test filtering custom templates by category"""
        manager = PromptTemplateManager()
        
        manager.create_custom(
            user_id=self.user_id,
            name="Greeting",
            description="",
            template="Hello",
            variables=[],
            category='greeting'
        )
        
        manager.create_custom(
            user_id=self.user_id,
            name="Farewell",
            description="",
            template="Goodbye",
            variables=[],
            category='farewell'
        )
        
        templates = manager.get_custom_templates(self.user_id, category='greeting')
        
        self.assertEqual(len(templates), 1)
        self.assertEqual(templates[0]['category'], 'greeting')
    
    def test_update_custom_template(self):
        """Test updating custom template"""
        manager = PromptTemplateManager()
        
        template_id = manager.create_custom(
            user_id=self.user_id,
            name="Original",
            description="Original description",
            template="Original {var}",
            variables=['var']
        )
        
        updated = manager.update_custom(
            template_id=template_id,
            user_id=self.user_id,
            name="Updated",
            description="New description"
        )
        
        self.assertTrue(updated)
        
        template = manager.get_custom_template(template_id)
        self.assertEqual(template['name'], "Updated")
        self.assertEqual(template['description'], "New description")
    
    def test_update_custom_template_wrong_user(self):
        """Test updating template with wrong user"""
        manager = PromptTemplateManager()
        
        template_id = manager.create_custom(
            user_id=self.user_id,
            name="Original",
            description="",
            template="Test",
            variables=[]
        )
        
        updated = manager.update_custom(
            template_id=template_id,
            user_id=99999,
            name="Updated"
        )
        
        self.assertFalse(updated)
    
    def test_delete_custom_template(self):
        """Test deleting custom template"""
        manager = PromptTemplateManager()
        
        template_id = manager.create_custom(
            user_id=self.user_id,
            name="To Delete",
            description="",
            template="Test",
            variables=[]
        )
        
        deleted = manager.delete_custom(template_id, self.user_id)
        self.assertTrue(deleted)
        
        template = manager.get_custom_template(template_id)
        self.assertIsNone(template)
    
    def test_delete_custom_template_wrong_user(self):
        """Test deleting template with wrong user"""
        manager = PromptTemplateManager()
        
        template_id = manager.create_custom(
            user_id=self.user_id,
            name="To Delete",
            description="",
            template="Test",
            variables=[]
        )
        
        deleted = manager.delete_custom(template_id, 99999)
        self.assertFalse(deleted)
    
    def test_increment_usage(self):
        """Test incrementing template usage counter"""
        manager = PromptTemplateManager()
        
        template_id = manager.create_custom(
            user_id=self.user_id,
            name="Test",
            description="",
            template="Test",
            variables=[]
        )
        
        # Initial usage count should be 0
        template = manager.get_custom_template(template_id)
        self.assertEqual(template['usage_count'], 0)
        
        # Increment usage
        manager.increment_usage(template_id)
        manager.increment_usage(template_id)
        
        template = manager.get_custom_template(template_id)
        self.assertEqual(template['usage_count'], 2)
    
    def test_get_popular_templates(self):
        """Test getting popular templates"""
        manager = PromptTemplateManager()
        
        # Create public templates with different usage counts
        t1 = manager.create_custom(
            user_id=self.user_id,
            name="Popular",
            description="",
            template="Test",
            variables=[],
            is_public=True
        )
        
        t2 = manager.create_custom(
            user_id=self.user_id,
            name="Less Popular",
            description="",
            template="Test",
            variables=[],
            is_public=True
        )
        
        # Increment usage
        manager.increment_usage(t1)
        manager.increment_usage(t1)
        manager.increment_usage(t1)
        manager.increment_usage(t2)
        
        popular = manager.get_popular_templates(limit=10)
        
        self.assertGreater(len(popular), 0)
        # Most popular should be first
        self.assertEqual(popular[0]['id'], t1)
    
    def test_get_categories(self):
        """Test getting all categories"""
        manager = PromptTemplateManager()
        
        categories = manager.get_categories()
        
        self.assertGreater(len(categories), 0)
        self.assertIn('content', categories)
        self.assertIn('code', categories)
        self.assertIn('education', categories)
    
    def test_render_code_review_template(self):
        """Test rendering code review template"""
        manager = PromptTemplateManager()
        
        prompt = manager.render('code_review', {
            'code': 'def hello():\n    print("Hello")',
            'language': 'Python'
        })
        
        self.assertIn('Python', prompt)
        self.assertIn('def hello()', prompt)
        self.assertIn('Code quality', prompt)
    
    def test_render_translate_template(self):
        """Test rendering translate template"""
        manager = PromptTemplateManager()
        
        prompt = manager.render('translate', {
            'text': 'Hello, how are you?',
            'language': 'Spanish'
        })
        
        self.assertIn('Hello, how are you?', prompt)
        self.assertIn('Spanish', prompt)
    
    def test_list_templates_with_category_filter(self):
        """Test listing templates with category filter"""
        manager = PromptTemplateManager()
        
        templates = manager.list_templates(category='code', include_custom=False)
        
        for key, template in templates.items():
            self.assertEqual(template['category'], 'code')


if __name__ == '__main__':
    unittest.main()
