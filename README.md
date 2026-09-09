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

## Design decisions

### Why RAG isn't used for the final budget-critical search

The project includes a working RAG pipeline (ChromaDB with 50 curated destinations) and it's fully functional for semantic search — see `rag_search()` and `seed_data.py`. However, the final `search_destinations` tool does **not** use it for the main recommendation flow.

**Reasoning:** RAG excels at retrieving stable, descriptive knowledge (destination vibes, themes, general info) but is a poor fit for time-sensitive, budget-critical data like flight prices, which change constantly and aren't something a static local database can track reliably. For a feature where staying within budget is the core requirement, real-time web search provides more trustworthy numbers than a vector database seeded once with general descriptions.

This is a deliberate tradeoff: I chose data reliability over reusing every technique learned, even though it means the RAG component is somewhat underused in the current flow. It remains available and could be reintroduced as a fast first-pass "inspiration" layer in a future iteration, with web search still handling final price validation.