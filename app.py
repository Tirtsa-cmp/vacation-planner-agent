from flask import Flask, request, jsonify
from agent import client, tools, SYSTEM_PROMPT, search_destinations, search_activities, compare_hotels, compare_flights, generate_booking_links, add_to_trip_budget, check_budget, extract_budget_from_text
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# In-memory session storage (simple approach: one global session for now)
sessions = {}

def get_or_create_session(session_id):
    if session_id not in sessions:
        sessions[session_id] = {
            "messages": [],
            "trip_items": [],
            "all_suggested_destinations": [],
            "budget_per_person": None
        }
    return sessions[session_id]


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    session_id = data.get("session_id", "default")
    user_message = data.get("message", "").strip()

    session = get_or_create_session(session_id)

    extracted_budget, extracted_travelers = extract_budget_from_text(user_message)
    if extracted_budget and extracted_travelers and session["budget_per_person"] is None:
        session["budget_per_person"] = extracted_budget / extracted_travelers

    session["messages"].append({"role": "user", "content": user_message})

    max_turns = 5
    turn_count = 0
    final_text = ""

    while turn_count < max_turns:
        turn_count += 1
        try:
            response = client.messages.create(
                model="claude-sonnet-5",
                max_tokens=2000,
                system=SYSTEM_PROMPT,
                tools=tools,
                messages=session["messages"]
            )

        except Exception as e:
            print(f"\n[ERROR] Something went wrong: {e}\n")
            break
        session["messages"].append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            final_text_parts = [block.text for block in response.content if block.type == "text"]
            final_text = "\n".join(final_text_parts)
            break

        tool_results = []

        for block in response.content:
            if block.type == "tool_use":
                if block.name == "search_destinations":
                    result = search_destinations(**block.input, already_suggested=session["all_suggested_destinations"])
                    for item in result:
                        if item.get("name") and item["name"] not in session["all_suggested_destinations"]:
                            session["all_suggested_destinations"].append(item["name"])
                    if "budget" in block.input and "num_travelers" in block.input:
                        session["budget_per_person"] = block.input["budget"] / block.input["num_travelers"]
                    add_to_trip_budget(session["trip_items"], result, "destination")

                elif block.name == "search_activities":
                    already_suggested = [item["name"] for item in session["trip_items"] if item["category"] == "activity"]
                    result = search_activities(**block.input, already_suggested=already_suggested)
                    add_to_trip_budget(session["trip_items"], result, "activity")

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

        budget_status = check_budget(session["trip_items"], session["budget_per_person"])
        budget_note = (
            f"\n\n(Budget tracker: total so far ${budget_status['total_per_person']}/person. "
            + (f"Budget: ${session['budget_per_person']:.0f}/person, remaining ${budget_status['remaining']:.0f}."
               if session["budget_per_person"] else "No budget specified yet.")
            + ")"
        )
        tool_results.append({"type": "text", "text": budget_note})

        session["messages"].append({"role": "user", "content": tool_results})
    else:
        final_text = "Sorry, I need more turns to complete this request. Please try rephrasing."

    return jsonify({"response": final_text})


if __name__ == "__main__":
    app.run(debug=True, port=5000)