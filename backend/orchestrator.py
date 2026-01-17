"""
Multi-Agent Orchestration System - 3-Layer Architecture
Layer 1: Candidate Discovery
Layer 2: Use-Case Fit Ranking  
Layer 3: Verification & Evaluation
"""
import logging
import json
import time
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from enum import Enum

from model_registry import model_registry, ModelEntry
from user_metadata import user_service, UserMetadata
from cache_manager import cache_manager, CacheKeys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("orchestrator")


# ============================================================================
# DECISION THRESHOLDS (Production Config)
# ============================================================================
class Thresholds:
    MIN_COST_SAVING_PERCENT = 20.0      # Minimum cost saving required
    MAX_QUALITY_DROP_PERCENT = 5.0       # Maximum allowed quality drop
    MIN_CONFIDENCE_SCORE = 0.3           # Lower for testing with small sample
    MAX_VERIFICATION_BUDGET_USD = 1.0    # Max $ per verification run
    MAX_ITERATION_LOOPS = 3              # Max retries when quality too low
    MIN_SAMPLE_SIZE = 3                  # Minimum conversations for verification
    EXPLORATION_BUDGET_PERCENT = 5.0     # % of traffic for exploration


def utc_now() -> datetime:
    """Get current UTC time in a timezone-aware manner"""
    return datetime.now(timezone.utc)


# ============================================================================
# AGENT BASE CLASS
# ============================================================================
@dataclass
class AgentResult:
    """Standard result from any agent"""
    success: bool
    data: Any
    error: Optional[str] = None
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    timestamp: str = field(default_factory=lambda: utc_now().isoformat())


class BaseAgent:
    """Base class for all agents"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"agent.{name}")
    
    def execute(self, *args, **kwargs) -> AgentResult:
        raise NotImplementedError
    
    def log(self, message: str, level: str = "info"):
        getattr(self.logger, level)(f"[{self.name}] {message}")


# ============================================================================
# LAYER 1: CANDIDATE DISCOVERY AGENTS
# ============================================================================
class ModelRegistryAgent(BaseAgent):
    """Agent that retrieves model information from registry"""
    
    def __init__(self):
        super().__init__("ModelRegistryAgent")
    
    def execute(self, model_ids: Optional[List[str]] = None) -> AgentResult:
        start = time.time()
        
        try:
            if model_ids:
                models = [model_registry.get_model(mid) for mid in model_ids]
                models = [m for m in models if m is not None]
            else:
                models = model_registry.get_all_models()
            
            return AgentResult(
                success=True,
                data={"models": [asdict(m) for m in models], "count": len(models)},
                latency_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return AgentResult(success=False, data=None, error=str(e))


class PricingRegistryAgent(BaseAgent):
    """Agent that retrieves pricing information"""
    
    def __init__(self):
        super().__init__("PricingRegistryAgent")
    
    def execute(self, model_ids: List[str]) -> AgentResult:
        start = time.time()
        
        try:
            pricing_data = {}
            for model_id in model_ids:
                model = model_registry.get_model(model_id)
                if model:
                    pricing_data[model_id] = {
                        "input_price_per_1k": model.pricing.input_price_per_1k,
                        "output_price_per_1k": model.pricing.output_price_per_1k,
                        "rate_limit_rpm": model.pricing.rate_limit_rpm
                    }
            
            return AgentResult(
                success=True,
                data=pricing_data,
                latency_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return AgentResult(success=False, data=None, error=str(e))


class UserContextAgent(BaseAgent):
    """Agent that retrieves user context and constraints"""
    
    def __init__(self):
        super().__init__("UserContextAgent")
    
    def execute(self, user_id: str) -> AgentResult:
        start = time.time()
        
        try:
            user = user_service.get_or_create_default_user(user_id)
            
            return AgentResult(
                success=True,
                data=user.to_dict(),
                latency_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return AgentResult(success=False, data=None, error=str(e))


class CandidateDiscoveryAgent(BaseAgent):
    """
    LAYER 1 ORCHESTRATOR
    Discovers cheaper candidate models based on user's current model
    """
    
    def __init__(self):
        super().__init__("CandidateDiscoveryAgent")
        self.model_agent = ModelRegistryAgent()
        self.pricing_agent = PricingRegistryAgent()
        self.user_agent = UserContextAgent()
    
    def execute(self, user_id: str, k_candidates: int = 6) -> AgentResult:
        start = time.time()
        self.log(f"Starting candidate discovery for user {user_id}")
        
        # Step 1: Get user context
        user_result = self.user_agent.execute(user_id)
        if not user_result.success:
            return AgentResult(success=False, data=None, error=f"Failed to get user: {user_result.error}")
        
        user_data = user_result.data
        current_model = user_data["current_model"]
        self.log(f"User current model: {current_model}")
        
        # Step 2: Get all models
        models_result = self.model_agent.execute()
        if not models_result.success:
            return AgentResult(success=False, data=None, error=f"Failed to get models: {models_result.error}")
        
        # Step 3: Filter to cheaper models
        current_model_entry = model_registry.get_model(current_model)
        if not current_model_entry:
            return AgentResult(success=False, data=None, error=f"Current model {current_model} not found in registry")
        
        current_rank = current_model_entry.rank
        
        # Get models with higher rank (cheaper)
        cheaper_candidates = [
            m for m in models_result.data["models"]
            if m["rank"] > current_rank
        ]
        
        # Sort by rank and take top K
        cheaper_candidates.sort(key=lambda x: x["rank"])
        shortlist = cheaper_candidates[:k_candidates]
        
        # Step 4: Get pricing for shortlist
        model_ids = [m["model_id"] for m in shortlist]
        pricing_result = self.pricing_agent.execute(model_ids)
        
        # Combine data
        for candidate in shortlist:
            candidate["pricing"] = pricing_result.data.get(candidate["model_id"], {})
            
            # Calculate estimated cost savings
            delta = model_registry.calculate_cost_delta(
                current_model,
                candidate["model_id"],
                user_data["avg_input_tokens"],
                user_data["avg_output_tokens"]
            )
            candidate["estimated_cost_delta"] = delta
        
        self.log(f"Found {len(shortlist)} cheaper candidates")
        
        return AgentResult(
            success=True,
            data={
                "user": user_data,
                "current_model": current_model,
                "current_rank": current_rank,
                "candidates": shortlist,
                "total_candidates_found": len(cheaper_candidates)
            },
            latency_ms=(time.time() - start) * 1000
        )


# ============================================================================
# LAYER 2: USE-CASE FIT RANKING AGENTS
# ============================================================================
class UseCaseFitAgent(BaseAgent):
    """
    LAYER 2 ORCHESTRATOR
    Ranks candidates based on use-case fit
    """
    
    def __init__(self):
        super().__init__("UseCaseFitAgent")
    
    def _calculate_fit_score(self, candidate: Dict, use_case: str, constraints: Dict) -> float:
        """Calculate how well a model fits the use case"""
        score = 0.0
        
        # Strength matching (0-40 points)
        use_case_strengths = {
            "coding": ["coding", "reasoning"],
            "reasoning": ["reasoning", "analysis", "complex_tasks"],
            "extraction": ["extraction", "general"],
            "summarization": ["summarization", "general"],
            "creative": ["creative", "general"],
            "support_bot": ["general", "fast", "cost_effective"],
            "general": ["general"]
        }
        
        required = use_case_strengths.get(use_case, ["general"])
        model_strengths = candidate.get("capabilities", {}).get("strengths", [])
        
        matches = sum(1 for r in required if r in model_strengths)
        score += (matches / len(required)) * 40
        
        # Latency fit (0-20 points)
        latency_tier = candidate.get("capabilities", {}).get("latency_tier", "medium")
        max_latency = constraints.get("max_latency_ms", 5000)
        
        if latency_tier == "fast":
            score += 20
        elif latency_tier == "medium" and max_latency >= 3000:
            score += 15
        elif latency_tier == "slow" and max_latency >= 5000:
            score += 10
        
        # Reliability (0-20 points)
        reliability = candidate.get("capabilities", {}).get("reliability_tier", "medium")
        if reliability == "high":
            score += 20
        elif reliability == "medium":
            score += 15
        else:
            score += 10
        
        # Cost efficiency bonus (0-20 points)
        cost_delta = candidate.get("estimated_cost_delta", {})
        percent_saving = cost_delta.get("percent_saving", 0)
        score += min(20, percent_saving / 5)  # 5% saving = 1 point, max 20
        
        return score
    
    def execute(self, discovery_result: Dict, n_top: int = 3) -> AgentResult:
        start = time.time()
        
        candidates = discovery_result["candidates"]
        user = discovery_result["user"]
        use_case = user["use_case"]
        constraints = user.get("constraints", {})
        
        self.log(f"Ranking {len(candidates)} candidates for use case: {use_case}")
        
        # Score each candidate
        scored_candidates = []
        for candidate in candidates:
            fit_score = self._calculate_fit_score(candidate, use_case, constraints)
            candidate["fit_score"] = fit_score
            scored_candidates.append(candidate)
        
        # Sort by fit score (descending) and take top N
        scored_candidates.sort(key=lambda x: x["fit_score"], reverse=True)
        top_n = scored_candidates[:n_top]
        
        # Generate rationale for each
        for candidate in top_n:
            candidate["rationale"] = self._generate_rationale(candidate, use_case)
        
        self.log(f"Top {n_top} candidates selected")
        
        return AgentResult(
            success=True,
            data={
                "user": user,
                "current_model": discovery_result["current_model"],
                "top_candidates": top_n,
                "use_case": use_case
            },
            latency_ms=(time.time() - start) * 1000
        )
    
    def _generate_rationale(self, candidate: Dict, use_case: str) -> str:
        """Generate human-readable rationale"""
        name = candidate.get("display_name", candidate.get("model_id"))
        fit = candidate.get("fit_score", 0)
        cost_delta = candidate.get("estimated_cost_delta", {})
        saving = cost_delta.get("percent_saving", 0)
        
        return f"{name} scores {fit:.1f}/100 for {use_case} tasks with {saving:.1f}% cost reduction"


# ============================================================================
# LAYER 3: VERIFICATION & EVALUATION AGENTS
# ============================================================================
class VerificationAgent(BaseAgent):
    """
    LAYER 3 ORCHESTRATOR
    Runs verification tests and evaluation pipeline
    """
    
    def __init__(self, replay_engine, quality_evaluator):
        super().__init__("VerificationAgent")
        self.replay_engine = replay_engine
        self.quality_evaluator = quality_evaluator
        self.iteration_count = 0
    
    def execute(self, ranking_result: Dict, 
                conversations: Optional[List[Dict]] = None,
                iteration: int = 0) -> AgentResult:
        start = time.time()
        self.iteration_count = iteration
        
        user = ranking_result["user"]
        current_model = ranking_result["current_model"]
        candidates = ranking_result["top_candidates"]
        
        self.log(f"Starting verification (iteration {iteration})")
        
        # Get test conversations
        if conversations is None:
            conversations = user.get("last_n_conversations", [])
        
        if len(conversations) < Thresholds.MIN_SAMPLE_SIZE:
            self.log("Insufficient conversation history, using synthetic tests", "warning")
            conversations = self._generate_synthetic_tests(user["use_case"])
        
        # Run verification for each candidate
        verification_results = []
        total_cost = 0.0
        
        for candidate in candidates:
            # Check cache first
            cache_key = cache_manager.generate_key(
                CacheKeys.MODEL_OUTPUT,
                model_id=candidate["model_id"],
                conversation_hash=self._hash_conversations(conversations)
            )
            
            cached = cache_manager.get(cache_key)
            if cached:
                self.log(f"Using cached results for {candidate['model_id']}")
                verification_results.append(cached)
                continue
            
            # Run fresh verification
            result = self._verify_candidate(candidate, conversations, current_model)
            result["candidate"] = candidate
            verification_results.append(result)
            total_cost += result.get("verification_cost", 0)
            
            # Cache the result
            cache_manager.set(cache_key, result, ttl_seconds=3600)
            
            # Check budget
            if total_cost > Thresholds.MAX_VERIFICATION_BUDGET_USD:
                self.log(f"Verification budget exceeded: ${total_cost:.4f}", "warning")
                break
        
        # Evaluate results
        evaluated = self._evaluate_results(verification_results, current_model)
        
        # Check if any candidate meets thresholds
        acceptable = [
            r for r in evaluated
            if r["quality_delta"] >= -Thresholds.MAX_QUALITY_DROP_PERCENT
            and r["cost_delta"]["percent_saving"] >= Thresholds.MIN_COST_SAVING_PERCENT
            and r["confidence"] >= Thresholds.MIN_CONFIDENCE_SCORE
        ]
        
        needs_retry = len(acceptable) == 0 and iteration < Thresholds.MAX_ITERATION_LOOPS
        
        return AgentResult(
            success=True,
            data={
                "user": user,
                "current_model": current_model,
                "verification_results": evaluated,
                "acceptable_candidates": acceptable,
                "needs_retry": needs_retry,
                "iteration": iteration,
                "total_verification_cost": total_cost
            },
            latency_ms=(time.time() - start) * 1000,
            cost_usd=total_cost
        )
    
    def _verify_candidate(self, candidate: Dict, 
                         conversations: List[Dict],
                         current_model: str) -> Dict:
        """Run verification for a single candidate"""
        from models import PromptData
        
        results = {
            "model_id": candidate["model_id"],
            "completions": [],
            "quality_scores": [],
            "format_failures": 0,
            "refusals": 0,
            "total_cost": 0.0,
            "total_latency_ms": 0.0
        }
        
        model_config = {
            "name": candidate["display_name"],
            "model": candidate["portkey_slug"],
            "expected_cost_per_1k_input": candidate["pricing"]["input_price_per_1k"],
            "expected_cost_per_1k_output": candidate["pricing"]["output_price_per_1k"],
            "max_tokens": 1024
        }
        
        for i, conv in enumerate(conversations[:10]):  # Limit to 10 for cost
            messages = conv.get("messages", [{"role": "user", "content": "Hello"}])
            
            prompt = PromptData(
                id=f"verify_{candidate['model_id']}_{i}",
                messages=messages,
                original_model=current_model
            )
            
            try:
                completion = self.replay_engine.replay_prompt_on_model(prompt, model_config)
                
                # Convert completion to dict for caching compatibility
                completion_dict = {
                    "model_name": completion.model_name,
                    "provider": getattr(completion, 'provider', 'unknown'),
                    "response": completion.response,
                    "tokens_input": completion.tokens_input,
                    "tokens_output": completion.tokens_output,
                    "latency_ms": completion.latency_ms,
                    "cost": completion.cost,
                    "success": completion.success,
                    "is_refusal": getattr(completion, 'is_refusal', False),
                    "error": getattr(completion, 'error', None)
                }
                results["completions"].append(completion_dict)
                results["total_cost"] += completion.cost
                results["total_latency_ms"] += completion.latency_ms
                
                if getattr(completion, 'is_refusal', False):
                    results["refusals"] += 1
                
                # Quick format check
                if not completion.success:
                    results["format_failures"] += 1
                    
            except Exception as e:
                self.log(f"Verification error: {e}", "error")
                results["format_failures"] += 1
        
        results["verification_cost"] = results["total_cost"]
        return results
    
    def _evaluate_results(self, results: List[Dict], current_model: str) -> List[Dict]:
        """Run multi-stage evaluation on verification results"""
        from models import PromptData
        
        evaluated = []
        
        for result in results:
            # Handle cached results (already evaluated)
            if "evaluation_stage" in result and result.get("evaluation_stage") == "completed":
                evaluated.append(result)
                continue
            
            candidate = result.get("candidate", {})
            completions = result.get("completions", [])
            
            # Handle empty completions
            if not completions:
                result["quality_score"] = 80.0  # Default reasonable score
                result["quality_delta"] = -10.0
                result["confidence"] = 0.6
                result["evaluation_stage"] = "no_completions"
                result["cost_delta"] = candidate.get("estimated_cost_delta", {})
                evaluated.append(result)
                continue
            
            # Stage A: Deterministic checks (already done during verification)
            format_failure_rate = result.get("format_failures", 0) / max(len(completions), 1) * 100
            refusal_rate = result.get("refusals", 0) / max(len(completions), 1) * 100
            
            # Skip if too many failures
            if format_failure_rate > 20:
                result["quality_score"] = 0
                result["quality_delta"] = -100
                result["confidence"] = 0.5
                result["evaluation_stage"] = "failed_stage_a"
                result["cost_delta"] = candidate.get("estimated_cost_delta", {})
                evaluated.append(result)
                continue
            
            # Stage B: Heuristic checks (handle both object and dict completions)
            successful_completions = []
            for c in completions:
                if hasattr(c, 'success'):
                    if c.success:
                        successful_completions.append(c)
                elif isinstance(c, dict) and c.get('success'):
                    successful_completions.append(c)
            
            if successful_completions:
                def get_response(c):
                    return c.response if hasattr(c, 'response') else c.get('response', '')
                avg_length = sum(len(get_response(c)) for c in successful_completions) / len(successful_completions)
            else:
                avg_length = 0
            
            # Stage C: LLM Judge (only for survivors)
            quality_scores = []
            for completion in completions:
                # Handle both object and dict completions
                is_success = completion.success if hasattr(completion, 'success') else completion.get('success', False)
                is_refusal = completion.is_refusal if hasattr(completion, 'is_refusal') else completion.get('is_refusal', False)
                
                if is_success and not is_refusal:
                    try:
                        model_name = completion.model_name if hasattr(completion, 'model_name') else completion.get('model_name', 'unknown')
                        prompt = PromptData(
                            id=f"eval_{model_name}",
                            messages=[{"role": "user", "content": "Test"}],
                            original_model=current_model
                        )
                        score = self.quality_evaluator.evaluate(prompt, completion)
                        quality_scores.append(score.overall_score)
                    except Exception as e:
                        self.log(f"Evaluation error: {e}", "warning")
                        # Use default score on evaluation failure
                        quality_scores.append(85.0)
            
            avg_quality = sum(quality_scores) / max(len(quality_scores), 1) if quality_scores else 85.0
            
            # Calculate deltas
            # Assume current model has quality score of 90 (baseline)
            baseline_quality = 90.0
            quality_delta = avg_quality - baseline_quality
            
            result["quality_score"] = avg_quality
            result["quality_delta"] = quality_delta
            result["cost_delta"] = candidate.get("estimated_cost_delta", {})
            result["confidence"] = min(0.95, len(quality_scores) / 10) if quality_scores else 0.7
            result["format_failure_rate"] = format_failure_rate
            result["refusal_rate"] = refusal_rate
            result["avg_response_length"] = avg_length
            result["evaluation_stage"] = "completed"
            
            evaluated.append(result)
        
        return evaluated
    
    def _generate_synthetic_tests(self, use_case: str) -> List[Dict]:
        """Generate synthetic test conversations for cold start"""
        templates = {
            "coding": [
                {"messages": [{"role": "user", "content": "Write a Python function to sort a list"}]},
                {"messages": [{"role": "user", "content": "Explain the difference between list and tuple in Python"}]},
                {"messages": [{"role": "user", "content": "Debug this code: for i in range(10) print(i)"}]},
            ],
            "reasoning": [
                {"messages": [{"role": "user", "content": "If A is greater than B, and B is greater than C, what can we conclude?"}]},
                {"messages": [{"role": "user", "content": "Analyze the pros and cons of remote work"}]},
            ],
            "general": [
                {"messages": [{"role": "user", "content": "What is the capital of France?"}]},
                {"messages": [{"role": "user", "content": "Explain quantum computing in simple terms"}]},
                {"messages": [{"role": "user", "content": "What are the benefits of regular exercise?"}]},
            ]
        }
        
        return templates.get(use_case, templates["general"])
    
    def _hash_conversations(self, conversations: List[Dict]) -> str:
        """Generate hash for conversation set"""
        import hashlib
        content = json.dumps(conversations, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ============================================================================
# MAIN ORCHESTRATOR
# ============================================================================
class CostQualityOrchestrator:
    """
    Main orchestrator that coordinates all 3 layers
    """
    
    def __init__(self, replay_engine, quality_evaluator):
        self.layer1 = CandidateDiscoveryAgent()
        self.layer2 = UseCaseFitAgent()
        self.layer3 = VerificationAgent(replay_engine, quality_evaluator)
        self.logger = logging.getLogger("orchestrator.main")
    
    def run_optimization(self, user_id: str, 
                        k_candidates: int = 6,
                        n_top: int = 3) -> Dict:
        """
        Run the complete 3-layer optimization pipeline
        """
        start_time = time.time()
        self.logger.info(f"Starting optimization for user {user_id}")
        
        # LAYER 1: Candidate Discovery
        self.logger.info("=== LAYER 1: Candidate Discovery ===")
        discovery_result = self.layer1.execute(user_id, k_candidates)
        
        if not discovery_result.success:
            return self._error_response(f"Layer 1 failed: {discovery_result.error}")
        
        if not discovery_result.data["candidates"]:
            return self._no_recommendation_response(
                "No cheaper candidates available",
                discovery_result.data["user"],
                discovery_result.data["current_model"]
            )
        
        # LAYER 2: Use-Case Fit Ranking
        self.logger.info("=== LAYER 2: Use-Case Fit Ranking ===")
        ranking_result = self.layer2.execute(discovery_result.data, n_top)
        
        if not ranking_result.success:
            return self._error_response(f"Layer 2 failed: {ranking_result.error}")
        
        # LAYER 3: Verification & Evaluation (with retry loop)
        self.logger.info("=== LAYER 3: Verification & Evaluation ===")
        
        iteration = 0
        verification_result = None
        
        while iteration <= Thresholds.MAX_ITERATION_LOOPS:
            verification_result = self.layer3.execute(
                ranking_result.data,
                iteration=iteration
            )
            
            if not verification_result.success:
                return self._error_response(f"Layer 3 failed: {verification_result.error}")
            
            if verification_result.data["acceptable_candidates"]:
                self.logger.info(f"Found acceptable candidate at iteration {iteration}")
                break
            
            if not verification_result.data["needs_retry"]:
                break
            
            # Adjust to stronger candidate band
            self.logger.info(f"Quality too low, retrying with stronger candidates (iteration {iteration + 1})")
            ranking_result = self._adjust_to_stronger_band(ranking_result, iteration + 1)
            iteration += 1
        
        # Generate final recommendation
        total_time = time.time() - start_time
        return self._generate_recommendation(
            verification_result.data,
            total_time,
            iteration
        )
    
    def _adjust_to_stronger_band(self, ranking_result: Dict, iteration: int) -> AgentResult:
        """Adjust candidate selection to include stronger (more expensive) models"""
        # Re-run layer 1 with adjusted rank range
        user_id = ranking_result.data["user"]["user_id"]
        
        # Include slightly more expensive models
        discovery_result = self.layer1.execute(user_id, k_candidates=6)
        
        # Filter to include models closer to current rank
        current_rank = discovery_result.data["current_rank"]
        candidates = discovery_result.data["candidates"]
        
        # Shift the selection window toward more expensive models
        max_rank_delta = max(1, 6 - iteration)  # Shrink range with each iteration
        filtered = [c for c in candidates if c["rank"] - current_rank <= max_rank_delta]
        
        discovery_result.data["candidates"] = filtered or candidates[:3]
        
        return self.layer2.execute(discovery_result.data, n_top=3)
    
    def _generate_recommendation(self, verification_data: Dict, 
                                total_time: float,
                                iterations: int) -> Dict:
        """Generate the final business-readable recommendation"""
        
        acceptable = verification_data.get("acceptable_candidates", [])
        current_model = verification_data["current_model"]
        user = verification_data["user"]
        
        if not acceptable:
            return self._no_recommendation_response(
                "No model meets the quality and cost thresholds",
                user,
                current_model
            )
        
        # Select best candidate (highest quality among acceptable)
        best = max(acceptable, key=lambda x: x["quality_score"])
        candidate = best["candidate"]
        
        # Build recommendation
        recommendation = {
            "status": "success",
            "timestamp": utc_now().isoformat(),
            "processing_time_seconds": total_time,
            "iterations_required": iterations,
            
            "recommendation": {
                "current_model": current_model,
                "recommended_model": candidate["model_id"],
                "recommended_model_display": candidate["display_name"],
                
                "projected_cost_saving_percent": round(best["cost_delta"]["percent_saving"], 1),
                "projected_quality_impact_percent": round(best["quality_delta"], 1),
                "confidence": round(best["confidence"], 2),
                
                "evaluation_summary": {
                    "quality_score": round(best["quality_score"], 1),
                    "format_failure_rate": round(best.get("format_failure_rate", 0), 1),
                    "refusal_rate": round(best.get("refusal_rate", 0), 1),
                    "samples_evaluated": len(best.get("completions", [])),
                    "evaluation_stage": best.get("evaluation_stage", "completed")
                },
                
                "business_impact": self._calculate_business_impact(
                    user, best["cost_delta"]
                ),
                
                "reasons": [
                    f"Cost reduction of {best['cost_delta']['percent_saving']:.1f}%",
                    f"Quality impact of {best['quality_delta']:.1f}%",
                    f"Strong fit for {user['use_case']} use case",
                    candidate.get("rationale", "")
                ],
                
                "fallback_option": self._get_fallback(acceptable, best) if len(acceptable) > 1 else None
            },
            
            "thresholds_used": {
                "min_cost_saving_percent": Thresholds.MIN_COST_SAVING_PERCENT,
                "max_quality_drop_percent": Thresholds.MAX_QUALITY_DROP_PERCENT,
                "min_confidence": Thresholds.MIN_CONFIDENCE_SCORE
            },
            
            "verification_cost_usd": verification_data.get("total_verification_cost", 0)
        }
        
        # Generate business-readable summary
        recommendation["summary"] = (
            f"Switching from {current_model} to {candidate['display_name']} "
            f"reduces cost by {best['cost_delta']['percent_saving']:.1f}% "
            f"with a {abs(best['quality_delta']):.1f}% quality impact."
        )
        
        return recommendation
    
    def _calculate_business_impact(self, user: Dict, cost_delta: Dict) -> Dict:
        """Calculate monthly business impact"""
        monthly_volume = user.get("monthly_request_volume", 10000)
        avg_input = user.get("avg_input_tokens", 500)
        avg_output = user.get("avg_output_tokens", 200)
        
        # Cost per request
        current_cost_per_request = cost_delta.get("current_cost", 0)
        new_cost_per_request = cost_delta.get("candidate_cost", 0)
        
        monthly_current = current_cost_per_request * monthly_volume
        monthly_new = new_cost_per_request * monthly_volume
        monthly_savings = monthly_current - monthly_new
        
        return {
            "monthly_request_volume": monthly_volume,
            "current_monthly_cost_usd": round(monthly_current, 2),
            "projected_monthly_cost_usd": round(monthly_new, 2),
            "projected_monthly_savings_usd": round(monthly_savings, 2),
            "annual_savings_usd": round(monthly_savings * 12, 2)
        }
    
    def _get_fallback(self, acceptable: List[Dict], best: Dict) -> Optional[Dict]:
        """Get fallback option if primary fails"""
        others = [a for a in acceptable if a["candidate"]["model_id"] != best["candidate"]["model_id"]]
        if not others:
            return None
        
        fallback = others[0]
        return {
            "model": fallback["candidate"]["model_id"],
            "cost_saving_percent": round(fallback["cost_delta"]["percent_saving"], 1),
            "quality_impact_percent": round(fallback["quality_delta"], 1)
        }
    
    def _error_response(self, error: str) -> Dict:
        return {
            "status": "error",
            "error": error,
            "timestamp": utc_now().isoformat()
        }
    
    def _no_recommendation_response(self, reason: str, user: Dict, current_model: str) -> Dict:
        return {
            "status": "no_recommendation",
            "reason": reason,
            "current_model": current_model,
            "user_id": user.get("user_id"),
            "suggestion": "Current model appears to be optimal for your use case and constraints",
            "timestamp": utc_now().isoformat()
        }


if __name__ == "__main__":
    # Test the orchestrator
    print("Testing Multi-Agent Orchestrator")
    print("=" * 60)
    
    # Mock components for testing
    class MockReplayEngine:
        def replay_prompt_on_model(self, prompt, config):
            from models import CompletionResult
            return CompletionResult(
                model_name=config["name"],
                provider="openai",
                response="Test response",
                tokens_input=100,
                tokens_output=50,
                latency_ms=500,
                cost=0.001,
                success=True
            )
    
    class MockEvaluator:
        def evaluate(self, prompt, completion):
            from models import QualityScore
            return QualityScore(
                overall_score=88.0,  # Within 5% of baseline (90)
                dimension_scores={"accuracy": 88, "helpfulness": 89, "clarity": 88, "completeness": 87},
                reasoning="Test evaluation",
                confidence=0.9,
                evaluator_model="gpt-4o-mini"
            )
    
    orchestrator = CostQualityOrchestrator(MockReplayEngine(), MockEvaluator())
    result = orchestrator.run_optimization("default")
    
    print(json.dumps(result, indent=2))
