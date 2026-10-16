import os

os.environ.pop("SSL_CERT_FILE", None)  # must come before the imports below

from src.pipelines.pipeline import run_research_pipeline

topic = "EV impact on fuel economy"

run_research_pipeline(topic)
