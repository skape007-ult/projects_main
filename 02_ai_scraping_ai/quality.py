"""
Content quality gate — scores extracts and filters junk before synthesis.
Runs between extraction and synthesis so bad articles never reach Gemini.
"""
import logging
from config import JUNK_TITLES, MIN_FULL_TEXT_LENGTH, MIN_TITLE_LENGTH, MIN_QUALITY_SCORE

logger = logging.getLogger(__name__)


def score_extract(extract: dict) -> float:
    """
    Score an extract from 0.0 (junk) to 1.0 (high quality).

    Scoring breakdown:
      - title quality:      0.0 - 0.25
      - full_text length:   0.0 - 0.30
      - metadata richness:  0.0 - 0.25
      - source reliability: 0.0 - 0.20
    """
    score = 0.0

    # ── title quality (0.25) ─────────────────────────────────────────────
    title = extract.get("title", "").strip()
    if title.lower() in JUNK_TITLES:
        return 0.0  # instant reject
    if len(title) >= MIN_TITLE_LENGTH:
        score += 0.15
        # bonus if title has real words (not just URL fragments or IDs)
        word_count = len(title.split())
        if word_count >= 3:
            score += 0.10

    # ── full_text length (0.30) ──────────────────────────────────────────
    full_text = extract.get("full_text", "")
    text_len = len(full_text)
    if text_len >= MIN_FULL_TEXT_LENGTH:
        score += 0.15
    if text_len >= 500:
        score += 0.10
    if text_len >= 1500:
        score += 0.05

    # ── metadata richness (0.25) ─────────────────────────────────────────
    if extract.get("summary"):
        score += 0.10
    if extract.get("keywords") and len(extract["keywords"]) >= 2:
        score += 0.10
    if extract.get("authors"):
        score += 0.05

    # ── source reliability (0.20) ────────────────────────────────────────
    source = extract.get("source", "").lower()
    high_trust = ["arxiv", "lilian weng", "bair", "google research",
                  "openai", "hugging face", "import ai", "deeplearning.ai"]
    medium_trust = ["hacker news", "r/localllama", "dwarkesh", "aws ml",
                    "cmu ml", "karpathy"]
    if any(s in source for s in high_trust):
        score += 0.20
    elif any(s in source for s in medium_trust):
        score += 0.12
    else:
        score += 0.05

    return round(min(score, 1.0), 3)


def passes_quality_gate(extract: dict) -> bool:
    """Returns True if the extract is worth synthesizing/embedding."""
    score = score_extract(extract)
    if score < MIN_QUALITY_SCORE:
        title = extract.get("title", "")[:50] or extract.get("url", "")[:50]
        logger.debug(f"Quality gate rejected (score={score}): {title}")
        return False
    return True


def filter_extracts(extracts: list[dict]) -> list[dict]:
    """Filter a list of extracts, returning only those that pass quality gate."""
    passed = []
    rejected = 0
    for extract in extracts:
        if passes_quality_gate(extract):
            passed.append(extract)
        else:
            rejected += 1

    if rejected > 0:
        logger.info(f"Quality gate: {len(passed)} passed, {rejected} rejected")

    return passed
