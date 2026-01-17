"""
Model Registry - Complete model properties and capabilities metadata
Versioned, conflict-aware, with multiple source tracking
"""
import json
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

REGISTRY_VERSION = "1.0.0"

@dataclass
class ModelCapabilities:
    """Model capability metadata"""
    context_window: int
    supports_function_calling: bool
    supports_json_mode: bool
    supports_vision: bool
    supports_streaming: bool
    latency_tier: str  # "fast", "medium", "slow"
    reliability_tier: str  # "high", "medium", "low"
    strengths: List[str]  # ["coding", "reasoning", "extraction", "summarization", "creative"]
    known_failure_modes: List[str] = field(default_factory=list)
    
@dataclass
class ModelPricing:
    """Model pricing information"""
    input_price_per_1k: float
    output_price_per_1k: float
    minimum_billing_increment: int = 1
    rate_limit_rpm: int = 1000
    rate_limit_tpm: int = 100000
    batch_discount_percent: float = 0.0
    
@dataclass
class ModelEntry:
    """Complete model registry entry"""
    model_id: str
    display_name: str
    provider: str
    portkey_slug: str  # @provider/model format
    rank: int  # 1 = most expensive/powerful, 10 = cheapest
    capabilities: ModelCapabilities
    pricing: ModelPricing
    last_verified: str
    confidence_score: float = 0.95
    source_urls: List[str] = field(default_factory=list)
    version: str = REGISTRY_VERSION


# Complete Model Registry - Ranked by cost (1=expensive, 10=cheap)
MODEL_REGISTRY: Dict[str, ModelEntry] = {
    "gpt-4-turbo": ModelEntry(
        model_id="gpt-4-turbo",
        display_name="GPT-4 Turbo",
        provider="openai",
        portkey_slug="@openai/gpt-4-turbo",
        rank=1,
        capabilities=ModelCapabilities(
            context_window=128000,
            supports_function_calling=True,
            supports_json_mode=True,
            supports_vision=True,
            supports_streaming=True,
            latency_tier="medium",
            reliability_tier="high",
            strengths=["reasoning", "coding", "analysis", "complex_tasks"],
            known_failure_modes=["expensive", "slower_than_gpt4o"]
        ),
        pricing=ModelPricing(
            input_price_per_1k=0.01,
            output_price_per_1k=0.03,
            rate_limit_rpm=500,
            rate_limit_tpm=30000
        ),
        last_verified=datetime.utcnow().isoformat(),
        source_urls=["https://openai.com/pricing"]
    ),
    
    "gpt-4o": ModelEntry(
        model_id="gpt-4o",
        display_name="GPT-4o",
        provider="openai",
        portkey_slug="@openai/gpt-4o",
        rank=2,
        capabilities=ModelCapabilities(
            context_window=128000,
            supports_function_calling=True,
            supports_json_mode=True,
            supports_vision=True,
            supports_streaming=True,
            latency_tier="fast",
            reliability_tier="high",
            strengths=["reasoning", "vision", "general", "multimodal"],
            known_failure_modes=[]
        ),
        pricing=ModelPricing(
            input_price_per_1k=0.005,
            output_price_per_1k=0.015,
            rate_limit_rpm=500,
            rate_limit_tpm=30000
        ),
        last_verified=datetime.utcnow().isoformat(),
        source_urls=["https://openai.com/pricing"]
    ),
    
    "gpt-4o-mini": ModelEntry(
        model_id="gpt-4o-mini",
        display_name="GPT-4o Mini",
        provider="openai",
        portkey_slug="@openai/gpt-4o-mini",
        rank=4,  # Cheapest OpenAI model
        capabilities=ModelCapabilities(
            context_window=128000,
            supports_function_calling=True,
            supports_json_mode=True,
            supports_vision=True,
            supports_streaming=True,
            latency_tier="fast",
            reliability_tier="high",
            strengths=["general", "reasoning", "creative", "cost_effective"],
            known_failure_modes=["less_capable_than_gpt4o"]
        ),
        pricing=ModelPricing(
            input_price_per_1k=0.00015,
            output_price_per_1k=0.0006,
            rate_limit_rpm=1000,
            rate_limit_tpm=100000
        ),
        last_verified=datetime.utcnow().isoformat(),
        source_urls=["https://openai.com/pricing"]
    ),
    
    "gpt-3.5-turbo": ModelEntry(
        model_id="gpt-3.5-turbo",
        display_name="GPT-3.5 Turbo",
        provider="openai",
        portkey_slug="@openai/gpt-3.5-turbo",
        rank=3,  # More expensive than gpt-4o-mini!
        capabilities=ModelCapabilities(
            context_window=16385,
            supports_function_calling=True,
            supports_json_mode=True,
            supports_vision=False,
            supports_streaming=True,
            latency_tier="fast",
            reliability_tier="high",
            strengths=["general", "fast", "cost_effective", "high_volume"],
            known_failure_modes=["less_reasoning", "shorter_context"]
        ),
        pricing=ModelPricing(
            input_price_per_1k=0.0005,
            output_price_per_1k=0.0015,
            rate_limit_rpm=3500,
            rate_limit_tpm=90000
        ),
        last_verified=datetime.utcnow().isoformat(),
        source_urls=["https://openai.com/pricing"]
    ),
}


class ModelRegistryService:
    """Service for managing model registry with versioning and conflict handling"""
    
    def __init__(self):
        self.registry = MODEL_REGISTRY
        self.version = REGISTRY_VERSION
        self.conflicts: List[Dict] = []
    
    def get_model(self, model_id: str) -> Optional[ModelEntry]:
        """Get a single model by ID"""
        return self.registry.get(model_id)
    
    def get_all_models(self) -> List[ModelEntry]:
        """Get all models sorted by rank"""
        return sorted(self.registry.values(), key=lambda x: x.rank)
    
    def get_models_by_rank_range(self, min_rank: int, max_rank: int) -> List[ModelEntry]:
        """Get models within a rank range (inclusive)"""
        return [m for m in self.registry.values() if min_rank <= m.rank <= max_rank]
    
    def get_cheaper_models(self, current_model_id: str) -> List[ModelEntry]:
        """Get all models cheaper than the current model (higher rank number)"""
        current = self.registry.get(current_model_id)
        if not current:
            return []
        return [m for m in self.registry.values() if m.rank > current.rank]
    
    def get_models_for_use_case(self, use_case: str) -> List[ModelEntry]:
        """Get models that are strong for a specific use case"""
        use_case_mapping = {
            "coding": ["coding", "reasoning"],
            "reasoning": ["reasoning", "analysis"],
            "extraction": ["extraction", "general"],
            "summarization": ["summarization", "general"],
            "creative": ["creative", "general"],
            "support_bot": ["general", "fast", "cost_effective"],
            "general": ["general"]
        }
        
        required_strengths = use_case_mapping.get(use_case, ["general"])
        scored_models = []
        
        for model in self.registry.values():
            score = sum(1 for s in required_strengths if s in model.capabilities.strengths)
            if score > 0:
                scored_models.append((model, score))
        
        scored_models.sort(key=lambda x: (-x[1], x[0].rank))
        return [m for m, s in scored_models]
    
    def calculate_cost(self, model_id: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for a model given token counts"""
        model = self.registry.get(model_id)
        if not model:
            return 0.0
        
        input_cost = (input_tokens / 1000) * model.pricing.input_price_per_1k
        output_cost = (output_tokens / 1000) * model.pricing.output_price_per_1k
        return input_cost + output_cost
    
    def calculate_cost_delta(self, current_model_id: str, candidate_model_id: str, 
                            avg_input_tokens: int, avg_output_tokens: int) -> Dict[str, float]:
        """Calculate cost savings between two models"""
        current_cost = self.calculate_cost(current_model_id, avg_input_tokens, avg_output_tokens)
        candidate_cost = self.calculate_cost(candidate_model_id, avg_input_tokens, avg_output_tokens)
        
        if current_cost == 0:
            return {"absolute_saving": 0, "percent_saving": 0}
        
        absolute_saving = current_cost - candidate_cost
        percent_saving = (absolute_saving / current_cost) * 100
        
        return {
            "current_cost": current_cost,
            "candidate_cost": candidate_cost,
            "absolute_saving": absolute_saving,
            "percent_saving": percent_saving
        }
    
    def register_conflict(self, model_id: str, field: str, 
                         value_a: Any, source_a: str,
                         value_b: Any, source_b: str):
        """Register a conflict when sources disagree"""
        self.conflicts.append({
            "model_id": model_id,
            "field": field,
            "values": [
                {"value": value_a, "source": source_a, "timestamp": datetime.utcnow().isoformat()},
                {"value": value_b, "source": source_b, "timestamp": datetime.utcnow().isoformat()}
            ],
            "resolved": False
        })
    
    def get_unresolved_conflicts(self) -> List[Dict]:
        """Get all unresolved conflicts"""
        return [c for c in self.conflicts if not c["resolved"]]
    
    def to_dict(self) -> Dict:
        """Export registry as dict"""
        return {
            "version": self.version,
            "models": {k: asdict(v) for k, v in self.registry.items()},
            "conflicts": self.conflicts
        }


# Global instance
model_registry = ModelRegistryService()


if __name__ == "__main__":
    print(f"Model Registry v{REGISTRY_VERSION}")
    print(f"Total models: {len(MODEL_REGISTRY)}")
    print("\nModels by rank:")
    for model in model_registry.get_all_models():
        print(f"  Rank {model.rank}: {model.display_name} (${model.pricing.input_price_per_1k}/1K in)")
