"""Tests for the FallbackIntentParser covering all 9 required contextual categories.

These tests verify that the fallback parser correctly extracts contextual
intent from natural-language shopping queries.
"""

import sys
from pathlib import Path

# Ensure the project root is on sys.path so `intent` can be imported.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from intent.fallback_parser import FallbackIntentParser


parser = FallbackIntentParser()


# ============================================================
# Helper
# ============================================================

def parse(message: str):
    """Convenience wrapper that returns the parsed ShoppingIntent."""
    return parser.parse(message)


def assert_occasion(result, expected_occasion, query_label=""):
    """Assert the parsed occasion matches expectations."""
    assert result.occasion == expected_occasion, (
        f"[{query_label}] Expected occasion={expected_occasion!r}, "
        f"got occasion={result.occasion!r}"
    )


def assert_has_preference(result, pref, query_label=""):
    """Assert a specific preference is present."""
    assert pref in result.preferences, (
        f"[{query_label}] Expected preference {pref!r} in "
        f"{result.preferences}"
    )


def assert_category(result, expected_category, query_label=""):
    """Assert the parsed category matches expectations."""
    assert result.category == expected_category, (
        f"[{query_label}] Expected category={expected_category!r}, "
        f"got category={result.category!r}"
    )


# ============================================================
# 1. Beach Outing
# ============================================================

class TestBeachOuting:
    """Beach outing should set occasion=beach with outdoor/lightweight prefs."""

    def test_occasion_beach(self):
        result = parse("I need something for a beach outing")
        assert_occasion(result, "beach", "beach outing")

    def test_preferences(self):
        result = parse("I need something for a beach outing")
        assert_has_preference(result, "outdoor", "beach outing")
        assert_has_preference(result, "lightweight", "beach outing")

    def test_beach_keyword_variants(self):
        for variant in [
            "beach trip",
            "beach party",
            "going to the beach",
            "beach outing with friends",
        ]:
            result = parse(variant)
            assert_occasion(result, "beach", variant)


# ============================================================
# 2. Party
# ============================================================

class TestParty:
    """Party should set occasion=party with stylish preference."""

    def test_occasion_party(self):
        result = parse("I want an outfit for a party")
        assert_occasion(result, "party", "party")

    def test_preferences(self):
        result = parse("I want an outfit for a party")
        assert_has_preference(result, "stylish", "party")

    def test_party_keyword_variants(self):
        for variant in [
            "party outfit",
            "going to a party",
            "birthday party",
            "house party",
        ]:
            result = parse(variant)
            assert_occasion(result, "party", variant)


# ============================================================
# 3. College
# ============================================================

class TestCollege:
    """College should set occasion=college."""

    def test_occasion_college(self):
        result = parse("Build me a college event outfit")
        assert_occasion(result, "college", "college event")

    def test_college_keyword_variants(self):
        for variant in [
            "college event",
            "college outfit",
            "for college",
            "campus event",
        ]:
            result = parse(variant)
            assert_occasion(result, "college", variant)


# ============================================================
# 4. Formal / Office Event
# ============================================================

class TestFormalOffice:
    """Formal office event should set occasion=office or occasion=formal."""

    def test_office_occasion(self):
        result = parse("I need formal attire for a office event")
        assert_occasion(result, "office", "office event")

    def test_formal_occasion(self):
        result = parse("I need something formal for the event")
        assert_occasion(result, "formal", "formal event")

    def test_professional_keyword(self):
        result = parse("professional attire for work")
        assert_occasion(result, "office", "professional work")

    def test_formal_preferences(self):
        result = parse("I need something formal")
        assert_has_preference(result, "elegant", "formal")


# ============================================================
# 5. Casual Outing
# ============================================================

class TestCasualOuting:
    """Casual outing should set occasion=casual."""

    def test_occasion_casual(self):
        result = parse("I need something for a casual outing")
        assert_occasion(result, "casual", "casual outing")

    def test_casual_keyword_variants(self):
        for variant in [
            "casual wear",
            "casual outfit",
            "casual day out",
        ]:
            result = parse(variant)
            assert_occasion(result, "casual", variant)


# ============================================================
# 6. Travel
# ============================================================

class TestTravel:
    """Travel should set occasion=travel with practical preference."""

    def test_occasion_travel(self):
        result = parse("I need something for travel")
        assert_occasion(result, "travel", "travel")

    def test_preferences(self):
        result = parse("I need something for travel")
        assert_has_preference(result, "practical", "travel")

    def test_trip_keyword(self):
        result = parse("I'm going on a trip")
        assert_occasion(result, "travel", "trip")

    def test_vacation_keyword(self):
        result = parse("I need vacation clothes")
        assert_occasion(result, "travel", "vacation")


# ============================================================
# 7. Gym
# ============================================================

class TestGym:
    """Gym should set occasion=gym with sporty preference."""

    def test_occasion_gym(self):
        result = parse("I need something for the gym")
        assert_occasion(result, "gym", "gym")

    def test_preferences(self):
        result = parse("I need something for the gym")
        assert_has_preference(result, "sporty", "gym")

    def test_workout_keyword(self):
        result = parse("workout clothes")
        assert_occasion(result, "gym", "workout")


# ============================================================
# 8. Wedding
# ============================================================

class TestWedding:
    """Wedding should set occasion=wedding."""

    def test_occasion_wedding(self):
        result = parse("I need something for a wedding")
        assert_occasion(result, "wedding", "wedding")

    def test_wedding_keyword_variants(self):
        for variant in [
            "wedding outfit",
            "wedding guest attire",
            "going to a wedding",
        ]:
            result = parse(variant)
            assert_occasion(result, "wedding", variant)


# ============================================================
# 9. Birthday
# ============================================================

class TestBirthday:
    """Birthday should set occasion=birthday."""

    def test_occasion_birthday(self):
        result = parse("I need a birthday gift")
        assert_occasion(result, "birthday", "birthday")

    def test_birthday_keyword_variants(self):
        for variant in [
            "birthday gift",
            "birthday present",
            "for my birthday",
        ]:
            result = parse(variant)
            assert_occasion(result, "birthday", variant)


# ============================================================
# Cross-category differentiation tests
# ============================================================

class TestDifferentiation:
    """Verify that different prompts produce DIFFERENT contextual values."""

    def test_beach_vs_party_occasions_differ(self):
        beach = parse("I need something for a beach outing")
        party = parse("I want an outfit for a party")
        assert beach.occasion != party.occasion, (
            f"Expected different occasions, both got {beach.occasion!r}"
        )

    def test_beach_vs_party_preferences_differ(self):
        beach = parse("I need something for a beach outing")
        party = parse("I want an outfit for a party")
        assert beach.preferences != party.preferences, (
            f"Expected different preferences: beach={beach.preferences}, "
            f"party={party.preferences}"
        )

    def test_all_nine_occasions_are_distinct(self):
        queries = {
            "beach": "beach outing",
            "party": "party outfit",
            "college": "college event",
            "office": "office event",
            "casual": "casual outing",
            "travel": "travel",
            "gym": "gym",
            "wedding": "wedding",
            "birthday": "birthday gift",
        }
        occasions = set()
        for label, keyword in queries.items():
            result = parse(f"I need something for a {keyword}")
            occasions.add(result.occasion)
            assert result.occasion is not None, (
                f"Occasion is None for query containing '{keyword}'"
            )
        assert len(occasions) >= 7, (
            f"Expected at least 7 distinct occasions, got {len(occasions)}: "
            f"{occasions}"
        )

    def test_contextual_occasions_are_not_none(self):
        """The core regression: previously these all returned None."""
        contextual_queries = [
            "beach outing",
            "party",
            "college event",
            "formal office event",
            "casual outing",
            "travel",
            "gym",
            "wedding",
            "birthday gift",
        ]
        for query in contextual_queries:
            result = parse(query)
            assert result.occasion is not None, (
                f"Occasion is None for '{query}' — contextual intent lost"
            )


# ============================================================
# Backward compatibility: existing queries still work
# ============================================================

class TestBackwardCompatibility:
    """Ensure previously-working queries are not broken."""

    def test_running_shoes_college(self):
        result = parse(
            "I need running shoes under ₹5000 for college. "
            "They should be comfortable but not flashy."
        )
        assert_category(result, "footwear", "running shoes college")
        assert_occasion(result, "college", "running shoes college")
        assert_has_preference(result, "comfortable", "running shoes college")
        assert result.budget == 5000.0

    def test_birthday_gift(self):
        result = parse(
            "I need a birthday gift for my sister around ₹2000. "
            "She loves fitness and I want something unique."
        )
        assert_occasion(result, "birthday", "birthday gift")
        assert_has_preference(result, "fitness", "birthday gift")
        assert result.budget == 2000.0
        assert result.discovery_level == 0.8

    def test_trip_practical(self):
        result = parse(
            "I'm going on a trip and need something practical under 3000."
        )
        assert_occasion(result, "travel", "trip practical")
        assert_has_preference(result, "practical", "trip practical")
        assert result.budget == 3000.0

    def test_exclusions(self):
        result = parse("I don't want Nike.")
        assert "nike" in result.exclusions

    def test_discovery_high(self):
        result = parse("Surprise me with something different.")
        assert result.discovery_level == 0.8

    def test_discovery_low(self):
        result = parse("I want something similar to what I usually buy.")
        assert result.discovery_level == 0.2

    def test_goal_preserved(self):
        query = "I need something for a beach outing"
        result = parse(query)
        assert result.goal == query


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
