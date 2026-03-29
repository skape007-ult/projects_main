import asyncio
import logging
import aiohttp
import feedparser
from sources import RSS_FEEDS, ARXIV_FEEDS, HN_TOP_STORIES_URL, HN_ITEM_URL, AI_KEYWORDS
from config import FETCH_TIMEOUT as TIMEOUT_SECONDS

logger = logging.getLogger(__name__)

FETCH_TIMEOUT = aiohttp.ClientTimeout(total=TIMEOUT_SECONDS)


async def _fetch_json(session: aiohttp.ClientSession, url: str):
    async with session.get(url) as resp:
        return await resp.json()


async def _fetch_text(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url) as resp:
        return await resp.text()


def fetch_rss_urls(feeds: list):
    """Parse RSS feeds (feedparser is sync but fast)."""
    articles = []
    for feed_info in feeds:
        feed = feedparser.parse(feed_info["url"])
        for entry in feed.entries[:8]:
            articles.append({
                "url": entry.get("link", ""),
                "title": entry.get("title", ""),
                "source": feed_info["name"],
                "date": str(entry.get("published", ""))
            })
    return articles


def fetch_arxiv_urls():
    articles = []
    for url in ARXIV_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            articles.append({
                "url": entry.get("link", ""),
                "title": entry.get("title", ""),
                "source": f"Arxiv ({url.split('/')[-1]})",
                "date": str(entry.get("published", ""))
            })
    return articles


async def fetch_hn_urls_async() -> list[dict]:
    """Fetch HN stories concurrently using aiohttp."""
    try:
        async with aiohttp.ClientSession(timeout=FETCH_TIMEOUT) as session:
            top_ids = await _fetch_json(session, HN_TOP_STORIES_URL)
            top_ids = top_ids[:80]

            tasks = [
                _fetch_json(session, HN_ITEM_URL.format(story_id))
                for story_id in top_ids
            ]
            items = await asyncio.gather(*tasks, return_exceptions=True)

            articles = []
            for item in items:
                if isinstance(item, Exception):
                    continue
                title = item.get("title", "").lower()
                if any(kw in title for kw in AI_KEYWORDS):
                    url = item.get("url", "")
                    if url:
                        articles.append({
                            "url": url,
                            "title": item.get("title", ""),
                            "source": "Hacker News",
                            "date": ""
                        })
                if len(articles) >= 5:
                    break

            return articles
    except Exception as e:
        logger.error(f"HN async fetch failed: {e}")
        return []


def fetch_hn_urls() -> list[dict]:
    """Sync wrapper for backward compat."""
    return asyncio.run(fetch_hn_urls_async())


def get_all_sources():
    all_articles = []
    all_articles.extend(fetch_rss_urls(RSS_FEEDS))
    all_articles.extend(fetch_hn_urls())
    all_articles.extend(fetch_arxiv_urls())
    return [a for a in all_articles if a.get("url")]


async def get_all_sources_async():
    """Fully async version: RSS+Arxiv in thread pool, HN via aiohttp concurrently."""
    loop = asyncio.get_event_loop()

    rss_task = loop.run_in_executor(None, fetch_rss_urls, RSS_FEEDS)
    arxiv_task = loop.run_in_executor(None, fetch_arxiv_urls)
    hn_task = fetch_hn_urls_async()

    rss_articles, arxiv_articles, hn_articles = await asyncio.gather(
        rss_task, arxiv_task, hn_task
    )

    all_articles = rss_articles + hn_articles + arxiv_articles
    return [a for a in all_articles if a.get("url")]
