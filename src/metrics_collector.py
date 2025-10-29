from database import get_db_connection
from datetime import datetime


class MetricsCollector:
    """Collector for LLM performance metrics"""
    
    def record(self, user_id, model, endpoint, prompt, response, 
               duration, error=None, cached=False):
        """Record metrics for an LLM request"""
        metrics = {
            'user_id': user_id,
            'model': model,
            'endpoint': endpoint,
            'prompt_tokens': len(prompt.split()) if prompt else 0,
            'response_tokens': len(response.split()) if response else 0,
            'duration_ms': int(duration * 1000),
            'cached': 1 if cached else 0,
            'error': 1 if error is not None else 0,
            'error_message': str(error) if error else None
        }
        
        metrics['total_tokens'] = (
            metrics['prompt_tokens'] + metrics['response_tokens']
        )
        metrics['tokens_per_second'] = (
            metrics['total_tokens'] / duration if duration > 0 else 0
        )
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO llm_metrics 
                (user_id, model, endpoint, prompt_tokens, response_tokens,
                 total_tokens, duration_ms, tokens_per_second, cached,
                 error, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metrics['user_id'],
                metrics['model'],
                metrics['endpoint'],
                metrics['prompt_tokens'],
                metrics['response_tokens'],
                metrics['total_tokens'],
                metrics['duration_ms'],
                metrics['tokens_per_second'],
                metrics['cached'],
                metrics['error'],
                metrics['error_message']
            ))
            conn.commit()
            return cursor.lastrowid
    
    def update_rating(self, metric_id, rating):
        """Update user rating for a metric"""
        if rating not in [-1, 0, 1]:
            raise ValueError("Rating must be -1, 0, or 1")
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE llm_metrics
                SET user_rating = ?
                WHERE id = ?
            ''', (rating, metric_id))
            conn.commit()
    
    def get_dashboard_stats(self, user_id=None, days=7):
        """Get metrics for dashboard"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Build query with optional user filter
            user_filter = 'AND user_id = ?' if user_id else ''
            params = [days]
            if user_id:
                params.append(user_id)
            
            # Overall stats
            cursor.execute(f'''
                SELECT 
                    COUNT(*) as total_requests,
                    SUM(CASE WHEN error = 1 THEN 1 ELSE 0 END) as errors,
                    AVG(duration_ms) as avg_duration,
                    AVG(tokens_per_second) as avg_tokens_per_sec,
                    SUM(CASE WHEN cached = 1 THEN 1 ELSE 0 END) as cache_hits,
                    SUM(total_tokens) as total_tokens
                FROM llm_metrics
                WHERE created_at >= datetime('now', '-' || ? || ' days')
                {user_filter}
            ''', tuple(params))
            
            stats = dict(cursor.fetchone())
            
            # Handle None values from aggregate functions when no data
            if stats['errors'] is None:
                stats['errors'] = 0
            if stats['cache_hits'] is None:
                stats['cache_hits'] = 0
            if stats['total_tokens'] is None:
                stats['total_tokens'] = 0
            
            # Calculate derived metrics
            if stats['total_requests'] > 0:
                stats['error_rate'] = stats['errors'] / stats['total_requests']
                stats['cache_hit_rate'] = stats['cache_hits'] / stats['total_requests']
            else:
                stats['error_rate'] = 0
                stats['cache_hit_rate'] = 0
            
            # Per-model stats
            params = [days]
            if user_id:
                params.append(user_id)
            
            cursor.execute(f'''
                SELECT 
                    model,
                    COUNT(*) as requests,
                    AVG(duration_ms) as avg_duration,
                    AVG(tokens_per_second) as avg_tps,
                    SUM(total_tokens) as total_tokens,
                    SUM(CASE WHEN error = 1 THEN 1 ELSE 0 END) as errors
                FROM llm_metrics
                WHERE created_at >= datetime('now', '-' || ? || ' days')
                {user_filter}
                GROUP BY model
                ORDER BY requests DESC
            ''', tuple(params))
            
            stats['by_model'] = [dict(row) for row in cursor.fetchall()]
            
            # Ratings summary
            params = [days]
            if user_id:
                params.append(user_id)
            
            cursor.execute(f'''
                SELECT 
                    SUM(CASE WHEN user_rating = 1 THEN 1 ELSE 0 END) as positive,
                    SUM(CASE WHEN user_rating = -1 THEN 1 ELSE 0 END) as negative,
                    SUM(CASE WHEN user_rating IS NOT NULL THEN 1 ELSE 0 END) as total_rated
                FROM llm_metrics
                WHERE created_at >= datetime('now', '-' || ? || ' days')
                {user_filter}
            ''', tuple(params))
            
            ratings = dict(cursor.fetchone())
            stats['ratings'] = ratings
            if ratings['total_rated'] is not None and ratings['total_rated'] > 0:
                stats['ratings']['satisfaction_rate'] = (
                    ratings['positive'] / ratings['total_rated']
                )
            else:
                stats['ratings']['satisfaction_rate'] = 0
            
            return stats
    
    def get_time_series(self, user_id=None, days=7, interval='hour'):
        """Get time series data for charts"""
        interval_format = {
            'hour': '%Y-%m-%d %H:00:00',
            'day': '%Y-%m-%d',
            'week': '%Y-W%W'
        }
        
        if interval not in interval_format:
            raise ValueError(f"Invalid interval: {interval}")
        
        user_filter = 'AND user_id = ?' if user_id else ''
        params = [days]
        if user_id:
            params.append(user_id)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT 
                    strftime(?, created_at) as time_bucket,
                    COUNT(*) as requests,
                    AVG(duration_ms) as avg_duration,
                    SUM(total_tokens) as total_tokens,
                    SUM(CASE WHEN error = 1 THEN 1 ELSE 0 END) as errors
                FROM llm_metrics
                WHERE created_at >= datetime('now', '-' || ? || ' days')
                {user_filter}
                GROUP BY time_bucket
                ORDER BY time_bucket
            ''', (interval_format[interval],) + tuple(params))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_endpoint_stats(self, user_id=None, days=7):
        """Get statistics per endpoint"""
        user_filter = 'AND user_id = ?' if user_id else ''
        params = [days]
        if user_id:
            params.append(user_id)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT 
                    endpoint,
                    COUNT(*) as requests,
                    AVG(duration_ms) as avg_duration,
                    SUM(CASE WHEN error = 1 THEN 1 ELSE 0 END) as errors
                FROM llm_metrics
                WHERE created_at >= datetime('now', '-' || ? || ' days')
                {user_filter}
                GROUP BY endpoint
                ORDER BY requests DESC
            ''', tuple(params))
            
            return [dict(row) for row in cursor.fetchall()]
