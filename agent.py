import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# --- Définition des outils ---
tools = [
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
                "preferences": {"type": "string", "description": "Type of trip desired, e.g. 'beach', 'city', 'mountains', 'culture'."}
            },
            "required": ["budget", "num_travelers"]
        }
    },
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

# --- Fonctions Python derrière chaque outil ---
def search_destinations(budget, num_travelers, preferences=None):
    search_prompt = (
        f"Search the web for current vacation destination ideas suitable for "
        f"{num_travelers} travelers with a total budget of ${budget}"
        + (f", focused on {preferences} trips." if preferences else ".")
        + " Give a short list (2-3 destinations) with an approximate cost per person "
        "and one sentence explaining why each fits."
    )
    sub_response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": search_prompt}]
    )
    text_parts = [block.text for block in sub_response.content if block.type == "text"]
    return "\n".join(text_parts)


def search_activities(destination, num_travelers, trip_duration_days=None):
    search_prompt = (
        f"Search the web for current activity ideas suitable for "
        f"{num_travelers} travelers in this destination: {destination}."
        + (f" The trip lasts {trip_duration_days} days." if trip_duration_days else "")
        + " Give a short list (2-3 activities) with an approximate cost per person "
        "and one sentence explaining why each fits."
    )
    sub_response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": search_prompt}]
    )
    text_parts = [block.text for block in sub_response.content if block.type == "text"]
    return "\n".join(text_parts)


# --- Boucle agentique principale ---
messages = [
    {"role": "user", "content": "We're going to Cancun for 5 days with 2 people, budget $3000. Suggest some activities for us."}
]

response = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=1000,
    tools=tools,
    messages=messages
)

print("--- First response ---")
print(response.content)
print("Stop reason:", response.stop_reason)

messages.append({"role": "assistant", "content": response.content})

if response.stop_reason == "tool_use":
    tool_results = []

    for block in response.content:
        if block.type == "tool_use":
            if block.name == "search_destinations":
                result = search_destinations(**block.input)
            elif block.name == "search_activities":
                result = search_activities(**block.input)

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result
            })

    messages.append({"role": "user", "content": tool_results})

    final_response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1000,
        tools=tools,
        messages=messages
    )

    print("\n--- Final response ---")
    print(final_response.content[0].text)