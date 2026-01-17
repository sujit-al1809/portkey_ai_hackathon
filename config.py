"""
Configuration file for the Cost-Quality Optimization System
"""
import os
from typing import List, Dict

# Portkey Configuration
PORTKEY_API_KEY = os.getenv("PORTKEY_API_KEY", "")

# Model Configurations for Testing
# Format: {"name": "display_name", "provider": "slug_from_portkey", "model": "model_name"}
MODELS_TO_TEST = [
    {
        "name": "GPT-4o-mini",
        "model": "@openai/gpt-4o-mini",  # Model Catalog format
        "expected_cost_per_1k_input": 0.00015,
        "expected_cost_per_1k_output": 0.0006
    },
    {
        "name": "GPT-3.5-turbo",
        "model": "@openai/gpt-3.5-turbo",  # Model Catalog format
        "expected_cost_per_1k_input": 0.0005,
        "expected_cost_per_1k_output": 0.0015
    }
]

# Quality Evaluation Settings
QUALITY_JUDGE_MODEL = "gpt-4o-mini"  # Model to use for quality evaluation
QUALITY_JUDGE_PROVIDER = "openai"

# Evaluation Criteria
EVALUATION_CRITERIA = {
    "accuracy": "How accurate and factual is the response?",
    "helpfulness": "How helpful and relevant is the response to the user's query?",
    "clarity": "How clear and well-structured is the response?",
    "completeness": "How complete and comprehensive is the response?"
}

# State Management
STATE_FILE = "replay_state.json"
RESULTS_FILE = "optimization_results.json"
CACHE_FILE = "evaluation_cache.json"

# Continuous Monitoring Settings
MONITORING_INTERVAL = 300  # Check for new prompts every 5 minutes
MAX_CONCURRENT_REPLAYS = 5  # Maximum number of concurrent replay operations

# Confidence Thresholds
MIN_CONFIDENCE_SCORE = 0.7  # Minimum confidence to recommend model switch
MIN_SAMPLE_SIZE = 10  # Minimum number of prompts needed for reliable analysis

# Failure Handling
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
TIMEOUT = 30  # seconds per request
