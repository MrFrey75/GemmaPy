"""
Conversation Persistence Manager for GemmaPy
Stores and retrieves conversation histories for multi-session continuity
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from database import get_db_connection


class ConversationManager:
    """Manages conversation persistence and history"""
    
    def create(self, user_id: int, title: str, model: str, system_prompt: Optional[str] = None) -> int:
        """
        Create a new conversation
        
        Args:
            user_id: User ID
            title: Conversation title
            model: Model to use for conversation
            system_prompt: Optional system prompt
            
        Returns:
            conversation_id: ID of created conversation
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO conversations (user_id, title, model)
                VALUES (?, ?, ?)
            ''', (user_id, title, model))
            conversation_id = cursor.lastrowid
            
            # Add system message if provided
            if system_prompt:
                cursor.execute('''
                    INSERT INTO conversation_messages 
                    (conversation_id, role, content)
                    VALUES (?, 'system', ?)
                ''', (conversation_id, system_prompt))
            
            conn.commit()
            return conversation_id
    
    def get(self, conversation_id: int) -> Optional[Dict]:
        """
        Get conversation details
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Conversation details or None
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, user_id, title, model, created_at, 
                       updated_at, message_count
                FROM conversations
                WHERE id = ?
            ''', (conversation_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def list_user_conversations(self, user_id: int, limit: int = 50) -> List[Dict]:
        """
        List all conversations for a user
        
        Args:
            user_id: User ID
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversations
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, title, model, created_at, updated_at, message_count
                FROM conversations
                WHERE user_id = ?
                ORDER BY updated_at DESC
                LIMIT ?
            ''', (user_id, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_messages(self, conversation_id: int) -> List[Dict]:
        """
        Get all messages in a conversation
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            List of messages
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, role, content, created_at
                FROM conversation_messages
                WHERE conversation_id = ?
                ORDER BY id ASC
            ''', (conversation_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def add_message(self, conversation_id: int, role: str, content: str) -> int:
        """
        Add a message to a conversation
        
        Args:
            conversation_id: Conversation ID
            role: Message role (system, user, assistant)
            content: Message content
            
        Returns:
            message_id: ID of created message
        """
        if role not in ['system', 'user', 'assistant']:
            raise ValueError(f"Invalid role: {role}")
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO conversation_messages
                (conversation_id, role, content)
                VALUES (?, ?, ?)
            ''', (conversation_id, role, content))
            message_id = cursor.lastrowid
            
            # Update conversation
            cursor.execute('''
                UPDATE conversations
                SET message_count = message_count + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (conversation_id,))
            conn.commit()
            
            return message_id
    
    def update_title(self, conversation_id: int, title: str) -> bool:
        """
        Update conversation title
        
        Args:
            conversation_id: Conversation ID
            title: New title
            
        Returns:
            True if updated, False otherwise
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE conversations
                SET title = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (title, conversation_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def delete(self, conversation_id: int, user_id: int) -> bool:
        """
        Delete a conversation (with permission check)
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID (for permission check)
            
        Returns:
            True if deleted, False otherwise
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM conversations
                WHERE id = ? AND user_id = ?
            ''', (conversation_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def generate_title(self, messages: List[Dict]) -> str:
        """
        Auto-generate conversation title from first message
        
        Args:
            messages: List of messages
            
        Returns:
            Generated title
        """
        if messages:
            first_user_msg = next(
                (m for m in messages if m.get('role') == 'user'), 
                None
            )
            if first_user_msg:
                content = first_user_msg['content']
                return content[:50] + ('...' if len(content) > 50 else '')
        return "New Conversation"
    
    def search_conversations(self, user_id: int, query: str, limit: int = 20) -> List[Dict]:
        """
        Search conversations by title or content
        
        Args:
            user_id: User ID
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching conversations
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT c.id, c.title, c.model, c.created_at, 
                       c.updated_at, c.message_count
                FROM conversations c
                LEFT JOIN conversation_messages m ON c.id = m.conversation_id
                WHERE c.user_id = ? 
                  AND (c.title LIKE ? OR m.content LIKE ?)
                ORDER BY c.updated_at DESC
                LIMIT ?
            ''', (user_id, f'%{query}%', f'%{query}%', limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self, user_id: int) -> Dict:
        """
        Get conversation statistics for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Statistics dictionary
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Total conversations
            cursor.execute('''
                SELECT COUNT(*) as total
                FROM conversations
                WHERE user_id = ?
            ''', (user_id,))
            total = cursor.fetchone()['total']
            
            # Total messages
            cursor.execute('''
                SELECT COUNT(*) as total
                FROM conversation_messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE c.user_id = ?
            ''', (user_id,))
            total_messages = cursor.fetchone()['total']
            
            # Most used models
            cursor.execute('''
                SELECT model, COUNT(*) as count
                FROM conversations
                WHERE user_id = ?
                GROUP BY model
                ORDER BY count DESC
                LIMIT 5
            ''', (user_id,))
            models = [dict(row) for row in cursor.fetchall()]
            
            return {
                'total_conversations': total,
                'total_messages': total_messages,
                'models_used': models
            }
