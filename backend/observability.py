"""
Structured Logging & Observability for Production Systems
Provides metrics, logging, and monitoring for the optimization system
"""
import logging
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from functools import wraps
from dataclasses import dataclass, asdict
import sqlite3

# Configure structured logging
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Setup file and console handlers
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f"system_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("optimization_system")


@dataclass
class SystemMetrics:
    """System-wide metrics for observability"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_refusals: int = 0
    total_cost: float = 0.0
    avg_latency_ms: float = 0.0
    uptime_seconds: float = 0.0
    last_updated: str = ""
    
    def to_dict(self):
        return asdict(self)


class MetricsCollector:
    """Collects and exposes metrics for monitoring"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.start_time = time.time()
        self.metrics = SystemMetrics()
        self.model_metrics: Dict[str, Dict[str, Any]] = {}
        self._latencies = []
    
    def record_request(
        self, 
        model: str, 
        success: bool, 
        latency_ms: float, 
        cost: float,
        is_refusal: bool = False
    ):
        """Record a model request"""
        self.metrics.total_requests += 1
        self.metrics.total_cost += cost
        self._latencies.append(latency_ms)
        
        if success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1
        
        if is_refusal:
            self.metrics.total_refusals += 1
        
        # Update avg latency
        self.metrics.avg_latency_ms = sum(self._latencies) / len(self._latencies)
        
        # Model-specific metrics
        if model not in self.model_metrics:
            self.model_metrics[model] = {
                "requests": 0,
                "successes": 0,
                "failures": 0,
                "refusals": 0,
                "total_cost": 0.0,
                "total_latency": 0.0
            }
        
        m = self.model_metrics[model]
        m["requests"] += 1
        m["total_cost"] += cost
        m["total_latency"] += latency_ms
        if success:
            m["successes"] += 1
        else:
            m["failures"] += 1
        if is_refusal:
            m["refusals"] += 1
        
        self.metrics.last_updated = datetime.utcnow().isoformat()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all current metrics"""
        self.metrics.uptime_seconds = time.time() - self.start_time
        
        model_stats = {}
        for model, m in self.model_metrics.items():
            model_stats[model] = {
                "requests": m["requests"],
                "success_rate": m["successes"] / m["requests"] * 100 if m["requests"] > 0 else 0,
                "refusal_rate": m["refusals"] / m["requests"] * 100 if m["requests"] > 0 else 0,
                "avg_latency_ms": m["total_latency"] / m["requests"] if m["requests"] > 0 else 0,
                "avg_cost": m["total_cost"] / m["requests"] if m["requests"] > 0 else 0
            }
        
        return {
            "system": self.metrics.to_dict(),
            "models": model_stats
        }
    
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        m = self.metrics
        
        lines.append(f"optimization_requests_total {m.total_requests}")
        lines.append(f"optimization_requests_successful {m.successful_requests}")
        lines.append(f"optimization_requests_failed {m.failed_requests}")
        lines.append(f"optimization_refusals_total {m.total_refusals}")
        lines.append(f"optimization_cost_total {m.total_cost:.6f}")
        lines.append(f"optimization_latency_avg_ms {m.avg_latency_ms:.2f}")
        lines.append(f"optimization_uptime_seconds {time.time() - self.start_time:.0f}")
        
        for model, stats in self.model_metrics.items():
            safe_model = model.replace("-", "_").replace(".", "_").lower()
            lines.append(f'optimization_model_requests{{model="{model}"}} {stats["requests"]}')
            lines.append(f'optimization_model_refusals{{model="{model}"}} {stats["refusals"]}')
        
        return "\n".join(lines)


# Global metrics collector
metrics = MetricsCollector()


def log_operation(operation_name: str):
    """Decorator to log operation timing and success"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start) * 1000
                logger.info(f"[{operation_name}] SUCCESS in {duration:.2f}ms")
                return result
            except Exception as e:
                duration = (time.time() - start) * 1000
                logger.error(f"[{operation_name}] FAILED in {duration:.2f}ms: {str(e)}")
                raise
        return wrapper
    return decorator


class StructuredLogger:
    """Structured JSON logging for production analysis"""
    
    def __init__(self, component: str):
        self.component = component
        self.log_file = LOG_DIR / f"{component}_{datetime.now().strftime('%Y%m%d')}.jsonl"
    
    def log_event(self, event_type: str, data: Dict[str, Any], level: str = "info"):
        """Log a structured event"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "component": self.component,
            "event_type": event_type,
            "level": level,
            "data": data
        }
        
        # Write to JSONL file
        with open(self.log_file, "a") as f:
            f.write(json.dumps(event) + "\n")
        
        # Also log to standard logger
        log_method = getattr(logger, level, logger.info)
        log_method(f"[{self.component}] {event_type}: {json.dumps(data)}")
    
    def log_model_call(
        self, 
        model: str, 
        prompt_id: str, 
        success: bool, 
        latency_ms: float,
        cost: float,
        is_refusal: bool = False,
        error: Optional[str] = None
    ):
        """Log a model API call"""
        self.log_event("model_call", {
            "model": model,
            "prompt_id": prompt_id,
            "success": success,
            "latency_ms": latency_ms,
            "cost": cost,
            "is_refusal": is_refusal,
            "error": error
        }, level="warning" if not success or is_refusal else "info")
        
        # Record in metrics
        metrics.record_request(model, success, latency_ms, cost, is_refusal)
    
    def log_evaluation(self, prompt_id: str, model: str, quality_score: float):
        """Log a quality evaluation"""
        self.log_event("quality_evaluation", {
            "prompt_id": prompt_id,
            "model": model,
            "quality_score": quality_score
        })
    
    def log_recommendation(
        self, 
        current_model: str, 
        recommended_model: str,
        cost_reduction: float,
        quality_impact: float
    ):
        """Log an optimization recommendation"""
        self.log_event("recommendation", {
            "current_model": current_model,
            "recommended_model": recommended_model,
            "cost_reduction_percent": cost_reduction,
            "quality_impact_percent": quality_impact
        }, level="info")


# Create loggers for each component
replay_logger = StructuredLogger("replay_engine")
eval_logger = StructuredLogger("quality_evaluator")
optimizer_logger = StructuredLogger("optimizer")
api_logger = StructuredLogger("api")


def get_system_health() -> Dict[str, Any]:
    """Get overall system health status"""
    m = metrics.get_metrics()
    
    # Calculate health score
    success_rate = m["system"]["successful_requests"] / max(m["system"]["total_requests"], 1) * 100
    refusal_rate = m["system"]["total_refusals"] / max(m["system"]["total_requests"], 1) * 100
    
    health_score = 100
    health_score -= min(30, (100 - success_rate))  # Up to -30 for failures
    health_score -= min(20, refusal_rate)  # Up to -20 for refusals
    
    status = "healthy" if health_score >= 80 else "degraded" if health_score >= 50 else "unhealthy"
    
    return {
        "status": status,
        "health_score": health_score,
        "success_rate": success_rate,
        "refusal_rate": refusal_rate,
        "uptime_seconds": m["system"]["uptime_seconds"],
        "total_requests": m["system"]["total_requests"],
        "metrics": m
    }


if __name__ == "__main__":
    # Test the logging system
    print("Testing observability module...")
    
    # Simulate some metrics
    metrics.record_request("GPT-4o-mini", True, 250.5, 0.0015)
    metrics.record_request("GPT-4o-mini", True, 180.2, 0.0012)
    metrics.record_request("GPT-3.5-turbo", True, 120.0, 0.0008, is_refusal=True)
    metrics.record_request("GPT-3.5-turbo", False, 0, 0)
    
    print("\n📊 Metrics:")
    print(json.dumps(metrics.get_metrics(), indent=2))
    
    print("\n🏥 Health Check:")
    print(json.dumps(get_system_health(), indent=2))
    
    print("\n📈 Prometheus Export:")
    print(metrics.export_prometheus())
