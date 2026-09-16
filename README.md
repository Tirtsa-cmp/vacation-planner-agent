 Vacation Planner Agent

An AI agent built with the Claude API that plans vacations through a natural, multi-turn conversation — searching destinations and activities within budget, comparing hotels and flights, and generating booking links once a destination is confirmed.

## Features

- **Interactive conversational agent**: chat with the agent in the terminal; it remembers context across turns (destination, budget, preferences) without needing to repeat information
- **Agentic tool-use loop**: the agent decides which tools to call, executes them, and chains multiple calls in sequence without user intervention
- **Five specialized tools**:
  - `search_destinations` — finds destinations that genuinely fit the user's budget per person
  - `search_activities` — suggests activities once a destination is chosen
  - `compare_hotels` — approximate hotel price comparisons for a destination
  - `compare_flights` — approximate flight price comparisons from a departure country
  - `generate_booking_links` — generates real search links to Google Flights, Booking.com, and GetYourGuide, pre-filled with the destination
- **No repeated suggestions**: the agent tracks every destination and activity already mentioned in the conversation and avoids repeating them, even after the user rejects an option or changes direction
- **Structured, code-verified budget tracking**: costs are parsed into structured JSON and tracked in a unified list. Totals are calculated in Python — not estimated by the LLM — and presented to the agent as plain contextual figures to reference
- **Budget-aware recommendations**: when there's significant budget left, the agent proactively suggests upgrades instead of leaving money unused
- **Local knowledge base (RAG)**: a persistent ChromaDB vector database with 50 curated destinations (see `rag_test.py`) — see "Design decisions" for why it's not used in the final budget-critical search
- **Unit tests**: core budget logic (`check_budget`, `add_to_trip_budget`) is covered by tests in `test_budget.py`, independent of any API calls

## Architecture

User (terminal input, ongoing conversation)
|
v
Main agent loop (multi-turn, persistent history)
|
|--- search_destinations --> web search sub-agent (budget-constrained, avoids repeats)
|--- search_activities ----> web search sub-agent (avoids repeats)
|--- compare_hotels -------> web search sub-agent (estimates only)
|--- compare_flights ------> web search sub-agent (estimates only)
|--- generate_booking_links -> direct URL construction (no API call)
|
v
Unified budget tracker (Python-calculated)
|
v
Agent response


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

7. Run the tests:

python test_budget.py


## Design decisions

### Why RAG isn't used for the final budget-critical search
RAG excels at retrieving stable, descriptive knowledge but is a poor fit for time-sensitive data like flight prices. Real-time web search provides more trustworthy numbers for budget-critical features, even though it means the RAG component is somewhat underused in the current flow.

### Why booking links are search links, not real reservations
Actually booking flights/hotels requires paid, authenticated APIs (Amadeus, Booking.com partner API) that aren't accessible for a learning project. Instead, `generate_booking_links` builds real, working search URLs that take the user directly to the relevant search on each platform, where they can see live prices and complete the booking themselves.

### Why hotel/flight comparisons are estimates, not live prices
`compare_hotels` and `compare_flights` use web search, which surfaces already-indexed content rather than live, personalized search results. Prices returned are realistic estimates to guide decision-making, not guaranteed fares — this limitation is stated explicitly in both tool descriptions so the agent communicates it to the user.

### Why budget totals are calculated in Python, not by the LLM
Early versions let Claude estimate totals conversationally, leading to inconsistencies. The current design has Python calculate exact totals from structured tool outputs, presented as plain contextual data for Claude to reference.

## What I learned building this

- Designing tool descriptions that let Claude reliably choose the right tool and communicate a tool's limitations to the user
- Preventing an agent from repeating already-rejected suggestions by explicitly tracking and excluding them in each new search
- The importance of keeping numeric calculations in code rather than trusting an LLM with arithmetic, while letting the LLM handle the natural language reasoning
- Framing a system note as plain contextual data rather than an imperative instruction — an overly forceful "system note" format caused Claude to treat it as suspicious rather than trustworthy
- Writing unit tests for core business logic, independent of the LLM, to catch regressions quickly
- Secure API key handling with `.gitignore` and environment variables, including recovering from an accidental key exposure caught by GitHub Push Protection

## Next steps

- Integrate hotel/flight comparison costs into the unified budget tracker
- Add a simple web interface as an alternative to the terminal
- Explore real booking API integrations (Amadeus, Booking.com partner API) for live prices