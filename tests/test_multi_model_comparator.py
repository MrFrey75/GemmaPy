"""
Tests for Multi-Model Comparison System
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from multi_model_comparator import MultiModelComparator
import time


class TestMultiModelComparator:
    """Test suite for MultiModelComparator"""
    
    @pytest.fixture
    def ollama_manager(self):
        """Mock Ollama manager"""
        manager = Mock()
        manager.generate = Mock(return_value={
            'response': 'Test response',
            'model': 'llama2'
        })
        return manager
    
    @pytest.fixture
    def comparator(self, ollama_manager):
        """Create comparator instance"""
        return MultiModelComparator(ollama_manager)
    
    def test_comparator_initialization(self, comparator):
        """Test comparator initialization"""
        assert comparator is not None
        assert comparator.ollama is not None
    
    def test_compare_models_success(self, comparator, ollama_manager):
        """Test successful model comparison"""
        result = comparator.compare_models(
            user_id=1,
            prompt="What is Python?",
            models=['llama2', 'mistral']
        )
        
        assert result is not None
        assert 'comparison_id' in result
        assert 'responses' in result
        assert len(result['responses']) == 2
        assert ollama_manager.generate.call_count == 2
    
    def test_compare_models_minimum_requirement(self, comparator):
        """Test that at least 2 models are required"""
        with pytest.raises(ValueError, match="At least 2 models required"):
            comparator.compare_models(
                user_id=1,
                prompt="Test",
                models=['llama2']
            )
    
    def test_compare_models_with_system_prompt(self, comparator, ollama_manager):
        """Test comparison with system prompt"""
        result = comparator.compare_models(
            user_id=1,
            prompt="Test prompt",
            models=['llama2', 'mistral'],
            system="You are a helpful assistant"
        )
        
        assert result is not None
        assert len(result['responses']) == 2
    
    def test_compare_models_with_temperature(self, comparator, ollama_manager):
        """Test comparison with custom temperature"""
        result = comparator.compare_models(
            user_id=1,
            prompt="Test prompt",
            models=['llama2', 'mistral'],
            temperature=0.5
        )
        
        assert result is not None
    
    def test_compare_models_handles_errors(self, comparator, ollama_manager):
        """Test that errors in one model don't stop comparison"""
        def generate_side_effect(*args, **kwargs):
            if kwargs.get('model') == 'llama2':
                return {'response': 'Success'}
            else:
                raise Exception("Model error")
        
        ollama_manager.generate.side_effect = generate_side_effect
        
        result = comparator.compare_models(
            user_id=1,
            prompt="Test",
            models=['llama2', 'mistral']
        )
        
        assert len(result['responses']) == 2
        assert result['responses'][0]['success'] == True
        assert result['responses'][1]['success'] == False
        assert result['responses'][1]['error'] is not None
    
    def test_compare_models_tracks_duration(self, comparator, ollama_manager):
        """Test that duration is tracked"""
        result = comparator.compare_models(
            user_id=1,
            prompt="Test",
            models=['llama2', 'mistral']
        )
        
        for response in result['responses']:
            assert 'duration_ms' in response
            assert response['duration_ms'] >= 0
    
    def test_compare_models_counts_tokens(self, comparator, ollama_manager):
        """Test token counting"""
        ollama_manager.generate.return_value = {
            'response': 'This is a test response with multiple words'
        }
        
        result = comparator.compare_models(
            user_id=1,
            prompt="Test",
            models=['llama2', 'mistral']
        )
        
        for response in result['responses']:
            assert 'tokens' in response
            assert response['tokens'] > 0
    
    def test_get_comparison(self, comparator):
        """Test retrieving a comparison"""
        # Create comparison first
        result = comparator.compare_models(
            user_id=1,
            prompt="Test",
            models=['llama2', 'mistral']
        )
        
        comparison_id = result['comparison_id']
        
        # Retrieve it
        retrieved = comparator.get_comparison(comparison_id, user_id=1)
        
        assert retrieved is not None
        assert retrieved['id'] == comparison_id
        assert retrieved['prompt'] == "Test"
        assert len(retrieved['responses']) == 2
    
    def test_get_comparison_permission_check(self, comparator):
        """Test that users can only access their own comparisons"""
        # Create comparison for user 1
        result = comparator.compare_models(
            user_id=1,
            prompt="Test",
            models=['llama2', 'mistral']
        )
        
        comparison_id = result['comparison_id']
        
        # Try to access as user 2
        retrieved = comparator.get_comparison(comparison_id, user_id=2)
        assert retrieved is None
    
    def test_list_comparisons(self, comparator):
        """Test listing comparisons"""
        # Create multiple comparisons
        comparator.compare_models(1, "Test 1", ['llama2', 'mistral'])
        comparator.compare_models(1, "Test 2", ['llama2', 'llama3'])
        
        # List them
        comparisons = comparator.list_comparisons(user_id=1)
        
        assert len(comparisons) >= 2
        assert all('prompt' in c for c in comparisons)
        assert all('model_count' in c for c in comparisons)
    
    def test_list_comparisons_limit(self, comparator):
        """Test comparison listing with limit"""
        # Create multiple comparisons
        for i in range(5):
            comparator.compare_models(1, f"Test {i}", ['llama2', 'mistral'])
        
        # List with limit
        comparisons = comparator.list_comparisons(user_id=1, limit=3)
        
        assert len(comparisons) == 3
    
    def test_rate_response(self, comparator):
        """Test rating a response"""
        # Create comparison
        result = comparator.compare_models(
            user_id=1,
            prompt="Test",
            models=['llama2', 'mistral']
        )
        
        response_id = result['responses'][0]['response_id']
        
        # Rate it
        success = comparator.rate_response(response_id, user_id=1, rating=1)
        assert success == True
        
        # Verify rating
        comparison = comparator.get_comparison(result['comparison_id'], user_id=1)
        assert comparison['responses'][0]['user_rating'] == 1
    
    def test_rate_response_invalid_rating(self, comparator):
        """Test that invalid ratings are rejected"""
        result = comparator.compare_models(
            user_id=1,
            prompt="Test",
            models=['llama2', 'mistral']
        )
        
        response_id = result['responses'][0]['response_id']
        
        with pytest.raises(ValueError, match="Rating must be"):
            comparator.rate_response(response_id, user_id=1, rating=5)
    
    def test_rate_response_permission_check(self, comparator):
        """Test rating permission check"""
        result = comparator.compare_models(
            user_id=1,
            prompt="Test",
            models=['llama2', 'mistral']
        )
        
        response_id = result['responses'][0]['response_id']
        
        # Try to rate as different user
        success = comparator.rate_response(response_id, user_id=2, rating=1)
        assert success == False
    
    def test_delete_comparison(self, comparator):
        """Test deleting a comparison"""
        result = comparator.compare_models(
            user_id=1,
            prompt="Test",
            models=['llama2', 'mistral']
        )
        
        comparison_id = result['comparison_id']
        
        # Delete it
        deleted = comparator.delete_comparison(comparison_id, user_id=1)
        assert deleted == True
        
        # Verify it's gone
        retrieved = comparator.get_comparison(comparison_id, user_id=1)
        assert retrieved is None
    
    def test_delete_comparison_permission_check(self, comparator):
        """Test delete permission check"""
        result = comparator.compare_models(
            user_id=1,
            prompt="Test",
            models=['llama2', 'mistral']
        )
        
        comparison_id = result['comparison_id']
        
        # Try to delete as different user
        deleted = comparator.delete_comparison(comparison_id, user_id=2)
        assert deleted == False
    
    def test_get_model_rankings(self, comparator):
        """Test getting model rankings"""
        # Create comparisons and rate them
        result1 = comparator.compare_models(1, "Test 1", ['llama2', 'mistral'])
        result2 = comparator.compare_models(1, "Test 2", ['llama2', 'llama3'])
        
        # Rate responses
        comparator.rate_response(result1['responses'][0]['response_id'], 1, 1)
        comparator.rate_response(result2['responses'][0]['response_id'], 1, 1)
        
        # Get rankings
        rankings = comparator.get_model_rankings(user_id=1)
        
        assert len(rankings) > 0
        assert all('model' in r for r in rankings)
        assert all('total_responses' in r for r in rankings)
        assert all('satisfaction_rate' in r for r in rankings)
    
    def test_get_model_rankings_calculations(self, comparator):
        """Test ranking calculations"""
        result = comparator.compare_models(1, "Test", ['llama2', 'mistral'])
        
        # Rate responses
        comparator.rate_response(result['responses'][0]['response_id'], 1, 1)
        comparator.rate_response(result['responses'][1]['response_id'], 1, -1)
        
        rankings = comparator.get_model_rankings(user_id=1, days=0)  # Only today's data
        
        # Find the models
        llama2_rank = next((r for r in rankings if r['model'] == 'llama2'), None)
        mistral_rank = next((r for r in rankings if r['model'] == 'mistral'), None)
        
        assert llama2_rank is not None
        assert mistral_rank is not None
        # Just verify they have the data we expect
        assert llama2_rank['positive_ratings'] >= 1
        assert mistral_rank['negative_ratings'] >= 1
    
    def test_get_statistics(self, comparator):
        """Test getting statistics"""
        # Create some comparisons
        comparator.compare_models(1, "Test 1", ['llama2', 'mistral'])
        comparator.compare_models(1, "Test 2", ['llama2', 'llama3'])
        
        stats = comparator.get_statistics(user_id=1)
        
        assert 'total_comparisons' in stats
        assert 'unique_models_compared' in stats
        assert 'most_compared_models' in stats
        assert stats['total_comparisons'] >= 2
    
    def test_statistics_most_compared(self, comparator):
        """Test most compared models statistic"""
        # Create comparisons with same model
        for i in range(3):
            comparator.compare_models(1, f"Test {i}", ['llama2', 'mistral'])
        
        stats = comparator.get_statistics(user_id=1)
        most_compared = stats['most_compared_models']
        
        assert len(most_compared) > 0
        # llama2 should appear multiple times
        llama2_entry = next((m for m in most_compared if m['model'] == 'llama2'), None)
        assert llama2_entry is not None
        assert llama2_entry['count'] >= 3
    
    def test_empty_models_list(self, comparator):
        """Test with empty models list"""
        with pytest.raises(ValueError):
            comparator.compare_models(1, "Test", [])
    
    def test_single_model(self, comparator):
        """Test with single model"""
        with pytest.raises(ValueError):
            comparator.compare_models(1, "Test", ['llama2'])
    
    def test_multiple_users_isolation(self, comparator):
        """Test that user data is isolated"""
        # User 1 creates comparisons
        comparator.compare_models(1, "User 1 Test", ['llama2', 'mistral'])
        
        # User 2 creates comparisons
        comparator.compare_models(2, "User 2 Test", ['llama2', 'llama3'])
        
        # Each user should only see their own
        user1_comparisons = comparator.list_comparisons(user_id=1)
        user2_comparisons = comparator.list_comparisons(user_id=2)
        
        # Check that at least one from each user exists
        user1_prompts = [c['prompt'] for c in user1_comparisons]
        user2_prompts = [c['prompt'] for c in user2_comparisons]
        
        assert any('User 1' in p for p in user1_prompts)
        assert any('User 2' in p for p in user2_prompts)
        assert not any('User 2' in p for p in user1_prompts)
        assert not any('User 1' in p for p in user2_prompts)
    
    def test_admin_view_all_rankings(self, comparator):
        """Test that None user_id shows all rankings"""
        # Create comparisons for multiple users
        comparator.compare_models(1, "Test 1", ['llama2', 'mistral'])
        comparator.compare_models(2, "Test 2", ['llama2', 'llama3'])
        
        # Get rankings for all users (admin view)
        rankings = comparator.get_model_rankings(user_id=None)
        
        assert len(rankings) > 0
