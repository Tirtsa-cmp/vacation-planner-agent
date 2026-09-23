# Vacation Planner Agent

An AI agent built with the Claude API that plans vacations through a natural, multi-turn conversation — searching destinations and activities within budget, comparing hotels and flights, and generating real booking search links. Accessible via a Flask API and a connected HTML/CSS/JS frontend.

## Features

- **Full-stack application**: Python/Flask backend exposing the agent via a REST API, consumed by an HTML/CSS/JS frontend chat interface
- **Interactive conversational agent**: chat naturally; the agent remembers context across turns (destination, budget, preferences) without needing to repeat information
- **Per-session memory**: each browser session gets a unique ID (generated client-side and stored in `sessionStorage`), keeping conversations isolated from one another — no cross-contamination between different planning sessions
- **Agentic tool-use loop**: the agent decides which tools to call, executes them, and chains multiple calls in sequence without user intervention
- **Six specialized tools**:
  - `search_destinations` — finds destinations that genuinely fit the user's budget per person, always including any destination the user explicitly requested (even if over budget, with the gap clearly explained)
  - `search_activities` — suggests activities once a destination is chosen
  - `compare_hotels` — approximate hotel price comparisons for a destination
  - `compare_flights` — approximate flight price comparisons from a departure country
  - `generate_booking_links` — generates real, clickable search links (Google Flights, Booking.com, GetYourGuide, Trainline) either generically for a destination or targeted at a specific confirmed choice (a named hotel, airline, train route, or activity)
- **Proactive link generation**: as soon as a destination, flight, hotel, or activity is confirmed, the agent generates its booking link automatically, without waiting to be asked
- **Streamlined destination-to-booking flow**: once a destination is chosen, the agent automatically compares flights and hotels and generates links in the same response, rather than requiring multiple back-and-forth confirmations
- **Flexible dates**: accepts free-text date descriptions (e.g., "sometime in July", "the last weekend of November") instead of requiring exact dates
- **No repeated suggestions**: the agent tracks every destination and activity already mentioned and avoids repeating them, even after the user rejects an option
- **Structured, code-verified budget tracking**: costs are parsed into structured JSON and tracked in a unified list; totals are calculated in Python and presented to the agent as plain contextual data to reference, not recalculate
- **Local knowledge base (RAG)**: a persistent ChromaDB vector database with 50 curated destinations (see `rag_test.py`) — see "Design decisions" for why it's not used in the final budget-critical search
- **Unit tests**: core budget logic (`check_budget`, `add_to_trip_budget`) is covered by tests in `test_budget.py`, independent of any API calls

## Architecture

Browser (HTML/CSS/JS chat UI)
|
| fetch POST /chat { message, session_id }
v
Flask API (app.py)
|
v
Main agent loop (multi-turn, per-session history)
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
JSON response { response: "..." }
|
v
Frontend renders formatted message (bold text, clickable booking-link buttons)


## Tech stack

- **Backend**: Python 3.14, Flask, Flask-CORS
- **AI**: Anthropic API (Claude Sonnet 5) — tool use, web search
- **Frontend**: HTML, CSS, vanilla JavaScript (fetch API)
- **Data**: ChromaDB (local vector database, RAG component)
- python-dotenv — secure API key management

## Setup

### Backend

1. Clone the repo and navigate to it:

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


6. Start the Flask API:

python app.py

   The API runs on `http://localhost:5000`.

### Frontend

Open the HTML file (e.g. `planner.html`) directly in a browser, or serve it with a simple local server (e.g. VS Code's Live Server extension). Make sure the Flask API is running first — the frontend calls `http://localhost:5000/chat`.

### Running the terminal version (alternative to the web UI)

python agent.py

Type your travel request, chat naturally with the agent, and type `quit` to exit.

### Running the tests

python test_budget.py


## Design decisions

### Why RAG isn't used for the final budget-critical search
RAG excels at retrieving stable, descriptive knowledge but is a poor fit for time-sensitive data like flight prices. Real-time web search provides more trustworthy numbers for budget-critical features, even though it means the RAG component is somewhat underused in the current flow.

### Why booking links are search links, not real reservations
Actually booking flights/hotels requires paid, authenticated APIs (Amadeus, Booking.com partner API) that aren't accessible for a learning project. Instead, `generate_booking_links` builds real, working search URLs that take the user directly to the relevant search on each platform, pre-filled with the destination, dates, traveler count, and specific choice when available.

### Why hotel/flight comparisons are estimates, not live prices
`compare_hotels` and `compare_flights` use web search, which surfaces already-indexed content rather than live, personalized search results. Prices returned are realistic estimates to guide decision-making, not guaranteed fares — this limitation is stated explicitly in both tool descriptions.

### Why budget totals are calculated in Python, not by the LLM
Early versions let Claude estimate totals conversationally, leading to inconsistencies (double-counting explored-but-unchosen options, arithmetic drift). The current design calculates exact totals in Python from structured tool outputs, and presents them to Claude as plain factual context rather than an imperative instruction — an earlier, more forceful "system note" format caused Claude to treat the data as suspicious rather than trustworthy.

### Why each browser session gets its own ID
Early versions used a hardcoded session ID, which caused conversation history (and budget context) to leak between unrelated planning sessions. Each page load now generates a unique ID via `crypto.randomUUID()`, stored in `sessionStorage`, keeping conversations properly isolated.

## Known limitations

- Session data is stored in memory on the server; restarting the Flask app clears all active conversations
- Flight and hotel price estimates are approximate and must be verified on the actual booking site
- Train booking links point to a generic search page, not a pre-filled itinerary, since no train-specific search API is integrated
- No user authentication or persistent storage across browser sessions

## What I learned building this

- Designing tool descriptions that let Claude reliably choose the right tool, include a user's explicit request even when it doesn't fit constraints, and communicate a tool's limitations to the user
- Preventing an agent from repeating already-rejected suggestions by explicitly tracking and excluding them
- The importance of keeping numeric calculations in code rather than trusting an LLM with arithmetic
- Framing contextual data as neutral information rather than an imperative instruction, to avoid the model treating it as suspicious
- Debugging a full-stack integration: matching parameter names between tool schemas and Python functions, keeping frontend and backend session identifiers in sync, and tracing errors across browser console, server logs, and API responses
- Writing unit tests for core business logic, independent of the LLM
- Secure API key handling with `.gitignore` and environment variables, including recovering from an accidental key exposure caught by GitHub Push Protection

## Next steps

- Persist sessions in a real datastore (Redis/PostgreSQL) instead of in-memory storage
- Integrate hotel/flight comparison costs into the unified budget tracker
- Explore real booking API integrations (Amadeus, Booking.com partner API) for live prices
- Dockerize and deploy the application (planned next project, focused on MLOps)