import unittest
import os
import sys
import time
from datetime import datetime, timedelta

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import get_db_connection, init_db
from metrics_collector import MetricsCollector
from cost_calculator import CostCalculator
from auth import hash_password


class TestMetricsCollector(unittest.TestCase):
    """Test suite for MetricsCollector (Phase 2)"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database"""
        os.environ['DATABASE_PATH'] = 'test_phase2.db'
        init_db()
        
        # Create test user
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO users (id, username, password, is_admin)
                VALUES (?, ?, ?, ?)
            ''', (999, 'testuser', hash_password('test123'), 0))
            conn.commit()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test database"""
        if os.path.exists('test_phase2.db'):
            os.remove('test_phase2.db')
    
    def setUp(self):
        """Clear metrics before each test"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM llm_metrics')
            conn.commit()
    
    def test_record_metric(self):
        """Test recording a single metric"""
        collector = MetricsCollector()
        
        metric_id = collector.record(
            user_id=999,
            model='llama2',
            endpoint='/api/ollama/generate',
            prompt='What is Python?',
            response='Python is a programming language.',
            duration=1.5,
            cached=False
        )
        
        self.assertIsNotNone(metric_id)
        self.assertGreater(metric_id, 0)
    
    def test_record_metric_with_error(self):
        """Test recording a metric with error"""
        collector = MetricsCollector()
        
        metric_id = collector.record(
            user_id=999,
            model='llama2',
            endpoint='/api/ollama/generate',
            prompt='Test prompt',
            response=None,
            duration=0.5,
            error=Exception('Connection timeout'),
            cached=False
        )
        
        self.assertIsNotNone(metric_id)
        
        # Verify error was recorded
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT error, error_message FROM llm_metrics WHERE id = ?', (metric_id,))
            row = cursor.fetchone()
            self.assertEqual(row['error'], 1)
            self.assertIn('Connection timeout', row['error_message'])
    
    def test_record_cached_metric(self):
        """Test recording a cached response metric"""
        collector = MetricsCollector()
        
        metric_id = collector.record(
            user_id=999,
            model='llama2',
            endpoint='/api/ollama/generate',
            prompt='Cached prompt',
            response='Cached response',
            duration=0.001,
            cached=True
        )
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT cached FROM llm_metrics WHERE id = ?', (metric_id,))
            row = cursor.fetchone()
            self.assertEqual(row['cached'], 1)
    
    def test_update_rating(self):
        """Test updating metric rating"""
        collector = MetricsCollector()
        
        metric_id = collector.record(
            user_id=999,
            model='llama2',
            endpoint='/api/ollama/generate',
            prompt='Test',
            response='Response',
            duration=1.0
        )
        
        # Update rating
        collector.update_rating(metric_id, 1)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_rating FROM llm_metrics WHERE id = ?', (metric_id,))
            row = cursor.fetchone()
            self.assertEqual(row['user_rating'], 1)
    
    def test_update_rating_invalid(self):
        """Test updating rating with invalid value"""
        collector = MetricsCollector()
        
        metric_id = collector.record(
            user_id=999,
            model='llama2',
            endpoint='/api/ollama/generate',
            prompt='Test',
            response='Response',
            duration=1.0
        )
        
        with self.assertRaises(ValueError):
            collector.update_rating(metric_id, 5)
    
    def test_dashboard_stats_empty(self):
        """Test dashboard stats with no data"""
        collector = MetricsCollector()
        stats = collector.get_dashboard_stats(user_id=999, days=7)
        
        self.assertEqual(stats['total_requests'], 0)
        self.assertEqual(stats['errors'], 0)
        self.assertEqual(stats['error_rate'], 0)
        self.assertEqual(stats['cache_hit_rate'], 0)
    
    def test_dashboard_stats_with_data(self):
        """Test dashboard stats with sample data"""
        collector = MetricsCollector()
        
        # Add some metrics
        for i in range(5):
            collector.record(
                user_id=999,
                model='llama2',
                endpoint='/api/ollama/generate',
                prompt=f'Prompt {i}',
                response=f'Response {i}',
                duration=1.0 + i * 0.1,
                cached=(i % 2 == 0)
            )
        
        # Add one error
        collector.record(
            user_id=999,
            model='llama2',
            endpoint='/api/ollama/generate',
            prompt='Error prompt',
            response=None,
            duration=0.5,
            error=Exception('Test error')
        )
        
        stats = collector.get_dashboard_stats(user_id=999, days=7)
        
        self.assertEqual(stats['total_requests'], 6)
        self.assertEqual(stats['errors'], 1)
        self.assertAlmostEqual(stats['error_rate'], 1/6, places=2)
        self.assertEqual(stats['cache_hits'], 3)
        self.assertAlmostEqual(stats['cache_hit_rate'], 3/6, places=2)
    
    def test_dashboard_stats_by_model(self):
        """Test dashboard stats grouped by model"""
        collector = MetricsCollector()
        
        # Add metrics for different models
        for model in ['llama2', 'llama3', 'mistral']:
            for i in range(3):
                collector.record(
                    user_id=999,
                    model=model,
                    endpoint='/api/ollama/generate',
                    prompt=f'Prompt {i}',
                    response=f'Response {i}',
                    duration=1.0
                )
        
        stats = collector.get_dashboard_stats(user_id=999, days=7)
        
        self.assertEqual(len(stats['by_model']), 3)
        self.assertEqual(stats['total_requests'], 9)
        
        # Check each model has 3 requests
        for model_stats in stats['by_model']:
            self.assertEqual(model_stats['requests'], 3)
    
    def test_dashboard_stats_with_ratings(self):
        """Test dashboard stats with user ratings"""
        collector = MetricsCollector()
        
        # Add metrics with ratings
        for i in range(10):
            metric_id = collector.record(
                user_id=999,
                model='llama2',
                endpoint='/api/ollama/generate',
                prompt=f'Prompt {i}',
                response=f'Response {i}',
                duration=1.0
            )
            # Rate half positive, quarter negative, quarter unrated
            if i < 5:
                collector.update_rating(metric_id, 1)
            elif i < 7:
                collector.update_rating(metric_id, -1)
        
        stats = collector.get_dashboard_stats(user_id=999, days=7)
        
        self.assertEqual(stats['ratings']['positive'], 5)
        self.assertEqual(stats['ratings']['negative'], 2)
        self.assertEqual(stats['ratings']['total_rated'], 7)
        self.assertAlmostEqual(stats['ratings']['satisfaction_rate'], 5/7, places=2)
    
    def test_time_series_hourly(self):
        """Test time series data with hourly intervals"""
        collector = MetricsCollector()
        
        # Add metrics
        for i in range(5):
            collector.record(
                user_id=999,
                model='llama2',
                endpoint='/api/ollama/generate',
                prompt=f'Prompt {i}',
                response=f'Response {i}',
                duration=1.0
            )
        
        time_series = collector.get_time_series(user_id=999, days=7, interval='hour')
        
        self.assertIsInstance(time_series, list)
        if len(time_series) > 0:
            self.assertIn('time_bucket', time_series[0])
            self.assertIn('requests', time_series[0])
    
    def test_time_series_daily(self):
        """Test time series data with daily intervals"""
        collector = MetricsCollector()
        
        for i in range(3):
            collector.record(
                user_id=999,
                model='llama2',
                endpoint='/api/ollama/generate',
                prompt=f'Prompt {i}',
                response=f'Response {i}',
                duration=1.0
            )
        
        time_series = collector.get_time_series(user_id=999, days=7, interval='day')
        
        self.assertIsInstance(time_series, list)
    
    def test_endpoint_stats(self):
        """Test endpoint statistics"""
        collector = MetricsCollector()
        
        # Add metrics for different endpoints
        endpoints = ['/api/ollama/generate', '/api/ollama/chat', '/api/rag/generate']
        
        for endpoint in endpoints:
            for i in range(2):
                collector.record(
                    user_id=999,
                    model='llama2',
                    endpoint=endpoint,
                    prompt=f'Prompt {i}',
                    response=f'Response {i}',
                    duration=1.0
                )
        
        stats = collector.get_endpoint_stats(user_id=999, days=7)
        
        self.assertEqual(len(stats), 3)
        for stat in stats:
            self.assertEqual(stat['requests'], 2)
    
    def test_admin_all_users_stats(self):
        """Test getting stats for all users (admin view)"""
        collector = MetricsCollector()
        
        # Add metrics for test user
        collector.record(
            user_id=999,
            model='llama2',
            endpoint='/api/ollama/generate',
            prompt='User test',
            response='Response',
            duration=1.0
        )
        
        # Add metrics for admin user
        collector.record(
            user_id=1,
            model='llama2',
            endpoint='/api/ollama/generate',
            prompt='Admin test',
            response='Response',
            duration=1.0
        )
        
        # Get all stats (no user_id filter)
        stats = collector.get_dashboard_stats(user_id=None, days=7)
        
        self.assertEqual(stats['total_requests'], 2)


class TestCostCalculator(unittest.TestCase):
    """Test suite for CostCalculator (Phase 2)"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database"""
        os.environ['DATABASE_PATH'] = 'test_phase2.db'
        init_db()
        
        # Ensure both test users exist
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO users (id, username, password, is_admin)
                VALUES (?, ?, ?, ?)
            ''', (998, 'costuser', hash_password('test123'), 0))
            cursor.execute('''
                INSERT OR IGNORE INTO users (id, username, password, is_admin)
                VALUES (?, ?, ?, ?)
            ''', (999, 'testuser', hash_password('test123'), 0))
            conn.commit()
    
    def setUp(self):
        """Clear metrics before each test"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM llm_metrics WHERE user_id = 998')
            conn.commit()
    
    def test_calculate_cost_simple(self):
        """Test basic cost calculation"""
        calculator = CostCalculator()
        
        cost = calculator.calculate_cost(
            model='llama2',
            prompt_tokens=1000,
            response_tokens=2000
        )
        
        self.assertEqual(cost['prompt_cost'], 0.0001 * 1)  # 1K tokens
        self.assertEqual(cost['response_cost'], 0.0002 * 2)  # 2K tokens
        self.assertEqual(cost['total_cost'], 0.0001 + 0.0004)
        self.assertEqual(cost['currency'], 'USD')
    
    def test_calculate_cost_different_models(self):
        """Test cost calculation for different models"""
        calculator = CostCalculator()
        
        models = ['llama2', 'llama3', 'mistral']
        
        for model in models:
            cost = calculator.calculate_cost(
                model=model,
                prompt_tokens=1000,
                response_tokens=1000
            )
            
            self.assertIn('total_cost', cost)
            self.assertGreater(cost['total_cost'], 0)
    
    def test_calculate_cost_unknown_model(self):
        """Test cost calculation for unknown model (should use default)"""
        calculator = CostCalculator()
        
        cost = calculator.calculate_cost(
            model='unknown_model',
            prompt_tokens=1000,
            response_tokens=1000
        )
        
        # Should fallback to llama2 pricing
        expected = calculator.calculate_cost('llama2', 1000, 1000)
        self.assertEqual(cost['total_cost'], expected['total_cost'])
    
    def test_get_user_costs_empty(self):
        """Test getting user costs with no data"""
        calculator = CostCalculator()
        
        costs = calculator.get_user_costs(user_id=998, period='month')
        
        self.assertEqual(costs['total_cost'], 0)
        self.assertEqual(len(costs['breakdown']), 0)
        self.assertEqual(costs['user_id'], 998)
    
    def test_get_user_costs_with_data(self):
        """Test getting user costs with sample data"""
        # Add metrics first
        collector = MetricsCollector()
        
        for i in range(5):
            collector.record(
                user_id=998,
                model='llama2',
                endpoint='/api/ollama/generate',
                prompt='word ' * 100,  # ~100 tokens
                response='word ' * 200,  # ~200 tokens
                duration=1.0
            )
        
        calculator = CostCalculator()
        costs = calculator.get_user_costs(user_id=998, period='month')
        
        self.assertGreater(costs['total_cost'], 0)
        self.assertEqual(len(costs['breakdown']), 1)
        self.assertEqual(costs['breakdown'][0]['model'], 'llama2')
        self.assertEqual(costs['breakdown'][0]['request_count'], 5)
    
    def test_get_user_costs_multiple_models(self):
        """Test getting user costs with multiple models"""
        collector = MetricsCollector()
        
        models = ['llama2', 'llama3', 'mistral']
        
        for model in models:
            for i in range(3):
                collector.record(
                    user_id=998,
                    model=model,
                    endpoint='/api/ollama/generate',
                    prompt='word ' * 100,
                    response='word ' * 200,
                    duration=1.0
                )
        
        calculator = CostCalculator()
        costs = calculator.get_user_costs(user_id=998, period='month')
        
        self.assertEqual(len(costs['breakdown']), 3)
        
        # Breakdown should be sorted by cost (descending)
        for i in range(len(costs['breakdown']) - 1):
            self.assertGreaterEqual(
                costs['breakdown'][i]['total_cost'],
                costs['breakdown'][i + 1]['total_cost']
            )
    
    def test_get_user_costs_different_periods(self):
        """Test getting user costs for different time periods"""
        collector = MetricsCollector()
        
        collector.record(
            user_id=998,
            model='llama2',
            endpoint='/api/ollama/generate',
            prompt='word ' * 100,
            response='word ' * 200,
            duration=1.0
        )
        
        calculator = CostCalculator()
        
        periods = ['day', 'week', 'month', 'quarter', 'year']
        
        for period in periods:
            costs = calculator.get_user_costs(user_id=998, period=period)
            self.assertEqual(costs['period'], period)
            self.assertIn('period_days', costs)
    
    def test_get_all_users_costs(self):
        """Test getting costs for all users"""
        collector = MetricsCollector()
        
        # Clear all metrics first
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM llm_metrics')
            conn.commit()
        
        # Add metrics for multiple users
        for user_id in [998, 999]:
            collector.record(
                user_id=user_id,
                model='llama2',
                endpoint='/api/ollama/generate',
                prompt='word ' * 100,
                response='word ' * 200,
                duration=1.0
            )
        
        calculator = CostCalculator()
        costs = calculator.get_all_users_costs(period='month')
        
        self.assertGreater(costs['total_cost'], 0)
        self.assertGreaterEqual(costs['user_count'], 2)
        self.assertGreaterEqual(len(costs['users']), 2)
        
        # Users should be sorted by cost (descending)
        for i in range(len(costs['users']) - 1):
            self.assertGreaterEqual(
                costs['users'][i]['total_cost'],
                costs['users'][i + 1]['total_cost']
            )
    
    def test_cost_projection_empty(self):
        """Test cost projection with no historical data"""
        calculator = CostCalculator()
        
        projection = calculator.get_cost_projection(user_id=998, period='month')
        
        self.assertEqual(projection['projected_total_cost'], 0)
        self.assertEqual(len(projection['breakdown']), 0)
    
    def test_cost_projection_with_data(self):
        """Test cost projection with historical data"""
        collector = MetricsCollector()
        
        # Add data for last 7 days
        for i in range(14):  # 2 per day for 7 days
            collector.record(
                user_id=998,
                model='llama2',
                endpoint='/api/ollama/generate',
                prompt='word ' * 100,
                response='word ' * 200,
                duration=1.0
            )
        
        calculator = CostCalculator()
        projection = calculator.get_cost_projection(user_id=998, period='month')
        
        self.assertGreater(projection['projected_total_cost'], 0)
        self.assertGreater(projection['daily_avg_cost'], 0)
        self.assertEqual(projection['projection_days'], 30)
        self.assertEqual(projection['based_on_days'], 7)
    
    def test_update_pricing(self):
        """Test updating model pricing"""
        calculator = CostCalculator()
        
        result = calculator.update_pricing('test_model', 0.001, 0.002)
        
        self.assertTrue(result)
        self.assertIn('test_model', calculator.COSTS)
        self.assertEqual(calculator.COSTS['test_model']['input'], 0.001)
        self.assertEqual(calculator.COSTS['test_model']['output'], 0.002)
    
    def test_get_pricing(self):
        """Test getting current pricing"""
        calculator = CostCalculator()
        
        pricing = calculator.get_pricing()
        
        self.assertIn('models', pricing)
        self.assertIn('currency', pricing)
        self.assertIn('unit', pricing)
        self.assertEqual(pricing['currency'], 'USD')
        self.assertIn('llama2', pricing['models'])


if __name__ == '__main__':
    unittest.main()
