import os
from dotenv import load_dotenv
import anthropic
import chromadb

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
    """Search for vacation destinations matching the given budget,
    number of travelers, and preferences. Tries the local RAG database first,
    falls back to a live web search if nothing relevant is found."""
    
    query = f"vacation destination for {preferences or 'general'} trip"
    
    # Try RAG first
    rag_result = rag_search(query)
    
    if rag_result:
        return f"[From internal knowledge base]\n{rag_result}"
    
    # Fallback to web search if nothing relevant found in the local database
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
    return f"[From live web search]\n" + "\n".join(text_parts)


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

# --- Main agent loop ---

messages = [
    {"role": "user", "content": "We want a nature-focused trip somewhere cold with glaciers and volcanoes, budget $2000, 2 travelers. Where should we go?"}
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

    for block in response.content:
        if block.type == "tool_use":
            if block.name == "search_destinations":
                result = search_destinations(**block.input)
                print("\n[DEBUG] Tool result:", result[:200])
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

    final_text_parts = [block.text for block in final_response.content if block.type == "text"]
    print("\n--- Final response ---")
    print("\n".join(final_text_parts))