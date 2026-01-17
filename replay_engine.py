"""
Historical Replay Engine - Replays prompts across multiple models
"""
import time
import logging
from typing import List, Dict, Optional
from portkey_ai import Portkey
from models import PromptData, CompletionResult
from config import (
    PORTKEY_API_KEY, MAX_RETRIES, RETRY_DELAY, TIMEOUT,
    MODELS_TO_TEST
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReplayEngine:
    """Replays historical prompts across multiple models with Portkey"""
    
    def __init__(self, api_key: str = PORTKEY_API_KEY):
        self.api_key = api_key
        self.models = MODELS_TO_TEST
        
    def _create_client(self, model: str) -> Portkey:
        """Create a Portkey client"""
        return Portkey(
            api_key=self.api_key
        )
    
    def _calculate_cost(self, model_config: Dict, tokens_input: int, tokens_output: int) -> float:
        """Calculate cost based on token usage"""
        input_cost = (tokens_input / 1000) * model_config["expected_cost_per_1k_input"]
        output_cost = (tokens_output / 1000) * model_config["expected_cost_per_1k_output"]
        return input_cost + output_cost
    
    def replay_prompt_on_model(
        self, 
        prompt: PromptData, 
        model_config: Dict,
        retry_count: int = 0
    ) -> CompletionResult:
        """
        Replay a single prompt on a specific model with retry logic
        """
        try:
            client = self._create_client(model_config["model"])
            
            start_time = time.time()
            
            response = client.chat.completions.create(
                model=model_config["model"],  # e.g., @openai/gpt-4o-mini
                messages=prompt.messages,
                timeout=TIMEOUT
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract response data
            completion_text = response.choices[0].message.content
            tokens_input = response.usage.prompt_tokens
            tokens_output = response.usage.completion_tokens
            
            # Calculate cost
            cost = self._calculate_cost(model_config, tokens_input, tokens_output)
            
            logger.info(f"✓ {model_config['name']}: {latency_ms:.0f}ms, ${cost:.6f}")
            
            return CompletionResult(
                model_name=model_config["name"],
                provider=model_config["model"].split("/")[0].replace("@", ""),  # Extract from @provider/model
                response=completion_text,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                latency_ms=latency_ms,
                cost=cost,
                success=True
            )
            
        except Exception as e:
            logger.error(f"✗ {model_config['name']}: {str(e)}")
            
            # Retry logic
            if retry_count < MAX_RETRIES:
                logger.info(f"Retrying {model_config['name']} (attempt {retry_count + 1}/{MAX_RETRIES})")
                time.sleep(RETRY_DELAY)
                return self.replay_prompt_on_model(prompt, model_config, retry_count + 1)
            
            return CompletionResult(
                model_name=model_config["name"],
                provider=model_config["model"].split("/")[0].replace("@", ""),  # Extract from @provider/model
                response="",
                tokens_input=0,
                tokens_output=0,
                latency_ms=0,
                cost=0,
                success=False,
                error=str(e)
            )
    
    def replay_prompt_across_models(self, prompt: PromptData) -> List[CompletionResult]:
        """
        Replay a prompt across all configured models
        Returns list of CompletionResult objects
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Replaying prompt: {prompt.id}")
        logger.info(f"{'='*60}")
        
        results = []
        
        for model_config in self.models:
            result = self.replay_prompt_on_model(prompt, model_config)
            results.append(result)
        
        successful_results = [r for r in results if r.success]
        logger.info(f"\nCompleted: {len(successful_results)}/{len(results)} models succeeded")
        
        return results
    
    def replay_batch(self, prompts: List[PromptData]) -> Dict[str, List[CompletionResult]]:
        """
        Replay a batch of prompts across all models
        Returns dict mapping prompt_id to list of results
        """
        all_results = {}
        
        for i, prompt in enumerate(prompts, 1):
            logger.info(f"\n[{i}/{len(prompts)}] Processing prompt {prompt.id}")
            results = self.replay_prompt_across_models(prompt)
            all_results[prompt.id] = results
        
        return all_results
