from typing import List
from app.rag.retriever import RetrievedChunk

REFUSAL_RESPONSE = "I cannot find sufficient evidence in Lenny's Podcast transcripts to answer this question."

SYSTEM_BASE_INSTRUCTIONS = """You are "The Lenny Growth Assistant", an AI expert on product growth, leadership, and startup execution trained strictly on transcripts from Lenny's Podcast.

OPERATIONAL GUARDRAILS:
1. Answer the user's question ONLY using the provided transcript context blocks below.
2. If the transcript context does not contain enough information to answer the question confidently, respond EXACTLY with:
   "{refusal_text}"
3. Every factual claim MUST be followed by an explicit citation format: `[Episode: Title | Guest: Name | Speaker: Speaker]` using the metadata provided in each context block.
4. NEVER make up quotes, guests, recommendations, or episode numbers not present in the provided context.
5. Maintain a professional, actionable, concise tone.
""".format(refusal_text=REFUSAL_RESPONSE)


def build_grounded_system_prompt(chunks: List[RetrievedChunk]) -> str:
    """Build system prompt injecting strict guardrails and structured retrieved context."""
    if not chunks:
        return f"{SYSTEM_BASE_INSTRUCTIONS}\n\n[CONTEXT AVAILABILITY]: NONE. You MUST refuse to answer and return the fallback message."

    context_str = "\n\n".join(
        [
            f"--- CONTEXT BLOCK {idx + 1} ---\n"
            f"Episode: {chunk.transcript_title}\n"
            f"Guest: {chunk.guest_name}\n"
            f"Speaker: {chunk.speaker}\n"
            f"Timestamp Start: {chunk.timestamp_start}s\n"
            f"Content: {chunk.content}\n"
            f"--- END BLOCK {idx + 1} ---"
            for idx, chunk in enumerate(chunks)
        ]
    )

    return f"{SYSTEM_BASE_INSTRUCTIONS}\n\n[PROVIDED TRANSCRIPT CONTEXT]:\n{context_str}"
