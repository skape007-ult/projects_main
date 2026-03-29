"""
Shared singleton for SentenceTransformer model and ChromaDB client.
Prevents loading the same model multiple times across modules.
"""
import logging
import chromadb
from sentence_transformers import SentenceTransformer
from config import CHROMA_PATH, EMBEDDING_MODEL, CHROMA_COLLECTION

logger = logging.getLogger(__name__)

_model = None
_chroma_client = None
_collection = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def get_chroma_client() -> chromadb.PersistentClient:
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    return _chroma_client


def get_collection():
    global _collection
    if _collection is None:
        _collection = get_chroma_client().get_or_create_collection(name=CHROMA_COLLECTION)
    return _collection
