from agent import check_budget, add_to_trip_budget
# Simple tests for budget logic — no API calls needed, fast and free to run

def test_check_budget_within_budget():
    trip_items = [
        {"category": "destination", "name": "Bali", "cost_per_person_usd": 500},
        {"category": "activity", "name": "Surf lesson", "cost_per_person_usd": 50},
    ]
    result = check_budget(trip_items, budget_per_person=1000)
    assert result["total_per_person"] == 550
    assert result["within_budget"] is True
    assert result["remaining"] == 450
    print("✅ test_check_budget_within_budget passed")


def test_check_budget_over_budget():
    trip_items = [
        {"category": "destination", "name": "Maldives", "cost_per_person_usd": 900},
        {"category": "activity", "name": "Diving", "cost_per_person_usd": 200},
    ]
    result = check_budget(trip_items, budget_per_person=1000)
    assert result["total_per_person"] == 1100
    assert result["within_budget"] is False
    assert result["remaining"] == -100
    print("✅ test_check_budget_over_budget passed")


def test_check_budget_no_budget_specified():
    trip_items = [{"category": "activity", "name": "Hike", "cost_per_person_usd": 30}]
    result = check_budget(trip_items, budget_per_person=None)
    assert result["within_budget"] is None
    assert result["remaining"] is None
    print("✅ test_check_budget_no_budget_specified passed")


def test_add_to_trip_budget_keeps_only_cheapest_destination():
    trip_items = []
    destinations = [
        {"name": "Fiji", "cost_per_person_usd": 1200},
        {"name": "Bali", "cost_per_person_usd": 500},
    ]
    add_to_trip_budget(trip_items, destinations, "destination")
    assert len(trip_items) == 1
    assert trip_items[0]["name"] == "Bali"
    assert trip_items[0]["cost_per_person_usd"] == 500
    print("✅ test_add_to_trip_budget_keeps_only_cheapest_destination passed")


def test_add_to_trip_budget_replaces_old_destination():
    trip_items = [{"category": "destination", "name": "Old Place", "cost_per_person_usd": 999}]
    new_destinations = [{"name": "Bali", "cost_per_person_usd": 500}]
    add_to_trip_budget(trip_items, new_destinations, "destination")
    assert len(trip_items) == 1
    assert trip_items[0]["name"] == "Bali"
    print("✅ test_add_to_trip_budget_replaces_old_destination passed")


def test_add_to_trip_budget_accumulates_activities():
    trip_items = []
    activities = [
        {"name": "Hike", "cost_per_person_usd": 30},
        {"name": "Spa", "cost_per_person_usd": 50},
    ]
    add_to_trip_budget(trip_items, activities, "activity")
    assert len(trip_items) == 2
    total = sum(item["cost_per_person_usd"] for item in trip_items)
    assert total == 80
    print("✅ test_add_to_trip_budget_accumulates_activities passed")


if __name__ == "__main__":
    test_check_budget_within_budget()
    test_check_budget_over_budget()
    test_check_budget_no_budget_specified()
    test_add_to_trip_budget_keeps_only_cheapest_destination()
    test_add_to_trip_budget_replaces_old_destination()
    test_add_to_trip_budget_accumulates_activities()
    print("\n🎉 All tests passed!")