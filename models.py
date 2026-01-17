"""
Data models for the Cost-Quality Optimization System
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime
import json


@dataclass
class PromptData:
    """Represents a prompt to be replayed"""
    id: str
    messages: List[Dict[str, str]]
    original_model: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self):
        return asdict(self)


@dataclass
class CompletionResult:
    """Result from a model completion"""
    model_name: str
    provider: str
    response: str
    tokens_input: int
    tokens_output: int
    latency_ms: float
    cost: float
    success: bool
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self):
        return asdict(self)


@dataclass
class QualityScore:
    """Quality evaluation score for a completion"""
    overall_score: float  # 0-100
    dimension_scores: Dict[str, float]  # Individual criteria scores
    reasoning: str
    confidence: float  # 0-1
    evaluator_model: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self):
        return asdict(self)


@dataclass
class ModelEvaluation:
    """Complete evaluation for a model on a prompt"""
    prompt_id: str
    model_name: str
    completion: CompletionResult
    quality: QualityScore
    cost_quality_ratio: float  # cost per quality point
    
    def to_dict(self):
        return asdict(self)


@dataclass
class OptimizationRecommendation:
    """Recommendation for model switching"""
    current_model: str
    recommended_model: str
    cost_reduction_percent: float
    quality_impact_percent: float
    confidence_score: float
    sample_size: int
    reasoning: str
    metrics: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self):
        return asdict(self)
    
    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class ReplayState:
    """State tracking for continuous monitoring"""
    last_processed_timestamp: str
    processed_prompt_ids: List[str] = field(default_factory=list)
    active_evaluations: Dict[str, str] = field(default_factory=dict)  # prompt_id -> status
    total_prompts_processed: int = 0
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**data)
