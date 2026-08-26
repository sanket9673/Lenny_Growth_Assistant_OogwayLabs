import logging
from typing import List, Optional, Tuple
import tiktoken

from app.llm.base import ChatMessage

logger = logging.getLogger(__name__)

# Model Context Limits Budget Matrix
MODEL_CONTEXT_LIMITS = {
    "llama-3.3-70b-versatile": 128000,
    "llama-3.1-8b-instant": 128000,
    "mixtral-8x7b-32768": 32768,
    "claude-3-5-sonnet-20241022": 200000,
    "claude-3-haiku-20240307": 200000,
    "llama3.2": 4096,
    "qwen2.5": 8192,
    "default": 8192,
}

class ContextBudgetManager:
    """Manages context window budgets and truncates messages intelligently."""

    def __init__(self):
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.tokenizer = None

    def estimate_tokens(self, text: str) -> int:
        """Estimates token count using tiktoken if available, falling back to 4 chars per token rule."""
        if not text:
            return 0
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        return max(1, len(text) // 4)

    def calculate_messages_tokens(self, messages: List[ChatMessage], system_prompt: Optional[str] = None) -> int:
        total = self.estimate_tokens(system_prompt or "")
        for m in messages:
            total += 4  # Formatting overhead per message
            total += self.estimate_tokens(m.content)
        return total

    def truncate_messages(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        model_name: str = "llama-3.3-70b-versatile",
        reserved_completion_tokens: int = 2048,
    ) -> Tuple[List[ChatMessage], int]:
        """
        Dynamically trims oldest middle conversation history while strictly preserving:
        1. System prompt
        2. The most recent User query / message.
        """
        max_context = MODEL_CONTEXT_LIMITS.get(model_name, MODEL_CONTEXT_LIMITS["default"])
        budget = max_context - reserved_completion_tokens

        if not messages:
            return [], self.estimate_tokens(system_prompt or "")

        total_tokens = self.calculate_messages_tokens(messages, system_prompt)

        if total_tokens <= budget:
            return messages, total_tokens

        logger.warning(
            f"Context tokens ({total_tokens}) exceed budget ({budget}) for model '{model_name}'. Truncating message history..."
        )

        system_tokens = self.estimate_tokens(system_prompt or "")
        recent_user_msg = messages[-1]
        recent_user_tokens = self.estimate_tokens(recent_user_msg.content) + 4

        current_cost = system_tokens + recent_user_tokens
        if current_cost > budget:
            logger.error("System prompt + latest user prompt alone exceed context limit!")
            return [recent_user_msg], current_cost

        # Keep history from most recent backwards
        trimmed_history: List[ChatMessage] = [recent_user_msg]
        remaining_budget = budget - current_cost

        for msg in reversed(messages[:-1]):
            msg_tokens = self.estimate_tokens(msg.content) + 4
            if remaining_budget - msg_tokens >= 0:
                trimmed_history.insert(0, msg)
                remaining_budget -= msg_tokens
            else:
                break

        final_tokens = self.calculate_messages_tokens(trimmed_history, system_prompt)
        logger.info(f"Successfully truncated context from {len(messages)} to {len(trimmed_history)} messages ({final_tokens} tokens).")
        return trimmed_history, final_tokens
