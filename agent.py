import os
import re
from dotenv import load_dotenv
import anthropic
import chromadb
import json

load_dotenv()  # Load environment variables from the .env file

# Create the Anthropic client using the API key stored in the environment variable
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))



# Persistent Chroma client, using the same folder as rag_test.py
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="destinations")
# --- Definition of the tools ---
tools = [
    # Tool 1: search_destinations
    {
        "name": "search_destinations",
        "description": (
            "Search for vacation destinations that match a given budget, "
            "number of travelers, and trip preferences (e.g. beach, city, "
            "mountains, culture). Use this tool whenever the user asks for "
            "destination ideas or wants help choosing where to go on vacation. "
            "Do not use this tool if the user already knows their destination "
            "and only needs help with flights, hotels, or activities. "
            "Returns a short list of candidate destinations with an estimated "
            "cost range and a brief reason why each fits the criteria."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "budget": {"type": "number", "description": "Total trip budget in USD."},
                "num_travelers": {"type": "integer", "description": "Number of people traveling together."},
                "preferences": {"type": "string", "description": "Type of trip desired, e.g. 'beach', 'city', 'mountains', 'culture'."},
                "country_of_departure": {"type": "string", "description": "The country from which the travelers will depart. efaults to France if not specified."}
            },
            "required": ["budget", "num_travelers"]
        }
    },
    # Tool 2: search_activities
    {
        "name": "search_activities",
        "description": (
            "Search for activities that travelers can do at their vacation destination, "
            "to maximize their enjoyment during the trip. Use this tool once a destination "
            "has already been chosen, and only if the travelers seem interested in activities "
            "and the budget allows for it. Do not use this tool if the travelers only want "
            "flights/hotels or haven't decided on a destination yet. "
            "Returns a list of suggested activities, each with the activity name, "
            "recommended age range, a short description, its theme (relaxation, adventure, "
            "sports, culture, etc.), and an estimated price."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "destination": {"type": "string", "description": "The travelers' vacation destination."},
                "num_travelers": {"type": "integer", "description": "Number of people traveling together."},
                "trip_duration_days": {"type": "integer", "description": "Length of the trip in days."}
            },
            "required": ["destination", "num_travelers"]
        }
    }
]


# --- Python functions behind each tool ---
def search_destinations(budget, num_travelers, preferences=None, country_of_departure="France"):
    """Search for vacation destinations that fit within the given budget,
    number of travelers, and preferences."""
    
    budget_per_person = budget / num_travelers
    
    query = f"vacation destination for {preferences or 'general'} trip"
    rag_result = rag_search(query)
    
    cost_prompt = (
        f"Search the web for 3 vacation destinations suitable for "
        f"{num_travelers} travelers departing from {country_of_departure}, "
        f"where the TOTAL cost per person (flight + accommodation + food for a "
        f"typical short trip) realistically fits within ${budget_per_person:.0f} per person. "
        + (f"Focus on {preferences} trips. " if preferences else "")
        + "Only suggest destinations that genuinely fit this budget — do not suggest "
        "luxury or expensive options that would exceed it. "
        "Respond ONLY with a valid JSON array of exactly 3 destinations, no other text, "
        "in this exact format: "
        '[{"name": "Destination Name", "flight_cost_per_person_usd": 400, '
        '"cost_per_person_usd": 900, "description": "short description"}]'
    )

    sub_response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1500,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": cost_prompt}]
    )
    text_parts = [block.text for block in sub_response.content if block.type == "text"]
    raw_text = "\n".join(text_parts)
    cleaned = raw_text.replace("```json", "").replace("```", "").strip()

    match = re.search(r'\[.*\]', cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)

    try:
        destinations = json.loads(cleaned)
    except json.JSONDecodeError:
        destinations = []

    return destinations
def search_activities(destination, num_travelers, trip_duration_days=None):
    """Search the web for activities at a given destination, returning
    structured data with estimated costs per person."""
    search_prompt = (
        f"Search the web for current activity ideas suitable for "
        f"{num_travelers} travelers in this destination: {destination}."
        + (f" The trip lasts {trip_duration_days} days." if trip_duration_days else "")
        + " Give a short list (2-3 activities). "
        "Respond ONLY with a valid JSON array, no other text, in this exact format: "
        '[{"name": "Activity Name", "cost_per_person_usd": 50, "description": "short description"}]'
    )

    sub_response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": search_prompt}]
    )

    text_parts = [block.text for block in sub_response.content if block.type == "text"]
    raw_text = "\n".join(text_parts)
    cleaned = raw_text.replace("```json", "").replace("```", "").strip()

    match = re.search(r'\[.*\]', cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)

    try:
        activities = json.loads(cleaned)
    except json.JSONDecodeError:
        activities = []
        print(f"[DEBUG] Failed to parse activities from cleaned text: {cleaned}")
    else:
        print(f"[DEBUG] Final parsed activities: {activities}")

    return activities  

def rag_search(query, n_results=2, distance_threshold=1.0):
    """Search the local Chroma vector database for relevant destination info.
    Returns matching text if results are close enough, otherwise returns None."""
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )

    documents = results["documents"][0]
    distances = results["distances"][0]

    # Keep only results that are close enough to be considered relevant
    relevant_docs = [
        doc for doc, dist in zip(documents, distances)
        if dist < distance_threshold
    ]

    if relevant_docs:
        return "\n".join(relevant_docs)
    return None

def add_to_trip_budget(trip_items, new_items, category):
    """Add cost items to the running trip budget tracker.
    For destinations, only the cheapest option is counted (since the user
    will pick just one). For activities, all items are added since the
    user may do several."""
    if category == "destination" and new_items:
        # Remove any previously tracked destination (only keep the latest search)
        trip_items[:] = [item for item in trip_items if item["category"] != "destination"]
        cheapest = min(new_items, key=lambda d: d.get("cost_per_person_usd", float("inf")))
        trip_items.append({
            "category": "destination",
            "name": cheapest.get("name", "Unknown"),
            "cost_per_person_usd": cheapest.get("cost_per_person_usd")
        })
    else:
        for item in new_items:
            cost = item.get("cost_per_person_usd")
            if cost is not None:
                trip_items.append({
                    "category": category,
                    "name": item.get("name", "Unknown"),
                    "cost_per_person_usd": cost
                })
    return trip_items 


def check_budget(trip_items, budget_per_person):
    """Calculate the total cost so far and compare it to the budget."""
    total = sum(item["cost_per_person_usd"] for item in trip_items)
    return {
        "total_per_person": total,
        "within_budget": total <= budget_per_person if budget_per_person else None,
        "remaining": (budget_per_person - total) if budget_per_person else None
    }
# --- Main agent loop ---
messages = [
    {"role": "user", "content": "We want a lovely 3-day beach trip, budget $2500, 2 travelers, love beaches. Pick the best destination for us and then suggest activities there too, all in one go."}
]

trip_items = []       # unified list of all costed items (destinations AND activities)
budget_per_person = None
max_turns = 5
turn_count = 0

while turn_count < max_turns:
    turn_count += 1

    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=2000,
        tools=tools,
        messages=messages
    )

    messages.append({"role": "assistant", "content": response.content})

    if response.stop_reason != "tool_use":
        final_text_parts = [block.text for block in response.content if block.type == "text"]
        print("\n--- Final response ---")
        print("\n".join(final_text_parts))
        print(f"\n[DEBUG] Trip items: {trip_items}")
        break

    tool_results = []

    for block in response.content:
        if block.type == "tool_use":
            print(f"[DEBUG] Turn {turn_count}: {block.name} called")

            if block.name == "search_destinations":
                result = search_destinations(**block.input)
                if "budget" in block.input and "num_travelers" in block.input:
                    budget_per_person = block.input["budget"] / block.input["num_travelers"]
                add_to_trip_budget(trip_items, result, "destination")

            elif block.name == "search_activities":
                result = search_activities(**block.input)
                add_to_trip_budget(trip_items, result, "activity")

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result)
            })

    # Single, unified budget check based on everything accumulated so far
    budget_status = check_budget(trip_items, budget_per_person)
    budget_note = (
        f"\n\n[SYSTEM NOTE: Running total so far: ${budget_status['total_per_person']}/person. "
        + (
            f"Budget: ${budget_per_person:.0f}/person. "
            f"{'Within budget' if budget_status['within_budget'] else 'OVER budget'} "
            f"(${budget_status['remaining']:.0f} remaining)."
            if budget_per_person else "No budget specified yet."
        )
        + " Take this into account for your response.]"
    )
    tool_results.append({"type": "text", "text": budget_note})

    messages.append({"role": "user", "content": tool_results})
else:
    print("\n[WARNING] Max turns reached without a final answer.")