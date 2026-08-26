import pytest
from app.rag.retrieval import retrieve_relevant_chunks, perform_grounded_search
from app.rag.grounding import StrictRefusalException, verify_grounding_score

def test_similarity_distance_filtering(db_session):
    # Query for out-of-domain knowledge
    results = retrieve_relevant_chunks(
        query="What is the orbital velocity of Jupiter in kilometers per second?",
        db=db_session,
        similarity_threshold=0.75
    )
    # Must return zero chunks due to low cosine similarity distance threshold
    assert len(results) == 0

def test_strict_refusal_on_unsupported_query(db_session):
    with pytest.raises(StrictRefusalException) as exc_info:
        perform_grounded_search(
            query="How do I configure Kubernetes ingress controllers for AWS EKS?",
            db=db_session
        )
    assert "refuse" in str(exc_info.value).lower() or "not contained" in str(exc_info.value).lower()

def test_citation_generation_formatting():
    chunks = [
        {"id": "chunk_01", "guest": "Shreyas Doshi", "title": "LNO Framework", "content": "Task categorization strategy."}
    ]
    formatted_citations = verify_grounding_score(chunks=chunks, generated_text="According to [Shreyas Doshi - LNO Framework]...")
    assert formatted_citations["grounded"] is True
    assert len(formatted_citations["citations"]) == 1
