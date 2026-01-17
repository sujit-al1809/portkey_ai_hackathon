"""
Configuration file for the Cost-Quality Optimization System
"""
import os
from typing import List, Dict

# Portkey Configuration
PORTKEY_API_KEY = os.getenv("PORTKEY_API_KEY", "")

# Model Configurations for Testing
# Multiple providers for better cost-quality comparison
MODELS_TO_TEST = [
    # OpenAI Models
    {
        "name": "GPT-4o-mini",
        "model": "@openai/gpt-4o-mini",
        "expected_cost_per_1k_input": 0.00015,
        "expected_cost_per_1k_output": 0.0006,
        "strengths": ["general", "reasoning", "creative"],
        "max_tokens": 1024
    },
    {
        "name": "GPT-3.5-turbo",
        "model": "@openai/gpt-3.5-turbo",
        "expected_cost_per_1k_input": 0.0005,
        "expected_cost_per_1k_output": 0.0015,
        "strengths": ["general", "fast", "cost-effective"],
        "max_tokens": 1024
    },
    {
        "name": "GPT-4-turbo",
        "model": "@openai/gpt-4-turbo",
        "expected_cost_per_1k_input": 0.01,
        "expected_cost_per_1k_output": 0.03,
        "strengths": ["reasoning", "code", "analysis"],
        "max_tokens": 1024
    },
    {
        "name": "GPT-4o",
        "model": "@openai/gpt-4o",
        "expected_cost_per_1k_input": 0.005,
        "expected_cost_per_1k_output": 0.015,
        "strengths": ["vision", "reasoning", "general"],
        "max_tokens": 1024
    },
    
    # Anthropic Claude
    {
        "name": "Claude-3-Sonnet",
        "model": "@anthropic/claude-3-sonnet-20240229",
        "expected_cost_per_1k_input": 0.003,
        "expected_cost_per_1k_output": 0.015,
        "strengths": ["reasoning", "code", "analysis"],
        "max_tokens": 1024
    },
    
    # AWS Bedrock
    {
        "name": "Claude-3-Haiku-Bedrock",
        "model": "@bedrock/anthropic.claude-3-haiku-20240307-v1:0",
        "expected_cost_per_1k_input": 0.00025,
        "expected_cost_per_1k_output": 0.00125,
        "strengths": ["fast", "cost-effective", "general"],
        "max_tokens": 1024
    },
    
    # Grok
    {
        "name": "Grok-2",
        "model": "@grok/grok-2",
        "expected_cost_per_1k_input": 0.002,
        "expected_cost_per_1k_output": 0.01,
        "strengths": ["reasoning", "creative", "general"],
        "max_tokens": 1024
    }
]

# Use Case Categories
USE_CASE_KEYWORDS = {
    "code": ["function", "code", "python", "javascript", "programming", "debug", "algorithm", "script"],
    "security": ["security", "vulnerability", "hack", "encrypt", "authentication", "secure", "threat"],
    "creative": ["story", "poem", "haiku", "creative", "write", "imagine", "design"],
    "analysis": ["analyze", "compare", "evaluate", "review", "assess", "explain"],
    "general": ["what", "how", "why", "tell", "describe"]
}

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
