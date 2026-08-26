# Design System & UI/UX Principles

## 1. Design Aesthetics & Visual Identity
"The Lenny Growth Assistant" adopts a minimalist, high-density, YC-startup aesthetic built for deep focus and productivity.
- **Primary Color:** `#FF6600` (Warm Orange)
- **Background Slate:** `#0F172A` (Dark Slate Gray)
- **Surface Elevation:** `#1E293B` (Elevated Panel Dark)
- **Typography Scale:** Inter / System UI Font Stack (`12px` caption, `14px` body, `18px` subheader, `24px` section header).

## 2. Information Architecture & Split-Pane Layout
The UI utilizes a dual-pane responsive layout:
- **Left Pane (40% width / collapsible):** Conversational RAG interface with persistent session history, streaming response text, and structured citation chips.
- **Right Pane (60% width):** Dynamic Artifact Canvas displaying rendered HTML/Markdown preview, code view, export controls (Copy, Download HTML).

## 3. Streaming Token UX & Interaction States
- **Token Streaming:** Uses Server-Sent Events (SSE) for zero-latency response generation.
- **Loading Skeleton:** Displays custom pulse animations while RAG vector similarity retrieval executes.
- **Citation Chips:** Clicking a transcript citation chip triggers an inline side-drawer preview displaying raw source transcript text with matching timestamps.

## 4. Accessibility & ARIA Compliance
- Full keyboard navigation support (Tab indexing across chat input and artifact actions).
- Minimum WCAG AA contrast ratio ($> 4.5:1$) across dark surface text.
- Standard ARIA labels (`aria-live="polite"` for streaming chat responses, `role="region"` for code previews).
