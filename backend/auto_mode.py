"""
Auto Mode - Automatic best model selection and response
Returns answer from best model without full analysis details
"""

from typing import Dict, Any, Tuple
from datetime import datetime
from knowledge_cutoff import knowledge_tracker


class AutoModeSelector:
    """Automatically selects and uses the best model"""
    
    def __init__(self):
        self.preference_weights = {
            "cost": 0.50,           # 50% - Cost is primary factor
            "quality": 0.35,        # 35% - Quality matters
            "latency": 0.10,        # 10% - Speed
            "reliability": 0.05     # 5% - Reliability/refusals
        }
    
    def select_best_model(self, evaluations: list, prompt: str) -> Tuple[str, Dict[str, Any]]:
        """
        Select best model and return response with summary
        Returns: (model_name, summary_dict)
        """
        if not evaluations or len(evaluations) == 0:
            return "gpt-4o", {"error": "No models available"}
        
        # Filter out failed models
        successful = [e for e in evaluations if e.completion.success]
        if not successful:
            return "gpt-4o", {"error": "All models failed"}
        
        # Calculate score for each model
        scores = {}
        for eval in successful:
            score = self._calculate_model_score(eval, prompt)
            scores[eval.model_name] = score
        
        # Get best model
        best_model_name = max(scores, key=scores.get)
        best_eval = next(e for e in successful if e.model_name == best_model_name)
        
        # Build summary
        summary = {
            "model": best_model_name,
            "response": best_eval.completion.response,
            "quality_score": best_eval.quality.overall_score,
            "cost": best_eval.completion.cost,
            "latency_ms": best_eval.completion.latency_ms,
            "score": scores[best_model_name],
            "all_scores": scores
        }
        
        return best_model_name, summary
    
    def _calculate_model_score(self, eval, prompt: str) -> float:
        """Calculate weighted score for model selection"""
        
        # Normalize cost (lower is better, so invert)
        max_cost = 0.01  # Reference cost
        cost_score = 1.0 - min(eval.completion.cost / max_cost, 1.0)
        
        # Normalize quality (0-100 to 0-1)
        quality_score = eval.quality.overall_score / 100.0
        
        # Normalize latency (lower is better)
        max_latency = 5000  # 5 seconds
        latency_score = 1.0 - min(eval.completion.latency_ms / max_latency, 1.0)
        
        # Reliability: assume success rate (we're looking at successful models)
        reliability_score = 0.95
        
        # Check knowledge cutoff for recent questions
        question_date = knowledge_tracker.detect_question_date(prompt)
        is_outdated, _ = knowledge_tracker.is_outdated_for_question(eval.model_name, question_date)
        if is_outdated:
            # Penalize outdated models for recent questions
            if (datetime.now() - question_date).days < 30:
                reliability_score = 0.7
        
        # Weighted score
        total_score = (
            self.preference_weights["cost"] * cost_score +
            self.preference_weights["quality"] * quality_score +
            self.preference_weights["latency"] * latency_score +
            self.preference_weights["reliability"] * reliability_score
        )
        
        return total_score
    
    def format_auto_response(self, model_name: str, summary: Dict[str, Any], use_case: str = "") -> Dict[str, Any]:
        """Format response for auto mode"""
        
        quality_level = self._get_quality_level(summary["quality_score"])
        cost_level = self._get_cost_level(summary["cost"])
        
        return {
            "mode": "auto",
            "status": "success",
            "answer": summary["response"],
            "model_used": model_name,
            "use_case": use_case,
            "summary": {
                "quality": {
                    "score": summary["quality_score"],
                    "level": quality_level
                },
                "cost": {
                    "amount": summary["cost"],
                    "level": cost_level
                },
                "latency_ms": summary["latency_ms"],
                "overall_score": summary["score"]
            },
            "model_selection_reason": self._get_selection_reason(model_name, summary),
            "alternatives": self._get_alternative_models(summary["all_scores"], exclude=model_name)
        }
    
    def _get_quality_level(self, score: float) -> str:
        """Get quality level description"""
        if score >= 85:
            return "Excellent"
        elif score >= 75:
            return "Very Good"
        elif score >= 65:
            return "Good"
        elif score >= 50:
            return "Acceptable"
        else:
            return "Poor"
    
    def _get_cost_level(self, cost: float) -> str:
        """Get cost level description"""
        if cost < 0.00001:
            return "Very Cheap"
        elif cost < 0.0001:
            return "Cheap"
        elif cost < 0.001:
            return "Moderate"
        elif cost < 0.01:
            return "Expensive"
        else:
            return "Very Expensive"
    
    def _get_selection_reason(self, model_name: str, summary: Dict) -> str:
        """Generate reason for model selection"""
        quality = summary["quality_score"]
        cost = summary["cost"]
        latency = summary["latency_ms"]
        
        reasons = []
        
        if quality >= 80:
            reasons.append(f"Excellent quality ({quality:.0f}/100)")
        if cost < 0.0001:
            reasons.append("Very cost-effective")
        if latency < 1000:
            reasons.append("Fast response")
        
        if not reasons:
            reasons.append("Best overall balance of cost and quality")
        
        return " + ".join(reasons)
    
    def _get_alternative_models(self, all_scores: Dict[str, float], exclude: str = "", limit: int = 2) -> list:
        """Get top alternative models"""
        alternatives = [
            {"model": model, "score": score}
            for model, score in all_scores.items()
            if model != exclude
        ]
        
        # Sort by score descending
        alternatives.sort(key=lambda x: x["score"], reverse=True)
        
        return alternatives[:limit]
    
    def set_preference(self, cost_weight: float = None, quality_weight: float = None, 
                      latency_weight: float = None, reliability_weight: float = None):
        """Allow user to adjust preference weights"""
        if cost_weight is not None:
            self.preference_weights["cost"] = cost_weight
        if quality_weight is not None:
            self.preference_weights["quality"] = quality_weight
        if latency_weight is not None:
            self.preference_weights["latency"] = latency_weight
        if reliability_weight is not None:
            self.preference_weights["reliability"] = reliability_weight
        
        # Normalize to sum to 1.0
        total = sum(self.preference_weights.values())
        for key in self.preference_weights:
            self.preference_weights[key] /= total


# Global instance
auto_selector = AutoModeSelector()
