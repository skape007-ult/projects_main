import logging
import requests
import feedparser
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def fetch_arxiv_historical(days_back: int = 90, max_results: int = 500) -> list[dict]:
    """Fetch papers from Arxiv cs.AI, cs.LG, cs.CL, stat.ML for past N days."""
    categories = ["cs.AI", "cs.LG", "cs.CL", "stat.ML"]
    articles = []

    for cat in categories:
        url = (
            f"http://export.arxiv.org/api/query?"
            f"search_query=cat:{cat}"
            f"&start=0"
            f"&max_results={max_results // len(categories)}"
            f"&sortBy=submittedDate"
            f"&sortOrder=descending"
        )
        feed = feedparser.parse(url)
        for entry in feed.entries:
            articles.append({
                "url": entry.get("link", ""),
                "title": entry.get("title", "").replace("\n", " ").strip(),
                "source": f"Arxiv ({cat})",
                "date": str(entry.get("published", ""))[:10]
            })
        logger.info(f"Fetched {len(feed.entries)} papers from {cat}")

    return articles


def fetch_hn_historical(days_back: int = 90, max_results: int = 200) -> list[dict]:
    """Fetch AI-related HN stories via Algolia API."""
    from_ts = int((datetime.now() - timedelta(days=days_back)).timestamp())

    keywords = ["llm", "ai", "machine learning", "neural", "gpt", "claude",
                "transformer", "inference", "fine-tuning", "embedding"]

    articles = []
    seen_urls = set()

    for kw in keywords[:5]:
        url = (
            f"https://hn.algolia.com/api/v1/search?"
            f"query={kw}"
            f"&tags=story"
            f"&numericFilters=created_at_i>{from_ts}"
            f"&hitsPerPage=40"
        )
        try:
            resp = requests.get(url, timeout=10).json()
            for hit in resp.get("hits", []):
                story_url = hit.get("url", "")
                if story_url and story_url not in seen_urls:
                    seen_urls.add(story_url)
                    articles.append({
                        "url": story_url,
                        "title": hit.get("title", ""),
                        "source": "Hacker News",
                        "date": hit.get("created_at", "")[:10]
                    })
        except Exception as e:
            logger.warning(f"HN fetch failed for '{kw}': {e}")

    return articles[:max_results]


def fetch_blog_archive(name: str, archive_url: str, max_posts: int = 20) -> list[dict]:
    """Fetch archive page from a blog and extract post links."""
    try:
        feed = feedparser.parse(archive_url)
        articles = []
        for entry in feed.entries[:max_posts]:
            articles.append({
                "url": entry.get("link", ""),
                "title": entry.get("title", ""),
                "source": name,
                "date": str(entry.get("published", ""))[:10]
            })
        return articles
    except Exception as e:
        logger.warning(f"Archive fetch failed for {name}: {e}")
        return []


def get_all_historical_sources(days_back: int = 90) -> list[dict]:
    all_articles = []

    logger.info("Fetching Arxiv historical papers...")
    all_articles.extend(fetch_arxiv_historical(days_back=days_back, max_results=400))

    logger.info("Fetching HN historical stories...")
    all_articles.extend(fetch_hn_historical(days_back=days_back))

    logger.info("Fetching blog archives...")
    blogs = [
        ("Lilian Weng", "https://lilianweng.github.io/index.xml"),
        ("Import AI", "https://importai.substack.com/feed"),
        ("The Batch", "https://www.deeplearning.ai/the-batch/feed/"),
        ("BAIR Blog", "https://bair.berkeley.edu/blog/feed.xml"),
        ("Hugging Face", "https://huggingface.co/blog/feed.xml"),
        ("Google Research", "https://research.google/blog/rss"),
        ("OpenAI", "https://openai.com/news/rss.xml"),
    ]
    for name, url in blogs:
        posts = fetch_blog_archive(name, url, max_posts=30)
        all_articles.extend(posts)
        logger.info(f"  {name}: {len(posts)} posts")

    # deduplicate by URL
    seen = set()
    unique = []
    for a in all_articles:
        if a["url"] and a["url"] not in seen:
            seen.add(a["url"])
            unique.append(a)

    logger.info(f"Total unique historical sources: {len(unique)}")
    return unique
