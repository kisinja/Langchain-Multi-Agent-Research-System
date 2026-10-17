import os

os.environ.pop("SSL_CERT_FILE", None)

import re
import streamlit as st
from src.agents.agents import build_job_agent

st.set_page_config(page_title="Job Hunter", page_icon="💼", layout="wide")
st.title("💼 Job Hunter Agent")


def parse_jobs(text: str):
    jobs = []
    for block in text.split("\n----\n"):
        t = re.search(r"Title:\s*(.+)", block)
        u = re.search(r"URL:\s*(\S+)", block)
        s = re.search(r"Snippet:\s*(.+)", block, re.S)
        if t and u:
            jobs.append(
                (t.group(1).strip(), u.group(1), s.group(1).strip() if s else "")
            )
    return jobs


query = st.text_input(
    "Roles to look for",
    "Agentic AI engineer or fullstack software developer, Kenya and remote",
)

if st.button("Search jobs", type="primary"):
    with st.status("Agent is searching job boards…", expanded=True) as s:
        res = build_job_agent().invoke(
            {"messages": [("user", f"Find current openings for: {query}")]}
        )
        s.update(label="Done", state="complete", expanded=False)

    # 1) The agent's written summary (may be empty with small models)
    final = (res["messages"][-1].content or "").strip()
    st.subheader("Agent summary")
    if final:
        st.markdown(final)
    else:
        st.warning("The model returned no summary. The raw results are listed below.")

    # 2) Raw listings straight from the search tool (always shown)
    seen, jobs = set(), []
    for m in res["messages"]:
        if getattr(m, "type", "") == "tool" and m.name == "search_jobs":
            for title, url, snippet in parse_jobs(str(m.content)):
                if url not in seen:
                    seen.add(url)
                    jobs.append((title, url, snippet))

    st.subheader(f"Listings found ({len(jobs)})")
    for title, url, snippet in jobs:
        st.markdown(f"**[{title}]({url})**")
        st.caption(snippet[:300])

    with st.expander("Tool calls (debug)"):
        for m in res["messages"]:
            for tc in getattr(m, "tool_calls", None) or []:
                st.json({tc["name"]: tc["args"]})
