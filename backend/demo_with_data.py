"""
Demo with Existing Data - Shows Complete Track 4 Analysis
Uses cached data from previous runs - works without API access
"""
import json
from pathlib import Path

def load_data():
    """Load existing optimization data"""
    data_dir = Path("data")
    
    replay_file = data_dir / "replay_state.json"
    results_file = data_dir / "optimization_results.json"
    eval_file = data_dir / "quality_evaluations.json"
    
    if not replay_file.exists():
        print("❌ No data found. Run 'python main.py' first to generate data.")
        return None, None, None
    
    with open(replay_file) as f:
        replay_data = json.load(f)
    
    evaluations = None
    if eval_file.exists():
        with open(eval_file) as f:
            evaluations = json.load(f)
    
    optimization = None
    if results_file.exists():
        with open(results_file) as f:
            opt_data = json.load(f)
            if opt_data:
                optimization = opt_data[0] if isinstance(opt_data, list) else opt_data
    
    return replay_data, evaluations, optimization


def display_complete_analysis():
    """Display complete Track 4 analysis from existing data"""
    
    print("\n" + "="*80)
    print("TRACK 4: COST-QUALITY OPTIMIZATION - COMPLETE ANALYSIS")
    print("="*80)
    print("\nShowing results from existing data (no API calls needed)")
    print("="*80)
    
    replay_data, evaluations, optimization = load_data()
    
    if not replay_data:
        return
    
    # Display prompt summary
    print(f"\n[DATASET] TESTED PROMPTS")
    print("-" * 80)
    print(f"Total prompts analyzed: {len(replay_data.get('prompts', []))}")
    
    for prompt in replay_data.get('prompts', [])[:3]:  # Show first 3
        msg = next((m['content'] for m in prompt.get('messages', []) if m['role'] == 'user'), 'N/A')
        preview = msg[:70] + "..." if len(msg) > 70 else msg
        print(f"  • {preview}")
    
    if len(replay_data.get('prompts', [])) > 3:
        print(f"  ... and {len(replay_data.get('prompts', [])) - 3} more")
    
    # Display model replay results
    print(f"\n[STEP 1/4] HISTORICAL REPLAY RESULTS")
    print("-" * 80)
    
    models_tested = set()
    total_completions = 0
    total_cost = 0
    
    for prompt in replay_data.get('prompts', []):
        for completion in prompt.get('completions', []):
            models_tested.add(completion.get('model_name'))
            total_completions += 1
            total_cost += completion.get('cost', 0)
    
    print(f"✓ Models tested: {len(models_tested)}")
    print(f"✓ Total completions: {total_completions}")
    print(f"✓ Total cost: ${total_cost:.6f}")
    print()
    
    for model in sorted(models_tested):
        model_completions = []
        for prompt in replay_data.get('prompts', []):
            for completion in prompt.get('completions', []):
                if completion.get('model_name') == model:
                    model_completions.append(completion)
        
        if model_completions:
            avg_tokens_in = sum(c.get('tokens_input', 0) for c in model_completions) / len(model_completions)
            avg_tokens_out = sum(c.get('tokens_output', 0) for c in model_completions) / len(model_completions)
            avg_cost = sum(c.get('cost', 0) for c in model_completions) / len(model_completions)
            avg_latency = sum(c.get('latency_ms', 0) for c in model_completions) / len(model_completions)
            success_rate = sum(1 for c in model_completions if c.get('success', False)) / len(model_completions)
            
            print(f"📊 {model}:")
            print(f"   Completions: {len(model_completions)}")
            print(f"   Avg tokens: {avg_tokens_in:.0f} in, {avg_tokens_out:.0f} out")
            print(f"   Avg cost: ${avg_cost:.6f} per prompt")
            print(f"   Avg latency: {avg_latency:.0f}ms")
            print(f"   Success rate: {success_rate*100:.1f}%")
            print()
    
    # Display quality scores
    if evaluations:
        print(f"\n[STEP 2/4] QUALITY EVALUATION (LLM-as-Judge)")
        print("-" * 80)
        print(f"✓ Total evaluations: {len(evaluations)}\n")
        
        # Group by model
        model_scores = {}
        for eval in evaluations:
            model = eval.get('model_name')
            if model not in model_scores:
                model_scores[model] = []
            model_scores[model].append(eval.get('quality', {}))
        
        for model, scores in sorted(model_scores.items()):
            if scores:
                avg_overall = sum(s.get('overall_score', 0) for s in scores) / len(scores)
                avg_accuracy = sum(s.get('dimension_scores', {}).get('accuracy', 0) for s in scores) / len(scores)
                avg_helpfulness = sum(s.get('dimension_scores', {}).get('helpfulness', 0) for s in scores) / len(scores)
                avg_clarity = sum(s.get('dimension_scores', {}).get('clarity', 0) for s in scores) / len(scores)
                avg_completeness = sum(s.get('dimension_scores', {}).get('completeness', 0) for s in scores) / len(scores)
                
                print(f"📊 {model}:")
                print(f"   Overall Score: {avg_overall:.1f}/100")
                quality_bar = "█" * int(avg_overall / 5) + "░" * (20 - int(avg_overall / 5))
                print(f"   Quality: [{quality_bar}]")
                print(f"   └─ Accuracy: {avg_accuracy:.1f}/100")
                print(f"   └─ Helpfulness: {avg_helpfulness:.1f}/100")
                print(f"   └─ Clarity: {avg_clarity:.1f}/100")
                print(f"   └─ Completeness: {avg_completeness:.1f}/100")
                print()
    
    # Display cost-quality comparison
    print(f"\n[STEP 3/4] COST-QUALITY TRADE-OFF ANALYSIS")
    print("-" * 80)
    
    if evaluations:
        # Calculate cost-quality ratios
        model_metrics = {}
        for eval in evaluations:
            model = eval.get('model_name')
            if model not in model_metrics:
                model_metrics[model] = {'costs': [], 'qualities': [], 'ratios': []}
            
            cost = eval.get('completion', {}).get('cost', 0)
            quality = eval.get('quality', {}).get('overall_score', 0)
            ratio = eval.get('cost_quality_ratio', 0)
            
            model_metrics[model]['costs'].append(cost)
            model_metrics[model]['qualities'].append(quality)
            model_metrics[model]['ratios'].append(ratio)
        
        print(f"\n{'Model':<20} {'Avg Quality':<15} {'Avg Cost':<15} {'Efficiency':<20}")
        print("-" * 80)
        
        for model in sorted(model_metrics.keys(), key=lambda m: sum(model_metrics[m]['qualities'])/len(model_metrics[m]['qualities']), reverse=True):
            metrics = model_metrics[model]
            avg_quality = sum(metrics['qualities']) / len(metrics['qualities'])
            avg_cost = sum(metrics['costs']) / len(metrics['costs'])
            avg_ratio = sum(metrics['ratios']) / len(metrics['ratios'])
            
            quality_bar = "█" * int(avg_quality / 5) + "░" * (20 - int(avg_quality / 5))
            print(f"{model:<20} {avg_quality:>5.1f}/100 [{quality_bar}] ${avg_cost:.6f}  {avg_ratio:.2e}")
    
    # Display optimization recommendation
    print(f"\n\n[STEP 4/4] OPTIMIZATION RECOMMENDATION")
    print("-" * 80)
    
    if evaluations and len(model_metrics) >= 2:
        # Calculate potential savings
        models_list = list(model_metrics.keys())
        model_stats = []
        
        for model in models_list:
            metrics = model_metrics[model]
            avg_quality = sum(metrics['qualities']) / len(metrics['qualities'])
            avg_cost = sum(metrics['costs']) / len(metrics['costs'])
            model_stats.append({
                'name': model,
                'quality': avg_quality,
                'cost': avg_cost
            })
        
        # Find most expensive and cheapest
        most_expensive = max(model_stats, key=lambda x: x['cost'])
        cheapest = min(model_stats, key=lambda x: x['cost'])
        
        if most_expensive['name'] != cheapest['name']:
            cost_reduction = ((most_expensive['cost'] - cheapest['cost']) / most_expensive['cost']) * 100
            quality_diff = most_expensive['quality'] - cheapest['quality']
            
            print(f"\n🎯 TRACK 4 EXPECTED OUTPUT:")
            print("=" * 80)
            print(f"\nSwitching from {most_expensive['name']} to {cheapest['name']}")
            print(f"reduces cost by {cost_reduction:.1f}% with {abs(quality_diff):.1f}% ")
            print(f"{'quality loss' if quality_diff > 0 else 'quality gain'}.")
            print("\n" + "=" * 80)
            
            print(f"\n📈 DETAILED COMPARISON:")
            print(f"\nCurrent Model ({most_expensive['name']}):")
            print(f"   Quality: {most_expensive['quality']:.1f}/100")
            print(f"   Cost: ${most_expensive['cost']:.6f} per prompt")
            
            print(f"\nRecommended Model ({cheapest['name']}):")
            print(f"   Quality: {cheapest['quality']:.1f}/100")
            print(f"   Cost: ${cheapest['cost']:.6f} per prompt")
            
            savings_per_1000 = (most_expensive['cost'] - cheapest['cost']) * 1000
            print(f"\n💰 PROJECTED SAVINGS:")
            print(f"   Per 1,000 prompts: ${savings_per_1000:.2f}")
            print(f"   Per 10,000 prompts: ${savings_per_1000*10:.2f}")
            print(f"   Per 100,000 prompts: ${savings_per_1000*100:.2f}")
    
    print("\n" + "="*80)
    print("✅ COMPLETE ANALYSIS SHOWN")
    print("="*80)
    print("\nThis demonstrates all Track 4 requirements:")
    print("  ✓ Historical replay across models")
    print("  ✓ Quality evaluation (LLM-as-judge)")
    print("  ✓ Cost and quality measurement")
    print("  ✓ Trade-off analysis")
    print("  ✓ Optimization recommendation")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    display_complete_analysis()
