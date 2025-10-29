"""
Prompt Templates Library for GemmaPy
Reusable prompt templates for common tasks
"""

import json
from typing import Dict, List, Optional
from database import get_db_connection


class PromptTemplateManager:
    """Manages prompt templates and rendering"""
    
    # Built-in templates
    TEMPLATES = {
        'summarize': {
            'name': 'Summarize Text',
            'description': 'Summarize text in a specified number of sentences',
            'template': 'Summarize the following text in {length} sentences:\n\n{text}',
            'variables': ['text', 'length'],
            'category': 'content',
            'model': 'llama2',
            'temperature': 0.7
        },
        'translate': {
            'name': 'Translate',
            'description': 'Translate text to another language',
            'template': 'Translate the following text to {language}:\n\n{text}',
            'variables': ['text', 'language'],
            'category': 'language',
            'model': 'llama2',
            'temperature': 0.5
        },
        'code_review': {
            'name': 'Code Review',
            'description': 'Review code and provide feedback',
            'template': '''Review the following {language} code and provide feedback:

```{language}
{code}
```

Focus on:
- Code quality
- Potential bugs
- Best practices
- Suggestions for improvement''',
            'variables': ['code', 'language'],
            'category': 'code',
            'model': 'llama2',
            'temperature': 0.3
        },
        'explain_eli5': {
            'name': 'Explain Like I\'m 5',
            'description': 'Explain a concept in simple terms',
            'template': 'Explain {concept} in simple terms that a 5-year-old would understand.',
            'variables': ['concept'],
            'category': 'education',
            'model': 'llama2',
            'temperature': 0.7
        },
        'email_formal': {
            'name': 'Formal Email',
            'description': 'Generate a formal email',
            'template': '''Write a formal email with the following details:

To: {recipient}
Subject: {subject}

Content:
{content}

Tone: Professional and courteous''',
            'variables': ['recipient', 'subject', 'content'],
            'category': 'writing',
            'model': 'llama2',
            'temperature': 0.6
        },
        'brainstorm': {
            'name': 'Brainstorm Ideas',
            'description': 'Generate creative ideas on a topic',
            'template': 'Generate {count} creative ideas for: {topic}\n\nProvide diverse and innovative suggestions.',
            'variables': ['topic', 'count'],
            'category': 'creativity',
            'model': 'llama2',
            'temperature': 0.9
        },
        'debug_code': {
            'name': 'Debug Code',
            'description': 'Help debug code with an error',
            'template': '''I have the following {language} code that produces an error:

Code:
```{language}
{code}
```

Error:
{error}

Please help me identify and fix the problem.''',
            'variables': ['language', 'code', 'error'],
            'category': 'code',
            'model': 'llama2',
            'temperature': 0.3
        },
        'meeting_notes': {
            'name': 'Meeting Notes Summary',
            'description': 'Summarize meeting notes into action items',
            'template': '''Summarize the following meeting notes and extract action items:

{notes}

Format the output as:
1. Key Discussion Points
2. Decisions Made
3. Action Items (with assigned person if mentioned)
4. Next Steps''',
            'variables': ['notes'],
            'category': 'business',
            'model': 'llama2',
            'temperature': 0.5
        },
        'compare': {
            'name': 'Compare and Contrast',
            'description': 'Compare two concepts or items',
            'template': '''Compare and contrast {item1} and {item2}.

Provide:
1. Similarities
2. Differences
3. Use cases for each
4. Pros and cons''',
            'variables': ['item1', 'item2'],
            'category': 'analysis',
            'model': 'llama2',
            'temperature': 0.6
        },
        'technical_doc': {
            'name': 'Technical Documentation',
            'description': 'Generate technical documentation',
            'template': '''Create technical documentation for:

Feature/Function: {feature}
Purpose: {purpose}

Include:
1. Overview
2. Parameters/Inputs
3. Return Values/Outputs
4. Examples
5. Edge Cases''',
            'variables': ['feature', 'purpose'],
            'category': 'documentation',
            'model': 'llama2',
            'temperature': 0.4
        }
    }
    
    def list_templates(self, category: Optional[str] = None, 
                       include_custom: bool = True,
                       user_id: Optional[int] = None) -> Dict:
        """
        List available templates
        
        Args:
            category: Filter by category
            include_custom: Include custom user templates
            user_id: User ID for custom templates
            
        Returns:
            Dictionary of templates
        """
        templates = {}
        
        # Add built-in templates
        for key, template in self.TEMPLATES.items():
            if category is None or template['category'] == category:
                templates[key] = template
        
        # Add custom templates
        if include_custom and user_id:
            custom = self.get_custom_templates(user_id, category)
            for template in custom:
                templates[f"custom_{template['id']}"] = template
        
        return templates
    
    def get_template(self, template_name: str) -> Optional[Dict]:
        """
        Get a specific template
        
        Args:
            template_name: Template name/ID
            
        Returns:
            Template dictionary or None
        """
        return self.TEMPLATES.get(template_name)
    
    def render(self, template_name: str, variables: Dict) -> str:
        """
        Render template with variables
        
        Args:
            template_name: Template name/ID
            variables: Variable values
            
        Returns:
            Rendered prompt
        """
        template = self.TEMPLATES.get(template_name)
        if not template:
            # Try to load custom template
            if template_name.startswith('custom_'):
                template_id = int(template_name.replace('custom_', ''))
                template = self.get_custom_template(template_id)
        
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        prompt = template['template']
        
        # Replace variables
        for var, value in variables.items():
            prompt = prompt.replace(f'{{{var}}}', str(value))
        
        # Check for missing variables
        if '{' in prompt and '}' in prompt:
            import re
            missing = re.findall(r'\{(\w+)\}', prompt)
            if missing:
                raise ValueError(f"Missing variables: {', '.join(missing)}")
        
        return prompt
    
    def create_custom(self, user_id: int, name: str, description: str,
                     template: str, variables: List[str], 
                     category: Optional[str] = None,
                     model: str = 'llama2',
                     temperature: float = 0.7,
                     is_public: bool = False) -> int:
        """
        Create custom template
        
        Args:
            user_id: User ID
            name: Template name
            description: Template description
            template: Template string with {variables}
            variables: List of variable names
            category: Template category
            model: Recommended model
            temperature: Recommended temperature
            is_public: Make template public
            
        Returns:
            template_id: ID of created template
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO prompt_templates
                (user_id, name, description, template, variables, 
                 category, model, temperature, is_public)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, name, description, template, 
                  json.dumps(variables), category, model, 
                  temperature, is_public))
            conn.commit()
            return cursor.lastrowid
    
    def get_custom_template(self, template_id: int) -> Optional[Dict]:
        """
        Get a custom template by ID
        
        Args:
            template_id: Template ID
            
        Returns:
            Template dictionary or None
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, user_id, name, description, template, 
                       variables, category, model, temperature, 
                       is_public, usage_count, created_at
                FROM prompt_templates
                WHERE id = ?
            ''', (template_id,))
            
            row = cursor.fetchone()
            if row:
                result = dict(row)
                result['variables'] = json.loads(result['variables'])
                return result
            return None
    
    def get_custom_templates(self, user_id: int, 
                            category: Optional[str] = None) -> List[Dict]:
        """
        Get user's custom templates
        
        Args:
            user_id: User ID
            category: Filter by category
            
        Returns:
            List of templates
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if category:
                cursor.execute('''
                    SELECT id, name, description, template, variables,
                           category, model, temperature, usage_count
                    FROM prompt_templates
                    WHERE user_id = ? AND category = ?
                    ORDER BY usage_count DESC, created_at DESC
                ''', (user_id, category))
            else:
                cursor.execute('''
                    SELECT id, name, description, template, variables,
                           category, model, temperature, usage_count
                    FROM prompt_templates
                    WHERE user_id = ?
                    ORDER BY usage_count DESC, created_at DESC
                ''', (user_id,))
            
            templates = []
            for row in cursor.fetchall():
                template = dict(row)
                template['variables'] = json.loads(template['variables'])
                templates.append(template)
            
            return templates
    
    def update_custom(self, template_id: int, user_id: int, **updates) -> bool:
        """
        Update a custom template
        
        Args:
            template_id: Template ID
            user_id: User ID (for permission check)
            **updates: Fields to update
            
        Returns:
            True if updated, False otherwise
        """
        allowed_fields = ['name', 'description', 'template', 'variables', 
                         'category', 'model', 'temperature', 'is_public']
        
        update_fields = []
        values = []
        
        for field, value in updates.items():
            if field in allowed_fields:
                update_fields.append(f"{field} = ?")
                if field == 'variables' and isinstance(value, list):
                    values.append(json.dumps(value))
                else:
                    values.append(value)
        
        if not update_fields:
            return False
        
        values.extend([template_id, user_id])
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE prompt_templates
                SET {', '.join(update_fields)}
                WHERE id = ? AND user_id = ?
            ''', values)
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_custom(self, template_id: int, user_id: int) -> bool:
        """
        Delete a custom template
        
        Args:
            template_id: Template ID
            user_id: User ID (for permission check)
            
        Returns:
            True if deleted, False otherwise
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM prompt_templates
                WHERE id = ? AND user_id = ?
            ''', (template_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def increment_usage(self, template_id: int):
        """
        Increment template usage counter
        
        Args:
            template_id: Template ID
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE prompt_templates
                SET usage_count = usage_count + 1
                WHERE id = ?
            ''', (template_id,))
            conn.commit()
    
    def get_popular_templates(self, limit: int = 10) -> List[Dict]:
        """
        Get most popular public templates
        
        Args:
            limit: Maximum results
            
        Returns:
            List of popular templates
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, description, category, usage_count
                FROM prompt_templates
                WHERE is_public = 1
                ORDER BY usage_count DESC
                LIMIT ?
            ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_categories(self) -> List[str]:
        """
        Get all template categories
        
        Returns:
            List of category names
        """
        categories = set()
        
        # Built-in categories
        for template in self.TEMPLATES.values():
            if template.get('category'):
                categories.add(template['category'])
        
        # Custom categories
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT category
                FROM prompt_templates
                WHERE category IS NOT NULL
            ''')
            
            for row in cursor.fetchall():
                categories.add(row['category'])
        
        return sorted(list(categories))
