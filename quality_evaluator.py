"""
AI-Powered Quality Evaluator - Uses LLM-as-judge for quality assessment
"""
import json
import logging
from typing import Dict, List
from portkey_ai import Portkey
from models import CompletionResult, QualityScore, PromptData
from config import (
    PORTKEY_API_KEY,
    QUALITY_JUDGE_MODEL,
    QUALITY_JUDGE_PROVIDER,
    EVALUATION_CRITERIA
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QualityEvaluator:
    """Uses LLM-as-judge to evaluate completion quality"""
    
    def __init__(self, api_key: str = PORTKEY_API_KEY):
        self.client = Portkey(
            api_key=api_key
        )
        self.judge_model = "@openai/gpt-4o-mini"  # Model Catalog format
        self.criteria = EVALUATION_CRITERIA
    
    def _build_evaluation_prompt(
        self, 
        original_prompt: PromptData, 
        completion: CompletionResult
    ) -> str:
        """Build the prompt for the LLM judge"""
        
        # Extract user query from messages
        user_query = ""
        for msg in original_prompt.messages:
            if msg["role"] == "user":
                user_query = msg["content"]
                break
        
        criteria_text = "\n".join([
            f"- {name}: {description}" 
            for name, description in self.criteria.items()
        ])
        
        prompt = f"""You are an expert AI evaluator. Evaluate the quality of the following AI response.

USER QUERY:
{user_query}

AI RESPONSE (from {completion.model_name}):
{completion.response}

EVALUATION CRITERIA:
{criteria_text}

Please evaluate this response and provide:
1. Individual scores (0-100) for each criterion
2. An overall quality score (0-100)
3. Brief reasoning for your scores
4. Your confidence level (0-1) in this evaluation

Respond ONLY with a valid JSON object in this exact format:
{{
    "dimension_scores": {{
        "accuracy": <score>,
        "helpfulness": <score>,
        "clarity": <score>,
        "completeness": <score>
    }},
    "overall_score": <score>,
    "reasoning": "<brief explanation>",
    "confidence": <0-1>
}}"""
        
        return prompt
    
    def evaluate(
        self, 
        prompt: PromptData, 
        completion: CompletionResult
    ) -> QualityScore:
        """
        Evaluate the quality of a completion using LLM-as-judge
        """
        if not completion.success:
            return QualityScore(
                overall_score=0.0,
                dimension_scores={k: 0.0 for k in self.criteria.keys()},
                reasoning="Model failed to generate completion",
                confidence=1.0,
                evaluator_model=self.judge_model
            )
        
        try:
            evaluation_prompt = self._build_evaluation_prompt(prompt, completion)
            
            response = self.client.chat.completions.create(
                model=self.judge_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert AI response evaluator. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": evaluation_prompt
                    }
                ],
                temperature=0.2  # Lower temperature for more consistent evaluations
            )
            
            result_text = response.choices[0].message.content
            
            # Parse JSON response
            # Handle markdown code blocks if present
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(result_text)
            
            logger.info(f"  Quality: {result['overall_score']:.1f}/100 (confidence: {result['confidence']:.2f})")
            
            return QualityScore(
                overall_score=result["overall_score"],
                dimension_scores=result["dimension_scores"],
                reasoning=result["reasoning"],
                confidence=result["confidence"],
                evaluator_model=self.judge_model
            )
            
        except Exception as e:
            logger.error(f"Evaluation failed for {completion.model_name}: {str(e)}")
            return QualityScore(
                overall_score=50.0,  # Default uncertain score
                dimension_scores={k: 50.0 for k in self.criteria.keys()},
                reasoning=f"Evaluation failed: {str(e)}",
                confidence=0.1,  # Low confidence
                evaluator_model=self.judge_model
            )
    
    def evaluate_batch(
        self, 
        prompt: PromptData, 
        completions: List[CompletionResult]
    ) -> Dict[str, QualityScore]:
        """
        Evaluate multiple completions for a single prompt
        Returns dict mapping model_name to QualityScore
        """
        logger.info(f"\nEvaluating {len(completions)} completions...")
        
        scores = {}
        for completion in completions:
            score = self.evaluate(prompt, completion)
            scores[completion.model_name] = score
        
        return scores
