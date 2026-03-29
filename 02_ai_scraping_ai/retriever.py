import logging
from model_cache import get_model, get_collection
from config import RELEVANCE_THRESHOLD

logger = logging.getLogger(__name__)


def retrieve(query: str, n_results: int = 8) -> list[dict]:
    collection = get_collection()
    model = get_model()

    if collection.count() == 0:
        logger.warning("ChromaDB is empty. Run embedder.py first.")
        return []

    query_embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, collection.count()),
        include=["documents", "metadatas", "distances"]
    )

    retrieved = []
    for i in range(len(results["ids"][0])):
        distance = results["distances"][0][i]
        relevance = 1 - (distance / 2)

        retrieved.append({
            "text": results["documents"][0][i],
            "title": results["metadatas"][0][i]["title"],
            "source": results["metadatas"][0][i]["source"],
            "date": results["metadatas"][0][i]["date"],
            "url": results["metadatas"][0][i]["url"],
            "keywords": results["metadatas"][0][i]["keywords"],
            "summary": results["metadatas"][0][i]["summary"],
            "relevance": round(relevance, 3)
        })

    retrieved = [r for r in retrieved if r["relevance"] >= RELEVANCE_THRESHOLD]
    return sorted(retrieved, key=lambda x: x["relevance"], reverse=True)
