from database import get_db_connection


class CostCalculator:
    """Calculator for tracking LLM computational costs"""
    
    # Cost per 1K tokens (example pricing - adjust based on actual costs)
    COSTS = {
        'llama2': {
            'input': 0.0001,   # $0.0001 per 1K tokens
            'output': 0.0002,
        },
        'llama2:7b': {
            'input': 0.0001,
            'output': 0.0002,
        },
        'llama2:13b': {
            'input': 0.0002,
            'output': 0.0004,
        },
        'llama2:70b': {
            'input': 0.0005,
            'output': 0.001,
        },
        'llama3': {
            'input': 0.00015,
            'output': 0.0003,
        },
        'llama3:8b': {
            'input': 0.00015,
            'output': 0.0003,
        },
        'llama3:70b': {
            'input': 0.0006,
            'output': 0.0012,
        },
        'mistral': {
            'input': 0.0001,
            'output': 0.0002,
        },
        'codellama': {
            'input': 0.0001,
            'output': 0.0002,
        }
    }
    
    def calculate_cost(self, model, prompt_tokens, response_tokens):
        """Calculate cost for a single request"""
        # Normalize model name
        model_key = model.lower()
        if model_key not in self.COSTS:
            # Try to match base model
            for cost_model in self.COSTS:
                if model_key.startswith(cost_model):
                    model_key = cost_model
                    break
            else:
                model_key = 'llama2'  # Default fallback
        
        pricing = self.COSTS[model_key]
        
        prompt_cost = (prompt_tokens / 1000) * pricing['input']
        response_cost = (response_tokens / 1000) * pricing['output']
        
        return {
            'prompt_cost': round(prompt_cost, 6),
            'response_cost': round(response_cost, 6),
            'total_cost': round(prompt_cost + response_cost, 6),
            'currency': 'USD'
        }
    
    def get_user_costs(self, user_id, period='month'):
        """Get cost summary for a user"""
        period_map = {
            'day': 1,
            'week': 7,
            'month': 30,
            'quarter': 90,
            'year': 365
        }
        
        days = period_map.get(period, 30)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    model,
                    SUM(prompt_tokens) as total_prompt_tokens,
                    SUM(response_tokens) as total_response_tokens,
                    COUNT(*) as request_count
                FROM llm_metrics
                WHERE user_id = ?
                  AND created_at >= datetime('now', '-' || ? || ' days')
                GROUP BY model
            ''', (user_id, days))
            
            total_cost = 0
            breakdown = []
            
            for row in cursor.fetchall():
                cost = self.calculate_cost(
                    row['model'],
                    row['total_prompt_tokens'],
                    row['total_response_tokens']
                )
                model_data = {
                    'model': row['model'],
                    'request_count': row['request_count'],
                    'prompt_tokens': row['total_prompt_tokens'],
                    'response_tokens': row['total_response_tokens'],
                    **cost
                }
                breakdown.append(model_data)
                total_cost += cost['total_cost']
            
            # Sort by cost descending
            breakdown.sort(key=lambda x: x['total_cost'], reverse=True)
            
            return {
                'user_id': user_id,
                'period': period,
                'period_days': days,
                'total_cost': round(total_cost, 6),
                'currency': 'USD',
                'breakdown': breakdown
            }
    
    def get_all_users_costs(self, period='month'):
        """Get cost summary for all users (admin only)"""
        period_map = {
            'day': 1,
            'week': 7,
            'month': 30,
            'quarter': 90,
            'year': 365
        }
        
        days = period_map.get(period, 30)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    m.user_id,
                    u.username,
                    m.model,
                    SUM(m.prompt_tokens) as total_prompt_tokens,
                    SUM(m.response_tokens) as total_response_tokens,
                    COUNT(*) as request_count
                FROM llm_metrics m
                JOIN users u ON m.user_id = u.id
                WHERE m.created_at >= datetime('now', '-' || ? || ' days')
                GROUP BY m.user_id, u.username, m.model
            ''', (days,))
            
            user_costs = {}
            total_cost = 0
            
            for row in cursor.fetchall():
                user_id = row['user_id']
                if user_id not in user_costs:
                    user_costs[user_id] = {
                        'user_id': user_id,
                        'username': row['username'],
                        'total_cost': 0,
                        'breakdown': []
                    }
                
                cost = self.calculate_cost(
                    row['model'],
                    row['total_prompt_tokens'],
                    row['total_response_tokens']
                )
                
                model_data = {
                    'model': row['model'],
                    'request_count': row['request_count'],
                    'prompt_tokens': row['total_prompt_tokens'],
                    'response_tokens': row['total_response_tokens'],
                    **cost
                }
                
                user_costs[user_id]['breakdown'].append(model_data)
                user_costs[user_id]['total_cost'] += cost['total_cost']
                total_cost += cost['total_cost']
            
            # Convert to list and sort by cost
            users_list = list(user_costs.values())
            for user in users_list:
                user['total_cost'] = round(user['total_cost'], 6)
                user['breakdown'].sort(key=lambda x: x['total_cost'], reverse=True)
            
            users_list.sort(key=lambda x: x['total_cost'], reverse=True)
            
            return {
                'period': period,
                'period_days': days,
                'total_cost': round(total_cost, 6),
                'currency': 'USD',
                'user_count': len(users_list),
                'users': users_list
            }
    
    def get_cost_projection(self, user_id, period='month'):
        """Project future costs based on current usage"""
        period_map = {
            'week': 7,
            'month': 30,
            'quarter': 90
        }
        
        projection_days = period_map.get(period, 30)
        
        # Get last 7 days of data for average
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    model,
                    SUM(prompt_tokens) as total_prompt_tokens,
                    SUM(response_tokens) as total_response_tokens
                FROM llm_metrics
                WHERE user_id = ?
                  AND created_at >= datetime('now', '-7 days')
                GROUP BY model
            ''', (user_id,))
            
            daily_avg_cost = 0
            breakdown = []
            
            for row in cursor.fetchall():
                # Calculate cost for 7 days
                cost = self.calculate_cost(
                    row['model'],
                    row['total_prompt_tokens'],
                    row['total_response_tokens']
                )
                
                # Average daily cost
                daily_cost = cost['total_cost'] / 7
                
                # Project for period
                projected_cost = daily_cost * projection_days
                
                breakdown.append({
                    'model': row['model'],
                    'daily_avg_cost': round(daily_cost, 6),
                    'projected_cost': round(projected_cost, 6)
                })
                
                daily_avg_cost += daily_cost
            
            projected_total = daily_avg_cost * projection_days
            
            return {
                'user_id': user_id,
                'projection_period': period,
                'projection_days': projection_days,
                'daily_avg_cost': round(daily_avg_cost, 6),
                'projected_total_cost': round(projected_total, 6),
                'currency': 'USD',
                'breakdown': breakdown,
                'based_on_days': 7
            }
    
    def update_pricing(self, model, input_cost, output_cost):
        """Update pricing for a model (admin function)"""
        self.COSTS[model] = {
            'input': input_cost,
            'output': output_cost
        }
        return True
    
    def get_pricing(self):
        """Get current pricing for all models"""
        return {
            'models': self.COSTS,
            'currency': 'USD',
            'unit': 'per 1K tokens'
        }
