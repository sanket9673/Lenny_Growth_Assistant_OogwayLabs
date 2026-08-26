# Agent Log 03: HTML Artifact Rendering & Security Sandboxing

## Objective
Implement dual-layer security model for rendering untrusted LLM-generated HTML artifact documents without exposing client sessions to XSS vector attacks.

## Iteration Log & Decisions
- **Challenge:** Native rendering of raw generated HTML exposed potential XSS vulnerabilities (e.g., `<script>` execution or `onload` image vector injections).
- **Resolution:**
  - Integrated server-side sanitization using `DOMPurify` rules to scrub inline execution handlers and script tags before persistence.
  - Implemented an isolated HTML preview iframe with strict CSP header: `sandbox="allow-scripts"`. Explicitly omitted `allow-same-origin` to ensure sandboxed iframe cannot read host `localStorage` or session cookies.

## Output
Security unit test suite (`test_security_sanitization.py`) passes 100% of malicious execution payload test vectors.
