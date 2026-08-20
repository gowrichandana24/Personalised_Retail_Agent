"""Tests for Priority 4: Score Differentiation and Category Alignment.

Verifies that:
1. Different missions produce different intent scores
2. compute_intent_score() uses goal and style_preference
3. mission_from_query() passes all preferences
4. Scoring differentiates products by mission
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from recommendation_ml.models.hybrid import compute_intent_score, compute_preference_score
from recommendation_ml.schemas import Mission, CustomerProfile


class TestIntentScoreDifferentiation:
    """Test that compute_intent_score() produces different scores for different missions."""

    def test_beach_mission_prefers_beach_products(self):
        """A beach mission should score beach products higher."""
        mission = Mission(
            goal="beach vacation",
            occasion="beach",
            preferred_categories=["footwear"],
            style_preference="waterproof, lightweight, comfortable",
        )
        beach_score = compute_intent_score("footwear", "Nike", mission)
        party_score = compute_intent_score("dress", "Zara", mission)
        assert beach_score > party_score

    def test_party_mission_prefers_party_products(self):
        """A party mission should score party products higher."""
        mission = Mission(
            goal="night out",
            occasion="party",
            preferred_categories=["dress"],
            style_preference="elegant, stylish",
        )
        party_score = compute_intent_score("dress", "Zara", mission)
        beach_score = compute_intent_score("footwear", "Nike", mission)
        assert party_score > beach_score

    def test_college_mission_prefers_college_products(self):
        """A college mission should score college products higher."""
        mission = Mission(
            goal="back to school",
            occasion="college",
            preferred_categories=["tshirt"],
            style_preference="comfortable, trendy",
        )
        college_score = compute_intent_score("tshirt", "H&M", mission)
        formal_score = compute_intent_score("blazer", "Armani", mission)
        assert college_score > formal_score

    def test_travel_mission_prefers_travel_products(self):
        """A travel mission should score travel products higher."""
        mission = Mission(
            goal="trip",
            occasion="travel",
            preferred_categories=["bags"],
            style_preference="lightweight, practical",
        )
        travel_score = compute_intent_score("bags", "Samsonite", mission)
        formal_score = compute_intent_score("blazer", "Armani", mission)
        assert travel_score > formal_score

    def test_no_mission_returns_low_score(self):
        """When no mission fields are set, score should be low (0.3)."""
        mission = Mission()
        score = compute_intent_score("anything", "any_brand", mission)
        assert score == 0.3

    def test_goal_match_increases_score(self):
        """Matching goal keywords should increase the score."""
        mission_with_goal = Mission(goal="running shoes")
        mission_without_goal = Mission(goal="")
        score_with = compute_intent_score("running shoes", "Nike", mission_with_goal)
        score_without = compute_intent_score("running shoes", "Nike", mission_without_goal)
        assert score_with > score_without

    def test_style_preference_match_increases_score(self):
        """Matching style preference should increase the score."""
        mission_with_style = Mission(style_preference="waterproof")
        mission_without_style = Mission(style_preference="")
        score_with = compute_intent_score("waterproof", "Nike", mission_with_style)
        score_without = compute_intent_score("waterproof", "Nike", mission_without_style)
        assert score_with > score_without


class TestMissionFromQuery:
    """Test that mission_from_query() passes all preferences."""

    def test_preferences_passed_to_style(self):
        """All preferences should be joined and passed to style_preference."""
        from backend.service import mission_from_query
        mission, parsed = mission_from_query("I need something for the beach")
        assert mission.style_preference != ""
        assert "," in mission.style_preference or len(mission.style_preference) > 0

    def test_occasion_preserved(self):
        """Occasion should be preserved in the mission."""
        from backend.service import mission_from_query
        mission, parsed = mission_from_query("I need something for a party")
        assert mission.occasion == "party"

    def test_category_preserved(self):
        """Category should be preserved in the mission."""
        from backend.service import mission_from_query
        mission, parsed = mission_from_query("I need running shoes")
        assert "footwear" in mission.preferred_categories or "shoes" in mission.preferred_categories


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
