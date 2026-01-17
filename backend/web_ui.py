"""
Smart Prompt Analyzer - Web UI for Model Recommendations
User enters prompt → System suggests best model for the use case
"""
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import logging
from models import PromptData
from replay_engine import ReplayEngine
from quality_evaluator import QualityEvaluator
from optimizer import CostQualityOptimizer
from config import USE_CASE_KEYWORDS, MODELS_TO_TEST

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.WARNING)

def detect_use_case(prompt: str) -> str:
    """Detect the use case category from prompt"""
    prompt_lower = prompt.lower()
    
    for category, keywords in USE_CASE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in prompt_lower:
                return category
    
    return "general"


def analyze_prompt(prompt: str):
    """Analyze prompt and recommend best model"""
    
    # Detect use case
    use_case = detect_use_case(prompt)
    
    # Create prompt data
    prompt_data = PromptData(
        id="web_prompt",
        messages=[{"role": "user", "content": prompt}],
        original_model="GPT-4o-mini"
    )
    
    # Replay across models
    replay_engine = ReplayEngine()
    completions = replay_engine.replay_prompt_across_models(prompt_data)
    
    # Evaluate quality
    evaluator = QualityEvaluator()
    quality_scores = evaluator.evaluate_batch(prompt_data, completions)
    
    # Create evaluations
    optimizer = CostQualityOptimizer()
    evaluations = []
    
    for completion in completions:
        if completion.success and completion.model_name in quality_scores:
            evaluation = optimizer.create_evaluation(
                prompt_data.id,
                completion,
                quality_scores[completion.model_name]
            )
            evaluations.append(evaluation)
    
    if not evaluations:
        return {
            "error": "No successful completions",
            "use_case": use_case
        }
    
    # Sort by quality
    evaluations.sort(key=lambda x: x.quality.overall_score, reverse=True)
    
    # Find best for this use case
    best_overall = evaluations[0]
    best_for_use_case = None
    
    for eval in evaluations:
        model_config = next((m for m in MODELS_TO_TEST if m["name"] == eval.model_name), None)
        if model_config and use_case in model_config.get("strengths", []):
            best_for_use_case = eval
            break
    
    # Find cheapest
    cheapest = min(evaluations, key=lambda x: x.completion.cost)
    
    # Calculate savings
    most_expensive = max(evaluations, key=lambda x: x.completion.cost)
    cost_savings = ((most_expensive.completion.cost - cheapest.completion.cost) / 
                   most_expensive.completion.cost * 100) if most_expensive.completion.cost > 0 else 0
    
    quality_diff = most_expensive.quality.overall_score - cheapest.quality.overall_score
    
    return {
        "prompt": prompt,
        "use_case": use_case,
        "use_case_display": use_case.replace("_", " ").title(),
        "best_overall": {
            "model": best_overall.model_name,
            "quality": best_overall.quality.overall_score,
            "cost": best_overall.completion.cost,
            "latency": best_overall.completion.latency_ms,
            "response_preview": best_overall.completion.response[:200] + "...",
            "reasoning": best_overall.quality.reasoning
        },
        "best_for_use_case": {
            "model": best_for_use_case.model_name if best_for_use_case else best_overall.model_name,
            "quality": best_for_use_case.quality.overall_score if best_for_use_case else best_overall.quality.overall_score,
            "cost": best_for_use_case.completion.cost if best_for_use_case else best_overall.completion.cost,
            "latency": best_for_use_case.completion.latency_ms if best_for_use_case else best_overall.completion.latency_ms,
            "why": f"Optimized for {use_case} tasks"
        } if best_for_use_case or best_overall else None,
        "cheapest": {
            "model": cheapest.model_name,
            "quality": cheapest.quality.overall_score,
            "cost": cheapest.completion.cost,
            "savings": f"{cost_savings:.1f}%",
            "quality_impact": f"{abs(quality_diff):.1f}%"
        },
        "all_models": [
            {
                "model": eval.model_name,
                "quality": eval.quality.overall_score,
                "cost": eval.completion.cost,
                "latency": eval.completion.latency_ms,
                "tokens": eval.completion.tokens_output,
                "accuracy": eval.quality.dimension_scores.get("accuracy", 0),
                "helpfulness": eval.quality.dimension_scores.get("helpfulness", 0),
                "clarity": eval.quality.dimension_scores.get("clarity", 0),
                "completeness": eval.quality.dimension_scores.get("completeness", 0)
            }
            for eval in evaluations
        ],
        "recommendation": f"For {use_case} tasks, use {best_for_use_case.model_name if best_for_use_case else best_overall.model_name}. Switching from {most_expensive.model_name} to {cheapest.model_name} reduces cost by {cost_savings:.1f}% with {abs(quality_diff):.1f}% quality {'loss' if quality_diff > 0 else 'gain'}."
    }


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Model Optimizer - Track 4</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .gradient-bg {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .loading {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body class="bg-gray-50">
    <div class="min-h-screen">
        <!-- Header -->
        <div class="gradient-bg text-white py-8 shadow-lg">
            <div class="container mx-auto px-4">
                <h1 class="text-4xl font-bold mb-2">🎯 AI Model Optimizer</h1>
                <p class="text-lg opacity-90">Track 4: Cost-Quality Optimization via Historical Replay</p>
                <p class="text-sm opacity-75 mt-1">Enter any prompt → Get smart model recommendations</p>
            </div>
        </div>

        <!-- Main Content -->
        <div class="container mx-auto px-4 py-8">
            <!-- Input Section -->
            <div class="bg-white rounded-lg shadow-md p-6 mb-6">
                <h2 class="text-2xl font-bold mb-4">Enter Your Prompt</h2>
                <textarea 
                    id="promptInput" 
                    class="w-full border-2 border-gray-300 rounded-lg p-4 focus:border-blue-500 focus:outline-none" 
                    rows="4" 
                    placeholder="Example: Write a Python function to validate email addresses securely&#10;Example: Explain quantum computing for beginners&#10;Example: Create a haiku about artificial intelligence"></textarea>
                
                <div class="mt-4 flex gap-4">
                    <button 
                        onclick="analyzePrompt()" 
                        class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-8 rounded-lg transition duration-200">
                        🚀 Analyze & Get Recommendations
                    </button>
                    <button 
                        onclick="clearResults()" 
                        class="bg-gray-300 hover:bg-gray-400 text-gray-700 font-bold py-3 px-6 rounded-lg transition duration-200">
                        Clear
                    </button>
                </div>
            </div>

            <!-- Loading -->
            <div id="loading" class="hidden text-center py-8">
                <div class="loading mx-auto mb-4"></div>
                <p class="text-gray-600">Analyzing across multiple models...</p>
            </div>

            <!-- Results -->
            <div id="results" class="hidden">
                <!-- Use Case Detection -->
                <div class="bg-blue-50 border-l-4 border-blue-500 p-4 mb-6 rounded">
                    <h3 class="font-bold text-blue-800">📋 Detected Use Case: <span id="useCase"></span></h3>
                </div>

                <!-- Recommendation Card -->
                <div class="bg-gradient-to-r from-green-50 to-blue-50 border-2 border-green-300 rounded-lg p-6 mb-6 shadow-lg">
                    <h2 class="text-2xl font-bold text-gray-800 mb-4">🎯 Smart Recommendation</h2>
                    <p id="recommendation" class="text-lg text-gray-700 leading-relaxed"></p>
                </div>

                <!-- Best Models Grid -->
                <div class="grid md:grid-cols-3 gap-6 mb-6">
                    <!-- Best Overall -->
                    <div class="bg-white rounded-lg shadow-md p-6 border-t-4 border-purple-500">
                        <h3 class="text-lg font-bold text-purple-700 mb-4">👑 Best Quality</h3>
                        <div id="bestOverall"></div>
                    </div>

                    <!-- Best for Use Case -->
                    <div class="bg-white rounded-lg shadow-md p-6 border-t-4 border-blue-500">
                        <h3 class="text-lg font-bold text-blue-700 mb-4">🎯 Best for Use Case</h3>
                        <div id="bestUseCase"></div>
                    </div>

                    <!-- Most Cost-Effective -->
                    <div class="bg-white rounded-lg shadow-md p-6 border-t-4 border-green-500">
                        <h3 class="text-lg font-bold text-green-700 mb-4">💰 Most Cost-Effective</h3>
                        <div id="cheapest"></div>
                    </div>
                </div>

                <!-- All Models Comparison -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h2 class="text-2xl font-bold mb-4">📊 Complete Model Comparison</h2>
                    <div class="overflow-x-auto">
                        <table class="w-full" id="modelsTable">
                            <thead class="bg-gray-100">
                                <tr>
                                    <th class="px-4 py-3 text-left">Model</th>
                                    <th class="px-4 py-3 text-left">Quality</th>
                                    <th class="px-4 py-3 text-left">Cost</th>
                                    <th class="px-4 py-3 text-left">Speed</th>
                                    <th class="px-4 py-3 text-left">Accuracy</th>
                                    <th class="px-4 py-3 text-left">Helpful</th>
                                    <th class="px-4 py-3 text-left">Clarity</th>
                                </tr>
                            </thead>
                            <tbody id="modelsTableBody"></tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Error -->
            <div id="error" class="hidden bg-red-50 border-l-4 border-red-500 p-4 rounded">
                <p class="text-red-700" id="errorMessage"></p>
            </div>
        </div>
    </div>

    <script>
        async function analyzePrompt() {
            const prompt = document.getElementById('promptInput').value.trim();
            
            if (!prompt) {
                alert('Please enter a prompt');
                return;
            }

            // Show loading
            document.getElementById('loading').classList.remove('hidden');
            document.getElementById('results').classList.add('hidden');
            document.getElementById('error').classList.add('hidden');

            try {
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: prompt })
                });

                const data = await response.json();

                if (data.error) {
                    showError(data.error);
                    return;
                }

                displayResults(data);
            } catch (error) {
                showError('Failed to analyze prompt: ' + error.message);
            } finally {
                document.getElementById('loading').classList.add('hidden');
            }
        }

        function displayResults(data) {
            // Show results section
            document.getElementById('results').classList.remove('hidden');

            // Use case
            document.getElementById('useCase').textContent = data.use_case_display;

            // Recommendation
            document.getElementById('recommendation').textContent = data.recommendation;

            // Best Overall
            const bestOverall = data.best_overall;
            document.getElementById('bestOverall').innerHTML = `
                <p class="font-bold text-xl mb-2">${bestOverall.model}</p>
                <p class="text-gray-700 mb-1">Quality: <span class="font-bold text-purple-600">${bestOverall.quality}/100</span></p>
                <p class="text-gray-700 mb-1">Cost: $${bestOverall.cost.toFixed(6)}</p>
                <p class="text-gray-700 mb-1">Speed: ${bestOverall.latency.toFixed(0)}ms</p>
                <p class="text-sm text-gray-600 mt-3 italic">${bestOverall.reasoning.substring(0, 100)}...</p>
            `;

            // Best for Use Case
            const bestUC = data.best_for_use_case;
            document.getElementById('bestUseCase').innerHTML = `
                <p class="font-bold text-xl mb-2">${bestUC.model}</p>
                <p class="text-gray-700 mb-1">Quality: <span class="font-bold text-blue-600">${bestUC.quality}/100</span></p>
                <p class="text-gray-700 mb-1">Cost: $${bestUC.cost.toFixed(6)}</p>
                <p class="text-gray-700 mb-1">Speed: ${bestUC.latency.toFixed(0)}ms</p>
                <p class="text-sm text-blue-600 mt-3 font-semibold">${bestUC.why}</p>
            `;

            // Cheapest
            const cheapest = data.cheapest;
            document.getElementById('cheapest').innerHTML = `
                <p class="font-bold text-xl mb-2">${cheapest.model}</p>
                <p class="text-gray-700 mb-1">Quality: <span class="font-bold text-green-600">${cheapest.quality}/100</span></p>
                <p class="text-gray-700 mb-1">Cost: $${cheapest.cost.toFixed(6)}</p>
                <p class="text-green-700 font-bold mt-3">Saves ${cheapest.savings}</p>
                <p class="text-gray-600 text-sm">Quality impact: ${cheapest.quality_impact}</p>
            `;

            // Models table
            const tbody = document.getElementById('modelsTableBody');
            tbody.innerHTML = '';
            
            data.all_models.forEach((model, index) => {
                const row = tbody.insertRow();
                row.className = index % 2 === 0 ? 'bg-gray-50' : 'bg-white';
                row.innerHTML = `
                    <td class="px-4 py-3 font-bold">${model.model}</td>
                    <td class="px-4 py-3">
                        <div class="flex items-center">
                            <div class="w-20 bg-gray-200 rounded-full h-2 mr-2">
                                <div class="bg-blue-600 h-2 rounded-full" style="width: ${model.quality}%"></div>
                            </div>
                            <span class="font-semibold">${model.quality}</span>
                        </div>
                    </td>
                    <td class="px-4 py-3 text-sm">$${model.cost.toFixed(6)}</td>
                    <td class="px-4 py-3 text-sm">${model.latency.toFixed(0)}ms</td>
                    <td class="px-4 py-3 text-sm">${model.accuracy}</td>
                    <td class="px-4 py-3 text-sm">${model.helpfulness}</td>
                    <td class="px-4 py-3 text-sm">${model.clarity}</td>
                `;
            });
        }

        function showError(message) {
            document.getElementById('error').classList.remove('hidden');
            document.getElementById('errorMessage').textContent = message;
        }

        function clearResults() {
            document.getElementById('promptInput').value = '';
            document.getElementById('results').classList.add('hidden');
            document.getElementById('error').classList.add('hidden');
        }

        // Example prompts
        const examples = [
            "Write a secure authentication function in Python",
            "Explain blockchain to a 10-year-old",
            "Create a REST API for user management",
            "Write a haiku about machine learning"
        ];
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the web UI"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """Analyze prompt and return recommendations"""
    data = request.json
    prompt = data.get('prompt', '').strip()
    
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400
    
    try:
        result = analyze_prompt(prompt)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Analysis error: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*80)
    print("🚀 AI MODEL OPTIMIZER - WEB UI")
    print("="*80)
    print("\nStarting web server...")
    print("\n✅ Open your browser to: http://localhost:5000")
    print("\nFeatures:")
    print("  • Enter any prompt")
    print("  • Automatic use case detection (code, security, creative, etc.)")
    print("  • Smart model recommendations")
    print("  • Cost-quality trade-off analysis")
    print("  • Complete comparison across all models")
    print("\n" + "="*80 + "\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')
