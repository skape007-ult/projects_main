# bulk_ingest.py
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from historical_fetcher import get_all_historical_sources
from sources import FOUNDATIONAL_SOURCES
from extractor import extract_article_intelligence
from store import load_store, save_to_store, is_already_processed, is_fuzzy_duplicate
from quality import passes_quality_gate
from embedder import embed_store
import config

logger = logging.getLogger(__name__)


def process_article(args):
    article_meta, store = args
    url = article_meta.get("url", "")

    if not url:
        return None

    if is_already_processed(store, url):
        return None

    title = article_meta.get("title", "")
    if title and is_fuzzy_duplicate(title):
        logger.debug(f"Fuzzy dup skipped: {title[:60]}")
        return None

    try:
        extract = extract_article_intelligence(url, article_meta)
        if not extract.get("full_text") and not extract.get("summary"):
            return None
        if not passes_quality_gate(extract):
            logger.debug(f"Quality gate rejected: {extract.get('title', url)[:60]}")
            return None
        save_to_store(store, url, extract)
        logger.info(f"Ingested: {extract.get('title', url)[:60]}")
        return extract
    except Exception as e:
        logger.warning(f"Failed: {url[:60]} — {e}")
        return None


def run_bulk_ingest():
    store = load_store()

    historical = get_all_historical_sources(days_back=90)
    all_sources = historical + FOUNDATIONAL_SOURCES

    new_sources = [s for s in all_sources if not is_already_processed(store, s["url"])]
    logger.info(f"{len(new_sources)} new articles to process ({len(all_sources) - len(new_sources)} already in store)")

    if not new_sources:
        logger.info("Nothing new to ingest.")
        return

    batch_size = config.BULK_BATCH_SIZE
    total_ingested = 0

    for i in range(0, len(new_sources), batch_size):
        batch = new_sources[i:i + batch_size]
        logger.info(f"Batch {i // batch_size + 1} of {len(new_sources) // batch_size + 1}...")

        with ThreadPoolExecutor(max_workers=config.BULK_WORKERS) as executor:
            results = list(executor.map(
                process_article,
                [(source, store) for source in batch]
            ))

        ingested = sum(1 for r in results if r is not None)
        total_ingested += ingested
        logger.info(f"  {ingested}/{len(batch)} ingested this batch")

        time.sleep(config.BULK_BATCH_PAUSE)

    logger.info(f"Bulk ingest complete. {total_ingested} new articles added.")
    logger.info("Building embeddings...")
    embed_store()
    logger.info("Done. Knowledge base is ready.")


if __name__ == "__main__":
    logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT, datefmt=config.LOG_DATE_FORMAT)
    run_bulk_ingest()
