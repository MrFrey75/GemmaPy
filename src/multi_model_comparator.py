"""
Multi-Model Comparison System for GemmaPy
Allows users to compare responses from multiple LLM models simultaneously
"""

import time
from typing import List, Dict, Optional
from datetime import datetime
from database import get_db_connection


class MultiModelComparator:
    """Compare responses from multiple models"""
    
    def __init__(self, ollama_manager):
        """
        Initialize comparator
        
        Args:
            ollama_manager: OllamaManager instance
        """
        self.ollama = ollama_manager
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Create comparison tables if they don't exist"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS model_comparisons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    prompt TEXT NOT NULL,
                    system_prompt TEXT,
                    temperature REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS comparison_responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    comparison_id INTEGER NOT NULL,
                    model TEXT NOT NULL,
                    response TEXT,
                    duration_ms INTEGER,
                    tokens INTEGER,
                    error TEXT,
                    user_rating INTEGER CHECK(user_rating IN (-1, 0, 1)),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (comparison_id) REFERENCES model_comparisons(id) ON DELETE CASCADE
                )
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_comp_user 
                ON model_comparisons(user_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_resp_comp 
                ON comparison_responses(comparison_id)
            ''')
            conn.commit()
    
    def compare_models(self, user_id: int, prompt: str, models: List[str],
                      system: Optional[str] = None, temperature: float = 0.7,
                      max_tokens: Optional[int] = None) -> Dict:
        """
        Generate responses from multiple models and compare
        
        Args:
            user_id: User ID
            prompt: The prompt text
            models: List of model names to compare
            system: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Comparison results dictionary
        """
        if not models or len(models) < 2:
            raise ValueError("At least 2 models required for comparison")
        
        # Create comparison record
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO model_comparisons 
                (user_id, prompt, system_prompt, temperature)
                VALUES (?, ?, ?, ?)
            ''', (user_id, prompt, system, temperature))
            comparison_id = cursor.lastrowid
            conn.commit()
        
        # Generate responses from each model
        responses = []
        for model in models:
            start_time = time.time()
            error = None
            response_text = None
            tokens = 0
            
            try:
                response = self.ollama.generate(
                    model=model,
                    prompt=prompt,
                    system=system,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                response_text = response.get('response', '')
                tokens = len(response_text.split()) if response_text else 0
            except Exception as e:
                error = str(e)
                response_text = ''  # Set to empty string instead of None
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Store response
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO comparison_responses
                    (comparison_id, model, response, duration_ms, tokens, error)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (comparison_id, model, response_text, duration_ms, tokens, error))
                response_id = cursor.lastrowid
                conn.commit()
            
            responses.append({
                'response_id': response_id,
                'model': model,
                'response': response_text,
                'duration_ms': duration_ms,
                'tokens': tokens,
                'error': error,
                'success': error is None
            })
        
        return {
            'comparison_id': comparison_id,
            'prompt': prompt,
            'models': models,
            'responses': responses,
            'created_at': datetime.now().isoformat()
        }
    
    def get_comparison(self, comparison_id: int, user_id: int) -> Optional[Dict]:
        """
        Get comparison results
        
        Args:
            comparison_id: Comparison ID
            user_id: User ID (for permission check)
            
        Returns:
            Comparison results or None
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get comparison
            cursor.execute('''
                SELECT id, user_id, prompt, system_prompt, temperature, created_at
                FROM model_comparisons
                WHERE id = ? AND user_id = ?
            ''', (comparison_id, user_id))
            
            comp_row = cursor.fetchone()
            if not comp_row:
                return None
            
            comparison = dict(comp_row)
            
            # Get responses
            cursor.execute('''
                SELECT id, model, response, duration_ms, tokens, 
                       error, user_rating, created_at
                FROM comparison_responses
                WHERE comparison_id = ?
                ORDER BY duration_ms ASC
            ''', (comparison_id,))
            
            comparison['responses'] = [dict(row) for row in cursor.fetchall()]
            
            return comparison
    
    def list_comparisons(self, user_id: int, limit: int = 50) -> List[Dict]:
        """
        List user's comparisons
        
        Args:
            user_id: User ID
            limit: Maximum results
            
        Returns:
            List of comparisons
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.id, c.prompt, c.created_at,
                       COUNT(r.id) as model_count,
                       GROUP_CONCAT(r.model) as models
                FROM model_comparisons c
                LEFT JOIN comparison_responses r ON c.id = r.comparison_id
                WHERE c.user_id = ?
                GROUP BY c.id
                ORDER BY c.created_at DESC
                LIMIT ?
            ''', (user_id, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def rate_response(self, response_id: int, user_id: int, rating: int) -> bool:
        """
        Rate a specific model's response in a comparison
        
        Args:
            response_id: Response ID
            user_id: User ID (for permission check)
            rating: Rating (-1, 0, 1)
            
        Returns:
            True if successful
        """
        if rating not in [-1, 0, 1]:
            raise ValueError("Rating must be -1, 0, or 1")
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verify permission
            cursor.execute('''
                SELECT r.id
                FROM comparison_responses r
                JOIN model_comparisons c ON r.comparison_id = c.id
                WHERE r.id = ? AND c.user_id = ?
            ''', (response_id, user_id))
            
            if not cursor.fetchone():
                return False
            
            # Update rating
            cursor.execute('''
                UPDATE comparison_responses
                SET user_rating = ?
                WHERE id = ?
            ''', (rating, response_id))
            conn.commit()
            
            return True
    
    def delete_comparison(self, comparison_id: int, user_id: int) -> bool:
        """
        Delete a comparison
        
        Args:
            comparison_id: Comparison ID
            user_id: User ID (for permission check)
            
        Returns:
            True if deleted
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM model_comparisons
                WHERE id = ? AND user_id = ?
            ''', (comparison_id, user_id))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
    
    def get_model_rankings(self, user_id: Optional[int] = None, 
                          days: int = 30) -> List[Dict]:
        """
        Get model rankings based on user ratings
        
        Args:
            user_id: Optional user ID filter
            days: Number of days to consider
            
        Returns:
            List of models with rankings
        """
        user_filter = 'AND c.user_id = ?' if user_id else ''
        params = [days]
        if user_id:
            params.append(user_id)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT 
                    r.model,
                    COUNT(*) as total_responses,
                    AVG(r.duration_ms) as avg_duration_ms,
                    AVG(r.tokens) as avg_tokens,
                    SUM(CASE WHEN r.user_rating = 1 THEN 1 ELSE 0 END) as positive_ratings,
                    SUM(CASE WHEN r.user_rating = -1 THEN 1 ELSE 0 END) as negative_ratings,
                    SUM(CASE WHEN r.user_rating IS NOT NULL THEN 1 ELSE 0 END) as total_ratings,
                    SUM(CASE WHEN r.error IS NULL THEN 1 ELSE 0 END) as successful_responses,
                    COUNT(*) - SUM(CASE WHEN r.error IS NULL THEN 1 ELSE 0 END) as failed_responses
                FROM comparison_responses r
                JOIN model_comparisons c ON r.comparison_id = c.id
                WHERE c.created_at >= datetime('now', '-' || ? || ' days')
                {user_filter}
                GROUP BY r.model
                ORDER BY positive_ratings DESC, avg_duration_ms ASC
            ''', tuple(params))
            
            rankings = []
            for row in cursor.fetchall():
                rank_data = dict(row)
                
                # Calculate metrics
                if rank_data['total_ratings'] > 0:
                    rank_data['satisfaction_rate'] = (
                        rank_data['positive_ratings'] / rank_data['total_ratings']
                    )
                else:
                    rank_data['satisfaction_rate'] = 0
                
                rank_data['success_rate'] = (
                    rank_data['successful_responses'] / rank_data['total_responses']
                    if rank_data['total_responses'] > 0 else 0
                )
                
                rankings.append(rank_data)
            
            return rankings
    
    def get_statistics(self, user_id: Optional[int] = None) -> Dict:
        """
        Get comparison statistics
        
        Args:
            user_id: Optional user ID filter
            
        Returns:
            Statistics dictionary
        """
        user_filter = 'WHERE user_id = ?' if user_id else ''
        params = [user_id] if user_id else []
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Total comparisons
            cursor.execute(f'''
                SELECT COUNT(*) as total
                FROM model_comparisons
                {user_filter}
            ''', tuple(params))
            total_comparisons = cursor.fetchone()['total']
            
            # Unique models compared
            cursor.execute(f'''
                SELECT COUNT(DISTINCT r.model) as total
                FROM comparison_responses r
                JOIN model_comparisons c ON r.comparison_id = c.id
                {user_filter}
            ''', tuple(params))
            unique_models = cursor.fetchone()['total']
            
            # Most compared models
            cursor.execute(f'''
                SELECT r.model, COUNT(*) as count
                FROM comparison_responses r
                JOIN model_comparisons c ON r.comparison_id = c.id
                {user_filter}
                GROUP BY r.model
                ORDER BY count DESC
                LIMIT 5
            ''', tuple(params))
            most_compared = [dict(row) for row in cursor.fetchall()]
            
            return {
                'total_comparisons': total_comparisons,
                'unique_models_compared': unique_models,
                'most_compared_models': most_compared
            }
