"""
Centralized configuration for the AI Briefing pipeline.
All tunable constants in one place — no more hunting across 8 files.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── API keys & credentials ──────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
EMAIL_RECIPIENT = os.environ.get("EMAIL_RECIPIENT", "")

# ── models ───────────────────────────────────────────────────────────────────
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
SYNTHESIS_MODEL = "gemini-2.5-flash"

# ── storage ──────────────────────────────────────────────────────────────────
CHROMA_PATH = "./chroma_store"
CHROMA_COLLECTION = "ai_briefings"
DB_PATH = "ai_briefing_store.db"
LEGACY_JSON_PATH = "ai_briefing_store.json"

# ── embedding ────────────────────────────────────────────────────────────────
TEXT_CHUNK_SIZE = 2500       # chars of full_text included in embedding
EMBED_BATCH_SIZE = 64        # sentence-transformers batch size
CHROMA_BATCH_SIZE = 5000     # max items per ChromaDB add()

# ── retrieval ────────────────────────────────────────────────────────────────
RELEVANCE_THRESHOLD = 0.2    # minimum cosine similarity to include
DEFAULT_RETRIEVAL_COUNT = 8  # articles to retrieve per query

# ── fetching ─────────────────────────────────────────────────────────────────
FETCH_TIMEOUT = 15           # seconds per HTTP request
HTTP_POOL_SIZE = 20          # connection pool size for requests.Session
MAX_EXTRACTION_WORKERS = 5   # threads for parallel article extraction
BULK_BATCH_SIZE = 20         # articles per batch in bulk_ingest
BULK_WORKERS = 3             # threads per batch in bulk_ingest
BULK_BATCH_PAUSE = 2         # seconds between bulk batches

# ── deduplication ────────────────────────────────────────────────────────────
FUZZY_TITLE_THRESHOLD = 0.85 # SequenceMatcher ratio for title dedup
FUZZY_LOOKBACK_DAYS = 30     # only check recent articles for fuzzy match

# ── quality gate ─────────────────────────────────────────────────────────────
MIN_QUALITY_SCORE = 0.3      # extracts below this are rejected
JUNK_TITLES = {
    "the heart of the internet",
    "please wait for verification",
    "just a moment",
    "access denied",
    "403 forbidden",
    "page not found",
    "404 not found",
    "subscribe to continue",
    "sign in",
    "",
}
MIN_FULL_TEXT_LENGTH = 200   # chars — below this is probably a landing page
MIN_TITLE_LENGTH = 10        # chars — below this is probably junk

# ── query cache ──────────────────────────────────────────────────────────────
CACHE_TTL_SECONDS = 3600     # 1 hour
CACHE_MAX_ENTRIES = 200

# ── synthesis ────────────────────────────────────────────────────────────────
PRIORITY_SOURCES = [
    "Arxiv", "Lilian Weng", "Import AI", "BAIR",
    "Google Research", "Hugging Face", "OpenAI", "Latent Space"
]
SYNTHESIS_TEXT_CAP = 1500    # chars of full_text sent to Gemini per article

# ── logging ──────────────────────────────────────────────────────────────────
LOG_FILE = "pipeline.log"
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
