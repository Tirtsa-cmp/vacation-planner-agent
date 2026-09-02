import os
from dotenv import load_dotenv
import anthropic

load_dotenv()  # Load environment variables from the .env file

# Create the Anthropic client using the API key stored in the environment variable
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

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
                "preferences": {"type": "string", "description": "Type of trip desired, e.g. 'beach', 'city', 'mountains', 'culture'."}
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

def search_destinations(budget, num_travelers, preferences=None):
    """Search the web for vacation destinations matching the given budget,
    number of travelers, and preferences."""
    search_prompt = (
        f"Search the web for current vacation destination ideas suitable for "
        f"{num_travelers} travelers with a total budget of ${budget}"
        + (f", focused on {preferences} trips." if preferences else ".")
        + " Give a short list (2-3 destinations) with an approximate cost per person "
        "and one sentence explaining why each fits."
    )

    # Run the search using the Claude model with the web search tool
    sub_response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": search_prompt}]
    )

    # Extract and join the text blocks from the response into a single string
    text_parts = [block.text for block in sub_response.content if block.type == "text"]
    return "\n".join(text_parts)


def search_activities(destination, num_travelers, trip_duration_days=None):
    """Search the web for activities at a given destination, based on the
    number of travelers and trip duration."""
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


# --- Main agent loop ---

messages = [
    {"role": "user", "content": "I want a relaxing trip, no specific budget, just me."}
]

response = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=1000,
    tools=tools,
    messages=messages
)

print("--- First response ---")
print(response.content)
print("Stop reason:", response.stop_reason)  # "tool_use" means Claude needs a tool result before it can continue

messages.append({"role": "assistant", "content": response.content})

if response.stop_reason == "tool_use":  # Check if Claude requested a tool call
    tool_results = []

    for block in response.content:  # Loop through response blocks to find tool_use requests
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
    print(final_response.content[0].text)  # Final answer for the user