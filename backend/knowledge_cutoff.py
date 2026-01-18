"""
Knowledge Cutoff Tracker
Tracks knowledge cutoff dates for each model and automatically suggests best model for recent queries
"""

from datetime import datetime
from typing import Dict, List, Tuple

# Knowledge cutoff dates for each model
KNOWLEDGE_CUTOFFS = {
    "gpt-4o": "2024-04-09",
    "gpt-4-turbo": "2024-04-09", 
    "gpt-3.5-turbo": "2023-04-09",
    "claude-3-5-sonnet": "2024-06-01",
    "claude-3-opus": "2024-02-29",
    "llama-2-70b": "2023-07-01",
    "mistral-7b": "2023-12-01",
    "command-r": "2024-03-01",
    "palm-2": "2023-12-01",
}

# Model recency ranking (for fallback selection)
MODEL_RECENCY_RANK = {
    "gpt-4o": 1,
    "gpt-4-turbo": 2,
    "claude-3-5-sonnet": 3,
    "claude-3-opus": 4,
    "command-r": 5,
    "mistral-7b": 6,
    "llama-2-70b": 7,
    "gpt-3.5-turbo": 8,
    "palm-2": 9,
}

class KnowledgeCutoffTracker:
    """Tracks and manages model knowledge cutoffs"""
    
    def __init__(self):
        self.cutoffs = KNOWLEDGE_CUTOFFS
        self.recency_rank = MODEL_RECENCY_RANK
    
    def get_cutoff_date(self, model_name: str) -> str:
        """Get knowledge cutoff date for a model"""
        normalized = self._normalize_model_name(model_name)
        return self.cutoffs.get(normalized, "2023-01-01")
    
    def _normalize_model_name(self, model_name: str) -> str:
        """Normalize model name to standard format"""
        model_name = model_name.lower().strip()
        
        # Handle common variations
        if "gpt-4o-mini" in model_name or "gpt4o-mini" in model_name:
            return "gpt-4o"
        if "gpt-4o" in model_name or "gpt4o" in model_name:
            return "gpt-4o"
        if "gpt-4" in model_name or "gpt4" in model_name:
            return "gpt-4-turbo"
        if "gpt-3.5" in model_name or "gpt35" in model_name:
            return "gpt-3.5-turbo"
        if "claude-3.5" in model_name or "claude-35" in model_name or "sonnet" in model_name:
            return "claude-3-5-sonnet"
        if "claude-3" in model_name or "claude3" in model_name:
            return "claude-3-opus"
        if "llama" in model_name:
            return "llama-2-70b"
        if "mistral" in model_name:
            return "mistral-7b"
        if "command" in model_name:
            return "command-r"
        if "palm" in model_name or "palm2" in model_name:
            return "palm-2"
        
        return model_name
    
    def is_outdated_for_question(self, model_name: str, question_date: datetime) -> Tuple[bool, str]:
        """
        Check if model's knowledge cutoff is before the question date
        Returns: (is_outdated, reason)
        """
        cutoff_str = self.get_cutoff_date(model_name)
        cutoff_date = datetime.strptime(cutoff_str, "%Y-%m-%d")
        
        if question_date > cutoff_date:
            days_outdated = (question_date - cutoff_date).days
            return True, f"Knowledge cutoff {cutoff_str}, question about {question_date.strftime('%Y-%m-%d')} ({days_outdated} days newer)"
        
        return False, ""
    
    def detect_question_date(self, question: str) -> datetime:
        """
        Try to detect if question is about recent events
        Returns datetime of implied question (defaults to current date if recent terms found)
        """
        question_lower = question.lower()
        
        # Keywords indicating recent/current questions
        recent_keywords = [
            "today", "yesterday", "current", "latest", "recent", "now", "just",
            "2025", "2026", "january", "february", "march", "april", "may", 
            "june", "july", "august", "september", "october", "november", "december",
            "this week", "this month", "this year", "this morning"
        ]
        
        for keyword in recent_keywords:
            if keyword in question_lower:
                return datetime.now()
        
        # Check for specific years
        import re
        year_match = re.search(r'\b(20\d{2})\b', question)
        if year_match:
            year = int(year_match.group(1))
            if year >= 2024:
                return datetime(year, 1, 1)
        
        # Default: assume question is about current time
        return datetime.now()
    
    def get_best_model_for_question(self, question: str, available_models: List[str]) -> str:
        """
        Get the best model for answering a question based on knowledge cutoff
        Returns the model name with most recent knowledge cutoff
        """
        question_date = self.detect_question_date(question)
        
        # Sort models by recency rank
        sorted_models = sorted(
            available_models,
            key=lambda m: self.recency_rank.get(self._normalize_model_name(m), 999)
        )
        
        # Find first model with knowledge cutoff after question date
        for model in sorted_models:
            is_outdated, _ = self.is_outdated_for_question(model, question_date)
            if not is_outdated:
                return model
        
        # If all models are outdated, return most recent one
        return sorted_models[0] if sorted_models else "gpt-4o"
    
    def get_fallback_model(self, primary_model: str, available_models: List[str]) -> str:
        """
        Get fallback model if primary model fails
        Returns the next most recent model
        """
        normalized_primary = self._normalize_model_name(primary_model)
        primary_rank = self.recency_rank.get(normalized_primary, 999)
        
        # Find next best model (higher rank = less recent)
        candidates = [
            m for m in available_models 
            if self.recency_rank.get(self._normalize_model_name(m), 999) > primary_rank
        ]
        
        if candidates:
            return min(candidates, key=lambda m: self.recency_rank.get(self._normalize_model_name(m), 999))
        
        return primary_model
    
    def should_use_fallback(self, response: str, model_name: str) -> Tuple[bool, str]:
        """
        Determine if we should use a fallback model based on response quality
        Returns: (should_fallback, reason)
        """
        response_lower = response.lower()
        
        # Indicators that model couldn't answer
        no_answer_indicators = [
            "i don't have information",
            "my knowledge cutoff",
            "i'm not aware",
            "i don't know",
            "unable to provide",
            "beyond my knowledge",
            "outside my training data",
            "cannot answer",
            "no information about",
            "after my training data",
        ]
        
        for indicator in no_answer_indicators:
            if indicator in response_lower:
                return True, f"Model indicated knowledge limitation: {indicator}"
        
        # If response is too short and vague
        if len(response) < 100 and any(word in response_lower for word in ["unclear", "vague", "uncertain"]):
            return True, "Response too vague or uncertain"
        
        return False, ""
    
    def format_fallback_note(self, primary_model: str, fallback_model: str, reason: str) -> str:
        """Format a note explaining the fallback"""
        return f"Note: {primary_model} indicated knowledge limitation. Using {fallback_model} response instead. Reason: {reason}"
    
    def get_model_info(self, model_name: str) -> Dict:
        """Get information about a model's knowledge cutoff"""
        normalized = self._normalize_model_name(model_name)
        cutoff = self.cutoffs.get(normalized, "Unknown")
        rank = self.recency_rank.get(normalized, "Unknown")
        
        return {
            "original_name": model_name,
            "normalized_name": normalized,
            "knowledge_cutoff": cutoff,
            "recency_rank": rank,
            "is_most_recent": rank == 1,
        }


# Global instance
knowledge_tracker = KnowledgeCutoffTracker()
