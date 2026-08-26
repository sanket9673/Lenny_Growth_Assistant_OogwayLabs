import logging
from typing import List, Dict, Any, Optional, Callable, AsyncGenerator
from app.skills.ship30.planner import Ship30Planner
from app.skills.ship30.drafter import Ship30Drafter
from app.skills.ship30.polisher import Ship30Polisher
from app.skills.ship30.schema import Ship30FinalResult

logger = logging.getLogger(__name__)


class Ship30SkillEngine:
    def __init__(self, llm_factory):
        self.llm_factory = llm_factory
        self.planner = Ship30Planner(llm_factory)
        self.drafter = Ship30Drafter(llm_factory)
        self.polisher = Ship30Polisher(llm_factory)

    async def run(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ) -> Ship30FinalResult:
        """Executes the complete 3-pass Ship 30 essay generation pipeline."""
        # Pass 1: Planning
        if progress_callback:
            await progress_callback("skill_progress", {"phase": "planning_outline", "message": "Generating 4-section outline..."})

        outline = await self.planner.generate_outline(query, context_chunks)

        # Pass 2: Drafting
        if progress_callback:
            await progress_callback("skill_progress", {"phase": "drafting_sections", "total_sections": len(outline.sections)})

        essay_draft = await self.drafter.draft_full_essay(outline, context_chunks)

        # Pass 3: Polish & Cadence Formatting
        if progress_callback:
            await progress_callback("skill_progress", {"phase": "polishing_format", "message": "Enforcing 1-3-1 cadence and 4 A's hook..."})

        final_result = await self.polisher.polish_and_assemble(essay_draft)
        return final_result

    async def run_stream(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Runs pipeline and yields SSE-compatible event dictionaries."""
        yield {
            "event": "skill_start",
            "data": {"skill": "ship30_essay", "status": "planning_outline"}
        }

        # Step 1: Planning
        outline = await self.planner.generate_outline(query, context_chunks)
        yield {
            "event": "skill_progress",
            "data": {"phase": "drafting_sections", "current_section": 1, "total_sections": len(outline.sections)}
        }

        # Step 2: Drafting
        essay_draft = await self.drafter.draft_full_essay(outline, context_chunks)
        yield {
            "event": "skill_progress",
            "data": {"phase": "polishing_format", "status": "applying_131_cadence"}
        }

        # Step 3: Polish
        final_result = await self.polisher.polish_and_assemble(essay_draft)

        # Stream text in word chunks to simulate fluid SSE token streaming
        words = final_result.essay_markdown.split(" ")
        chunk_size = 5
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size]) + " "
            yield {
                "event": "token",
                "data": {"text": chunk}
            }

        yield {
            "event": "done",
            "data": {
                "word_count": final_result.word_count,
                "citations": final_result.citations,
                "is_compliant": final_result.is_compliant
            }
        }
