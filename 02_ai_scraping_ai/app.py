import streamlit as st
from query import ask
from retriever import retrieve
from model_cache import get_collection
from config import DEFAULT_RETRIEVAL_COUNT, SYNTHESIS_MODEL
import numpy as np
import pandas as pd

collection = get_collection()

# -- page config --
st.set_page_config(
    page_title="AI Knowledge Base",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -- custom css --
st.markdown("""
<style>
    .main { padding-top: 1rem; }
    .stTextInput > div > div > input {
        font-size: 16px;
        padding: 12px;
    }
    .source-card {
        background: #f8f9fa;
        border-left: 3px solid #4a90e2;
        padding: 10px 14px;
        margin: 6px 0;
        border-radius: 0 6px 6px 0;
        font-size: 13px;
    }
    .source-card a {
        color: #185FA5;
        text-decoration: none;
        font-weight: 500;
    }
    .source-card a:hover { text-decoration: underline; }
    .relevance-badge {
        display: inline-block;
        background: #e8f0fe;
        color: #185FA5;
        border-radius: 12px;
        padding: 2px 8px;
        font-size: 11px;
        font-weight: 600;
        margin-left: 6px;
    }
    .stat-box {
        background: #f0f4ff;
        border-radius: 8px;
        padding: 12px 16px;
        text-align: center;
        margin-bottom: 8px;
    }
    .stat-number {
        font-size: 28px;
        font-weight: 700;
        color: #185FA5;
    }
    .stat-label {
        font-size: 11px;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
</style>
""", unsafe_allow_html=True)

# -- session state --
if "messages" not in st.session_state:
    st.session_state.messages = []
if "query_history" not in st.session_state:
    st.session_state.query_history = []


# -- sidebar --
with st.sidebar:
    st.markdown("### 🧠 AI Knowledge Base")
    st.markdown("---")

    total_vectors = collection.count()
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-number">{total_vectors:,}</div>
        <div class="stat-label">Articles in knowledge base</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Settings")
    n_results = st.slider(
        "Articles to retrieve",
        min_value=4,
        max_value=20,
        value=DEFAULT_RETRIEVAL_COUNT,
        help="More articles = broader context but slower response"
    )

    model_choice = st.selectbox(
        "Synthesis model",
        ["gemini-2.5-flash", "gemini-2.5-pro"],
        index=0 if SYNTHESIS_MODEL == "gemini-2.5-flash" else 1,
        help="Flash is free and fast. Pro is slower but better for complex synthesis."
    )

    st.markdown("---")

    if st.session_state.query_history:
        st.markdown("### Recent queries")
        for i, q in enumerate(reversed(st.session_state.query_history[-8:])):
            if st.button(
                q[:45] + "..." if len(q) > 45 else q,
                key=f"hist_{i}",
                width="stretch"
            ):
                st.session_state.prefill_query = q

    st.markdown("---")
    if st.button("Clear conversation", width="stretch"):
        st.session_state.messages = []
        st.rerun()


# -- helper to render source cards --
def render_source_cards(sources: list[dict]):
    for source in sources:
        relevance_pct = int(source["relevance"] * 100)
        st.markdown(f"""
        <div class="source-card">
            <a href="{source['url']}" target="_blank">
                {source['title'] or 'Untitled'}
            </a>
            <span class="relevance-badge">{relevance_pct}% match</span>
            <br>
            <span style="color:#888; font-size:11px;">
                {source['source']} · {source['date']}
            </span>
        </div>
        """, unsafe_allow_html=True)


# -- tabs --
tab_chat, tab_viz = st.tabs(["💬 Chat", "🗺️ Knowledge Map"])


# ======================================================================
# TAB 1 — CHAT
# ======================================================================
with tab_chat:
    st.markdown("## Ask your knowledge base")
    st.markdown(f"*Searching {total_vectors:,} articles from your AI/ML briefing archive*")

    st.markdown("**Try asking:**")
    suggestions = [
        "What do my sources say about inference efficiency?",
        "What safety risks have been discussed around AI agents?",
        "What's the latest on reward hacking in RL?",
        "How has speculative decoding evolved?",
        "What are the most significant model releases recently?",
    ]

    cols = st.columns(len(suggestions))
    for i, suggestion in enumerate(suggestions):
        with cols[i]:
            if st.button(
                suggestion[:35] + "...",
                key=f"sug_{i}",
                width="stretch"
            ):
                st.session_state.prefill_query = suggestion

    st.markdown("---")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                st.markdown(message["content"])
                if "sources" in message and message["sources"]:
                    with st.expander(
                        f"📚 {len(message['sources'])} sources retrieved",
                        expanded=False
                    ):
                        render_source_cards(message["sources"])
            else:
                st.markdown(message["content"])

    prefill = st.session_state.pop("prefill_query", "")
    query = st.chat_input(
        "Ask anything about AI/ML developments in your knowledge base..."
    )

    if prefill and not query:
        query = prefill

    if query:
        st.session_state.messages.append({"role": "user", "content": query})
        if query not in st.session_state.query_history:
            st.session_state.query_history.append(query)

        with st.chat_message("user"):
            st.markdown(query)

        with st.chat_message("assistant"):
            # single retrieve call — passed to ask() to avoid double retrieval
            with st.spinner("Searching knowledge base..."):
                sources = retrieve(query, n_results=n_results)

            if not sources:
                answer = (
                    "Your knowledge base doesn't have strong coverage on this "
                    "topic yet. Try running `main.py` to fetch fresh content, "
                    "or rephrase your query."
                )
                st.markdown(answer)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": []
                })
            else:
                with st.spinner(
                    f"Synthesizing answer from {len(sources)} sources..."
                ):
                    # pass pre_retrieved to avoid calling retrieve() again
                    # pass model_choice so the sidebar selector actually works
                    answer = ask(
                        query,
                        n_results=n_results,
                        model=model_choice,
                        pre_retrieved=sources
                    )

                st.markdown(answer)

                with st.expander(
                    f"📚 {len(sources)} sources retrieved",
                    expanded=True
                ):
                    render_source_cards(sources)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources
                })

        st.rerun()


# ======================================================================
# TAB 2 — KNOWLEDGE MAP (UMAP preferred, t-SNE fallback)
# ======================================================================
with tab_viz:
    st.markdown("## Knowledge Map")
    st.markdown(
        "A 2D projection of your knowledge base. "
        "Articles with similar meaning cluster together. "
        "Hover over any point to see the title and source."
    )

    @st.cache_data(show_spinner="Building knowledge map...")
    def build_viz_data():
        data = collection.get(include=["embeddings", "metadatas"])
        embeddings = np.array(data["embeddings"])
        metadatas = data["metadatas"]

        if len(embeddings) < 10:
            return None, "too_few"

        # try UMAP first (O(n log n)), fall back to t-SNE (O(n^2))
        try:
            import umap
            n_neighbors = min(15, len(embeddings) - 1)
            reducer = umap.UMAP(
                n_components=2,
                n_neighbors=n_neighbors,
                min_dist=0.1,
                random_state=42,
                metric="cosine"
            )
            reduced = reducer.fit_transform(embeddings)
        except ImportError:
            try:
                from sklearn.manifold import TSNE
                perplexity = min(30, len(embeddings) - 1)
                reducer = TSNE(n_components=2, random_state=42, perplexity=perplexity)
                reduced = reducer.fit_transform(embeddings)
            except ImportError:
                return None, "missing_deps"

        df = pd.DataFrame({
            "x": reduced[:, 0],
            "y": reduced[:, 1],
            "title": [m.get("title", "Untitled")[:60] for m in metadatas],
            "source": [m.get("source", "Unknown").split("(")[0].strip() for m in metadatas],
            "date": [m.get("date", "") for m in metadatas],
            "url": [m.get("url", "") for m in metadatas],
            "keywords": [m.get("keywords", "") for m in metadatas],
        })

        return df, "ok"

    col1, col2 = st.columns([3, 1])

    with col2:
        st.markdown("### Filters")
        if st.button("🔄 Rebuild map", width="stretch"):
            st.cache_data.clear()
            st.rerun()
        st.markdown(
            "*Map is cached. Click rebuild after adding new articles.*"
        )

    with col1:
        df, status = build_viz_data()

        if status == "missing_deps":
            st.error(
                "Missing dependencies. Run:\n"
                "```\npip install umap-learn scikit-learn plotly\n```"
            )
        elif status == "too_few":
            st.warning(
                "Not enough articles to visualize yet. "
                "Run `main.py` to fetch more content."
            )
        elif df is not None:
            try:
                import plotly.express as px

                all_sources = sorted(df["source"].unique().tolist())
                selected_sources = st.multiselect(
                    "Filter by source",
                    all_sources,
                    default=all_sources,
                    key="viz_sources"
                )

                filtered_df = df[df["source"].isin(selected_sources)]

                fig = px.scatter(
                    filtered_df,
                    x="x",
                    y="y",
                    color="source",
                    hover_data={
                        "title": True,
                        "date": True,
                        "keywords": True,
                        "x": False,
                        "y": False
                    },
                    height=620,
                    title=f"Knowledge Base — {len(filtered_df):,} articles",
                    template="plotly_white"
                )

                fig.update_traces(
                    marker=dict(size=7, opacity=0.75),
                    selector=dict(mode="markers")
                )

                fig.update_layout(
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    margin=dict(l=0, r=0, t=40, b=0),
                    xaxis=dict(
                        showticklabels=False, showgrid=False,
                        zeroline=False, title=""
                    ),
                    yaxis=dict(
                        showticklabels=False, showgrid=False,
                        zeroline=False, title=""
                    ),
                    plot_bgcolor="white",
                )

                st.plotly_chart(fig, width="stretch")
                st.markdown(
                    f"*Showing {len(filtered_df):,} of {len(df):,} articles. "
                    "Points close together have similar meaning. "
                    "Hover to inspect any article.*"
                )

            except ImportError:
                st.error(
                    "Plotly not installed. Run:\n"
                    "```\npip install plotly\n```"
                )
