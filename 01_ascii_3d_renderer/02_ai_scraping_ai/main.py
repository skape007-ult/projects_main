"""
AI Briefing Pipeline — modular stages that can run independently.

Usage:
    python main.py                  # full pipeline (fetch + extract + synthesize + embed + email)
    python main.py fetch            # fetch sources only, print what was found
    python main.py extract          # fetch + extract, store results, no synthesis
    python main.py synthesize       # synthesize from today's stored articles
    python main.py embed            # embed all unembedded articles into ChromaDB
    python main.py email            # re-send today's briefing (requires prior synthesis)
"""
import asyncio
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date

import config
from fetcher import get_all_sources_async
from extractor import extract_article_intelligence
from store import load_store, save_to_store, is_already_processed, is_fuzzy_duplicate, get_articles_by_date
from quality import passes_quality_gate, filter_extracts
from synthesizer import synthesize_briefing
from emailer import send_briefing
from embedder import embed_store

logger = logging.getLogger(__name__)


# ── logging setup ────────────────────────────────────────────────────────────
def _setup_logging():
    root = logging.getLogger()
    root.setLevel(getattr(logging, config.LOG_LEVEL))

    fmt = logging.Formatter(config.LOG_FORMAT, datefmt=config.LOG_DATE_FORMAT)

    # console handler
    console = logging.StreamHandler()
    console.setFormatter(fmt)
    root.addHandler(console)

    # file handler
    file_handler = logging.FileHandler(config.LOG_FILE)
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)


# ── stage: fetch ─────────────────────────────────────────────────────────────
async def stage_fetch() -> list[dict]:
    """Fetch all source URLs. Returns list of article metadata dicts."""
    logger.info(f"=== AI Briefing — {date.today()} ===")
    sources = await get_all_sources_async()
    logger.info(f"Found {len(sources)} sources to check.")
    return sources


# ── stage: extract ───────────────────────────────────────────────────────────
def _process_article(args):
    article_meta, store = args
    url = article_meta["url"]

    if is_already_processed(store, url):
        return None, "skipped"

    title = article_meta.get("title", "")
    if title and is_fuzzy_duplicate(title):
        return None, "fuzzy_dup"

    extract = extract_article_intelligence(url, article_meta)

    if not extract.get("full_text"):
        return None, "no_content"

    # quality gate — reject junk before it reaches the store
    if not passes_quality_gate(extract):
        return None, "low_quality"

    save_to_store(store, url, extract)
    return extract, "success"


def stage_extract(sources: list[dict]) -> tuple[list[dict], dict]:
    """Extract articles in parallel. Returns (extracts, stats)."""
    store = load_store()

    with ThreadPoolExecutor(max_workers=config.MAX_EXTRACTION_WORKERS) as executor:
        results = list(executor.map(
            _process_article,
            [(source, store) for source in sources]
        ))

    stats = {
        "total_sources_checked": len(sources),
        "successfully_extracted": 0,
        "skipped_already_seen": 0,
        "skipped_fuzzy_dup": 0,
        "failed_no_content": 0,
        "rejected_low_quality": 0,
        "used_in_briefing": 0,
        "sources_by_type": {},
    }

    todays_extracts = []
    for result, status in results:
        if status == "skipped":
            stats["skipped_already_seen"] += 1
        elif status == "fuzzy_dup":
            stats["skipped_fuzzy_dup"] += 1
        elif status == "no_content":
            stats["failed_no_content"] += 1
        elif status == "low_quality":
            stats["rejected_low_quality"] += 1
        elif status == "success":
            stats["successfully_extracted"] += 1
            todays_extracts.append(result)

    stats["used_in_briefing"] = len(todays_extracts)

    for extract in todays_extracts:
        source = extract.get("source", "Unknown")
        base = source.split("(")[0].strip()
        stats["sources_by_type"][base] = stats["sources_by_type"].get(base, 0) + 1

    logger.info(f"{stats['successfully_extracted']} new articles processed.")
    if stats["skipped_fuzzy_dup"] > 0:
        logger.info(f"{stats['skipped_fuzzy_dup']} fuzzy duplicates skipped.")
    if stats["rejected_low_quality"] > 0:
        logger.info(f"{stats['rejected_low_quality']} rejected by quality gate.")

    return todays_extracts, stats


# ── stage: synthesize ────────────────────────────────────────────────────────
def stage_synthesize(extracts: list[dict]) -> str:
    """Synthesize a briefing from extracts."""
    logger.info(f"Synthesizing briefing from {len(extracts)} articles...")
    return synthesize_briefing(extracts)


# ── stage: embed ─────────────────────────────────────────────────────────────
def stage_embed() -> dict:
    """Embed all unembedded articles into ChromaDB."""
    logger.info("Embedding new articles into vector store...")
    return embed_store()


# ── full pipeline ────────────────────────────────────────────────────────────
async def run_daily_briefing():
    start_time = time.time()

    # fetch
    sources = await stage_fetch()

    # extract
    fetch_start = time.time()
    todays_extracts, stats = stage_extract(sources)
    stats["fetch_time_seconds"] = round(time.time() - fetch_start, 1)

    if not todays_extracts:
        logger.info("No new content today. Briefing skipped.")
        stage_embed()
        return

    # synthesize + embed in parallel
    logger.info("Synthesizing briefing + embedding in parallel...")
    synthesis_start = time.time()

    with ThreadPoolExecutor(max_workers=2) as executor:
        synthesis_future = executor.submit(stage_synthesize, todays_extracts)
        embed_future = executor.submit(stage_embed)

        briefing = synthesis_future.result()
        rag_stats = embed_future.result()

    stats["synthesis_time_seconds"] = round(time.time() - synthesis_start, 1)
    stats["total_time_seconds"] = round(time.time() - start_time, 1)

    logger.info(f"Pipeline complete in {stats['total_time_seconds']}s")

    stats["rag_new_embedded"] = rag_stats["new_embedded"]
    stats["rag_total_vectors"] = rag_stats["total_vectors"]

    # email
    send_briefing(briefing, stats)
    logger.info("Done.")


# ── CLI entry point ──────────────────────────────────────────────────────────
def main():
    _setup_logging()

    if len(sys.argv) <= 1:
        asyncio.run(run_daily_briefing())
        return

    command = sys.argv[1].lower()

    if command == "fetch":
        sources = asyncio.run(stage_fetch())
        for s in sources:
            print(f"  [{s['source']}] {s['title'][:60]} — {s['url']}")
        print(f"\nTotal: {len(sources)} sources")

    elif command == "extract":
        sources = asyncio.run(stage_fetch())
        extracts, stats = stage_extract(sources)
        print(f"\nExtracted: {stats['successfully_extracted']}")
        print(f"Skipped:   {stats['skipped_already_seen']}")
        print(f"Rejected:  {stats['rejected_low_quality']}")
        print(f"No content: {stats['failed_no_content']}")

    elif command == "synthesize":
        articles = get_articles_by_date()
        if not articles:
            logger.warning("No articles found for today. Run 'extract' first.")
            return
        extracts = [a["extract"] for a in articles]
        extracts = filter_extracts(extracts)
        briefing = stage_synthesize(extracts)
        print(briefing)

    elif command == "embed":
        rag_stats = stage_embed()
        print(f"New: {rag_stats['new_embedded']}, Total: {rag_stats['total_vectors']}")

    elif command == "email":
        logger.warning("Re-send not yet implemented — run the full pipeline instead.")

    else:
        print(__doc__)


if __name__ == "__main__":
    main()
