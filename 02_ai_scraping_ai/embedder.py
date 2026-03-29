import logging
from model_cache import get_model, get_collection
from quality import passes_quality_gate
from config import TEXT_CHUNK_SIZE, EMBED_BATCH_SIZE, CHROMA_BATCH_SIZE, JUNK_TITLES

logger = logging.getLogger(__name__)


def load_store():
    """Load from SQLite via store module."""
    from store import load_store as _load
    return _load()


def build_text_for_embedding(extract):
    """
    Concatenates all meaningful fields into one rich string.
    Uses configurable TEXT_CHUNK_SIZE chars of full text for semantic coverage.
    """
    parts = [
        f"Title: {extract.get('title', '')}",
        f"Source: {extract.get('source', '')}",
        f"Keywords: {', '.join(extract.get('keywords', []))}",
        f"Summary: {extract.get('summary', '')}",
        f"Full text: {extract.get('full_text', '')[:TEXT_CHUNK_SIZE]}",
    ]
    return "\n".join(parts)


def embed_store() -> dict:
    store = load_store()
    if not store:
        return {"new_embedded": 0, "skipped": 0, "total_vectors": 0}

    collection = get_collection()
    model = get_model()

    urls_to_embed = []
    texts_to_embed = []
    metadatas_to_embed = []

    for url, data in store.items():
        try:
            existing = collection.get(ids=[url])
            if existing["ids"]:
                continue
        except Exception:
            pass

        extract = data.get("extract", {})
        if not extract:
            continue

        # use quality gate instead of just junk title check
        if not passes_quality_gate(extract):
            continue

        text = build_text_for_embedding(extract)
        urls_to_embed.append(url)
        texts_to_embed.append(text)
        metadatas_to_embed.append({
            "title": extract.get("title", ""),
            "source": extract.get("source", ""),
            "date": data.get("date", ""),
            "url": url,
            "keywords": ", ".join(extract.get("keywords", [])),
            "summary": extract.get("summary", "")[:500]
        })

    skipped = len(store) - len(urls_to_embed)

    if not texts_to_embed:
        total_vectors = collection.count()
        logger.info(f"Embedder: 0 new, {skipped} skipped. Total vectors: {total_vectors}")
        return {"new_embedded": 0, "skipped_already_embedded": skipped, "total_vectors": total_vectors}

    logger.info(f"Embedding {len(texts_to_embed)} articles in batches of {EMBED_BATCH_SIZE}...")
    all_embeddings = model.encode(
        texts_to_embed,
        batch_size=EMBED_BATCH_SIZE,
        show_progress_bar=True,
        normalize_embeddings=True
    )

    for i in range(0, len(urls_to_embed), CHROMA_BATCH_SIZE):
        end = min(i + CHROMA_BATCH_SIZE, len(urls_to_embed))
        collection.add(
            ids=urls_to_embed[i:end],
            embeddings=all_embeddings[i:end].tolist(),
            documents=texts_to_embed[i:end],
            metadatas=metadatas_to_embed[i:end]
        )

    new = len(urls_to_embed)
    total_vectors = collection.count()
    logger.info(f"Embedder: {new} new, {skipped} skipped. Total vectors: {total_vectors}")

    return {
        "new_embedded": new,
        "skipped_already_embedded": skipped,
        "total_vectors": total_vectors
    }


if __name__ == "__main__":
    import config
    logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT, datefmt=config.LOG_DATE_FORMAT)
    embed_store()
