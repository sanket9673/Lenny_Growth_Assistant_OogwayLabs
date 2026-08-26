# Product Requirements Document (PRD): The Lenny Growth Assistant

## 1. Executive Summary & Problem Brief
"The Lenny Growth Assistant" is an AI-powered conversational search and artifact creation tool built on top of Lenny Rachitsky's podcast transcript corpus. Product managers and founders often struggle to extract precise, actionable frameworks from hundreds of hours of interviews. This system provides strict vector-grounded answers with verifiable citations and auto-generates structured artifacts (e.g., Ship 30 for 30 essays, PRDs, frameworks).

## 2. Target Persona & User Stories
- **Primary Persona:** Early-stage Founder & Lead Product Manager.
- **User Story 1:** As a PM, I want to query growth tactics from industry guests (e.g., Elena Verna, Shreyas Doshi) so that I get factual, un-hallucinated advice backed by direct transcript quotes.
- **User Story 2:** As a founder, I want to convert transcript insights into structured 1,250-word Ship 30 essays with a click, so I can publish high-quality leadership content.

## 3. Success Metrics & Quality Targets

| Metric | Target | Measurement Strategy |
| :--- | :--- | :--- |
| **Fact Grounding Rate** | $\ge 98\%$ | Automated cosine distance filtering and citation claim verification |
| **Refusal Accuracy** | $100\%$ | Out-of-domain questions correctly rejected without hallucination |
| **Artifact Generation Time** | $< 12\text{s}$ | End-to-end multi-pass generation pipeline latency |
| **XSS Vulnerability Rate** | $0\%$ | Automated DOMPurify sanitization & sandboxed execution verification |

## 4. System Assumptions & Scope Boundaries

### In Scope
- Vector retrieval over postgres + `pgvector` index.
- LLM Provider Abstraction supporting Anthropic, Groq, and local Ollama (`llama3.2`).
- Dual-layer secure artifact sandbox execution.

### Out of Scope
- Direct voice audio ingestion.
- Multi-tenant enterprise RBAC billing models.

## 5. Risk Assessment & Mitigations
- **Risk:** LLM hallucinating guest statements.
  - **Mitigation:** Strict cosine distance thresholding ($< 0.75$ distance cut-off) with automated fallback refusal logic.
- **Risk:** Malicious HTML payload in generated artifact stealing browser storage.
  - **Mitigation:** Server-side XSS stripping + iframe `sandbox="allow-scripts"` (omitting `allow-same-origin`).
