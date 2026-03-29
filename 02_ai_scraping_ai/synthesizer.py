import logging
from google import genai
from config import GEMINI_API_KEY, SYNTHESIS_MODEL, PRIORITY_SOURCES, SYNTHESIS_TEXT_CAP

logger = logging.getLogger(__name__)

client = genai.Client(api_key=GEMINI_API_KEY)


def synthesize_briefing(extracts: list[dict], model: str = None) -> str:
    """Synthesize a daily briefing from extracts. Model is configurable."""
    model = model or SYNTHESIS_MODEL

    def source_priority(e):
        for i, s in enumerate(PRIORITY_SOURCES):
            if s.lower() in e.get("source", "").lower():
                return i
        return len(PRIORITY_SOURCES)

    sorted_extracts = sorted(extracts, key=source_priority)

    formatted = ""
    for e in sorted_extracts:
        formatted += f"""
---
SOURCE: {e.get('source', '')}
TITLE: {e.get('title', '')}
DATE: {e.get('date', '')}
KEYWORDS: {', '.join(e.get('keywords', []))}
SUMMARY: {e.get('summary', '')}
FULL TEXT: {e.get('full_text', '')[:SYNTHESIS_TEXT_CAP]}
URL: {e.get('url', '')}
"""

    logger.info(f"Synthesizing briefing from {len(extracts)} articles with {model}")

    response = client.models.generate_content(
        model=model,
        contents=f"""
You are a technical AI/ML research analyst writing a daily briefing.
You have {len(extracts)} source articles to draw from today.

Write a technically precise daily briefing structured as follows:

**TOP SIGNAL**
The single most important development today. Must be from a primary source
(research paper, official blog, or major publication). Explain the technical
significance precisely — specific numbers, benchmarks, architectural details.
Format source as [Title](url).

**RANKED DEVELOPMENTS**
8-10 items minimum. Each must come from a DIFFERENT source — no source may
appear more than once across all ranked items. For each:
- Core technical claim with specific evidence
- Why it matters for someone building AI systems
- Format source as [Title](url)

**CROSS-SOURCE PATTERNS**
3-4 themes that appear across MULTIPLE sources today. Each pattern must
reference at least 2 different sources with [Title](url) links. Do not
repeat themes already covered in ranked developments.

**CONTRADICTIONS OR TENSIONS**
2-3 genuine conflicts between sources, or findings that challenge established
thinking. Must cite specific claims from specific sources with [Title](url).

**WHAT TO WATCH**
4-5 concrete predictions for the next 1-2 weeks based on today's signals.
Each must be grounded in a specific source with [Title](url).

STRICT RULES:
- Each source may only be the PRIMARY citation in ONE section total
- Minimum 8 distinct sources cited across the entire briefing
- Be technically precise — cite specific numbers, benchmarks, model names
- Explain significance in plain language after the technical claim
- No hype, no filler, every sentence carries information
- Format ALL source references as [Title](url) for clickable links

---
{formatted}
"""
    )
    return response.text
