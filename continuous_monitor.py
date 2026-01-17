"""
Continuous Monitor - Runs the optimization system continuously
"""
import time
import logging
from typing import List
from datetime import datetime
from models import PromptData
from replay_engine import ReplayEngine
from quality_evaluator import QualityEvaluator
from optimizer import CostQualityOptimizer
from state_manager import StateManager
from config import MONITORING_INTERVAL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContinuousMonitor:
    """Continuously monitors and optimizes model usage"""
    
    def __init__(self):
        self.replay_engine = ReplayEngine()
        self.evaluator = QualityEvaluator()
        self.optimizer = CostQualityOptimizer()
        self.state_manager = StateManager()
        self.running = False
    
    def fetch_new_prompts(self, since_timestamp: str) -> List[PromptData]:
        """
        Fetch new prompts from your data source
        In production, this would query your database/logs
        For demo, we return empty list
        """
        # TODO: Implement actual prompt fetching from Portkey logs or your database
        # This is a placeholder
        return []
    
    def process_prompts(self, prompts: List[PromptData]):
        """Process a batch of prompts through the optimization pipeline"""
        if not prompts:
            logger.info("No new prompts to process")
            return
        
        state = self.state_manager.load_state()
        all_evaluations = []
        
        for prompt in prompts:
            # Skip if already processed
            if prompt.id in state.processed_prompt_ids:
                logger.info(f"Skipping already processed prompt: {prompt.id}")
                continue
            
            logger.info(f"\n{'='*70}")
            logger.info(f"Processing Prompt: {prompt.id}")
            logger.info(f"{'='*70}")
            
            # Replay across models
            completions = self.replay_engine.replay_prompt_across_models(prompt)
            
            # Evaluate quality
            quality_scores = self.evaluator.evaluate_batch(prompt, completions)
            
            # Create evaluations
            for completion in completions:
                if completion.model_name in quality_scores:
                    evaluation = self.optimizer.create_evaluation(
                        prompt.id,
                        completion,
                        quality_scores[completion.model_name]
                    )
                    all_evaluations.append(evaluation)
            
            # Mark as processed
            self.state_manager.mark_prompt_processed(state, prompt.id)
        
        # Save results
        if all_evaluations:
            self.state_manager.save_evaluations(all_evaluations)
            state.last_processed_timestamp = datetime.utcnow().isoformat()
            self.state_manager.save_state(state)
            
            logger.info(f"\n{'='*70}")
            logger.info(f"Batch complete: {len(all_evaluations)} evaluations saved")
            logger.info(f"{'='*70}")
    
    def generate_recommendations(self, current_model: str):
        """Generate optimization recommendations based on collected data"""
        # Load all evaluations
        eval_data = self.state_manager.load_evaluations()
        
        if not eval_data:
            logger.warning("No evaluation data available for recommendations")
            return None
        
        # Convert to ModelEvaluation objects
        from models import ModelEvaluation, CompletionResult, QualityScore
        evaluations = []
        for data in eval_data:
            completion = CompletionResult(**data['completion'])
            quality = QualityScore(**data['quality'])
            eval = ModelEvaluation(
                prompt_id=data['prompt_id'],
                model_name=data['model_name'],
                completion=completion,
                quality=quality,
                cost_quality_ratio=data['cost_quality_ratio']
            )
            evaluations.append(eval)
        
        # Generate recommendation
        recommendation = self.optimizer.recommend_optimization(
            current_model,
            evaluations
        )
        
        if recommendation:
            logger.info(f"\n{'='*70}")
            logger.info("OPTIMIZATION RECOMMENDATION")
            logger.info(f"{'='*70}")
            print(recommendation.to_json())
            logger.info(f"{'='*70}\n")
        
        return recommendation
    
    def run_once(self, prompts: List[PromptData], current_model: str = "GPT-4o-mini"):
        """Run one cycle of the optimization system"""
        logger.info("\n" + "="*70)
        logger.info("COST-QUALITY OPTIMIZATION SYSTEM - Single Run")
        logger.info("="*70 + "\n")
        
        # Process prompts
        self.process_prompts(prompts)
        
        # Generate recommendations
        recommendation = self.generate_recommendations(current_model)
        
        return recommendation
    
    def start_continuous_monitoring(self):
        """Start continuous monitoring loop"""
        logger.info("\n" + "="*70)
        logger.info("COST-QUALITY OPTIMIZATION SYSTEM - Continuous Mode")
        logger.info(f"Checking for new prompts every {MONITORING_INTERVAL}s")
        logger.info("="*70 + "\n")
        
        self.running = True
        state = self.state_manager.load_state()
        
        while self.running:
            try:
                # Fetch new prompts
                new_prompts = self.fetch_new_prompts(state.last_processed_timestamp)
                
                if new_prompts:
                    self.process_prompts(new_prompts)
                    state = self.state_manager.load_state()
                else:
                    logger.info(f"No new prompts. Next check in {MONITORING_INTERVAL}s...")
                
                # Sleep until next check
                time.sleep(MONITORING_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("\nStopping continuous monitoring...")
                self.running = False
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(MONITORING_INTERVAL)
    
    def stop(self):
        """Stop continuous monitoring"""
        self.running = False
