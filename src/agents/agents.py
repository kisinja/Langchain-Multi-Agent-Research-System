from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.tools.tools import web_search, scrape_url, search_jobs
from dotenv import load_dotenv

load_dotenv()

# Model Initialization
llm = ChatOllama(
    model="qwen3.5:2b",
    temperature=0,
    reasoning=False,  # turns thinking off
    num_predict=300,
)
job_llm = ChatOllama(
    model="qwen3.5:2b",
    temperature=0,
    reasoning=False,  # turns thinking off
    num_predict=1500,
)

# Job search tool prompt
JOB_PROMPT = """You are a job-hunting assistant for a fullstack developer
(Next.js, TypeScript, Prisma, PostgreSQL) moving into agentic AI engineering roles,
open to Kenya (on-site) and remote work abroad.

Rules:
- Call search_jobs at least twice with different queries (e.g. Kenya, remote worldwide).
- Optionally call scrape_url on the 1-2 best listings to get salary and requirements.
- Show salaries in KES per month. If a listing uses another currency or period, show the
  original and an approximate KES/month conversion, noting the rate is approximate.
  If no salary is listed, write "not listed". Never invent salaries.
- Only include URLs that appeared in tool results.
- Output a table: Role | Company | Location/Remote | Salary (KES/month) | Why it fits | URL
"""


# 1st Agent: Search Agent
def build_search_agent():
    return create_agent(model=llm, tools=[web_search])


# 2nd Agent: Reader Agent
def build_reader_agent():
    return create_agent(model=llm, tools=[scrape_url])


# 3rd Agent: Job Search Agent
def build_job_agent():
    return create_agent(model=job_llm, tools=[scrape_url, search_jobs], system_prompt=JOB_PROMPT)


# writer chain

writer_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert research writer. Write clear, structured and insightful reports.",
        ),
        (
            "human",
            """Write a detailed research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Conclusion
- Sources (list all URLs found in the research)

Be detailed, factual and professional.""",
        ),
    ]
)

writer_chain = writer_prompt | llm | StrOutputParser()


# critic_chain

critic_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a sharp and constructive research critic. Be honest and specific.",
        ),
        (
            "human",
            """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
...""",
        ),
    ]
)

critic_chain = critic_prompt | llm | StrOutputParser()
