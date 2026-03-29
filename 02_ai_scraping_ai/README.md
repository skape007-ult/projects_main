# "AI Scraping AI" Pipeline & Knowledge Base

An autonomous, end-to-end data pipeline that scrapes, scores, embeds, and synthesizes the latest artificial intelligence research and news. This project functions both as a daily briefing generator (via email) and a persistent, searchable Retrieval-Augmented Generation (RAG) knowledge base.

[Example Email Briefing]
<img width="1326" height="1388" alt="image" src="https://github.com/user-attachments/assets/aebe9e21-ced8-442e-968d-db057222082b" />

## Technical Focus
This project was built to explore unstructured data processing and semantic search. Key mathematical and architectural concepts include:
* **Vector Embeddings & Semantic Search:** Utilizing `all-MiniLM-L6-v2` and ChromaDB to map document semantics into high-dimensional space for dense retrieval.
* **Cosine Similarity:** Calculating the cosine of the angle between query and document vectors to surface highly relevant context (threshold: >0.20).
* **Heuristic Quality Scoring:** An algorithmic gatekeeper that evaluates scraped extracts based on text length, metadata richness, and source reputation, dynamically rejecting low-entropy "junk" pages before embedding.
* **Asynchronous I/O:** Concurrent fetching of RSS feeds, Arxiv papers, and Hacker News API endpoints using `aiohttp` and `ThreadPoolExecutor`.

## System Architecture

The pipeline is entirely modular and can be run in discrete stages:

1.  **Fetch & Extract:** Aggregates URLs from foundational sources, RSS feeds, and APIs. Extracts core text and metadata using `trafilatura` and `newspaper3k`.
2.  **Quality Gate:** Scores raw extracts. Only high-quality, non-duplicate content is saved to the local SQLite metadata store.
3.  **Embed:** Converts cleaned text into normalized vector embeddings, batched into ChromaDB.
4.  **Synthesize:** Prompts Gemini 2.5 Flash/Pro with the day's top extracts to write a structured, citations-backed technical briefing.
5.  **Deliver:** Compiles the briefing and pipeline telemetry statistics into an HTML email.
6.  **RAG Interface:** A Streamlit dashboard (`app.py`) allowing semantic chat with the historical knowledge base and 2D UMAP visualizations of the vector space.

[Knowledge Map]
<img width="1431" height="799" alt="newplot" src="https://github.com/user-attachments/assets/7438d4cb-5cf8-4c0a-959a-e1c823120a45" />
