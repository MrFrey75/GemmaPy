from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from database import get_db_connection, init_db
from auth import hash_password, verify_password, generate_token, require_auth, require_admin
from ollama_manager import OllamaManager
from llm_cache import LLMCache
from retry_manager import RetryManager
from rag_manager import RAGManager
from metrics_collector import MetricsCollector
from cost_calculator import CostCalculator
from conversation_manager import ConversationManager
from prompt_templates import PromptTemplateManager
import os
import json
import time

app = Flask(__name__)
CORS(app)

# Initialize database on startup only if not in testing mode
if not app.config.get('TESTING'):
    with app.app_context():
        init_db()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        
        if not user or not verify_password(password, user['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        token = generate_token(user['id'], user['username'], bool(user['is_admin']))
        return jsonify({
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'is_admin': bool(user['is_admin'])
            }
        }), 200

@app.route('/api/data', methods=['GET'])
@require_auth
def get_data():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT d.*, u.username 
            FROM data d 
            JOIN users u ON d.user_id = u.id 
            WHERE d.user_id = ?
            ORDER BY d.created_at DESC
        ''', (request.user['user_id'],))
        
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        
        return jsonify({'data': data}), 200

@app.route('/api/data', methods=['POST'])
@require_auth
def create_data():
    data = request.get_json()
    content = data.get('content')
    
    if not content:
        return jsonify({'error': 'Content is required'}), 400
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO data (user_id, content) VALUES (?, ?)',
            (request.user['user_id'], content)
        )
        conn.commit()
        data_id = cursor.lastrowid
        
        return jsonify({
            'message': 'Data created successfully',
            'id': data_id
        }), 201

@app.route('/api/admin/users', methods=['GET'])
@require_admin
def get_all_users():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, is_admin, created_at FROM users')
        rows = cursor.fetchall()
        users = [dict(row) for row in rows]
        
        return jsonify({'users': users}), 200

@app.route('/api/admin/users', methods=['POST'])
@require_admin
def create_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    is_admin = data.get('is_admin', False)
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    hashed_pw = hash_password(password)
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)',
                (username, hashed_pw, int(is_admin))
            )
            conn.commit()
            user_id = cursor.lastrowid
            
            return jsonify({
                'message': 'User created successfully',
                'id': user_id,
                'username': username
            }), 201
    except Exception as e:
        return jsonify({'error': 'Username already exists'}), 400

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/api/version', methods=['GET'])
def version():
    """Get API version information"""
    return jsonify({
        'version': '1.1.0-dev',
        'release_date': 'TBD',
        'status': 'Development',
        'python_version': '3.8+',
        'features': {
            'authentication': True,
            'profiles': True,
            'ollama': True,
            'caching': True,
            'retry': True,
            'rag': True,
            'metrics': True,
            'costs': True,
            'conversations': True,
            'templates': True,
            'comparison': True
        }
    }), 200

# Profile management endpoints
@app.route('/api/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get the authenticated user's profile information"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, email, full_name, bio, phone, address, city, 
                   country, date_of_birth, website, company, job_title,
                   created_at, updated_at
            FROM users WHERE id = ?
        ''', (request.user['user_id'],))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'profile': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'full_name': user['full_name'],
                'bio': user['bio'],
                'phone': user['phone'],
                'address': user['address'],
                'city': user['city'],
                'country': user['country'],
                'date_of_birth': user['date_of_birth'],
                'website': user['website'],
                'company': user['company'],
                'job_title': user['job_title'],
                'created_at': user['created_at'],
                'updated_at': user['updated_at']
            }
        }), 200

@app.route('/api/profile', methods=['PUT'])
@require_auth
def update_profile():
    """Update the authenticated user's profile information"""
    data = request.get_json()
    
    # Fields that can be updated
    updatable_fields = {
        'email': data.get('email'),
        'full_name': data.get('full_name'),
        'bio': data.get('bio'),
        'phone': data.get('phone'),
        'address': data.get('address'),
        'city': data.get('city'),
        'country': data.get('country'),
        'date_of_birth': data.get('date_of_birth'),
        'website': data.get('website'),
        'company': data.get('company'),
        'job_title': data.get('job_title')
    }
    
    # Build dynamic update query
    updates = []
    params = []
    
    for field, value in updatable_fields.items():
        if value is not None:
            updates.append(f'{field} = ?')
            params.append(value)
    
    if not updates:
        return jsonify({'error': 'No fields to update'}), 400
    
    # Add updated_at timestamp
    updates.append('updated_at = CURRENT_TIMESTAMP')
    params.append(request.user['user_id'])
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
        
        # Fetch updated profile
        cursor.execute('''
            SELECT id, username, email, full_name, bio, phone, address, city,
                   country, date_of_birth, website, company, job_title,
                   created_at, updated_at
            FROM users WHERE id = ?
        ''', (request.user['user_id'],))
        user = cursor.fetchone()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'profile': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'full_name': user['full_name'],
                'bio': user['bio'],
                'phone': user['phone'],
                'address': user['address'],
                'city': user['city'],
                'country': user['country'],
                'date_of_birth': user['date_of_birth'],
                'website': user['website'],
                'company': user['company'],
                'job_title': user['job_title'],
                'created_at': user['created_at'],
                'updated_at': user['updated_at']
            }
        }), 200

@app.route('/api/profile/password', methods=['PUT'])
@require_auth
def change_password():
    """Change the authenticated user's password"""
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'error': 'Current password and new password required'}), 400
    
    if len(new_password) < 6:
        return jsonify({'error': 'New password must be at least 6 characters'}), 400
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM users WHERE id = ?', (request.user['user_id'],))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Verify current password
        if not verify_password(current_password, user['password']):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Update password
        new_hashed_password = hash_password(new_password)
        cursor.execute(
            'UPDATE users SET password = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (new_hashed_password, request.user['user_id'])
        )
        conn.commit()
        
        return jsonify({'message': 'Password changed successfully'}), 200

@app.route('/api/profile', methods=['DELETE'])
@require_auth
def delete_profile():
    """Delete the authenticated user's account and all associated data"""
    data = request.get_json()
    password = data.get('password')
    
    if not password:
        return jsonify({'error': 'Password required to delete account'}), 400
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT password, is_admin FROM users WHERE id = ?', (request.user['user_id'],))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Verify password
        if not verify_password(password, user['password']):
            return jsonify({'error': 'Invalid password'}), 401
        
        # Prevent deletion of admin account
        if user['is_admin']:
            return jsonify({'error': 'Cannot delete admin account'}), 403
        
        # Delete user's data first (foreign key constraint)
        cursor.execute('DELETE FROM data WHERE user_id = ?', (request.user['user_id'],))
        
        # Delete user account
        cursor.execute('DELETE FROM users WHERE id = ?', (request.user['user_id'],))
        conn.commit()
        
        return jsonify({'message': 'Account deleted successfully'}), 200

# Ollama/LLM endpoints
ollama = OllamaManager()
llm_cache = LLMCache()
retry_manager = RetryManager()
rag_manager = RAGManager(ollama)

@app.route('/api/ollama/status', methods=['GET'])
@require_auth
def ollama_status():
    """Check if Ollama service is running"""
    is_running = ollama.is_running()
    return jsonify({
        'running': is_running,
        'message': 'Ollama is running' if is_running else 'Ollama is not running'
    }), 200

@app.route('/api/ollama/models', methods=['GET'])
@require_auth
def ollama_list_models():
    """List all available Ollama models"""
    try:
        models = ollama.list_models()
        return jsonify({
            'models': models,
            'count': len(models)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ollama/models/<model_name>', methods=['GET'])
@require_auth
def ollama_model_info(model_name):
    """Get detailed information about a specific model"""
    try:
        info = ollama.show_model_info(model_name)
        return jsonify(info), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ollama/models/pull', methods=['POST'])
@require_auth
def ollama_pull_model():
    """Pull/download a model"""
    data = request.get_json()
    model_name = data.get('model')
    
    if not model_name:
        return jsonify({'error': 'Model name is required'}), 400
    
    try:
        result = ollama.pull_model(model_name)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ollama/models/<model_name>', methods=['DELETE'])
@require_admin
def ollama_delete_model(model_name):
    """Delete a model (admin only)"""
    try:
        result = ollama.delete_model(model_name)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ollama/generate', methods=['POST'])
@require_auth
def ollama_generate():
    """Generate text from a prompt with caching and retry support"""
    data = request.get_json()
    model = data.get('model', 'llama2')
    prompt = data.get('prompt')
    system = data.get('system')
    temperature = data.get('temperature', 0.7)
    max_tokens = data.get('max_tokens')
    use_cache = data.get('use_cache', True)
    use_retry = data.get('use_retry', True)
    
    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400
    
    start_time = time.time()
    metrics_collector = MetricsCollector()
    error = None
    cached = False
    response_text = None
    
    try:
        # Check cache first
        cached_response = None
        cache_key = None
        if use_cache:
            cache_key = llm_cache.generate_cache_key(
                model, prompt, system, temperature, max_tokens
            )
            cached_response = llm_cache.get(cache_key)
        
        if cached_response:
            cached = True
            response_text = cached_response
            duration = time.time() - start_time
            
            # Record metrics
            metrics_collector.record(
                user_id=request.user['user_id'],
                model=model,
                endpoint='/api/ollama/generate',
                prompt=prompt,
                response=response_text,
                duration=duration,
                cached=True
            )
            
            return jsonify({
                'response': cached_response,
                'cached': True,
                'cache_key': cache_key,
                'model': model
            }), 200
        
        # Generate with retry if enabled
        if use_retry:
            response = retry_manager.generate_with_retry(
                ollama,
                model=model,
                prompt=prompt,
                system=system,
                temperature=temperature,
                max_tokens=max_tokens
            )
        else:
            response = ollama.generate(
                model=model,
                prompt=prompt,
                system=system,
                temperature=temperature,
                max_tokens=max_tokens
            )
        
        response_text = response.get('response', '')
        duration = time.time() - start_time
        
        # Cache the response
        if use_cache and cache_key:
            llm_cache.set(
                cache_key, model, prompt, response_text,
                system, temperature, max_tokens
            )
        
        # Record metrics
        metrics_collector.record(
            user_id=request.user['user_id'],
            model=model,
            endpoint='/api/ollama/generate',
            prompt=prompt,
            response=response_text,
            duration=duration,
            cached=False
        )
        
        # Store generation in database
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO data (user_id, content)
                VALUES (?, ?)
            ''', (request.user['user_id'], f"Ollama: {prompt[:100]}... -> {response_text[:100]}..."))
            conn.commit()
        
        return jsonify(response), 200
    except Exception as e:
        error = e
        duration = time.time() - start_time
        
        # Record error metrics
        metrics_collector.record(
            user_id=request.user['user_id'],
            model=model,
            endpoint='/api/ollama/generate',
            prompt=prompt,
            response=None,
            duration=duration,
            error=error,
            cached=False
        )
        
        return jsonify({'error': str(e)}), 500

@app.route('/api/ollama/generate/stream', methods=['POST'])
@require_auth
def ollama_generate_stream():
    """Generate text with streaming response"""
    data = request.get_json()
    model = data.get('model', 'llama2')
    prompt = data.get('prompt')
    system = data.get('system')
    temperature = data.get('temperature', 0.7)
    max_tokens = data.get('max_tokens')
    
    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400
    
    def generate():
        try:
            for chunk in ollama.generate_stream(
                model=model,
                prompt=prompt,
                system=system,
                temperature=temperature,
                max_tokens=max_tokens
            ):
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )

@app.route('/api/ollama/chat', methods=['POST'])
@require_auth
def ollama_chat():
    """Chat completion with conversation history"""
    data = request.get_json()
    model = data.get('model', 'llama2')
    messages = data.get('messages')
    temperature = data.get('temperature', 0.7)
    
    if not messages or not isinstance(messages, list):
        return jsonify({'error': 'Messages array is required'}), 400
    
    start_time = time.time()
    metrics_collector = MetricsCollector()
    
    try:
        response = ollama.chat(
            model=model,
            messages=messages,
            temperature=temperature
        )
        
        duration = time.time() - start_time
        last_message = messages[-1].get('content', '') if messages else ''
        response_text = response.get('message', {}).get('content', '')
        
        # Record metrics
        metrics_collector.record(
            user_id=request.user['user_id'],
            model=model,
            endpoint='/api/ollama/chat',
            prompt=last_message,
            response=response_text,
            duration=duration,
            cached=False
        )
        
        # Store chat in database
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO data (user_id, content)
                VALUES (?, ?)
            ''', (request.user['user_id'], f"Chat: {last_message[:100]}... -> {response_text[:100]}..."))
            conn.commit()
        
        return jsonify(response), 200
    except Exception as e:
        duration = time.time() - start_time
        last_message = messages[-1].get('content', '') if messages else ''
        
        # Record error metrics
        metrics_collector.record(
            user_id=request.user['user_id'],
            model=model,
            endpoint='/api/ollama/chat',
            prompt=last_message,
            response=None,
            duration=duration,
            error=e,
            cached=False
        )
        
        return jsonify({'error': str(e)}), 500

@app.route('/api/ollama/chat/stream', methods=['POST'])
@require_auth
def ollama_chat_stream():
    """Chat completion with streaming response"""
    data = request.get_json()
    model = data.get('model', 'llama2')
    messages = data.get('messages')
    temperature = data.get('temperature', 0.7)
    
    if not messages or not isinstance(messages, list):
        return jsonify({'error': 'Messages array is required'}), 400
    
    def generate():
        try:
            for chunk in ollama.chat_stream(
                model=model,
                messages=messages,
                temperature=temperature
            ):
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )

@app.route('/api/ollama/embeddings', methods=['POST'])
@require_auth
def ollama_embeddings():
    """Generate embeddings for text"""
    data = request.get_json()
    model = data.get('model', 'llama2')
    text = data.get('text')
    
    if not text:
        return jsonify({'error': 'Text is required'}), 400
    
    try:
        embeddings = ollama.embeddings(model, text)
        return jsonify({
            'embeddings': embeddings,
            'dimensions': len(embeddings)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Phase 1 Enhancement Endpoints

# Cache Management
@app.route('/api/cache/stats', methods=['GET'])
@require_auth
def cache_stats():
    """Get cache statistics"""
    try:
        stats = llm_cache.get_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cache/clear', methods=['POST'])
@require_admin
def cache_clear():
    """Clear cache (admin only)"""
    data = request.get_json() or {}
    pattern = data.get('pattern')
    
    try:
        deleted = llm_cache.invalidate(pattern)
        return jsonify({
            'message': 'Cache cleared successfully',
            'deleted_entries': deleted
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cache/clear-expired', methods=['POST'])
@require_admin
def cache_clear_expired():
    """Clear expired cache entries (admin only)"""
    try:
        deleted = llm_cache.clear_expired()
        return jsonify({
            'message': 'Expired cache entries cleared',
            'deleted_entries': deleted
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Retry Statistics
@app.route('/api/retry/stats', methods=['GET'])
@require_admin
def retry_stats():
    """Get retry statistics (admin only)"""
    try:
        stats = retry_manager.get_stats()
        failure_rate = retry_manager.get_failure_rate()
        stats['failure_rate'] = failure_rate
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# RAG Endpoints
@app.route('/api/rag/documents', methods=['POST'])
@require_auth
def rag_add_document():
    """Add a document to the RAG system"""
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    source = data.get('source')
    metadata = data.get('metadata')
    
    if not title or not content:
        return jsonify({'error': 'Title and content are required'}), 400
    
    try:
        doc_id = rag_manager.add_document(
            user_id=request.user['user_id'],
            title=title,
            content=content,
            source=source,
            metadata=metadata
        )
        return jsonify({
            'message': 'Document added successfully',
            'document_id': doc_id
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rag/documents', methods=['GET'])
@require_auth
def rag_list_documents():
    """List user's documents"""
    try:
        documents = rag_manager.list_documents(request.user['user_id'])
        return jsonify({'documents': documents}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rag/documents/<int:doc_id>', methods=['DELETE'])
@require_auth
def rag_delete_document(doc_id):
    """Delete a document"""
    try:
        success = rag_manager.delete_document(doc_id, request.user['user_id'])
        if success:
            return jsonify({'message': 'Document deleted successfully'}), 200
        else:
            return jsonify({'error': 'Document not found or access denied'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rag/search', methods=['POST'])
@require_auth
def rag_search():
    """Search for relevant document chunks"""
    data = request.get_json()
    query = data.get('query')
    top_k = data.get('top_k', 3)
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    try:
        results = rag_manager.search(query, request.user['user_id'], top_k)
        return jsonify({'results': results}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rag/generate', methods=['POST'])
@require_auth
def rag_generate():
    """Generate response using RAG"""
    data = request.get_json()
    query = data.get('query')
    model = data.get('model', 'llama2')
    top_k = data.get('top_k', 3)
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    try:
        result = rag_manager.generate_with_context(
            query, request.user['user_id'], model, top_k
        )
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rag/stats', methods=['GET'])
@require_admin
def rag_stats():
    """Get RAG statistics (admin only)"""
    try:
        stats = rag_manager.get_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# PHASE 2: Metrics and Cost Tracking Endpoints
# ============================================================================

@app.route('/api/metrics/dashboard', methods=['GET'])
@require_auth
def metrics_dashboard():
    """Get metrics dashboard data"""
    try:
        days = request.args.get('days', 7, type=int)
        collector = MetricsCollector()
        
        # Users get their own stats, admins can see all
        user_id = None if request.user.get('is_admin') else request.user['user_id']
        stats = collector.get_dashboard_stats(user_id=user_id, days=days)
        
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/timeseries', methods=['GET'])
@require_auth
def metrics_timeseries():
    """Get time series metrics data"""
    try:
        days = request.args.get('days', 7, type=int)
        interval = request.args.get('interval', 'hour')
        collector = MetricsCollector()
        
        user_id = None if request.user.get('is_admin') else request.user['user_id']
        data = collector.get_time_series(user_id=user_id, days=days, interval=interval)
        
        return jsonify({'data': data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/endpoints', methods=['GET'])
@require_auth
def metrics_endpoints():
    """Get endpoint statistics"""
    try:
        days = request.args.get('days', 7, type=int)
        collector = MetricsCollector()
        
        user_id = None if request.user.get('is_admin') else request.user['user_id']
        data = collector.get_endpoint_stats(user_id=user_id, days=days)
        
        return jsonify({'endpoints': data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/<int:metric_id>/rate', methods=['POST'])
@require_auth
def rate_metric(metric_id):
    """Rate a specific metric/response"""
    try:
        data = request.get_json()
        rating = data.get('rating')
        
        if rating not in [-1, 0, 1]:
            return jsonify({'error': 'Rating must be -1, 0, or 1'}), 400
        
        collector = MetricsCollector()
        collector.update_rating(metric_id, rating)
        
        return jsonify({'message': 'Rating recorded successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/costs/summary', methods=['GET'])
@require_auth
def cost_summary():
    """Get cost summary for the user"""
    try:
        period = request.args.get('period', 'month')
        calculator = CostCalculator()
        
        costs = calculator.get_user_costs(
            user_id=request.user['user_id'],
            period=period
        )
        
        return jsonify(costs), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/costs/projection', methods=['GET'])
@require_auth
def cost_projection():
    """Get cost projection for the user"""
    try:
        period = request.args.get('period', 'month')
        calculator = CostCalculator()
        
        projection = calculator.get_cost_projection(
            user_id=request.user['user_id'],
            period=period
        )
        
        return jsonify(projection), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/costs/all', methods=['GET'])
@require_admin
def admin_all_costs():
    """Get costs for all users (admin only)"""
    try:
        period = request.args.get('period', 'month')
        calculator = CostCalculator()
        
        costs = calculator.get_all_users_costs(period=period)
        
        return jsonify(costs), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/costs/pricing', methods=['GET'])
@require_admin
def get_pricing():
    """Get current pricing model (admin only)"""
    try:
        calculator = CostCalculator()
        pricing = calculator.get_pricing()
        
        return jsonify(pricing), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/costs/pricing', methods=['PUT'])
@require_admin
def update_pricing():
    """Update pricing for a model (admin only)"""
    try:
        data = request.get_json()
        model = data.get('model')
        input_cost = data.get('input_cost')
        output_cost = data.get('output_cost')
        
        if not all([model, input_cost is not None, output_cost is not None]):
            return jsonify({'error': 'Model, input_cost, and output_cost required'}), 400
        
        calculator = CostCalculator()
        calculator.update_pricing(model, input_cost, output_cost)
        
        return jsonify({'message': f'Pricing updated for {model}'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# PHASE 3: CONVERSATION PERSISTENCE ENDPOINTS
# ============================================================================

@app.route('/api/conversations', methods=['POST'])
@require_auth
def create_conversation():
    """Create a new conversation"""
    try:
        data = request.get_json()
        title = data.get('title')
        model = data.get('model', 'llama2')
        system_prompt = data.get('system_prompt')
        
        if not title:
            return jsonify({'error': 'Title required'}), 400
        
        manager = ConversationManager()
        conversation_id = manager.create(
            user_id=request.user['user_id'],
            title=title,
            model=model,
            system_prompt=system_prompt
        )
        
        return jsonify({
            'message': 'Conversation created',
            'conversation_id': conversation_id
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversations', methods=['GET'])
@require_auth
def list_conversations():
    """List user's conversations"""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        manager = ConversationManager()
        conversations = manager.list_user_conversations(
            user_id=request.user['user_id'],
            limit=limit
        )
        
        return jsonify({'conversations': conversations}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversations/<int:conversation_id>', methods=['GET'])
@require_auth
def get_conversation(conversation_id):
    """Get conversation details with messages"""
    try:
        manager = ConversationManager()
        conversation = manager.get(conversation_id)
        
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        # Check permission
        if conversation['user_id'] != request.user['user_id']:
            return jsonify({'error': 'Access denied'}), 403
        
        messages = manager.get_messages(conversation_id)
        conversation['messages'] = messages
        
        return jsonify({'conversation': conversation}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversations/<int:conversation_id>', methods=['PUT'])
@require_auth
def update_conversation(conversation_id):
    """Update conversation title"""
    try:
        data = request.get_json()
        title = data.get('title')
        
        if not title:
            return jsonify({'error': 'Title required'}), 400
        
        manager = ConversationManager()
        conversation = manager.get(conversation_id)
        
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        if conversation['user_id'] != request.user['user_id']:
            return jsonify({'error': 'Access denied'}), 403
        
        updated = manager.update_title(conversation_id, title)
        
        if updated:
            return jsonify({'message': 'Conversation updated'}), 200
        return jsonify({'error': 'Update failed'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversations/<int:conversation_id>', methods=['DELETE'])
@require_auth
def delete_conversation(conversation_id):
    """Delete a conversation"""
    try:
        manager = ConversationManager()
        deleted = manager.delete(
            conversation_id=conversation_id,
            user_id=request.user['user_id']
        )
        
        if deleted:
            return jsonify({'message': 'Conversation deleted'}), 200
        return jsonify({'error': 'Conversation not found or access denied'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversations/<int:conversation_id>/messages', methods=['POST'])
@require_auth
def add_message(conversation_id):
    """Add a message to conversation"""
    try:
        data = request.get_json()
        role = data.get('role')
        content = data.get('content')
        
        if not role or not content:
            return jsonify({'error': 'Role and content required'}), 400
        
        manager = ConversationManager()
        conversation = manager.get(conversation_id)
        
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        if conversation['user_id'] != request.user['user_id']:
            return jsonify({'error': 'Access denied'}), 403
        
        message_id = manager.add_message(conversation_id, role, content)
        
        return jsonify({
            'message': 'Message added',
            'message_id': message_id
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversations/<int:conversation_id>/generate', methods=['POST'])
@require_auth
def conversation_generate(conversation_id):
    """Generate response in conversation context"""
    try:
        data = request.get_json()
        user_message = data.get('message')
        temperature = data.get('temperature', 0.7)
        use_cache = data.get('use_cache', True)
        use_retry = data.get('use_retry', True)
        
        if not user_message:
            return jsonify({'error': 'Message required'}), 400
        
        manager = ConversationManager()
        conversation = manager.get(conversation_id)
        
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        if conversation['user_id'] != request.user['user_id']:
            return jsonify({'error': 'Access denied'}), 403
        
        # Add user message
        manager.add_message(conversation_id, 'user', user_message)
        
        # Get conversation history
        messages = manager.get_messages(conversation_id)
        
        # Build context from messages
        context = ""
        system_prompt = None
        for msg in messages:
            if msg['role'] == 'system':
                system_prompt = msg['content']
            elif msg['role'] == 'user':
                context += f"User: {msg['content']}\n"
            elif msg['role'] == 'assistant':
                context += f"Assistant: {msg['content']}\n"
        
        # Generate response
        start_time = time.time()
        ollama = OllamaManager()
        
        if use_retry:
            retry_manager = RetryManager()
            response = retry_manager.generate_with_retry(
                model=conversation['model'],
                prompt=user_message,
                system=system_prompt,
                temperature=temperature,
                context=context
            )
        else:
            response = ollama.generate(
                model=conversation['model'],
                prompt=user_message,
                system=system_prompt,
                temperature=temperature
            )
        
        duration = time.time() - start_time
        
        # Add assistant message
        manager.add_message(conversation_id, 'assistant', response['response'])
        
        # Collect metrics
        metrics = MetricsCollector()
        metrics.record(
            user_id=request.user['user_id'],
            model=conversation['model'],
            endpoint='/api/conversations/generate',
            prompt=user_message,
            response=response['response'],
            duration=duration,
            cached=response.get('cached', False)
        )
        
        return jsonify({
            'response': response['response'],
            'conversation_id': conversation_id,
            'model': conversation['model']
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversations/search', methods=['GET'])
@require_auth
def search_conversations():
    """Search conversations"""
    try:
        query = request.args.get('q', '')
        limit = request.args.get('limit', 20, type=int)
        
        if not query:
            return jsonify({'error': 'Query parameter required'}), 400
        
        manager = ConversationManager()
        results = manager.search_conversations(
            user_id=request.user['user_id'],
            query=query,
            limit=limit
        )
        
        return jsonify({'results': results}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversations/statistics', methods=['GET'])
@require_auth
def conversation_statistics():
    """Get conversation statistics for user"""
    try:
        manager = ConversationManager()
        stats = manager.get_statistics(request.user['user_id'])
        
        return jsonify({'statistics': stats}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# PHASE 3: PROMPT TEMPLATES ENDPOINTS
# ============================================================================

@app.route('/api/templates', methods=['GET'])
@require_auth
def list_templates():
    """List available templates"""
    try:
        category = request.args.get('category')
        include_custom = request.args.get('include_custom', 'true').lower() == 'true'
        
        manager = PromptTemplateManager()
        templates = manager.list_templates(
            category=category,
            include_custom=include_custom,
            user_id=request.user['user_id'] if include_custom else None
        )
        
        return jsonify({'templates': templates}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/templates/categories', methods=['GET'])
@require_auth
def list_categories():
    """List template categories"""
    try:
        manager = PromptTemplateManager()
        categories = manager.get_categories()
        
        return jsonify({'categories': categories}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/templates/<template_name>', methods=['GET'])
@require_auth
def get_template(template_name):
    """Get specific template"""
    try:
        manager = PromptTemplateManager()
        template = manager.get_template(template_name)
        
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        return jsonify({'template': template}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/templates/render', methods=['POST'])
@require_auth
def render_template():
    """Render template with variables"""
    try:
        data = request.get_json()
        template_name = data.get('template_name')
        variables = data.get('variables', {})
        generate = data.get('generate', False)
        model = data.get('model', 'llama2')
        temperature = data.get('temperature', 0.7)
        
        if not template_name:
            return jsonify({'error': 'template_name required'}), 400
        
        manager = PromptTemplateManager()
        prompt = manager.render(template_name, variables)
        
        # Optionally generate response immediately
        if generate:
            start_time = time.time()
            ollama = OllamaManager()
            response = ollama.generate(
                model=model,
                prompt=prompt,
                temperature=temperature
            )
            duration = time.time() - start_time
            
            # Collect metrics
            metrics = MetricsCollector()
            metrics.record(
                user_id=request.user['user_id'],
                model=model,
                endpoint='/api/templates/render',
                prompt=prompt,
                response=response['response'],
                duration=duration
            )
            
            return jsonify({
                'prompt': prompt,
                'response': response['response']
            }), 200
        
        return jsonify({'prompt': prompt}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/templates/custom', methods=['POST'])
@require_auth
def create_custom_template():
    """Create custom template"""
    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        template = data.get('template')
        variables = data.get('variables', [])
        category = data.get('category')
        model = data.get('model', 'llama2')
        temperature = data.get('temperature', 0.7)
        is_public = data.get('is_public', False)
        
        if not name or not template:
            return jsonify({'error': 'name and template required'}), 400
        
        manager = PromptTemplateManager()
        template_id = manager.create_custom(
            user_id=request.user['user_id'],
            name=name,
            description=description,
            template=template,
            variables=variables,
            category=category,
            model=model,
            temperature=temperature,
            is_public=is_public
        )
        
        return jsonify({
            'message': 'Template created',
            'template_id': template_id
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/templates/custom/<int:template_id>', methods=['GET'])
@require_auth
def get_custom_template(template_id):
    """Get custom template"""
    try:
        manager = PromptTemplateManager()
        template = manager.get_custom_template(template_id)
        
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        return jsonify({'template': template}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/templates/custom/<int:template_id>', methods=['PUT'])
@require_auth
def update_custom_template(template_id):
    """Update custom template"""
    try:
        data = request.get_json()
        
        manager = PromptTemplateManager()
        updated = manager.update_custom(
            template_id=template_id,
            user_id=request.user['user_id'],
            **data
        )
        
        if updated:
            return jsonify({'message': 'Template updated'}), 200
        return jsonify({'error': 'Template not found or access denied'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/templates/custom/<int:template_id>', methods=['DELETE'])
@require_auth
def delete_custom_template(template_id):
    """Delete custom template"""
    try:
        manager = PromptTemplateManager()
        deleted = manager.delete_custom(
            template_id=template_id,
            user_id=request.user['user_id']
        )
        
        if deleted:
            return jsonify({'message': 'Template deleted'}), 200
        return jsonify({'error': 'Template not found or access denied'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/templates/popular', methods=['GET'])
@require_auth
def get_popular_templates():
    """Get popular templates"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        manager = PromptTemplateManager()
        templates = manager.get_popular_templates(limit=limit)
        
        return jsonify({'templates': templates}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# PHASE 4: MULTI-MODEL COMPARISON ENDPOINTS
# ============================================================================

@app.route('/api/compare/models', methods=['POST'])
@require_auth
def compare_models():
    """Compare responses from multiple models"""
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        models = data.get('models', [])
        system = data.get('system')
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens')
        
        if not prompt:
            return jsonify({'error': 'Prompt required'}), 400
        
        if not models or len(models) < 2:
            return jsonify({'error': 'At least 2 models required'}), 400
        
        from multi_model_comparator import MultiModelComparator
        comparator = MultiModelComparator(ollama)
        
        result = comparator.compare_models(
            user_id=request.user['user_id'],
            prompt=prompt,
            models=models,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/compare/comparisons', methods=['GET'])
@require_auth
def list_comparisons():
    """List user's comparisons"""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        from multi_model_comparator import MultiModelComparator
        comparator = MultiModelComparator(ollama)
        
        comparisons = comparator.list_comparisons(
            user_id=request.user['user_id'],
            limit=limit
        )
        
        return jsonify({'comparisons': comparisons}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/compare/comparisons/<int:comparison_id>', methods=['GET'])
@require_auth
def get_comparison(comparison_id):
    """Get comparison details"""
    try:
        from multi_model_comparator import MultiModelComparator
        comparator = MultiModelComparator(ollama)
        
        comparison = comparator.get_comparison(
            comparison_id=comparison_id,
            user_id=request.user['user_id']
        )
        
        if not comparison:
            return jsonify({'error': 'Comparison not found'}), 404
        
        return jsonify({'comparison': comparison}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/compare/comparisons/<int:comparison_id>', methods=['DELETE'])
@require_auth
def delete_comparison(comparison_id):
    """Delete a comparison"""
    try:
        from multi_model_comparator import MultiModelComparator
        comparator = MultiModelComparator(ollama)
        
        deleted = comparator.delete_comparison(
            comparison_id=comparison_id,
            user_id=request.user['user_id']
        )
        
        if deleted:
            return jsonify({'message': 'Comparison deleted'}), 200
        return jsonify({'error': 'Comparison not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/compare/responses/<int:response_id>/rate', methods=['POST'])
@require_auth
def rate_comparison_response(response_id):
    """Rate a specific model's response"""
    try:
        data = request.get_json()
        rating = data.get('rating')
        
        if rating not in [-1, 0, 1]:
            return jsonify({'error': 'Rating must be -1, 0, or 1'}), 400
        
        from multi_model_comparator import MultiModelComparator
        comparator = MultiModelComparator(ollama)
        
        success = comparator.rate_response(
            response_id=response_id,
            user_id=request.user['user_id'],
            rating=rating
        )
        
        if success:
            return jsonify({'message': 'Rating recorded'}), 200
        return jsonify({'error': 'Response not found or access denied'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/compare/rankings', methods=['GET'])
@require_auth
def get_model_rankings():
    """Get model rankings based on user ratings"""
    try:
        days = request.args.get('days', 30, type=int)
        
        from multi_model_comparator import MultiModelComparator
        comparator = MultiModelComparator(ollama)
        
        # Regular users see their own rankings, admins see all
        user_id = None if request.user.get('is_admin') else request.user['user_id']
        
        rankings = comparator.get_model_rankings(
            user_id=user_id,
            days=days
        )
        
        return jsonify({'rankings': rankings}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/compare/statistics', methods=['GET'])
@require_auth
def get_comparison_statistics():
    """Get comparison statistics"""
    try:
        from multi_model_comparator import MultiModelComparator
        comparator = MultiModelComparator(ollama)
        
        # Regular users see their own stats, admins see all
        user_id = None if request.user.get('is_admin') else request.user['user_id']
        
        stats = comparator.get_statistics(user_id=user_id)
        
        return jsonify({'statistics': stats}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
