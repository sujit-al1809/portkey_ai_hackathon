"""
Cost-Quality Optimization System - Main Demo
Production-ready system for Track 4: Cost-Quality Optimization via Historical Replay

This system demonstrates:
- Historical replay across multiple models
- AI-powered quality evaluation (LLM-as-judge)
- Cost-quality trade-off analysis
- State management and caching
- Continuous monitoring capability
- Explainable recommendations
"""
import logging
from models import PromptData
from continuous_monitor import ContinuousMonitor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_prompts():
    """Create sample prompts for demonstration"""
    prompts = [
        PromptData(
            id="prompt_001",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": "Explain quantum computing in simple terms for a 10-year-old."}
            ],
            original_model="GPT-4o-mini"
        ),
        PromptData(
            id="prompt_002",
            messages=[
                {"role": "system", "content": "You are a creative writing assistant."},
                {"role": "user", "content": "Write a haiku about artificial intelligence."}
            ],
            original_model="GPT-4o-mini"
        ),
        PromptData(
            id="prompt_003",
            messages=[
                {"role": "user", "content": "What are the three laws of robotics by Isaac Asimov?"}
            ],
            original_model="GPT-4o-mini"
        ),
        PromptData(
            id="prompt_004",
            messages=[
                {"role": "system", "content": "You are a technical documentation expert."},
                {"role": "user", "content": "Explain the difference between REST and GraphQL APIs."}
            ],
            original_model="GPT-4o-mini"
        ),
        PromptData(
            id="prompt_005",
            messages=[
                {"role": "user", "content": "How do neural networks learn? Keep it brief."}
            ],
            original_model="GPT-4o-mini"
        ),
    ]
    return prompts


def main():
    """Main demonstration function"""
    print("\n" + "="*70)
    print("COST-QUALITY OPTIMIZATION SYSTEM")
    print("Track 4: Historical Replay & Trade-off Analysis")
    print("="*70 + "\n")
    
    # Initialize monitor
    monitor = ContinuousMonitor()
    
    # Create sample data
    print("Creating sample prompts for demonstration...")
    sample_prompts = create_sample_prompts()
    
    print(f"Generated {len(sample_prompts)} sample prompts\n")
    
    # Run optimization
    print("Starting optimization analysis...")
    print("This will:")
    print("  1. Replay each prompt across all configured models")
    print("  2. Use LLM-as-judge to evaluate quality")
    print("  3. Calculate cost-quality trade-offs")
    print("  4. Generate optimization recommendations")
    print("\nThis may take a few minutes...\n")
    
    try:
        # Run single cycle with sample prompts
        recommendation = monitor.run_once(
            prompts=sample_prompts,
            current_model="GPT-4o-mini"
        )
        
        if recommendation:
            print("\n" + "="*70)
            print("SUCCESS! Recommendation generated")
            print("="*70)
            print(f"\nRecommendation: Switch from {recommendation.current_model} to {recommendation.recommended_model}")
            print(f"Cost Reduction: {recommendation.cost_reduction_percent:.1f}%")
            print(f"Quality Impact: {recommendation.quality_impact_percent:+.1f}%")
            print(f"Confidence: {recommendation.confidence_score:.2f}")
            print(f"\nSee 'optimization_results.json' for detailed results")
        else:
            print("\n" + "="*70)
            print("Analysis complete - More data needed for confident recommendation")
            print("="*70)
            print("\nContinue adding more prompts to improve recommendation confidence.")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        print("\nMake sure to:")
        print("  1. Set PORTKEY_API_KEY environment variable")
        print("  2. Configure virtual keys in Portkey dashboard")
        print("  3. Check your internet connection")
    
    print("\n" + "="*70)
    print("SYSTEM INFO")
    print("="*70)
    print("State file: replay_state.json")
    print("Results file: optimization_results.json")
    print("Cache file: evaluation_cache.json")
    print("\nTo run in continuous mode, use:")
    print("  python continuous_mode.py")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
