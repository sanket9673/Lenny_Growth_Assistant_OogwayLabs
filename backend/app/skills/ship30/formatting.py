import re
from typing import List, Tuple


def count_words(text: str) -> int:
    """Calculates clean word count excluding markdown formatting symbols."""
    clean_text = re.sub(r"[#*`_\[\]()\-]", " ", text)
    words = [w for w in clean_text.split() if w.strip()]
    return len(words)


def extract_citations(text: str) -> List[str]:
    """Extracts explicit citations formatted as [Guest/Episode Citation]."""
    matches = re.findall(r"\[(.*?)\]", text)
    return [m.strip() for m in matches if m.strip()]


def enforce_131_cadence(text: str) -> str:
    """
    Ensures text paragraphs adhere to the 1-3-1 cadence:
    1 line lead-in, 3 lines narrative/supporting body, 1 line takeaway punchline.
    Re-formats block paragraphs into rhythmically spaced blocks.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    formatted_paragraphs = []

    for p in paragraphs:
        if p.startswith("#") or p.startswith("- ") or p.startswith("* "):
            formatted_paragraphs.append(p)
            continue

        sentences = re.split(r"(?<=[.!?])\s+", p)
        if len(sentences) >= 5:
            lead = sentences[0]
            body = " ".join(sentences[1:4])
            punchline = " ".join(sentences[4:])
            cadence_block = f"{lead}\n\n{body}\n\n**{punchline}**"
            formatted_paragraphs.append(cadence_block)
        elif len(sentences) >= 3:
            lead = sentences[0]
            body = " ".join(sentences[1:-1])
            punchline = sentences[-1]
            cadence_block = f"{lead}\n\n{body}\n\n**{punchline}**"
            formatted_paragraphs.append(cadence_block)
        else:
            formatted_paragraphs.append(p)

    return "\n\n".join(formatted_paragraphs)


def format_skimmable_markdown(text: str) -> str:
    """Ensures proper H2/H3 hierarchy and bolding of core concepts."""
    lines = text.split("\n")
    processed_lines = []

    for line in lines:
        if line.startswith("Section ") or line.startswith("Part "):
            processed_lines.append(f"## {line.lstrip('#').strip()}")
        elif line.startswith("Takeaway:") or line.startswith("Key Framework:"):
            processed_lines.append(f"### {line.lstrip('#').strip()}")
        else:
            processed_lines.append(line)

    return "\n".join(processed_lines)


def validate_ship30_format(text: str) -> Tuple[bool, List[str]]:
    """Validates Ship 30 essay formatting compliance."""
    issues = []
    w_count = count_words(text)

    if w_count < 1100:
        issues.append(f"Word count too low: {w_count} words (minimum required: 1100)")
    elif w_count > 1500:
        issues.append(f"Word count too high: {w_count} words (maximum target: 1400)")

    if "## " not in text:
        issues.append("Missing skimmable H2 headers")

    if "**" not in text:
        issues.append("Missing bold emphasis on key principles")

    has_citations = len(extract_citations(text)) > 0
    if not has_citations:
        issues.append("Missing grounded transcript citations")

    return len(issues) == 0, issues
