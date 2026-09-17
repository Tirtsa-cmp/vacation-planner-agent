import urllib.parse


def generate_flight_search_link(
    origin,
    destination,
    departure_date,
    return_date,
    travelers=1
):
    """
    Test flight link generation.
    """

    params = {
        "origin": origin,
        "destination": destination,
        "departure": departure_date,
        "return": return_date,
        "travelers": travelers
    }

    query = urllib.parse.urlencode(params)

    url = (
        "https://www.google.com/travel/flights?"
        + query
    )

    return url


# =====================
# TEST
# =====================

link = generate_flight_search_link(
    origin="PAR",
    destination="BUD",
    departure_date="2026-10-15",
    return_date="2026-10-19",
    travelers=2
)

print("\n===== FLIGHT LINK =====\n")
print(link)