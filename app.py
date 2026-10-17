import os

# Temporary workaround for a broken SSL_CERT_FILE env var (must run before the imports below)
os.environ.pop("SSL_CERT_FILE", None)

import re
import time

import streamlit as st

from src.agents.agents import (
    build_reader_agent,
    build_search_agent,
    writer_chain,
    critic_chain,
)

st.set_page_config(
    page_title="Multi-Agent Research System", page_icon="🔎", layout="wide"
)

EXAMPLES = [
    "The impact of AI on the job market in 2026",
    "Latest developments in solid-state batteries",
    "State of mobile money adoption in East Africa",
]


# ───────────────────────── helpers ─────────────────────────
def extract_trace(agent_result: dict) -> list[dict]:
    """Pull tool calls + tool outputs out of an agent's message history."""
    trace = []
    for m in agent_result.get("messages", []):
        for tc in getattr(m, "tool_calls", None) or []:
            trace.append({"kind": "call", "tool": tc["name"], "args": tc["args"]})
        if getattr(m, "type", "") == "tool":
            trace.append({"kind": "result", "tool": m.name, "content": str(m.content)})
    return trace


def render_trace(trace: list[dict], agent_name: str):
    if not any(t["kind"] == "call" for t in trace):
        st.warning(
            f"{agent_name} never called a tool. Small models often skip tool calls, "
            "so the output below may be hallucinated."
        )
        return
    for t in trace:
        if t["kind"] == "call":
            st.markdown(f"**🔧 Tool call:** `{t['tool']}`")
            st.json(t["args"])
        else:
            st.markdown(f"**📥 Tool output:** `{t['tool']}`")
            st.code(t["content"][:3000], language="text")


def parse_score(feedback: str):
    m = re.search(r"Score:\s*(\d+(?:\.\d+)?)\s*/\s*10", feedback or "")
    return m.group(1) if m else None


# ───────────────────────── sidebar ─────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")
    pass_chars = st.slider(
        "Search-result characters passed to the Reader agent",
        min_value=400,
        max_value=4000,
        value=2000,
        step=200,
        help="Your original pipeline used 800. Too small can cut a URL in half.",
    )
    st.divider()
    st.caption("Example topics")
    for ex in EXAMPLES:
        if st.button(ex, use_container_width=True):
            st.session_state["topic"] = ex

# ───────────────────────── main ─────────────────────────
st.title("🔎 Multi-Agent Research System")
st.caption("Search agent → Reader agent → Writer → Critic")

topic = st.text_input(
    "Research topic",
    key="topic",
    value=st.session_state.get("topic", EXAMPLES[0]),
    placeholder="e.g. The impact of AI on the job market in 2026",
)
run = st.button("🚀 Run research pipeline", type="primary", disabled=not topic.strip())

if run:
    state: dict = {"topic": topic.strip(), "timings": {}, "traces": {}}
    st.session_state["result"] = state
    try:
        # Step 1 – Search agent
        with st.status(
            "Step 1 — Search agent is searching the web…", expanded=True
        ) as s:
            t0 = time.time()
            res = build_search_agent().invoke(
                {
                    "messages": [
                        (
                            "user",
                            f"Find recent, reliable and detailed information about: {state['topic']}",
                        )
                    ]
                }
            )
            state["search_results"] = res["messages"][-1].content
            state["traces"]["search"] = extract_trace(res)
            state["timings"]["Search"] = time.time() - t0
            s.update(
                label=f"Step 1 — Search done ({state['timings']['Search']:.1f}s)",
                state="complete",
                expanded=False,
            )

        # Step 2 – Reader agent
        with st.status(
            "Step 2 — Reader agent is scraping the top source…", expanded=True
        ) as s:
            t0 = time.time()
            res = build_reader_agent().invoke(
                {
                    "messages": [
                        (
                            "user",
                            f"Based on the following search results about '{state['topic']}', "
                            f"pick the most relevant URL and scrape it for deeper content.\n\n"
                            f"Search Results:\n{state['search_results'][:pass_chars]}",
                        )
                    ]
                }
            )
            state["scraped_content"] = res["messages"][-1].content
            state["traces"]["reader"] = extract_trace(res)
            state["timings"]["Reader"] = time.time() - t0
            s.update(
                label=f"Step 2 — Scraping done ({state['timings']['Reader']:.1f}s)",
                state="complete",
                expanded=False,
            )

        # Step 3 – Writer
        with st.status("Step 3 — Writer is drafting the report…", expanded=True) as s:
            t0 = time.time()
            research_combined = (
                f"SEARCH RESULTS : \n {state['search_results']} \n\n"
                f"DETAILED SCRAPED CONTENT : \n {state['scraped_content']}"
            )
            state["report"] = writer_chain.invoke(
                {"topic": state["topic"], "research": research_combined}
            )
            state["timings"]["Writer"] = time.time() - t0
            s.update(
                label=f"Step 3 — Report drafted ({state['timings']['Writer']:.1f}s)",
                state="complete",
                expanded=False,
            )

        # Step 4 – Critic
        with st.status("Step 4 — Critic is reviewing the report…", expanded=True) as s:
            t0 = time.time()
            state["feedback"] = critic_chain.invoke({"report": state["report"]})
            state["timings"]["Critic"] = time.time() - t0
            s.update(
                label=f"Step 4 — Review done ({state['timings']['Critic']:.1f}s)",
                state="complete",
                expanded=False,
            )

    except Exception as e:  # keep partial results visible
        st.error(f"Pipeline stopped: {e}")
        st.exception(e)

# ───────────────────────── results ─────────────────────────
state = st.session_state.get("result")
if state:
    st.divider()
    st.subheader(f"Results — {state['topic']}")

    if state["timings"]:
        cols = st.columns(len(state["timings"]) + 1)
        for col, (name, secs) in zip(cols, state["timings"].items()):
            col.metric(name, f"{secs:.1f}s")
        cols[-1].metric("Total", f"{sum(state['timings'].values()):.1f}s")

    tabs = st.tabs(
        ["📄 Report", "🧐 Critic", "🔍 Search", "📖 Scraped", "🛠️ Agent trace"]
    )

    with tabs[0]:
        if "report" in state:
            st.markdown(state["report"])
            combined = f"# {state['topic']}\n\n{state['report']}"
            if "feedback" in state:
                combined += f"\n\n---\n## Critic review\n\n{state['feedback']}"
            st.download_button(
                "⬇️ Download report (.md)",
                combined,
                file_name="research_report.md",
                mime="text/markdown",
            )
        else:
            st.info("Report not generated yet.")

    with tabs[1]:
        if "feedback" in state:
            score = parse_score(state["feedback"])
            if score:
                st.metric("Critic score", f"{score}/10")
            st.markdown(state["feedback"])
        else:
            st.info("No critic review yet.")

    with tabs[2]:
        st.text(state.get("search_results", "No search results yet."))

    with tabs[3]:
        st.text(state.get("scraped_content", "No scraped content yet."))

    with tabs[4]:
        for key, label in (("search", "Search agent"), ("reader", "Reader agent")):
            if key in state["traces"]:
                st.markdown(f"### {label}")
                render_trace(state["traces"][key], label)
