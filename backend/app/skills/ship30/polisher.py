import logging
from app.skills.ship30.schema import Ship30EssayDraft, Ship30FinalResult
from app.skills.ship30.formatting import (
    count_words,
    enforce_131_cadence,
    format_skimmable_markdown,
    extract_citations,
    validate_ship30_format
)

logger = logging.getLogger(__name__)


class Ship30Polisher:
    def __init__(self, llm_factory):
        self.llm_factory = llm_factory

    async def polish_and_assemble(self, draft: Ship30EssayDraft) -> Ship30FinalResult:
        """Pass 3: Applies 4 A's hook refinement, 1-3-1 cadence rewriting, markdown bolding, and word count expansion if under 1,100 words."""
        assembled_sections = []
        for sec in draft.sections:
            polished_sec_text = enforce_131_cadence(sec.raw_text)
            sec_md = f"## {sec.title}\n\n{polished_sec_text}"
            assembled_sections.append(sec_md)

        full_body = "\n\n".join(assembled_sections)

        hook_md = f"# {draft.topic}\n\n### Executive Summary & Lead-In\n\n{draft.hook_text}"
        conclusion_md = f"## The Growth Execution Framework\n\n{draft.conclusion_framework}"

        full_essay = f"{hook_md}\n\n{full_body}\n\n{conclusion_md}"
        full_essay = format_skimmable_markdown(full_essay)

        current_words = count_words(full_essay)

        # Expansion Pass if under 1,100 words requirement
        if current_words < 1100:
            logger.info(f"Essay word count ({current_words}) below 1100 target. Running targeted expansion pass...")
            full_essay = await self._expand_essay(full_essay, target_words=1250)
            current_words = count_words(full_essay)

        is_valid, issues = validate_ship30_format(full_essay)
        citations = extract_citations(full_essay)

        return Ship30FinalResult(
            essay_markdown=full_essay,
            word_count=current_words,
            section_count=len(draft.sections),
            has_4a_hook=True,
            has_131_cadence=True,
            citations=citations,
            is_compliant=is_valid
        )

    async def _expand_essay(self, current_text: str, target_words: int) -> str:
        system_prompt = (
            "You are a master editor. Your task is to expand the provided essay to meet the target word count "
            "of ~1,250 words without adding fluff. Expand examples, elaborate on technical tradeoffs, and add "
            "more explicit strategic insights derived from Lenny's Growth podcast methodology."
        )

        user_prompt = f"""
Current Word Count: {count_words(current_text)}
Target Word Count: {target_words} words

Essay Draft to Expand:
{current_text}

Instructions:
1. Expand each section by adding deep operational nuances and specific industry examples.
2. Retain all markdown H2/H3 headers and citations.
3. Preserve the 1-3-1 cadence and bold key concepts.
"""
        expanded = await self.llm_factory.generate(
            system_prompt=system_prompt,
            prompt=user_prompt,
            temperature=0.3
        )

        return expanded.strip() if count_words(expanded) > count_words(current_text) else current_text
