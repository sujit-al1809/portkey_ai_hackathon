"""
Dashboard API Server
Serves optimization data to the Next.js dashboard
Integrates the Multi-Agent Orchestration System
"""

from flask import Flask, jsonify, request, session
from flask_cors import CORS
import json
import os
from pathlib import Path
from models import PromptData
from replay_engine import ReplayEngine
from quality_evaluator import QualityEvaluator
from optimizer import CostQualityOptimizer
from database import (
    init_db, get_dashboard_data, save_prompt, 
    save_completion, save_quality_evaluation, save_recommendation
)
from observability import (
    get_system_health, metrics, api_logger, replay_logger
)
from orchestrator import CostQualityOrchestrator
from user_metadata import user_service
from cache_manager import cache_manager
from session_manager import session_manager, chat_manager

app = Flask(__name__)
CORS(app)  # Enable CORS for Next.js frontend
app.secret_key = os.getenv("SECRET_KEY", "hackathon-secret-key-change-in-prod")

# Initialize database
init_db()

# Initialize global components
_replay_engine = None
_quality_evaluator = None
_orchestrator = None


def get_replay_engine():
    global _replay_engine
    if _replay_engine is None:
        _replay_engine = ReplayEngine()
    return _replay_engine


def get_quality_evaluator():
    global _quality_evaluator
    if _quality_evaluator is None:
        _quality_evaluator = QualityEvaluator()
    return _quality_evaluator


def get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = CostQualityOrchestrator(get_replay_engine(), get_quality_evaluator())
    return _orchestrator


def get_latest_analysis_results():
    """
    Get the most recent analysis results from cache or database.
    Used by /api/optimize to ensure data consistency with /analyze
    """
    import sqlite3
    from pathlib import Path
    
    try:
        db_path = Path(__file__).parent / "data" / "optimization.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get most recent prompt analysis
        cursor.execute("""
            SELECT DISTINCT p.id, p.prompt, p.use_case, p.created_at
            FROM prompts p
            ORDER BY p.created_at DESC
            LIMIT 1
        """)
        
        prompt_row = cursor.fetchone()
        if not prompt_row:
            conn.close()
            return None
        
        prompt_id = prompt_row['id']
        
        # Get completions for this prompt
        cursor.execute("""
            SELECT model_name, completion, cost, latency_ms, success
            FROM completions
            WHERE prompt_id = ?
        """, (prompt_id,))
        
        completions = []
        for row in cursor.fetchall():
            completions.append({
                'model_name': row['model_name'],
                'response': row['completion'],
                'cost': row['cost'],
                'latency_ms': row['latency_ms'],
                'success': bool(row['success'])
            })
        
        # Get quality evaluations
        cursor.execute("""
            SELECT model_name, overall_score, dimension_scores
            FROM quality_evaluations
            WHERE prompt_id = ?
        """, (prompt_id,))
        
        evaluations = []
        for row in cursor.fetchall():
            evaluations.append({
                'model_name': row['model_name'],
                'quality_score': row['overall_score'] / 100.0,  # Convert to 0-1 scale
                'cost': next((c['cost'] for c in completions if c['model_name'] == row['model_name']), 0)
            })
        
        conn.close()
        
        return {
            'completions': completions,
            'evaluations': evaluations
        }
    except Exception as e:
        print(f"Error fetching latest analysis: {e}")
        return None


# ============================================================================
# SESSION & AUTHENTICATION ENDPOINTS
# ============================================================================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """
    Simple username-based login (no password for hackathon).
    Creates session and returns user's historical conversations.
    """
    try:
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        
        if not username:
            return jsonify({'error': 'Username required'}), 400
        
        # Create or retrieve session
        session_data = session_manager.login(username)
        
        # Get user's conversation history
        history = chat_manager.get_user_history(session_data.user_id, limit=20)
        
        return jsonify({
            'status': 'success',
            'session_id': session_data.session_id,
            'username': session_data.username,
            'user_id': session_data.user_id,
            'history': [
                {
                    'chat_id': h.chat_id,
                    'question': h.question,
                    'response': h.response,
                    'model_used': h.model_used,
                    'quality_score': h.quality_score,
                    'cost': h.cost,
                    'created_at': h.created_at
                }
                for h in history
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout user"""
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id')
        
        if session_id:
            session_manager.logout(session_id)
        
        return jsonify({'status': 'logged_out'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/history/<user_id>')
def get_history(user_id: str):
    """Get user's conversation history"""
    try:
        history = chat_manager.get_user_history(user_id, limit=50)
        
        return jsonify({
            'user_id': user_id,
            'total': len(history),
            'chats': [
                {
                    'chat_id': h.chat_id,
                    'question': h.question[:100] + '...' if len(h.question) > 100 else h.question,
                    'model': h.model_used,
                    'quality': h.quality_score,
                    'cost': h.cost,
                    'date': h.created_at
                }
                for h in history
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/history/<user_id>/similar', methods=['POST'])
def find_similar_question(user_id: str):
    """
    Find if user asked similar question before.
    If found, return cached response (no LLM call needed!).
    """
    try:
        data = request.get_json() or {}
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'similar': None})
        
        # Check if similar question exists in history
        similar = chat_manager.find_similar_question(
            user_id, 
            question,
            similarity_threshold=0.75
        )
        
        if similar:
            return jsonify({
                'similar': True,
                'similarity_score': similar.similarity_score,
                'original_question': similar.question,
                'cached_response': similar.response,
                'model_used': similar.model_used,
                'quality_score': similar.quality_score,
                'cost': 0.0,  # No cost for cached response
                'message': f'Found similar question (similarity: {similar.similarity_score:.0%}). Using cached response!'
            })
        else:
            return jsonify({
                'similar': False,
                'message': 'No similar question found. Will run fresh analysis.'
            })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health_check():
    """System health check endpoint for monitoring"""
    health = get_system_health()
    status_code = 200 if health['status'] == 'healthy' else 503
    return jsonify(health), status_code


@app.route('/metrics')
def get_metrics():
    """Prometheus-compatible metrics endpoint"""
    return metrics.export_prometheus(), 200, {'Content-Type': 'text/plain'}


@app.route('/api/system-stats')
def get_system_stats():
    """Get detailed system statistics"""
    return jsonify(metrics.get_metrics())


@app.route('/api/optimize', methods=['POST'])
def run_optimization():
    """
    Run the multi-agent cost-quality optimization pipeline
    Uses most recent analysis data from database for accuracy
    
    Request body:
    {
        "user_id": "optional_user_id"
    }
    
    Returns business-readable recommendation based on actual test data
    """
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id', 'default')
        
        api_logger.log_event('optimize_request', {'user_id': user_id})
        
        # Get most recent analysis results from database
        latest_analysis = get_latest_analysis_results()
        
        if not latest_analysis or not latest_analysis.get('evaluations'):
            # Fallback to orchestrator if no analysis exists
            orchestrator = get_orchestrator()
            result = orchestrator.run_optimization(user_id, 6, 3)
        else:
            # Use actual analysis results for consistency with /analyze endpoint
            evaluations = latest_analysis.get('evaluations', [])
            
            if not evaluations:
                orchestrator = get_orchestrator()
                result = orchestrator.run_optimization(user_id, 6, 3)
            else:
                # Build result from actual analysis data
                evaluations_sorted = sorted(evaluations, key=lambda x: x['cost'], reverse=True)
                
                if len(evaluations_sorted) >= 2:
                    most_expensive = evaluations_sorted[0]
                    cheapest = evaluations_sorted[-1]
                    cost_reduction = ((most_expensive['cost'] - cheapest['cost']) / most_expensive['cost']) * 100
                    quality_diff = (most_expensive['quality_score'] - cheapest['quality_score']) * 100  # Convert to percentage
                else:
                    cost_reduction = 0
                    quality_diff = 0
                
                # Find best model (highest quality, reasonable cost)
                best_model = None
                best_score = -999
                for eval_data in evaluations:
                    # Score = quality - (cost_penalty)
                    score = eval_data['quality_score'] - (eval_data['cost'] * 10000)
                    if score > best_score:
                        best_score = score
                        best_model = eval_data['model_name']
                
                result = {
                    'status': 'success',
                    'recommendation': {
                        'current_model': 'GPT-4o',
                        'recommended_model': best_model or 'GPT-4o-mini',
                        'projected_cost_saving_percent': cost_reduction,
                        'projected_quality_impact_percent': quality_diff,
                        'confidence': 90,
                        'reasons': [
                            f'Switching to {best_model} reduces cost by {cost_reduction:.1f}%',
                            f'Quality change: {quality_diff:+.1f}%'
                        ]
                    },
                    'processing_time_seconds': 0.1,
                    'verification_cost_usd': 0.0
                }
        
        # Log the outcome
        if result.get('status') == 'success':
            api_logger.log_event('optimization_complete', {
                'user_id': user_id,
                'recommended_model': result['recommendation']['recommended_model'],
                'cost_saving_percent': result['recommendation']['projected_cost_saving_percent']
            })
        
        return jsonify(result)
        
    except Exception as e:
        api_logger.log_event('optimize_error', {'error': str(e)}, level='error')
        import traceback
        traceback.print_exc()
        # Fallback to orchestrator on error
        try:
            orchestrator = get_orchestrator()
            result = orchestrator.run_optimization(user_id, 6, 3)
            return jsonify(result)
        except:
            return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/user/<user_id>', methods=['GET', 'POST'])
def user_profile(user_id: str):
    """
    GET: Retrieve user profile and constraints
    POST: Update user profile settings
    """
    try:
        if request.method == 'GET':
            user = user_service.get_or_create_default_user(user_id)
            return jsonify(user.to_dict())
        
        else:  # POST
            data = request.get_json() or {}
            user = user_service.get_or_create_default_user(user_id)
            
            # Update fields if provided
            if 'current_model' in data:
                user.current_model = data['current_model']
            if 'use_case' in data:
                user.use_case = data['use_case']
            if 'constraints' in data:
                from user_metadata import UserConstraints
                user.constraints = UserConstraints(**data['constraints'])
            if 'avg_input_tokens' in data:
                user.avg_input_tokens = data['avg_input_tokens']
            if 'avg_output_tokens' in data:
                user.avg_output_tokens = data['avg_output_tokens']
            if 'monthly_request_volume' in data:
                user.monthly_request_volume = data['monthly_request_volume']
            
            # Save updated user
            user_service.save_user(user)
            
            # Invalidate cache for this user
            cache_manager.invalidate_by_prefix(f"user:{user_id}")
            
            return jsonify({'status': 'updated', 'user': user.to_dict()})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/user/<user_id>/conversations', methods=['POST'])
def add_conversation(user_id: str):
    """Add a conversation to user's history for verification"""
    try:
        data = request.get_json()
        messages = data.get('messages', [])
        
        if not messages:
            return jsonify({'error': 'No messages provided'}), 400
        
        user_service.add_conversation(user_id, messages)
        
        return jsonify({'status': 'added', 'message': 'Conversation added to history'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cache/stats')
def cache_stats():
    """Get cache statistics"""
    return jsonify(cache_manager.get_stats())


@app.route('/api/cache/invalidate', methods=['POST'])
def invalidate_cache():
    """Invalidate cache entries"""
    try:
        data = request.get_json() or {}
        
        if 'key' in data:
            success = cache_manager.invalidate(data['key'])
            return jsonify({'status': 'invalidated' if success else 'not_found'})
        
        if 'prefix' in data:
            count = cache_manager.invalidate_by_prefix(data['prefix'])
            return jsonify({'status': 'invalidated', 'count': count})
        
        return jsonify({'error': 'Provide key or prefix to invalidate'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard-data')
def get_dashboard_data_api():
    """
    Get dashboard data from database
    """
    try:
        data = get_dashboard_data()
        
        # Format for frontend
        total_prompts = data['total_prompts']
        total_cost = sum(m.get('total_cost', 0) or 0 for m in data['model_costs'].values())
        
        quality_scores_list = [m['avg_score'] for m in data['model_quality'].values() if m.get('avg_score')]
        avg_quality = sum(quality_scores_list) / len(quality_scores_list) if quality_scores_list else 0
        
        # Get latest recommendation
        latest_rec = data['recommendations'][0] if data['recommendations'] else None
        recommendation = {
            'current_model': latest_rec['current_model'] if latest_rec else 'GPT-4o-mini',
            'recommended_model': latest_rec['recommended_model'] if latest_rec else 'GPT-3.5-turbo',
            'cost_reduction_percent': latest_rec['cost_reduction_percent'] if latest_rec else 0,
            'quality_impact_percent': latest_rec['quality_impact_percent'] if latest_rec else 0,
            'confidence_score': 85,
            'reasoning': f"Based on {total_prompts} tested prompts"
        }
        
        # Build model stats
        models = []
        chart_data = []
        model_reliability = data.get('model_reliability', {})
        for model_name, cost_data in data['model_costs'].items():
            quality_data = data['model_quality'].get(model_name, {})
            reliability = model_reliability.get(model_name, {'success_rate': 100, 'refusal_rate': 0})
            avg_cost = cost_data.get('total_cost', 0) / quality_data.get('count', 1) if quality_data.get('count') else 0
            avg_quality = quality_data.get('avg_score', 0)
            
            models.append({
                'name': model_name,
                'avgCost': avg_cost,
                'avgQuality': avg_quality,
                'avgLatency': cost_data.get('avg_latency', 0),
                'successRate': reliability.get('success_rate', 100),
                'refusalRate': reliability.get('refusal_rate', 0),
                'prompts': quality_data.get('count', 0)
            })
            
            chart_data.append({
                'model': model_name,
                'cost': avg_cost,
                'quality': avg_quality,
                'efficiency': avg_quality / avg_cost if avg_cost > 0 else 0
            })
        
        # Recent prompts
        prompts = []
        for p in data['recent_prompts'][:5]:
            prompts.append({
                'id': p['prompt_id'],
                'content': p['content'][:100] + '...' if len(p['content']) > 100 else p['content'],
                'bestModel': 'GPT-4o-mini',
                'quality': 85,
                'cost': 0.001
            })
        
        activities = [
            {'type': 'analysis', 'message': f'Analyzed {total_prompts} prompts', 'time': 'Recently'}
        ]
        
        return jsonify({
            'stats': {
                'totalPrompts': total_prompts,
                'totalCost': total_cost,
                'avgQuality': avg_quality,
                'costSavings': recommendation['cost_reduction_percent']
            },
            'recommendation': recommendation,
            'chartData': chart_data,
            'qualityScores': {'accuracy': 85, 'helpfulness': 90, 'clarity': 88, 'completeness': 87},
            'models': models,
            'prompts': prompts,
            'activities': activities
        })
        
    except Exception as e:
        print(f"Error loading data: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/analyze', methods=['POST'])
def analyze_prompt():
    """
    Analyze a user prompt across all models
    Returns use case detection, recommendations, and full comparison
    
    Also saves to user's conversation history and checks for similar questions.
    """
    try:
        data = request.get_json()
        prompt = data.get('prompt', '').strip()
        user_id = data.get('user_id', 'default')  # User ID for history
        
        if not prompt:
            return jsonify({'error': 'No prompt provided'}), 400
        
        # STEP 1: Check if similar question exists in user's history
        # Using 0.20 threshold for practical cache hits (20%+ meaningful word overlap)
        similar = chat_manager.find_similar_question(user_id, prompt, similarity_threshold=0.35)
        
        if similar:
            # Return cached response - no LLM calls needed!
            print(f"\nFound similar question in history! Returning cached response.")
            print(f"Similarity: {similar.similarity_score:.0%}\n")
            
            # Ensure quality_score is in 0-100 range
            quality_score_percent = similar.quality_score * 100 if similar.quality_score <= 1.0 else similar.quality_score
            
            return jsonify({
                'status': 'cached',
                'message': f'Found similar question in your history (similarity: {similar.similarity_score:.0%}). Returning cached response!',
                'use_case': 'cached_response',
                'recommended_model': similar.model_used,
                'quality_score': quality_score_percent / 100.0,  # Return as decimal 0-1
                'cost': 0.0,  # Free - no LLM call
                'cached_from': similar.created_at,
                'original_question': similar.question,
                'response': similar.response,
                'models': [{
                    'model_name': similar.model_used,
                    'quality_score': quality_score_percent,  # Return as 0-100 for display
                    'cost': 0.0,
                    'latency_ms': 0,
                    'response': similar.response,
                    'success': True,
                    'is_cached': True
                }]
            })
        
        print(f"\n{'='*80}")
        print(f"Analyzing prompt: {prompt[:100]}...")
        print(f"User: {user_id}")
        print(f"{'='*80}\n")
        
        # STEP 2: No cached response - run fresh analysis
        # Create prompt data
        prompt_data = PromptData(
            id="web_test_prompt",
            messages=[{"role": "user", "content": prompt}],
            original_model="GPT-4o-mini"
        )
        
        # Detect use case
        use_case = detect_use_case(prompt)
        print(f"Detected use case: {use_case}")
        
        # Save prompt to database
        save_prompt(prompt_data.id, prompt, use_case)
        
        # Replay across models
        replay_engine = ReplayEngine()
        completions = replay_engine.replay_prompt_across_models(prompt_data)
        print(f"Completed replay: {len(completions)} models tested")
        
        # Save completions to database
        for completion in completions:
            save_completion(prompt_data.id, completion.model_name, {
                "completion": completion.response,
                "tokens_input": completion.tokens_input,
                "tokens_output": completion.tokens_output,
                "latency_ms": completion.latency_ms,
                "cost": completion.cost,
                "success": completion.success,
                "is_refusal": getattr(completion, 'is_refusal', False),
                "error": completion.error,
                "retry_count": getattr(completion, 'retry_count', 0)
            })
            
            # Log for observability
            replay_logger.log_model_call(
                model=completion.model_name,
                prompt_id=prompt_data.id,
                success=completion.success,
                latency_ms=completion.latency_ms,
                cost=completion.cost,
                is_refusal=getattr(completion, 'is_refusal', False),
                error=completion.error
            )
        
        # Evaluate quality
        evaluator = QualityEvaluator()
        quality_scores = evaluator.evaluate_batch(prompt_data, completions)
        print(f"Quality evaluation complete: {len(quality_scores)} scores")
        
        # Create evaluations and save to database
        optimizer = CostQualityOptimizer()
        evaluations = []
        for completion in completions:
            if completion.model_name in quality_scores and completion.success:
                evaluation = optimizer.create_evaluation(
                    prompt_data.id,
                    completion,
                    quality_scores[completion.model_name]
                )
                evaluations.append(evaluation)
                
                # Save quality evaluation to database
                save_quality_evaluation(prompt_data.id, completion.model_name, {
                    "overall_score": evaluation.quality.overall_score,
                    "dimension_scores": evaluation.quality.dimension_scores,
                    "reasoning": evaluation.quality.reasoning
                })
        
        # Find best model for this use case
        recommended_model = get_recommended_model(use_case, evaluations)
        
        # Calculate savings and quality impact
        evaluations_sorted = sorted(evaluations, key=lambda x: x.completion.cost, reverse=True)
        if len(evaluations_sorted) >= 2:
            most_expensive = evaluations_sorted[0]
            cheapest = evaluations_sorted[-1]
            cost_reduction = ((most_expensive.completion.cost - cheapest.completion.cost) / most_expensive.completion.cost) * 100
            quality_diff = most_expensive.quality.overall_score - cheapest.quality.overall_score
        else:
            cost_reduction = 0
            quality_diff = 0
        
        # Build response
        models_results = []
        best_response = None
        best_quality = 0
        for eval in evaluations:
            models_results.append({
                'model_name': eval.model_name,
                'quality_score': eval.quality.overall_score,
                'cost': eval.completion.cost,
                'latency_ms': eval.completion.latency_ms,
                'response': eval.completion.response,
                'success': eval.completion.success,
                'dimension_scores': eval.quality.dimension_scores
            })
            # Track best response for history saving
            if eval.model_name == recommended_model:
                best_response = eval.completion.response
                best_quality = eval.quality.overall_score
        
        # Get reasoning
        reasoning = get_recommendation_reasoning(use_case, recommended_model, evaluations)
        
        # Save recommendation to database
        save_recommendation({
            "current_model": "GPT-4o-mini",
            "recommended_model": recommended_model,
            "cost_reduction_percent": cost_reduction,
            "quality_impact_percent": quality_diff,
            "avg_quality_loss": quality_diff,
            "cost_quality_ratio": 0.85,
            "use_case": use_case
        })
        
        # STEP 3: Save to user's conversation history for future cache hits
        if best_response and user_id != 'default':
            try:
                # Get cost of recommended model
                recommended_cost = 0
                for eval in evaluations:
                    if eval.model_name == recommended_model:
                        recommended_cost = eval.completion.cost
                        break
                
                chat_manager.save_chat(
                    user_id=user_id,
                    question=prompt,
                    response=best_response,
                    model_used=recommended_model,
                    quality_score=best_quality,
                    cost=recommended_cost
                )
                print(f"✓ Saved to conversation history for user {user_id}")
            except Exception as e:
                print(f"⚠ Failed to save to history: {e}")
        
        result = {
            'use_case': use_case,
            'recommended_model': recommended_model,
            'reasoning': reasoning,
            'cost_savings_percent': cost_reduction,
            'quality_impact_percent': quality_diff,
            'models': models_results,
            'timestamp': prompt_data.messages[0].get('timestamp', '')
        }
        
        print(f"\n{'='*80}")
        print(f"Analysis complete - Recommended: {recommended_model}")
        print(f"Saved to database ✓")
        print(f"{'='*80}\n")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error analyzing prompt: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


def detect_use_case(prompt: str) -> str:
    """Detect the use case type from the prompt"""
    prompt_lower = prompt.lower()
    
    # Code-related keywords
    if any(word in prompt_lower for word in ['function', 'code', 'python', 'javascript', 'implement', 'algorithm', 'debug', 'programming']):
        return 'Code Generation'
    
    # Security-related keywords
    if any(word in prompt_lower for word in ['security', 'vulnerability', 'exploit', 'attack', 'penetration', 'hack', 'malware', 'audit']):
        return 'Security Analysis'
    
    # Creative-related keywords
    if any(word in prompt_lower for word in ['write', 'story', 'creative', 'poem', 'haiku', 'narrative', 'fiction', 'imagine']):
        return 'Creative Writing'
    
    # Data analysis keywords
    if any(word in prompt_lower for word in ['analyze', 'data', 'statistics', 'chart', 'graph', 'insights', 'trends']):
        return 'Data Analysis'
    
    # Documentation keywords
    if any(word in prompt_lower for word in ['document', 'explain', 'describe', 'how to', 'tutorial', 'guide']):
        return 'Documentation'
    
    return 'General Task'


def get_recommended_model(use_case: str, evaluations) -> str:
    """Get recommended model based on use case"""
    if not evaluations:
        return "GPT-3.5-turbo"
    
    # For code generation, prefer quality
    if 'Code' in use_case:
        return max(evaluations, key=lambda x: x.quality.overall_score).model_name
    
    # For security, prefer most accurate
    if 'Security' in use_case:
        return max(evaluations, key=lambda x: x.quality.dimension_scores.get('accuracy', 0)).model_name
    
    # For creative, prefer quality
    if 'Creative' in use_case:
        return max(evaluations, key=lambda x: x.quality.overall_score).model_name
    
    # For general tasks, prefer cost-efficiency
    return min(evaluations, key=lambda x: x.cost_quality_ratio).model_name


def get_recommendation_reasoning(use_case: str, recommended_model: str, evaluations) -> str:
    """Generate reasoning for the recommendation"""
    rec_eval = next((e for e in evaluations if e.model_name == recommended_model), None)
    if not rec_eval:
        return "Model selected based on use case optimization."
    
    if 'Code' in use_case:
        return f"{recommended_model} recommended for code generation with {rec_eval.quality.overall_score:.1f}/100 quality score and excellent accuracy in technical tasks."
    
    if 'Security' in use_case:
        accuracy = rec_eval.quality.dimension_scores.get('accuracy', 0)
        return f"{recommended_model} recommended for security analysis with {accuracy}/100 accuracy score, ensuring reliable vulnerability detection."
    
    if 'Creative' in use_case:
        return f"{recommended_model} recommended for creative writing with {rec_eval.quality.overall_score:.1f}/100 quality score and strong creative capabilities."
    
    if 'General' in use_case or 'Documentation' in use_case:
        cost_per_1k = rec_eval.completion.cost * 1000
        return f"{recommended_model} recommended for general tasks offering best cost-quality balance at ${cost_per_1k:.3f} per 1,000 prompts with {rec_eval.quality.overall_score:.1f}/100 quality."
    
    return f"{recommended_model} provides optimal performance for this task type with quality score of {rec_eval.quality.overall_score:.1f}/100."


if __name__ == '__main__':
    print("=" * 60)
    print("  LLM Cost-Quality Optimization API")
    print("  Multi-Agent Architecture v2.0")
    print("=" * 60)
    print("\nServer: http://localhost:5000")
    print("\nAPI Endpoints:")
    print("  CORE:")
    print("    GET  /health                    - System health check")
    print("    GET  /metrics                   - Prometheus metrics")
    print("    GET  /api/system-stats          - Detailed statistics")
    print()
    print("  MULTI-AGENT ORCHESTRATION:")
    print("    POST /api/optimize              - Run 3-layer optimization")
    print("         → Returns: 'Switching from A to B reduces cost by 42%...'")
    print()
    print("  USER MANAGEMENT:")
    print("    GET  /api/user/<id>             - Get user profile")
    print("    POST /api/user/<id>             - Update user settings")
    print("    POST /api/user/<id>/conversations - Add conversation history")
    print()
    print("  CACHE MANAGEMENT:")
    print("    GET  /api/cache/stats           - Cache statistics")
    print("    POST /api/cache/invalidate      - Invalidate cache entries")
    print()
    print("  LEGACY:")
    print("    GET  /api/dashboard-data        - Dashboard summary data")
    print("    POST /analyze                   - Single prompt analysis")
    print()
    print("Frontend: http://localhost:3000")
    print("=" * 60)
    app.run(debug=True, port=5000)
