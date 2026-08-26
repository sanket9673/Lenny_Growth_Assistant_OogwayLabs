import json
import logging
from typing import List, Dict, Any
from app.skills.ship30.schema import Ship30Outline, SectionOutline

logger = logging.getLogger(__name__)


class Ship30Planner:
    def __init__(self, llm_factory):
        self.llm_factory = llm_factory

    async def generate_outline(self, query: str, context_chunks: List[Dict[str, Any]]) -> Ship30Outline:
        """Pass 1: Converts query and retrieved context into a structured 4-section outline targeting ~1250 words."""
        context_text = "\n\n".join([
            f"--- Transcript Excerpt ({c.get('guest_name', 'Unknown')}) ---\n{c.get('content', '')}"
            for c in context_chunks
        ])

        system_prompt = (
            "You are a Master Content Architect specializing in Ship 30 for 30 essay frameworks. "
            "Your job is to structure a 1,250-word deep-dive digital essay based on Lenny's Podcast transcripts. "
            "You MUST output valid JSON only, matching the requested schema."
        )

        user_prompt = f"""
User Query: {query}

Retrieved Transcript Context:
{context_text}

Generate a detailed 4-section outline for a 1,250-word essay.
Target 300 words per section.
Map exact guest names and quotes from the transcript context to each section.

Required JSON Structure:
{{
    "topic": "Essay Topic",
    "target_audience": "Growth PMs & Product Leaders",
    "core_thesis": "Central thesis statement",
    "hook_attention": "Attention grabbing line",
    "hook_agitate": "Agitation of pain point",
    "hook_articulate": "Articulation of underlying problem",
    "hook_action": "Actionable solution promised",
    "sections": [
        {{
            "section_index": 1,
            "title": "H2 Title for Section 1",
            "key_takeaway": "Key strategy covered",
            "transcript_citations": ["Guest Name Citation"],
            "target_word_count": 300
        }},
        ... (generate exactly 4 sections)
    ],
    "total_target_words": 1250
}}
"""
        response_text = await self.llm_factory.generate(
            system_prompt=system_prompt,
            prompt=user_prompt,
            temperature=0.2,
            response_format="json"
        )

        try:
            data = json.loads(response_text)
            return Ship30Outline(**data)
        except Exception as e:
            logger.error(f"Failed to parse planner output, falling back to schema default: {e}")
            return self._build_fallback_outline(query, context_chunks)

    def _build_fallback_outline(self, query: str, context_chunks: List[Dict[str, Any]]) -> Ship30Outline:
        citations = [c.get("guest_name", "Lenny's Guest") for c in context_chunks[:4]]
        if not citations:
            citations = ["Lenny's Podcast Transcript"]

        return Ship30Outline(
            topic=query,
            target_audience="Product Managers & Growth Leaders",
            core_thesis=f"Mastering {query} requires structured operational execution.",
            hook_attention=f"Most product teams struggle with {query} without knowing why.",
            hook_agitate="They waste months pursuing vague playbooks with zero leverage.",
            hook_articulate="The core issue is lack of structured, evidence-based systems.",
            hook_action="Here is the proven framework derived directly from world-class product leaders.",
            sections=[
                SectionOutline(
                    section_index=1,
                    title="1. The Diagnostic Framework",
                    key_takeaway="Identify root bottlenecks before executing solution sets.",
                    transcript_citations=[citations[0]],
                    target_word_count=300
                ),
                SectionOutline(
                    section_index=2,
                    title="2. Strategic Execution & Alignment",
                    key_takeaway="Align cross-functional execution against leverage metrics.",
                    transcript_citations=[citations[min(1, len(citations)-1)]],
                    target_word_count=300
                ),
                SectionOutline(
                    section_index=3,
                    title="3. Tactical Scaling Playbook",
                    key_takeaway="Scale operational cadences without losing product quality.",
                    transcript_citations=[citations[min(2, len(citations)-1)]],
                    target_word_count=300
                ),
                SectionOutline(
                    section_index=4,
                    title="4. Measurement & Continuous Optimization",
                    key_takeaway="Establish feedback loops to compound strategic gains.",
                    transcript_citations=[citations[min(3, len(citations)-1)]],
                    target_word_count=300
                )
            ],
            total_target_words=1250
        )
