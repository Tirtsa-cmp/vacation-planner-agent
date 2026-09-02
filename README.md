Voici le contenu complet à copier-coller directement dans ton fichier README.md :

markdown
# Vacation Planner Agent

An AI agent built with the Claude API that plans vacations by orchestrating multiple tools — destination search, activity search, and a local knowledge base — based on budget, number of travelers, and preferences.

## Features

- **Agentic tool-use loop**: the agent decides which tools to call, executes them, and synthesizes a final response
- **Two specialized tools**:
  - `search_destinations` — suggests destinations matching budget, travelers, and preferences
  - `search_activities` — suggests activities once a destination is chosen
- **Hybrid RAG + web search**: each tool first checks a local Chroma vector database (50 curated destinations) for fast, reliable answers, and falls back to a live web search when nothing relevant is found locally
- **Sub-agent pattern**: each tool internally makes its own Claude API call with web search, keeping the main agent's logic clean and modular

## Architecture

User request
|
v
Main agent (Claude + tool definitions)
|
|--- search_destinations ---> RAG (Chroma) --> fallback: web search sub-agent
|
|--- search_activities -----> web search sub-agent
|
v
Final synthesized response


## Tech stack

- Python 3.14
- Anthropic API (Claude Sonnet 5) — tool use, web search
- ChromaDB — local vector database for RAG
- python-dotenv — secure API key management

## Setup

1. Clone the repo:

git clone https://github.com/Tirtsa-cmp/vacation-planner-agent.git
cd vacation-planner-agent


2. Create and activate a virtual environment:

python -m venv venv
venv\Scripts\activate


3. Install dependencies:

pip install -r requirements.txt


4. Add your Anthropic API key in a `.env` file:

ANTHROPIC_API_KEY=your_key_here


5. Seed the vector database (one-time step):

python seed_data.py


6. Run the agent:

python agent.py


## What I learned building this

- How to design tool descriptions that let Claude reliably choose the right tool and ask for missing required information instead of guessing
- The limits of pure vector similarity search on a small corpus, and how enriching the dataset improved retrieval accuracy
- How to combine a local knowledge base (RAG) with live web search as a fallback, balancing speed/cost against coverage
- Secure API key handling with `.gitignore` and environment variables, including recovering from an accidental key exposure caught by GitHub Push Protection

## Next steps

- Add a search_flights / search_hotels tool
- Improve retrieval with reranking or query expansion
- Add a simple CLI or web interface