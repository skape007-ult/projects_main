import logging
import trafilatura
import requests
from newspaper import Article
from config import FETCH_TIMEOUT, HTTP_POOL_SIZE

logger = logging.getLogger(__name__)

# reusable session with connection pooling and default timeout
_session = requests.Session()
_session.headers.update({"User-Agent": "AI-Briefing-Bot/1.0"})
_adapter = requests.adapters.HTTPAdapter(
    pool_connections=HTTP_POOL_SIZE,
    pool_maxsize=HTTP_POOL_SIZE,
    max_retries=1
)
_session.mount("http://", _adapter)
_session.mount("https://", _adapter)


def fetch_full_content(url):
    try:
        response = _session.get(url, timeout=FETCH_TIMEOUT)
        response.raise_for_status()
        html = response.text

        text = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
            favor_precision=True
        )
        return text or ""
    except requests.Timeout:
        logger.warning(f"Timeout fetching {url}")
        return ""
    except Exception as e:
        logger.warning(f"trafilatura failed for {url}: {e}")
        return ""


def extract_article_intelligence(url, metadata):
    full_text = fetch_full_content(url)

    try:
        article = Article(url)
        article.download()
        article.parse()
        article.nlp()

        return {
            "title": article.title or metadata.get("title", ""),
            "source": metadata.get("source", ""),
            "date": str(article.publish_date or metadata.get("date", "")),
            "authors": article.authors,
            "keywords": article.keywords,
            "summary": article.summary,
            "full_text": full_text,
            "url": url
        }

    except Exception as e:
        logger.warning(f"newspaper3k failed for {url}: {e}")
        return {
            "title": metadata.get("title", ""),
            "source": metadata.get("source", ""),
            "date": metadata.get("date", ""),
            "authors": [],
            "keywords": [],
            "summary": full_text[:500],
            "full_text": full_text,
            "url": url
        }
