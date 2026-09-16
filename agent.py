import os
from dotenv import load_dotenv
import anthropic
import chromadb
import json
import re
import urllib.parse

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
                "budget": {
                    "type": "number",
                    "description": "Total trip budget in USD."
                },
                "num_travelers": {
                    "type": "integer",
                    "description": "Number of people traveling together."
                },
                "preferences": {
                    "type": "string",
                    "description": (
                        "Type of trip desired, e.g. "
                        "'beach', 'city', 'mountains', 'culture'."
                    )
                },
                "country_of_departure": {
                    "type": "string",
                    "description": (
                        "The country from which the travelers will depart. "
                        "Defaults to France if not specified."
                    )
                }
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
            "recommended age range, a short description, its theme "
            "(relaxation, adventure, sports, culture, etc.), and an estimated price."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "description": "The travelers' vacation destination."
                },
                "num_travelers": {
                    "type": "integer",
                    "description": "Number of people traveling together."
                },
                "trip_duration_days": {
                    "type": "integer",
                    "description": "Length of the trip in days."
                }
            },
            "required": ["destination", "num_travelers"]
        }
    },

    # Tool 3: compare_hotels
    {
        "name": "compare_hotels",
        "description": (
            "Search the web for hotel options in a destination and provide indicative "
            "price comparisons. Use this once a destination is confirmed and the user "
            "wants to explore accommodation options. IMPORTANT: prices returned are "
            "approximate estimates based on web search results, not real-time availability "
            "or guaranteed prices — the user must verify final prices directly on a "
            "booking site before purchasing. Returns 2-3 hotel options with estimated "
            "price per night and a brief description."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "description": "The confirmed destination city or region."
                },
                "budget_level": {
                    "type": "string",
                    "description": (
                        "Optional: 'budget', 'mid-range', or 'luxury'."
                    )
                }
            },
            "required": ["destination"]
        }
    },

    # Tool 4: compare_flights
    {
        "name": "compare_flights",
        "description": (
            "Search the web for flight price estimates from a departure country to a "
            "destination. Use this once a destination is confirmed. IMPORTANT: prices "
            "returned are approximate estimates based on general web search results, "
            "not real-time fares — actual prices vary by date, airline, and booking time. "
            "The user must check a flight search engine directly for accurate current prices. "
            "Returns 2-3 approximate price ranges from different airlines or booking approaches."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "description": "The confirmed destination city or region."
                },
                "country_of_departure": {
                    "type": "string",
                    "description": "Departure country."
                },
                "num_travelers": {
                    "type": "integer",
                    "description": "Number of travelers."
                }
            },
            "required": [
                "destination",
                "num_travelers",
                "country_of_departure"
            ]
        }
    },
    {
    "name": "generate_booking_links",
    "description": (
        "Generate search links to booking websites (flights, hotels, activities) "
        "for a specific destination. Use this tool once the user has confirmed "
        "a destination and wants to move toward actually booking the trip. Returns "
        "links to Google Flights, Booking.com, and GetYourGuide pre-filled with the "
        "destination, so the user can search real availability and prices themselves. "
        "These are search links, not confirmed bookings."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "destination": {"type": "string", "description": "The confirmed destination city or region."},
            "country_of_departure": {"type": "string", "description": "Departure country, for flight search context."}
        },
        "required": ["destination"]
    }
}
]


# --- Python functions behind each tool ---
def search_destinations(budget, num_travelers, preferences=None, country_of_departure="France", already_suggested=None):
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
def search_activities(destination, num_travelers, trip_duration_days=None, already_suggested=None):
    """Search the web for activities at a given destination, returning
    structured data with estimated costs per person. Avoids repeating
    activities already suggested earlier in the conversation."""
    
    exclusion_text = ""
    if already_suggested:
        names = ", ".join(already_suggested)
        exclusion_text = (
            f" Do NOT suggest any of these activities again, as they were already "
            f"proposed earlier in this conversation: {names}. Find different options."
        )

    search_prompt = (
        f"Search the web for current activity ideas suitable for "
        f"{num_travelers} travelers in this destination: {destination}."
        + (f" The trip lasts {trip_duration_days} days." if trip_duration_days else "")
        + " Give a short list (2-3 activities)."
        + exclusion_text
        + " Respond ONLY with a valid JSON array, no other text, in this exact format: "
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
def compare_hotels(destination, budget_level=None):
    """Search the web for approximate hotel price comparisons at a destination.
    Returns estimates only — not real-time prices."""
    search_prompt = (
        f"Search the web for 2-3 hotel options in {destination}"
        + (f" in the {budget_level} price range" if budget_level else "")
        + ". For each, give an approximate price per night and a short description. "
        "Respond ONLY with a valid JSON array, no other text, in this exact format: "
        '[{"name": "Hotel Name", "price_per_night_usd": 80, "description": "short description"}]'
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
        hotels = json.loads(cleaned)
    except json.JSONDecodeError:
        hotels = []
    return hotels


def compare_flights(destination, num_travelers, country_of_departure="France"):
    """Search the web for approximate flight price comparisons.
    Returns estimates only — not real-time fares."""
    search_prompt = (
        f"Search the web for approximate flight prices per person from "
        f"{country_of_departure} to {destination} for {num_travelers} travelers. "
        "Give 2-3 price estimates (e.g., budget airline vs. standard carrier). "
        "Respond ONLY with a valid JSON array, no other text, in this exact format: "
        '[{"option": "Budget airline", "price_per_person_usd": 150, "description": "short description"}]'
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
        flights = json.loads(cleaned)
    except json.JSONDecodeError:
        flights = []
    return flights

def generate_booking_links(destination, country_of_departure="France"):
    """Generate generic search links to booking platforms for the given
    destination. These are search URLs, not confirmed bookings."""
    
    encoded_destination = urllib.parse.quote(destination)
    encoded_departure = urllib.parse.quote(country_of_departure)

    links = {
        "flights": f"https://www.google.com/travel/flights?q=Flights%20from%20{encoded_departure}%20to%20{encoded_destination}",
        "hotels": f"https://www.booking.com/searchresults.html?ss={encoded_destination}",
        "activities": f"https://www.getyourguide.com/s/?q={encoded_destination}"
    }

    return links
# --- Interactive main agent loop ---
if __name__ == "__main__":
    print("🌴 Vacation Planner Agent — type 'quit' to exit\n")

    messages = []
    trip_items = []
    all_suggested_destinations = []
    budget_per_person = None

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ["quit", "exit"]:
            print("Goodbye! Have a great trip. ✈️")
            break

        messages.append({"role": "user", "content": user_input})

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
                print(f"\nAgent: {''.join(final_text_parts)}\n")
                break

            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    print(f"[DEBUG] Turn {turn_count}: {block.name} called")
                    if block.name == "search_destinations":
                        result = search_destinations(**block.input, already_suggested=all_suggested_destinations)

                        for item in result:
                            if item.get("name") and item["name"] not in all_suggested_destinations:
                                all_suggested_destinations.append(item["name"])

                        if "budget" in block.input and "num_travelers" in block.input:
                            budget_per_person = block.input["budget"] / block.input["num_travelers"]
                            add_to_trip_budget(trip_items, result, "destination")        
                    elif block.name == "search_activities":
                        result = search_activities(**block.input)
                        add_to_trip_budget(trip_items, result, "activity")
                    elif block.name == "compare_hotels":
                        result = compare_hotels(**block.input)
                    elif block.name == "compare_flights":
                        result = compare_flights(**block.input)
                    elif block.name == "generate_booking_links":
                        result = generate_booking_links(**block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result)
                    })

            budget_status = check_budget(trip_items, budget_per_person)

            items_breakdown = "\n".join(
                f"- {item['name']} ({item['category']}): ${item['cost_per_person_usd']}/person"
                for item in trip_items
            )

            if budget_per_person:
                budget_note = (
                    f"\n\n(Budget tracker — calculated by the app from the tool results above: "
                    f"itemized costs: {items_breakdown if trip_items else 'none yet'}. "
                    f"Total so far: ${budget_status['total_per_person']}/person. "
                    f"User's budget: ${budget_per_person:.0f}/person. "
                    f"Remaining: ${budget_status['remaining']:.0f}/person.)"
                )
            else:
                budget_note = (
                    f"\n\n(Budget tracker: no budget specified by the user yet.)"
                )
            tool_results.append({"type": "text", "text": budget_note})

            messages.append({"role": "user", "content": tool_results})
        else:
            print("\n[WARNING] Max turns reached without a final answer.\n")