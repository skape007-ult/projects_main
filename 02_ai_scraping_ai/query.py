import logging
import hashlib
import time
from google import genai
from retriever import retrieve
from config import GEMINI_API_KEY, SYNTHESIS_MODEL, CACHE_TTL_SECONDS, CACHE_MAX_ENTRIES

logger = logging.getLogger(__name__)

client = genai.Client(api_key=GEMINI_API_KEY)

# simple in-memory query cache: {cache_key: (response, timestamp)}
_query_cache = {}


def _cache_key(question: str, n_results: int, model: str) -> str:
    return hashlib.sha256(f"{question.strip().lower()}:{n_results}:{model}".encode()).hexdigest()


def ask(question: str, n_results: int = 8, model: str = None,
        pre_retrieved: list[dict] = None, verbose: bool = False) -> str:
    """
    Answer a question using the knowledge base.

    Args:
        question: The user's question
        n_results: How many articles to retrieve (ignored if pre_retrieved is set)
        model: Gemini model to use (defaults to config.SYNTHESIS_MODEL)
        pre_retrieved: Pre-fetched retrieval results (avoids duplicate retrieve calls)
        verbose: Print debug info
    """
    model = model or SYNTHESIS_MODEL

    # check cache
    key = _cache_key(question, n_results, model)
    if key in _query_cache:
        cached_response, cached_at = _query_cache[key]
        if time.time() - cached_at < CACHE_TTL_SECONDS:
            logger.debug("Cache hit for query")
            return cached_response
        else:
            del _query_cache[key]

    # use pre-retrieved results if provided, otherwise retrieve
    results = pre_retrieved if pre_retrieved is not None else retrieve(question, n_results=n_results)

    if not results:
        return (
            "Your knowledge base doesn't have strong coverage on this topic yet. "
            "This could mean the topic hasn't appeared in your sources, or the store "
            "needs more articles. Try running main.py to fetch fresh content."
        )
    if verbose:
        logger.info(f"Retrieved {len(results)} articles")
        for r in results:
            logger.debug(f"  {r['relevance']} | {r['date']} | {r['title']}")

    context = ""
    for i, r in enumerate(results, 1):
        context += f"""
    [{i}] {r['title']}
    Source: {r['source']}
    Date: {r['date']}
    URL: {r['url']}
    Relevance: {r['relevance']}
    Content: {r['summary']}
    ---
    """

    response = client.models.generate_content(
        model=model,
        contents=f"""You are a personal AI research assistant. You have access to a
    curated knowledge base of AI/ML articles and papers collected over time.

    Answer the following question using ONLY the provided sources.
    Be technically precise. For every key claim, cite the source number in brackets e.g. [1], [2].
    If the sources don't contain enough information to answer well, say so clearly —
    do not fill gaps with outside knowledge.

    End your response with a "Sources" section listing each source you cited:
    [N] Title — Date — URL

    QUESTION: {question}

    SOURCES:
    {context}
    """
    )

    answer = response.text

    # store in cache
    _query_cache[key] = (answer, time.time())

    # evict old entries if cache grows too large
    if len(_query_cache) > CACHE_MAX_ENTRIES:
        oldest_key = min(_query_cache, key=lambda k: _query_cache[k][1])
        del _query_cache[oldest_key]

    return answer


def main():
    import config
    logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT, datefmt=config.LOG_DATE_FORMAT)

    print("\n" + "=" * 50)
    print("  AI Knowledge Base — CLI")
    print("  Type 'quit' to exit | 'verbose' to toggle debug")
    print("=" * 50 + "\n")

    verbose = False

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if not user_input:
            continue

        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye.")
            break

        if user_input.lower() == "verbose":
            verbose = not verbose
            print(f"Verbose mode: {'on' if verbose else 'off'}\n")
            continue

        if user_input.lower() == "count":
            from model_cache import get_collection
            print(f"Articles in knowledge base: {get_collection().count()}\n")
            continue

        print("\nSearching knowledge base...\n")
        answer = ask(user_input, verbose=verbose)
        print(f"Assistant:\n{answer}\n")
        print("-" * 50 + "\n")


if __name__ == "__main__":
    main()
