"""
Test User Prompt - Complete Analysis Demo
Shows all analysis: replay, quality evaluation, cost comparison, and recommendations
"""
import sys
import logging
from models import PromptData
from replay_engine import ReplayEngine
from quality_evaluator import QualityEvaluator
from optimizer import CostQualityOptimizer

logging.basicConfig(level=logging.WARNING)

def analyze_user_prompt(user_prompt: str):
    """Run complete analysis on a user prompt"""
    
    print("\n" + "="*80)
    print("TRACK 4: COST-QUALITY OPTIMIZATION - USER PROMPT ANALYSIS")
    print("="*80)
    print(f"\nUser Prompt: \"{user_prompt}\"")
    print("\n" + "="*80)
    
    # Step 1: Create prompt data
    prompt_data = PromptData(
        id="test_prompt",
        messages=[
            {"role": "user", "content": user_prompt}
        ],
        original_model="GPT-4o-mini"
    )
    
    print("\n[STEP 1/4] REPLAYING ACROSS MODELS...")
    print("-" * 80)
    
    # Step 2: Replay across models
    replay_engine = ReplayEngine()
    completions = replay_engine.replay_prompt_across_models(prompt_data)
    
    print(f"✓ Tested {len(completions)} models\n")
    
    for i, completion in enumerate(completions, 1):
        status = "✓" if completion.success else "✗"
        print(f"{status} Model {i}: {completion.model_name}")
        print(f"   Tokens: {completion.tokens_input} in, {completion.tokens_output} out")
        print(f"   Cost: ${completion.cost:.6f}")
        print(f"   Latency: {completion.latency_ms:.0f}ms")
        if completion.success:
            response_preview = completion.response[:100] + "..." if len(completion.response) > 100 else completion.response
            print(f"   Response: {response_preview}")
        print()
    
    # Step 3: Evaluate quality
    print("\n[STEP 2/4] EVALUATING QUALITY (LLM-as-Judge)...")
    print("-" * 80)
    
    evaluator = QualityEvaluator()
    quality_scores = evaluator.evaluate_batch(prompt_data, completions)
    
    print(f"✓ Evaluated {len(quality_scores)} responses\n")
    
    for model_name, quality in quality_scores.items():
        print(f"📊 {model_name}:")
        print(f"   Overall Score: {quality.overall_score}/100")
        print(f"   └─ Accuracy: {quality.dimension_scores['accuracy']}/100")
        print(f"   └─ Helpfulness: {quality.dimension_scores['helpfulness']}/100")
        print(f"   └─ Clarity: {quality.dimension_scores['clarity']}/100")
        print(f"   └─ Completeness: {quality.dimension_scores['completeness']}/100")
        print(f"   Reasoning: {quality.reasoning[:120]}...")
        print(f"   Confidence: {quality.confidence:.0%}")
        print()
    
    # Step 4: Compare costs and quality
    print("\n[STEP 3/4] COST-QUALITY COMPARISON...")
    print("-" * 80)
    
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
    
    # Sort by quality
    evaluations_by_quality = sorted(evaluations, key=lambda x: x.quality.overall_score, reverse=True)
    
    print(f"\n{'Model':<20} {'Quality':<12} {'Cost':<15} {'Efficiency':<20}")
    print("-" * 80)
    
    for eval in evaluations_by_quality:
        quality_bar = "█" * int(eval.quality.overall_score / 5) + "░" * (20 - int(eval.quality.overall_score / 5))
        print(f"{eval.model_name:<20} {eval.quality.overall_score:>3}/100 [{quality_bar}] ${eval.completion.cost:.6f}  {eval.cost_quality_ratio:.2e}")
    
    # Step 5: Generate recommendation
    print("\n\n[STEP 4/4] OPTIMIZATION RECOMMENDATION...")
    print("-" * 80)
    
    # Find best and most expensive
    if not evaluations:
        print("\n⚠️  No successful completions to analyze.")
        print("This may be due to API connectivity issues.")
        print("\nPlease check:")
        print("  1. Portkey API key is set: PORTKEY_API_KEY environment variable")
        print("  2. Internet connection is working")
        print("  3. Portkey service is accessible")
        print("\nTo see a working demo, run: python demo_with_data.py")
        return
    
    best_quality = evaluations_by_quality[0]
    evaluations_by_cost = sorted(evaluations, key=lambda x: x.completion.cost, reverse=True)
    most_expensive = evaluations_by_cost[0]
    cheapest = evaluations_by_cost[-1]
    
    if len(evaluations) >= 2 and most_expensive.model_name != cheapest.model_name:
        cost_reduction = ((most_expensive.completion.cost - cheapest.completion.cost) / most_expensive.completion.cost) * 100
        quality_diff = most_expensive.quality.overall_score - cheapest.quality.overall_score
        
        print(f"\n🎯 TRACK 4 OUTPUT:")
        print("=" * 80)
        print(f"\nSwitching from {most_expensive.model_name} to {cheapest.model_name}")
        print(f"reduces cost by {cost_reduction:.1f}% with {abs(quality_diff):.1f}% {'quality loss' if quality_diff > 0 else 'quality gain'}.")
        print("\n" + "=" * 80)
        
        print(f"\n📈 DETAILED ANALYSIS:")
        print(f"\nCurrent ({most_expensive.model_name}):")
        print(f"   Quality: {most_expensive.quality.overall_score}/100")
        print(f"   Cost: ${most_expensive.completion.cost:.6f} per prompt")
        print(f"   Latency: {most_expensive.completion.latency_ms:.0f}ms")
        
        print(f"\nRecommended ({cheapest.model_name}):")
        print(f"   Quality: {cheapest.quality.overall_score}/100")
        print(f"   Cost: ${cheapest.completion.cost:.6f} per prompt")
        print(f"   Latency: {cheapest.completion.latency_ms:.0f}ms")
        
        savings_per_1000 = (most_expensive.completion.cost - cheapest.completion.cost) * 1000
        print(f"\n💰 PROJECTED SAVINGS:")
        print(f"   Per 1,000 prompts: ${savings_per_1000:.2f}")
        print(f"   Per 10,000 prompts: ${savings_per_1000*10:.2f}")
        print(f"   Per 100,000 prompts: ${savings_per_1000*100:.2f}")
    else:
        print(f"\n✓ Currently using optimal model: {best_quality.model_name}")
        print(f"   Quality: {best_quality.quality.overall_score}/100")
        print(f"   Cost: ${best_quality.completion.cost:.6f}")
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Use command line argument
        user_input = " ".join(sys.argv[1:])
    else:
        # Interactive mode
        print("\n" + "="*80)
        print("TRACK 4: USER PROMPT TESTING")
        print("="*80)
        print("\nThis will test ANY user prompt across all models and show:")
        print("  ✓ Replay results from each model")
        print("  ✓ Quality scores (LLM-as-judge)")
        print("  ✓ Cost comparison")
        print("  ✓ Optimization recommendation")
        print("\n" + "="*80)
        user_input = input("\nEnter your prompt: ").strip()
    
    if not user_input:
        print("Error: No prompt provided")
        sys.exit(1)
    
    analyze_user_prompt(user_input)
