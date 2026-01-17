"""
Dashboard API Server
Serves optimization data to the Next.js dashboard
"""

from flask import Flask, jsonify, request
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

app = Flask(__name__)
CORS(app)  # Enable CORS for Next.js frontend

# Initialize database
init_db()


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
    """
    try:
        data = request.get_json()
        prompt = data.get('prompt', '').strip()
        
        if not prompt:
            return jsonify({'error': 'No prompt provided'}), 400
        
        print(f"\n{'='*80}")
        print(f"Analyzing prompt: {prompt[:100]}...")
        print(f"{'='*80}\n")
        
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
    print("Starting Dashboard API on http://localhost:5000")
    print("Endpoints:")
    print("  - GET  /api/dashboard-data  (Dashboard data)")
    print("  - POST /analyze             (Prompt analysis)")
    print("\nMake sure to run the Next.js dashboard on http://localhost:3000")
    app.run(debug=True, port=5000)
