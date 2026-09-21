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
            "Returns a short list of 3 candidates destinations : Do not select only one destination."
"For each destination, include:"
"-destination name and country"
"- why it matches the user's preferences and travel style"
"- the atmosphere/style of the destination"
"- suggested 3-5 activities"
"- estimated cost per person."
           "If the user mentions a specific destination, include it among the 3 recommendations when relevant, but still provide alternatives."
           "Do not rank destinations or select a preferred option. "
"The user must decide which destination to continue with."
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
                "origin_city": {
                    "type": "string",
                    "description": (
                        "The city from which the travelers will depart. "
                        "Defaults to Paris if not specified."
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
            "Search the web for approximate flight price estimates from a departure city "
            "to a destination city. Use this once a destination is confirmed. IMPORTANT: prices "
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
                "origin_city": {
                    "type": "string",
                    "description": "Departure city."
                },
                "num_travelers": {
                    "type": "integer",
                    "description": "Number of travelers."
                },
              
            },
            "required": [
                "destination",
                "num_travelers",
                "origin_city"
            ]
        }
    },
    {
    "name": "generate_booking_links",
    "description": (
        "Generate search links to booking websites for a confirmed trip. "
        "Use this tool once the user has confirmed a destination and wants "
        "to see real booking/search options. Include the departure city, "
        "travel dates (exact or flexible), and number of travelers when available. "
        "Returns search links for flights, hotels, and activities. "
        "These are search links, not confirmed bookings."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "destination": {
                "type": "string",
                "description": "The confirmed destination city or region."
            },
            "origin_city": {
                "type": "string",
                "description": "Departure city chosen by the traveler, for example Paris, Lyon, Marseille."
            },
            "travelers": {
                "type": "integer",
                "description": "Number of travelers."
            },
            "specific_choice": {
                "type": "string",
                "description": "The specific hotel name, airline, or activity name the user confirmed. Omit if generating generic search links."
            },
            "item_type": {
                "type": "string",
                "description": "Type of the specific choice: 'flight', 'hotel', or 'activity'. Required if specific_choice is given."
            },
            "travel_dates": {
                "type": "string",
                "description": (
                    "Travel dates or date flexibility, as the user described it — e.g. "
                    "'2026-07-10 to 2026-07-15', 'anytime in July', 'a week around August 10th, "
                    "flexible by 2 days'. Pass the user's description as-is, do not force exact dates."
                )
            }
        },
        "required": ["destination"]
    }

}
]


# --- Python functions behind each tool ---
def search_destinations(budget, num_travelers, preferences=None, origin_city="Paris", already_suggested=None):
    """Search for vacation destinations based on the user's preferences, desired atmosphere, budget, number of travelers, and constraints.

The goal is to help the user compare options, not to choose for them.

Rules:
- Always return exactly 3 different destination options.
- Never select a winner or give a final recommendation.
- Never say "my recommendation", "the best choice", "I would choose", or similar phrases.
- End by asking the user which destination they want to select.

Handling explicit destinations:
- If the user mentions a destination as inspiration or an example (for example: "like Venice", "similar to Paris", "such as Bali"), treat it as a strong preference.
- Always include that mentioned destination as one of the 3 options.
- Do not remove it only because another destination is cheaper.
- Use the other 2 options as alternatives with a similar atmosphere.

Recommendation priority:
1. Respect destinations explicitly mentioned by the user.
2. Match the requested travel style and atmosphere.
3. Check compatibility with the budget.
4. Suggest budget adjustments only if necessary.

For each destination provide:
- Destination name and country
- Why it matches the user's request
- Atmosphere / travel style
- 3-5 relevant activities
- Estimated cost

Do not optimize only for the cheapest destination."""
    
    budget_per_person = budget / num_travelers
    
    query = f"vacation destination for {preferences or 'general'} trip"
    rag_result = rag_search(query)
    
    cost_prompt = (
        f"Search the web for 3 vacation destinations suitable for "
        f"{num_travelers} travelers departing from {origin_city}, "
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
def compare_flights(destination, origin_city, num_travelers):
    """
    Search approximate flight price estimates.
    These are estimates, not real-time booking prices.
    """

    search_prompt = (
        f"Search the web for realistic, current flight prices per person from "
        f"{origin_city} to {destination} for {num_travelers} travelers. "
        f"Consider that prices vary significantly by season and demand — if this "
        f"is around a holiday period, prices are typically higher than average. "
        f"Give 2-3 realistic price estimates based on actual current airline "
        f"pricing patterns, not outdated or unusually low fares. "
        "Respond ONLY with a valid JSON array in this format: "
        '[{"option": "Budget airline", '
        '"price_per_person_usd": 150, '
        '"description": "short description"}]'
    )

    sub_response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1000,
        tools=[
            {
                "type": "web_search_20250305",
                "name": "web_search"
            }
        ],
        messages=[
            {
                "role": "user",
                "content": search_prompt
            }
        ]
    )

    text_parts = [
        block.text
        for block in sub_response.content
        if block.type == "text"
    ]

    raw_text = "\n".join(text_parts)

    cleaned = (
        raw_text
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )

    match = re.search(r'\[.*\]', cleaned, re.DOTALL)

    if match:
        cleaned = match.group(0)

    try:
        flights = json.loads(cleaned)
    except json.JSONDecodeError:
        flights = []

    return flights

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
{
    "name": "compare_flights",
    "description": (
        "Search the web for approximate flight price estimates from a departure city "
        "to a destination city. Use this once a destination is confirmed. IMPORTANT: "
        "prices returned are approximate estimates based on general web search results, "
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
            "origin_city": {
                "type": "string",
                "description": "The departure city, for example Paris."
            },
            "num_travelers": {
                "type": "integer",
                "description": "Number of travelers."
            }
        },
        "required": [
            "destination",
            "origin_city",
            "num_travelers"
        ]
    }
},
def generate_booking_links(
    destination,
    origin_city="Paris",
    travelers=1,
    specific_choice=None,
    item_type=None,
    travel_dates=None
):
    """Generate search links for flights, hotels and activities.
    If specific_choice and item_type are given, generates one targeted link
    for that specific hotel/flight/activity instead of generic destination links.
    These are search links, not confirmed bookings."""

    encoded_destination = urllib.parse.quote(destination)
    encoded_departure = urllib.parse.quote(origin_city)
    dates_text = f"%20{urllib.parse.quote(travel_dates)}" if travel_dates else ""
    travelers_text = f"%20for%20{travelers}%20travelers" if travelers else ""

    if specific_choice and item_type:
        encoded_choice = urllib.parse.quote(specific_choice)

        if item_type == "hotel":
            link = (
                f"https://www.booking.com/searchresults.html"
                f"?ss={encoded_choice}%20{encoded_destination}{dates_text}"
            )
        elif item_type == "flight":
            link = (
                f"https://www.google.com/travel/flights"
                f"?q=Flights%20from%20{encoded_departure}%20to%20{encoded_destination}"
                f"%20{encoded_choice}{travelers_text}{dates_text}"
            )
        elif item_type == "activity":
            link = (
                f"https://www.getyourguide.com/s/"
                f"?q={encoded_choice}%20{encoded_destination}"
            )
        else:
            link = f"https://www.google.com/search?q={encoded_choice}%20{encoded_destination}"

        return {
            "item_type": item_type,
            "specific_choice": specific_choice,
            "link": link
        }

    # Fallback: generic links for all three categories (no specific choice given)
    links = {
        "flights": (
            f"https://www.google.com/travel/flights"
            f"?q=Flights%20from%20{encoded_departure}%20to%20{encoded_destination}"
            f"{travelers_text}{dates_text}"
        ),
        "hotels": (
            f"https://www.booking.com/searchresults.html"
            f"?ss={encoded_destination}{dates_text}"
        ),
        "activities": (
            f"https://www.getyourguide.com/s/"
            f"?q={encoded_destination}"
        )
    }
    return links
def extract_budget_from_text(text):
    """
    Extract total budget and traveler count from free text.

    Examples:
    "$2000 budget for 2 travelers" -> (2000, 2)
    "budget 700$ for 2 people" -> (700, 2)

    Returns (None, None) if unclear.
    """

    # Look specifically for money amounts
    budget_match = re.search(
        r'(?:budget|total|around|about|of)?\s*\$?\s*(\d{3,6})\s*(?:\$|usd|dollars)?',
        text,
        re.IGNORECASE
    )

    travelers_match = re.search(
        r'(\d+)\s*(?:travelers?|people|persons?|pax)',
        text,
        re.IGNORECASE
    )

    budget = int(budget_match.group(1)) if budget_match else None
    travelers = int(travelers_match.group(1)) if travelers_match else None

    return budget, travelers
# --- Interactive main agent loop ---
SYSTEM_PROMPT = (
    "You are a vacation planning assistant. You can search for destination ideas "
    "even with partial information (e.g., just a budget and vague preferences) — "
    "don't block progress waiting for every detail. However, when you DO need to "
    "ask the user for missing information, batch related questions together in "
    "a single message rather than asking one at a time across multiple turns. "
    "For dates, always accept flexible descriptions (e.g., 'sometime in July', "
    "'a week around August 10th') rather than requiring exact dates.\n\n"
    "IMPORTANT — streamlined flow: after presenting 3 destination options, as "
    "soon as the user names their chosen destination, immediately call "
    "compare_flights and compare_hotels for it in the same turn, THEN "
    "IMMEDIATELY call generate_booking_links using the cheapest reasonable "
    "flight and hotel option found — do this in the SAME response, without "
    "waiting for the user to confirm dates or ask for links separately. If "
    "exact dates are unknown, generate the links anyway with dates omitted or "
    "marked as flexible — links can always be refined later. Present the final "
    "links directly, along with a brief cost summary, in one complete answer."
)
if __name__ == "__main__":
    print("🌴 Vacation Planner Agent — type 'quit' to exit\n")

    messages = []
    trip_items = []
    all_suggested_destinations = []
    budget_per_person = None
    selected_destination = None
    while True:
        user_input = input("You: ").strip()
        if not user_input:
            print("Please enter a message.\n")
            continue
        if user_input.lower() in ["quit", "exit"]:
            print("Goodbye! Have a great trip. ✈️")
            break

        # Best-effort: capture budget mentioned directly by the user, even if no
        # tool call happens to set it explicitly
        extracted_budget, extracted_travelers = extract_budget_from_text(user_input)
        if extracted_budget and extracted_travelers and budget_per_person is None:
            budget_per_person = extracted_budget / extracted_travelers
            print(
f"[DEBUG] Extracted total budget: ${extracted_budget}, "
f"travelers: {extracted_travelers}, "
f"budget/person: ${budget_per_person:.0f}"
)
        # Detect if user selected one of the suggested destinations
        for destination in all_suggested_destinations:
            if destination.lower() in user_input.lower():
                selected_destination = destination
                print(f"[DEBUG] Selected destination: {selected_destination}")
                break

        messages.append({"role": "user", "content": user_input})
        if user_input.lower() in ["quit", "exit"]:
            print("Goodbye! Have a great trip. ✈️")
            break


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
                            #add_to_trip_budget(trip_items, result, "destination")        
                    elif block.name == "search_activities":
                        result = search_activities(**block.input)
                        add_to_trip_budget(trip_items, result, "activity")
                    elif block.name == "compare_hotels":
                        result = compare_hotels(**block.input)
                        add_to_trip_budget(trip_items, result, "hotel")

                    elif block.name == "compare_flights":
                        result = compare_flights(**block.input)
                        add_to_trip_budget(trip_items, result, "flight")

                    elif block.name == "generate_booking_links":
                        result = generate_booking_links(**block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result)
                    })
            print(f"[DEBUG] budget_per_person: {budget_per_person}, trip_items: {trip_items}")
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