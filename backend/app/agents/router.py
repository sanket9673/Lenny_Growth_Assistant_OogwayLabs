import re
import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RouteDecision(BaseModel):
    selected_skill: str = Field(..., description="Target skill: 'ship30' or 'standard_qa'")
    confidence: float = Field(..., description="Routing confidence level from 0.0 to 1.0")
    reasoning: str = Field(..., description="Explanation of why this route was selected")


class SkillRouter:
    """Routes user queries to either standard grounded RAG Q&A or the Ship 30 Content Skill Engine."""

    SHIP30_KEYWORDS: List[str] = [
        "write an essay",
        "ship 30",
        "long-form guide",
        "1250-word framework",
        "1250 word",
        "digital essay",
        "comprehensive playbook",
        "detailed essay",
        "write a deep dive"
    ]

    def __init__(self, llm_factory=None):
        self.llm_factory = llm_factory

    def route_by_keywords(self, query: str, skill_override: Optional[str] = None) -> Optional[RouteDecision]:
        if skill_override and skill_override.lower() == "ship30":
            return RouteDecision(
                selected_skill="ship30",
                confidence=1.0,
                reasoning="Explicit skill override payload flag set to 'ship30'."
            )

        query_lower = query.lower()
        for kw in self.SHIP30_KEYWORDS:
            if kw in query_lower:
                return RouteDecision(
                    selected_skill="ship30",
                    confidence=0.95,
                    reasoning=f"Query matched high-intent keyword pattern: '{kw}'."
                )

        return None

    async def route(self, query: str, skill_override: Optional[str] = None) -> RouteDecision:
        """Determines routing logic based on overrides, regex keyword matching, or LLM fallback classification."""
        fast_decision = self.route_by_keywords(query, skill_override)
        if fast_decision:
            return fast_decision

        if self.llm_factory is None:
            return RouteDecision(
                selected_skill="standard_qa",
                confidence=0.7,
                reasoning="Defaulted to standard Q&A (no LLM classifier available)."
            )

        try:
            system_prompt = "You are an intent classification agent. Route queries to either 'ship30' or 'standard_qa'."
            user_prompt = f"""
Query: "{query}"

Does the user request a long-form structured essay, publication guide, or Ship 30 style framework?
Respond with JSON containing:
{{
    "selected_skill": "ship30" OR "standard_qa",
    "confidence": 0.9,
    "reasoning": "explanation"
}}
"""
            res = await self.llm_factory.generate(
                system_prompt=system_prompt,
                prompt=user_prompt,
                temperature=0.0,
                response_format="json"
            )
            import json
            data = json.loads(res)
            return RouteDecision(**data)
        except Exception as e:
            logger.warning(f"LLM routing classification failed ({e}). Defaulting to standard_qa.")
            return RouteDecision(
                selected_skill="standard_qa",
                confidence=0.6,
                reasoning="Fallback to standard Q&A due to classifier exception."
            )
