"""
State Manager - Handles persistence and state tracking
"""
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path
from models import ReplayState, ModelEvaluation
from config import STATE_FILE, RESULTS_FILE, CACHE_FILE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StateManager:
    """Manages persistent state for continuous monitoring"""
    
    def __init__(
        self, 
        state_file: str = STATE_FILE,
        results_file: str = RESULTS_FILE,
        cache_file: str = CACHE_FILE
    ):
        self.state_file = Path(state_file)
        self.results_file = Path(results_file)
        self.cache_file = Path(cache_file)
    
    def load_state(self) -> ReplayState:
        """Load state from disk or create new"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                logger.info(f"Loaded state: {data['total_prompts_processed']} prompts processed")
                return ReplayState.from_dict(data)
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
        
        logger.info("Creating new state")
        return ReplayState(last_processed_timestamp="1970-01-01T00:00:00Z")
    
    def save_state(self, state: ReplayState):
        """Save state to disk"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state.to_dict(), f, indent=2)
            logger.info(f"State saved: {state.total_prompts_processed} prompts processed")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def save_evaluations(self, evaluations: List[ModelEvaluation]):
        """Append evaluations to results file"""
        try:
            # Load existing results
            existing = []
            if self.results_file.exists():
                with open(self.results_file, 'r') as f:
                    existing = json.load(f)
            
            # Append new evaluations
            new_data = [eval.to_dict() for eval in evaluations]
            existing.extend(new_data)
            
            # Save
            with open(self.results_file, 'w') as f:
                json.dump(existing, f, indent=2)
            
            logger.info(f"Saved {len(evaluations)} evaluations (total: {len(existing)})")
        except Exception as e:
            logger.error(f"Failed to save evaluations: {e}")
    
    def load_evaluations(self) -> List[Dict]:
        """Load all evaluations from results file"""
        if not self.results_file.exists():
            return []
        
        try:
            with open(self.results_file, 'r') as f:
                data = json.load(f)
            logger.info(f"Loaded {len(data)} evaluations")
            return data
        except Exception as e:
            logger.error(f"Failed to load evaluations: {e}")
            return []
    
    def get_evaluation_cache(self, prompt_id: str, model_name: str) -> Optional[Dict]:
        """Check if evaluation exists in cache"""
        if not self.cache_file.exists():
            return None
        
        try:
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
            
            cache_key = f"{prompt_id}:{model_name}"
            return cache.get(cache_key)
        except Exception as e:
            logger.error(f"Failed to read cache: {e}")
            return None
    
    def save_to_cache(self, prompt_id: str, model_name: str, evaluation: Dict):
        """Save evaluation to cache"""
        try:
            cache = {}
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
            
            cache_key = f"{prompt_id}:{model_name}"
            cache[cache_key] = evaluation
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save to cache: {e}")
    
    def mark_prompt_processed(self, state: ReplayState, prompt_id: str):
        """Mark a prompt as processed in state"""
        if prompt_id not in state.processed_prompt_ids:
            state.processed_prompt_ids.append(prompt_id)
            state.total_prompts_processed += 1
