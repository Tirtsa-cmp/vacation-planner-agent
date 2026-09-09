# Vacation Planner Agent

An AI agent built with the Claude API that plans vacations by orchestrating multiple tools — destination search, activity search, and budget tracking — through a natural, multi-turn conversation.

## Features

- **Interactive conversational agent**: chat with the agent in the terminal; it remembers context across turns (destination, budget, preferences) without needing to repeat information
- **Agentic tool-use loop**: the agent decides which tools to call, executes them, and synthesizes responses — including chaining multiple tool calls in sequence (e.g., destination search followed by activity search) without user intervention
- **Two specialized tools**:
  - `search_destinations` — finds destinations that genuinely fit the user's budget per person, returning structured cost data
  - `search_activities` — suggests activities once a destination is chosen, with structured per-person costs
- **Structured, code-verified budget tracking**: every cost returned by tools is parsed into structured JSON and tracked in a single unified list (`trip_items`). The running total, remaining budget, and status are calculated in Python — not estimated by the LLM — and injected into the conversation as exact figures the agent must reference rather than recalculate
- **Budget-aware recommendations**: when there's significant budget left, the agent proactively suggests upgrades (better accommodation, premium activities, private guides) instead of leaving money unused
- **Local knowledge base (RAG)**: a persistent ChromaDB vector database with 50 curated destinations, fully functional for semantic search (see `rag_test.py`) — see "Design decisions" below for why it's not used in the final budget-critical flow
- **Sub-agent pattern**: each tool internally makes its own Claude API call with web search, keeping the main agent's logic modular
- **Robust JSON parsing**: tool outputs are cleaned and extracted via regex before parsing, with graceful fallback if the LLM's output isn't perfectly formatted

## Architecture

User (terminal input)
|
v
Main agent loop (multi-turn, persistent conversation history)
|
|--- search_destinations ---> web search sub-agent (budget-constrained query)
|
|--- search_activities -----> web search sub-agent
|
v
Unified budget tracker (Python-calculated, injected as exact figures)
|
v
Agent response (references exact totals, suggests upgrades if budget allows)


## Tech stack

- Python 3.14
- Anthropic API (Claude Sonnet 5) — tool use, web search
- ChromaDB — local vector database (RAG component)
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


5. (Optional) Seed the vector database, used by the standalone RAG demo:

python seed_data.py


6. Run the interactive agent:

python agent.py

   Type your travel request, chat naturally with the agent, and type `quit` to exit.

## Design decisions

### Why RAG isn't used for the final budget-critical search

The project includes a working RAG pipeline (ChromaDB with 50 curated destinations) and it's fully functional for semantic search. However, the final `search_destinations` tool does not use it for the main recommendation flow.

**Reasoning:** RAG excels at retrieving stable, descriptive knowledge but is a poor fit for time-sensitive, budget-critical data like flight prices. For a feature where staying within budget is the core requirement, real-time web search provides more trustworthy numbers than a vector database seeded once with general descriptions. This is a deliberate tradeoff: prioritizing data reliability over reusing every technique learned.

### Why budget totals are calculated in Python, not by the LLM

Early versions let Claude estimate total costs conversationally, which led to inconsistencies (e.g., summing costs from multiple explored-but-not-chosen destinations, or minor arithmetic drift). The current design has Python calculate exact totals from structured tool outputs, then instructs Claude to reference — not recompute — these figures. This makes the budget tracking reliable regardless of the LLM's own arithmetic.

### Why only one destination is counted toward the budget

When `search_destinations` returns multiple options, only the cheapest is added to the running budget total — since the user will ultimately book just one. Any previously tracked destination is replaced (not accumulated) each time a new search is performed.

## What I learned building this

- Designing tool descriptions that let Claude reliably choose the right tool and ask for missing required information instead of guessing
- The limits of pure vector similarity search on a small corpus, and how enriching the dataset improved retrieval accuracy
- Knowing when *not* to use a technique (RAG) even after implementing it, based on the actual requirements of the feature
- Building a multi-turn agentic loop (`while` loop with turn limits) instead of a single request/response cycle, to support tool chaining and ongoing conversations
- Keeping numeric calculations in code rather than trusting an LLM to do arithmetic reliably, while still letting the LLM handle the natural language reasoning around those numbers
- Secure API key handling with `.gitignore` and environment variables, including recovering from an accidental key exposure caught by GitHub Push Protection

## Next steps

- Avoid near-duplicate activity suggestions across multiple search calls within the same conversation
- Add automated tests for core functions (`search_destinations`, `search_activities`, `check_budget`)
- Add a simple web interface as an alternative to the terminal
- Add a `search_flights` / `search_hotels` tool for more granular cost breakdowns