"""Project C - A Streamlit conversational application.

Run:
    python -m pip install -r requirements/llm.txt
    python -m streamlit run projects/chatbots-rag/app_streamlit.py

This file is deliberately thin: the interface owns no retrieval, generation, or
citation logic. It calls ``RAGChatbot`` and renders what comes back. That is why
changing ``min_score`` in the sidebar changes behaviour without touching the app.

Streamlit is not part of the core dependency set, so this module is imported by
Streamlit only. The offline tests do not import it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent
REPO_ROOT = PROJECT_DIR.parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from chatbot_core import GenerationConfig, RAGChatbot  # noqa: E402
from chatbot_core.generation import render_answer  # noqa: E402

DEFAULT_CORPUS = REPO_ROOT / "data" / "chatbots-rag" / "corpus"

st.set_page_config(page_title="AITopics course assistant", page_icon="💬", layout="wide")


@st.cache_resource(show_spinner="Indexing documents...")
def load_bot(corpus: str, k: int, min_score: float) -> RAGChatbot:
    return RAGChatbot.from_directory(
        Path(corpus),
        config=GenerationConfig(k=k, min_score=min_score),
    )


def init_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "bot" not in st.session_state:
        st.session_state.bot = None


def sidebar() -> tuple[str, int, float]:
    st.sidebar.header("Settings")
    corpus = st.sidebar.text_input("Corpus directory", value=str(DEFAULT_CORPUS))
    k = st.sidebar.slider("Retrieved chunks (k)", min_value=1, max_value=8, value=4)
    min_score = st.sidebar.slider(
        "Minimum retrieval score", min_value=0.0, max_value=0.9, value=0.12, step=0.02,
        help="Below this the assistant refuses instead of guessing.",
    )
    if st.sidebar.button("Rebuild index"):
        st.cache_resource.clear()
        st.session_state.bot = None
        st.session_state.messages = []
        st.rerun()

    st.sidebar.markdown(
        "---\n"
        "**Model:** offline extractive stand-in. No document text leaves this machine.\n\n"
        "A confident paragraph is not evidence. Check the sources."
    )
    return corpus, k, min_score


def render_sources(answer) -> None:
    if answer.citations:
        with st.expander(f"Sources ({len(answer.citations)})", expanded=False):
            for citation in answer.citations:
                st.markdown(f"**[{citation.number}] {citation.title} - {citation.section}**")
                st.caption(f"`{citation.source}`  ·  score {citation.score:.3f}")
    elif answer.abstained:
        st.caption("No sources cited: the documents do not support an answer.")


def main() -> None:
    init_state()
    st.title("AITopics course assistant")
    st.caption("Ask about the Study Hub documentation. The assistant refuses when the evidence is missing.")

    corpus, k, min_score = sidebar()

    if st.session_state.bot is None:
        corpus_path = Path(corpus)
        if not corpus_path.exists():
            st.error(
                f"Corpus not found: {corpus_path}\n\n"
                "Generate the sample corpus first:\n\n"
                "`python scripts/make_chatbot_data.py`"
            )
            return
        st.session_state.bot = load_bot(corpus, k, min_score)

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("answer") is not None:
                render_sources(message["answer"])

    prompt = st.chat_input("Ask a question about the documentation")
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Retrieving and answering..."):
            answer = st.session_state.bot.ask(prompt)
        st.markdown(answer.text)
        if answer.conflict:
            st.warning(answer.conflict_note)
        render_sources(answer)
        if answer.quarantined_chunks:
            st.info(
                "Some retrieved text was withheld because it looked like an instruction "
                f"attempt: {', '.join(answer.quarantined_chunks)}"
            )
        with st.expander("Debug details"):
            st.json(answer.as_dict())
            st.code(render_answer(answer), language="text")

    st.session_state.messages.append(
        {"role": "assistant", "content": answer.text, "answer": answer}
    )


if __name__ == "__main__":
    main()
