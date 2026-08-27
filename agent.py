import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# --- Étape 1 : définir l'outil ---
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
                    "description": "Type of trip desired, e.g. 'beach', 'city', 'mountains', 'culture'."
                }
            },
            "required": ["budget", "num_travelers"]
        }
    }
]
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

# --- Étape 3 : envoyer la première requête avec les outils disponibles ---
messages = [
    {"role": "user", "content": "I have a budget of $3000 for 2 people, we love beaches. Where should we go?"}
]

response = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=1000,
    tools=tools,
    messages=messages
)

print("--- First response from Claude ---")
print(response.content)
print("Stop reason:", response.stop_reason)
# --- Étape 3 : premier appel avec les outils disponibles ---
messages = [
    {"role": "user", "content": "I have a budget of $3000 for 2 people, we love beaches. Where should we go?"}
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

# --- Étape 4 : ajouter la réponse de Claude à l'historique de conversation ---
messages.append({"role": "assistant", "content": response.content})

# --- Étape 5 : si Claude a demandé un outil, l'exécuter et boucler ---
if response.stop_reason == "tool_use":
    tool_results = []

    for block in response.content:
        if block.type == "tool_use":
            if block.name == "search_destinations":
                result = search_destinations(**block.input)

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result
                })

    # On renvoie les résultats des outils comme un nouveau message "user"
    messages.append({"role": "user", "content": tool_results})

    # Deuxième appel : Claude reçoit le résultat et formule sa vraie réponse
    final_response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1000,
        tools=tools,
        messages=messages
    )

    print("\n--- Final response ---")
    print(final_response.content[0].text)