import logging
from typing import List, Dict, Any
from app.skills.ship30.schema import Ship30Outline, SectionOutline, Ship30SectionDraft, Ship30EssayDraft
from app.skills.ship30.formatting import count_words

logger = logging.getLogger(__name__)


class Ship30Drafter:
    def __init__(self, llm_factory):
        self.llm_factory = llm_factory

    async def draft_section(
        self,
        outline: Ship30Outline,
        section: SectionOutline,
        context_chunks: List[Dict[str, Any]]
    ) -> Ship30SectionDraft:
        """Pass 2: Expands a single section outline into a complete ~300-word draft with citations."""
        relevant_context = "\n".join([
            f"[{c.get('guest_name', 'Transcript')}]: {c.get('content', '')}"
            for c in context_chunks
        ])

        system_prompt = (
            "You are an expert ghostwriter drafting long-form essays in the Ship 30 for 30 style. "
            "Your goal is to write a detailed, highly specific, 300-word essay section. "
            "Write in crisp, direct language. Include concrete examples and quote transcript evidence."
        )

        user_prompt = f"""
Topic: {outline.topic}
Section Title: {section.title}
Key Strategic Takeaway: {section.key_takeaway}
Target Word Count: 300 words

Context from Lenny's Podcast Transcripts:
{relevant_context}

Instructions:
1. Write EXACTLY ~300 words for this section.
2. Integrate citations explicitly like [Guest Name, Episode Citation].
3. Maintain high density of practical insight. No fluff.

Draft Section Content:
"""
        draft_text = await self.llm_factory.generate(
            system_prompt=system_prompt,
            prompt=user_prompt,
            temperature=0.4
        )

        w_count = count_words(draft_text)

        return Ship30SectionDraft(
            section_index=section.section_index,
            title=section.title,
            raw_text=draft_text.strip(),
            word_count=w_count,
            citations_included=section.transcript_citations
        )

    async def draft_full_essay(
        self,
        outline: Ship30Outline,
        context_chunks: List[Dict[str, Any]]
    ) -> Ship30EssayDraft:
        """Drafts all sections sequentially to preserve narrative flow."""
        section_drafts = []
        for sec in outline.sections:
            draft = await self.draft_section(outline, sec, context_chunks)
            section_drafts.append(draft)

        hook_text = (
            f"{outline.hook_attention}\n\n"
            f"{outline.hook_agitate}\n\n"
            f"{outline.hook_articulate}\n\n"
            f"**Actionable Solution:** {outline.hook_action}"
        )

        conclusion_framework = await self._draft_conclusion_framework(outline, context_chunks)
        total_words = count_words(hook_text) + sum(d.word_count for d in section_drafts) + count_words(conclusion_framework)

        return Ship30EssayDraft(
            topic=outline.topic,
            hook_text=hook_text,
            sections=section_drafts,
            conclusion_framework=conclusion_framework,
            total_word_count=total_words
        )

    async def _draft_conclusion_framework(self, outline: Ship30Outline, context_chunks: List[Dict[str, Any]]) -> str:
        prompt = f"""
Summarize the essay topic '{outline.topic}' into an actionable 5-step operational framework matrix.
Use clear bullet points, **bold terms**, and actionable advice. Target ~150 words.
"""
        return await self.llm_factory.generate(
            system_prompt="You produce sharp executive execution frameworks.",
            prompt=prompt,
            temperature=0.3
        )
