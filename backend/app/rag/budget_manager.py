import logging
from typing import List
import tiktoken
from app.llm.base import ChatMessage
from app.db.models import Message

logger = logging.getLogger(__name__)

class ContextBudgetManager:
    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.tokenizer = None

    def estimate_tokens(self, text: str) -> int:
        if not text:
            return 0
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        return max(1, len(text) // 4)

    def truncate_history(
        self,
        system_prompt: str,
        history: List[Message],
        current_user_message: str
    ) -> List[ChatMessage]:
        """
        Truncate older messages from the history list to stay under the budget (max_tokens).
        Returns a list of ChatMessage, starting with the system prompt, then the remaining history,
        and finally the current user message.
        """
        system_msg = ChatMessage(role="system", content=system_prompt)
        current_msg = ChatMessage(role="user", content=current_user_message)

        sys_tokens = self.estimate_tokens(system_msg.content) + 4
        curr_tokens = self.estimate_tokens(current_msg.content) + 4
        base_tokens = sys_tokens + curr_tokens

        if base_tokens > self.max_tokens:
            logger.warning("System prompt and current message exceed token budget. Returning only system and current user message.")
            return [system_msg, current_msg]

        budget_left = self.max_tokens - base_tokens
        retained_history: List[ChatMessage] = []

        skipped_current = False
        for db_msg in reversed(history):
            if not skipped_current and db_msg.role == "user" and db_msg.content == current_user_message:
                skipped_current = True
                continue

            msg_tokens = self.estimate_tokens(db_msg.content) + 4
            if budget_left >= msg_tokens:
                retained_history.insert(0, ChatMessage(role=db_msg.role, content=db_msg.content))
                budget_left -= msg_tokens
            else:
                break

        return [system_msg] + retained_history + [current_msg]
