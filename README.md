# LangChain Multi-Agent Research System

An AI-powered research assistant that turns a topic into a structured report. A LangChain pipeline searches the web, extracts content from a relevant page, drafts a report, and asks a critic model to review it. The project includes an interactive Streamlit interface and a command-line entry point.

## Features

- Search for recent information with Tavily.
- Scrape and extract readable page content with Trafilatura, Readability, and Beautiful Soup.
- Draft a report with an introduction, key findings, conclusion, and source URLs.
- Review the draft and return a score, strengths, areas to improve, and a verdict.
- View the intermediate search and scraping results in the web interface and download the report as Markdown.

## Requirements

- Python 3.11
- [Ollama](https://ollama.com/) with the `qwen3.5:2b` model available locally
- A [Tavily API key](https://tavily.com/)

## Setup

1. Clone the repository and move into its directory.
2. Create and activate a virtual environment:

   ```powershell
   py -3.11 -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   If PowerShell prevents activation, use `.\.venv\Scripts\python.exe` instead of `python` in the commands below.

3. Install the Python dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Download the Ollama model:

   ```powershell
   ollama pull qwen3.5:2b
   ```

   Make sure the Ollama service is running before starting a research run.

5. Create a `.env` file in the repository root and add your Tavily key:

   ```dotenv
   TAVILY_API_KEY=your_tavily_api_key
   ```

Keep the `.env` file private; do not commit API keys.

## Run the application

Start the interactive Streamlit app:

```powershell
python -m streamlit run app.py
```

Open the local URL printed by Streamlit, enter a research topic, and select **Run Research Pipeline**. The results include the raw search output, extracted page content, the report, and the critic's feedback. Use **Download Report (.md)** to save the report.

To run the command-line pipeline instead:

```powershell
python main.py
```

The CLI currently uses the example topic defined in `main.py` and prints each pipeline stage and its output.

## Research workflow

1. **Search agent** asks Tavily for up to five web results.
2. **Reader agent** selects a relevant URL from the results and extracts page content.
3. **Writer chain** combines the search results and extracted content into a structured report.
4. **Critic chain** reviews the report and provides a score and feedback.

## Project structure

```text
app.py                  Streamlit user interface
main.py                 Command-line example
src\agents\agents.py    Ollama model, agents, and writing/review chains
src\pipelines\pipeline.py
                        Command-line research pipeline
src\tools\tools.py      Tavily search and web-page extraction tools
requirements.txt        Python dependencies
```

## Notes

- The language model runs locally through Ollama; web search requires internet access and a valid Tavily API key.
- Research quality depends on the available search results and the pages that can be accessed and extracted. Review sources and verify important claims before relying on the generated report.
- The project is licensed under the Apache License 2.0; see [LICENSE](LICENSE).
