# Agent Log 01: Architecture & Vector Retrieval Engine Setup

## Objective
Design and implement high-precision vector chunking, retrieval distance thresholds, and strict refusal logic for out-of-domain queries.

## Iteration Log & Decisions
- **Challenge:** Initial cosine similarity threshold ($0.60$) allowed out-of-domain questions (e.g., astrophysics topics) to retrieve weak transcript matches and hallucinate.
- **Resolution:** Updated distance formula to use exact cosine distance in `pgvector` (`vector_cosine_ops`) with a strict cutoff filter at similarity $\ge 0.75$.
- **Refusal System:** Implemented custom `StrictRefusalException` when zero chunks satisfy the threshold, returning an explicit refusal message to the user rather than hallucinating.

## Output
Retesting verified that out-of-domain questions are rejected with $100\%$ precision while valid growth strategy queries return accurate citations.
