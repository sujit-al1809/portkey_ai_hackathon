"""
Cost-Quality Optimizer - Analyzes results and generates recommendations
"""
import logging
from typing import List, Dict, Optional
from statistics import mean, stdev
from models import (
    ModelEvaluation, 
    OptimizationRecommendation, 
    CompletionResult, 
    QualityScore
)
from config import MIN_CONFIDENCE_SCORE, MIN_SAMPLE_SIZE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CostQualityOptimizer:
    """Analyzes model performance and recommends optimal trade-offs"""
    
    def __init__(self, min_confidence: float = MIN_CONFIDENCE_SCORE, min_samples: int = MIN_SAMPLE_SIZE):
        self.min_confidence = min_confidence
        self.min_samples = min_samples
    
    def create_evaluation(
        self,
        prompt_id: str,
        completion: CompletionResult,
        quality: QualityScore
    ) -> ModelEvaluation:
        """Create a ModelEvaluation from completion and quality score"""
        
        # Calculate cost-quality ratio (lower is better)
        if quality.overall_score > 0:
            cost_quality_ratio = completion.cost / quality.overall_score
        else:
            cost_quality_ratio = float('inf')
        
        return ModelEvaluation(
            prompt_id=prompt_id,
            model_name=completion.model_name,
            completion=completion,
            quality=quality,
            cost_quality_ratio=cost_quality_ratio
        )
    
    def analyze_model_performance(
        self,
        evaluations: List[ModelEvaluation]
    ) -> Dict[str, Dict]:
        """
        Aggregate performance metrics across multiple evaluations per model
        """
        model_data = {}
        
        for eval in evaluations:
            model = eval.model_name
            
            if model not in model_data:
                model_data[model] = {
                    "costs": [],
                    "quality_scores": [],
                    "latencies": [],
                    "success_count": 0,
                    "total_count": 0,
                    "cost_quality_ratios": []
                }
            
            data = model_data[model]
            data["total_count"] += 1
            
            if eval.completion.success:
                data["success_count"] += 1
                data["costs"].append(eval.completion.cost)
                data["quality_scores"].append(eval.quality.overall_score)
                data["latencies"].append(eval.completion.latency_ms)
                data["cost_quality_ratios"].append(eval.cost_quality_ratio)
        
        # Calculate aggregate metrics
        metrics = {}
        for model, data in model_data.items():
            if data["success_count"] > 0:
                metrics[model] = {
                    "avg_cost": mean(data["costs"]),
                    "avg_quality": mean(data["quality_scores"]),
                    "avg_latency": mean(data["latencies"]),
                    "avg_cost_quality_ratio": mean(data["cost_quality_ratios"]),
                    "success_rate": data["success_count"] / data["total_count"],
                    "sample_size": data["total_count"],
                    "quality_stdev": stdev(data["quality_scores"]) if len(data["quality_scores"]) > 1 else 0
                }
            else:
                metrics[model] = {
                    "avg_cost": 0,
                    "avg_quality": 0,
                    "avg_latency": 0,
                    "avg_cost_quality_ratio": float('inf'),
                    "success_rate": 0,
                    "sample_size": data["total_count"],
                    "quality_stdev": 0
                }
        
        return metrics
    
    def recommend_optimization(
        self,
        current_model: str,
        all_evaluations: List[ModelEvaluation]
    ) -> Optional[OptimizationRecommendation]:
        """
        Generate optimization recommendation for switching from current model
        """
        # Check minimum sample size
        if len(all_evaluations) < self.min_samples:
            logger.warning(f"Insufficient data: {len(all_evaluations)} samples (minimum: {self.min_samples})")
            return None
        
        # Analyze performance
        metrics = self.analyze_model_performance(all_evaluations)
        
        if current_model not in metrics:
            logger.error(f"Current model {current_model} not found in evaluations")
            return None
        
        current_metrics = metrics[current_model]
        
        # Find best alternative based on cost-quality ratio
        best_model = None
        best_improvement = 0
        
        for model, model_metrics in metrics.items():
            if model == current_model:
                continue
            
            # Skip models with poor success rate
            if model_metrics["success_rate"] < 0.8:
                continue
            
            # Calculate improvement score (lower cost-quality ratio is better)
            if current_metrics["avg_cost_quality_ratio"] > 0:
                improvement = (
                    (current_metrics["avg_cost_quality_ratio"] - model_metrics["avg_cost_quality_ratio"]) 
                    / current_metrics["avg_cost_quality_ratio"]
                )
                
                if improvement > best_improvement:
                    best_improvement = improvement
                    best_model = model
        
        if not best_model:
            logger.info("No better alternative model found")
            return None
        
        recommended_metrics = metrics[best_model]
        
        # Calculate cost and quality impacts
        cost_reduction = ((current_metrics["avg_cost"] - recommended_metrics["avg_cost"]) 
                         / current_metrics["avg_cost"] * 100)
        quality_impact = ((recommended_metrics["avg_quality"] - current_metrics["avg_quality"]) 
                         / current_metrics["avg_quality"] * 100)
        
        # Calculate confidence based on sample size and quality variance
        sample_confidence = min(len(all_evaluations) / (self.min_samples * 2), 1.0)
        variance_confidence = 1.0 - min(recommended_metrics["quality_stdev"] / 50, 1.0)
        confidence = (sample_confidence + variance_confidence) / 2
        
        # Build reasoning
        reasoning = f"""
Based on analysis of {len(all_evaluations)} prompts:

Current Model ({current_model}):
- Average Cost: ${current_metrics['avg_cost']:.6f}
- Average Quality: {current_metrics['avg_quality']:.1f}/100
- Average Latency: {current_metrics['avg_latency']:.0f}ms
- Success Rate: {current_metrics['success_rate']*100:.1f}%

Recommended Model ({best_model}):
- Average Cost: ${recommended_metrics['avg_cost']:.6f}
- Average Quality: {recommended_metrics['avg_quality']:.1f}/100
- Average Latency: {recommended_metrics['avg_latency']:.0f}ms
- Success Rate: {recommended_metrics['success_rate']*100:.1f}%

The switch reduces costs by {abs(cost_reduction):.1f}% while {'improving' if quality_impact > 0 else 'reducing'} quality by {abs(quality_impact):.1f}%.
Cost-quality efficiency improves by {best_improvement*100:.1f}%.
        """.strip()
        
        return OptimizationRecommendation(
            current_model=current_model,
            recommended_model=best_model,
            cost_reduction_percent=cost_reduction,
            quality_impact_percent=quality_impact,
            confidence_score=confidence,
            sample_size=len(all_evaluations),
            reasoning=reasoning,
            metrics={
                "current": current_metrics,
                "recommended": recommended_metrics
            }
        )
