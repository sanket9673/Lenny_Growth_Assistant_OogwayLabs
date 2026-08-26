class StrictRefusalException(Exception):
    """Exception raised when an unsupported out-of-domain query is encountered."""
    pass


def verify_grounding_score(chunks, generated_text):
    """
    Verifies that the generated LLM text is correctly grounded in retrieved chunks
    and parses citations format.
    """
    citations = []
    
    # Check each retrieved chunk in the generated text (either by title or guest)
    for chunk in chunks:
        guest = chunk.get("guest") or chunk.get("guest_name") or ""
        title = chunk.get("title") or chunk.get("transcript_title") or ""
        
        # Check if the guest or title name is referenced in citation formatting [Guest - Title]
        citation_reference = f"{guest} - {title}"
        if guest in generated_text or title in generated_text or citation_reference in generated_text:
            citations.append(chunk)
            
    return {
        "grounded": len(citations) > 0,
        "citations": citations
    }
