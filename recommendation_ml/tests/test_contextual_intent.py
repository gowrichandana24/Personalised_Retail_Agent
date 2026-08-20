"""Focused tests for contextual intent-to-product matching.

Verifies that compute_intent_score() matches contextual intents
(beach, party, college, office, casual, travel, gym) against
product metadata (use_cases, title, description, style).
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from recommendation_ml.models.hybrid import compute_intent_score
from recommendation_ml.schemas import Mission


def _make_mission(occasion, style="", goal="", categories=None):
    return Mission(
        goal=goal,
        occasion=occasion,
        preferred_categories=categories or [],
        style_preference=style,
    )


BEACH_PRODUCTS = {
    "P013": {
        "category": "accessories", "brand": "Ray-Ban", "title": "SunGuard UV Protection Sunglasses",
        "description": "Stylish UV-protective sunglasses for beach outings, travel, and outdoor activities.",
        "properties": {"style": "stylish", "use_cases": ["beach", "travel", "outdoor"]},
    },
    "P014": {
        "category": "footwear", "brand": "Havaianas", "title": "Stride Beach Sandals",
        "description": "Comfortable quick-dry beach sandals with cushioned sole.",
        "properties": {"style": "casual", "use_cases": ["beach", "poolside", "summer"]},
    },
    "P015": {
        "category": "clothing", "brand": "Decathlon", "title": "Ocean Breeze Swim Trunks",
        "description": "Lightweight quick-dry swim trunks for beach, pool, and water sports.",
        "properties": {"style": "casual", "use_cases": ["beach", "swimming", "water sports"]},
    },
    "P016": {
        "category": "accessories", "brand": "GoSun", "title": "Coastal Straw Sun Hat",
        "description": "Wide-brim straw sun hat for beach outings, vacation, and outdoor protection.",
        "properties": {"style": "casual", "use_cases": ["beach", "vacation", "outdoor"]},
    },
    "P037": {
        "category": "bags", "brand": "American Tourister", "title": "Beach Tote Bag",
        "description": "Spacious waterproof tote bag for beach outings, poolside, and summer travel.",
        "properties": {"style": "casual", "use_cases": ["beach", "poolside", "summer"]},
    },
}

PARTY_PRODUCTS = {
    "P017": {
        "category": "clothing", "brand": "H&M", "title": "Velvet Nights Party Blazer",
        "description": "Slim-fit velvet blazer for parties, celebrations, and evening events.",
        "properties": {"style": "formal", "use_cases": ["party", "celebration", "evening"]},
    },
    "P018": {
        "category": "accessories", "brand": "Swarovski", "title": "Crystal Edge Statement Earrings",
        "description": "Elegant crystal drop earrings for parties, weddings, and special occasions.",
        "properties": {"style": "elegant", "use_cases": ["party", "wedding", "special occasion"]},
    },
    "P019": {
        "category": "bags", "brand": "Lavie", "title": "Midnight Satin Clutch",
        "description": "Sleek satin clutch bag for parties, dinners, and evening events.",
        "properties": {"style": "elegant", "use_cases": ["party", "dinner", "evening"]},
    },
}

COLLEGE_PRODUCTS = {
    "P020": {
        "category": "clothing", "brand": "Levi's", "title": "Campus Classic Denim Jeans",
        "description": "Comfortable straight-fit denim jeans for college, casual outings, and everyday wear.",
        "properties": {"style": "casual", "use_cases": ["college", "everyday", "casual"]},
    },
    "P021": {
        "category": "bags", "brand": "Skybags", "title": "TechFit College Backpack",
        "description": "Spacious college backpack with laptop compartment, multiple pockets.",
        "properties": {"style": "casual", "use_cases": ["college", "daily use"]},
    },
    "P040": {
        "category": "footwear", "brand": "Converse", "title": "College Casual Sneakers",
        "description": "Classic canvas sneakers for college, casual outings, and everyday wear.",
        "properties": {"style": "casual", "use_cases": ["college", "casual", "everyday"]},
    },
}

OFFICE_PRODUCTS = {
    "P022": {
        "category": "footwear", "brand": "Clarks", "title": "Formal Executive Leather Shoes",
        "description": "Premium leather formal shoes for office, meetings, and professional events.",
        "properties": {"style": "formal", "use_cases": ["office", "meetings", "professional"]},
    },
    "P023": {
        "category": "accessories", "brand": "Raymond", "title": "Executive Silk Tie Set",
        "description": "Pure silk tie with matching pocket square for formal events, office, and business.",
        "properties": {"style": "formal", "use_cases": ["office", "formal event", "business"]},
    },
    "P032": {
        "category": "accessories", "brand": "Fossil", "title": "Minimalist Chronograph Watch",
        "description": "Sleek chronograph watch for formal events, office, and everyday elegance.",
        "properties": {"style": "minimal", "use_cases": ["formal", "office", "everyday"]},
    },
}

CASUAL_PRODUCTS = {
    "P033": {
        "category": "clothing", "brand": "FabIndia", "title": "Casual Linen Shirt",
        "description": "Breathable linen shirt for casual outings, travel, and summer wear.",
        "properties": {"style": "casual", "use_cases": ["casual", "travel", "summer"]},
    },
    "P040": {
        "category": "footwear", "brand": "Converse", "title": "College Casual Sneakers",
        "description": "Classic canvas sneakers for college, casual outings, and everyday wear.",
        "properties": {"style": "casual", "use_cases": ["college", "casual", "everyday"]},
    },
}

TRAVEL_PRODUCTS = {
    "P003": {
        "category": "footwear", "brand": "Skechers", "title": "CloudStep Walking Shoes",
        "description": "Lightweight comfortable walking shoes for long flights, travel, everyday walking.",
        "properties": {"style": "casual", "use_cases": ["travel", "walking"]},
    },
    "P012": {
        "category": "travel", "brand": "TravelEase", "title": "QuietComfort Flight Neck Pillow",
        "description": "Soft supportive neck pillow for long flights, road travel, and rest.",
        "properties": {"style": "comfortable", "use_cases": ["long flight", "travel"]},
    },
}

GYM_PRODUCTS = {
    "P024": {
        "category": "gym", "brand": "Decathlon", "title": "Studio Yoga Mat",
        "description": "Non-slip eco-friendly yoga mat for gym workouts, yoga sessions, and home fitness.",
        "properties": {"style": "sporty", "use_cases": ["gym", "yoga", "fitness"]},
    },
    "P025": {
        "category": "gym", "brand": "Under Armour", "title": "PowerLift Training Gloves",
        "description": "Breathable training gloves with wrist support for gym workouts, weightlifting.",
        "properties": {"style": "sporty", "use_cases": ["gym", "weightlifting", "training"]},
    },
}


class TestBeachIntent:
    def test_beach_products_score_higher_than_non_beach(self):
        mission = _make_mission("beach")
        beach_scores = [
            compute_intent_score(p["category"], p["brand"], mission, p)
            for p in BEACH_PRODUCTS.values()
        ]
        non_beach_product = {
            "category": "gym", "brand": "Under Armour", "title": "PowerLift Training Gloves",
            "description": "Breathable training gloves for gym workouts.",
            "properties": {"style": "sporty", "use_cases": ["gym", "weightlifting"]},
        }
        non_beach_score = compute_intent_score(
            non_beach_product["category"], non_beach_product["brand"], mission, non_beach_product
        )
        assert min(beach_scores) > non_beach_score, (
            f"Beach products {beach_scores} should all score higher than non-beach {non_beach_score}"
        )

    def test_beach_via_use_cases(self):
        mission = _make_mission("beach")
        product = BEACH_PRODUCTS["P013"]
        score = compute_intent_score(product["category"], product["brand"], mission, product)
        assert score > 0.0, "Beach intent should match products with 'beach' in use_cases"


class TestPartyIntent:
    def test_party_products_score_higher_than_non_party(self):
        mission = _make_mission("party")
        party_scores = [
            compute_intent_score(p["category"], p["brand"], mission, p)
            for p in PARTY_PRODUCTS.values()
        ]
        non_party_product = {
            "category": "gym", "brand": "Under Armour", "title": "PowerLift Training Gloves",
            "description": "Breathable training gloves for gym workouts.",
            "properties": {"style": "sporty", "use_cases": ["gym", "weightlifting"]},
        }
        non_party_score = compute_intent_score(
            non_party_product["category"], non_party_product["brand"], mission, non_party_product
        )
        assert min(party_scores) > non_party_score

    def test_party_via_use_cases(self):
        mission = _make_mission("party")
        product = PARTY_PRODUCTS["P017"]
        score = compute_intent_score(product["category"], product["brand"], mission, product)
        assert score > 0.0


class TestCollegeIntent:
    def test_college_products_score_higher(self):
        mission = _make_mission("college")
        college_scores = [
            compute_intent_score(p["category"], p["brand"], mission, p)
            for p in COLLEGE_PRODUCTS.values()
        ]
        non_college = {
            "category": "gym", "brand": "Decathlon", "title": "Studio Yoga Mat",
            "description": "Non-slip yoga mat for gym workouts.",
            "properties": {"style": "sporty", "use_cases": ["gym", "yoga"]},
        }
        non_score = compute_intent_score(non_college["category"], non_college["brand"], mission, non_college)
        assert min(college_scores) > non_score

    def test_college_via_use_cases(self):
        mission = _make_mission("college")
        product = COLLEGE_PRODUCTS["P021"]
        score = compute_intent_score(product["category"], product["brand"], mission, product)
        assert score > 0.0


class TestOfficeIntent:
    def test_office_products_score_higher(self):
        mission = _make_mission("office")
        office_scores = [
            compute_intent_score(p["category"], p["brand"], mission, p)
            for p in OFFICE_PRODUCTS.values()
        ]
        non_office = {
            "category": "gym", "brand": "Decathlon", "title": "Studio Yoga Mat",
            "description": "Non-slip yoga mat for gym workouts.",
            "properties": {"style": "sporty", "use_cases": ["gym", "yoga"]},
        }
        non_score = compute_intent_score(non_office["category"], non_office["brand"], mission, non_office)
        assert min(office_scores) > non_score

    def test_office_via_use_cases(self):
        mission = _make_mission("office")
        product = OFFICE_PRODUCTS["P022"]
        score = compute_intent_score(product["category"], product["brand"], mission, product)
        assert score > 0.0


class TestCasualIntent:
    def test_casual_products_score_higher(self):
        mission = _make_mission("casual")
        casual_scores = [
            compute_intent_score(p["category"], p["brand"], mission, p)
            for p in CASUAL_PRODUCTS.values()
        ]
        non_casual = {
            "category": "gym", "brand": "Under Armour", "title": "PowerLift Training Gloves",
            "description": "Breathable training gloves for gym workouts.",
            "properties": {"style": "sporty", "use_cases": ["gym", "weightlifting"]},
        }
        non_score = compute_intent_score(non_casual["category"], non_casual["brand"], mission, non_casual)
        assert min(casual_scores) > non_score

    def test_casual_via_use_cases(self):
        mission = _make_mission("casual")
        product = CASUAL_PRODUCTS["P033"]
        score = compute_intent_score(product["category"], product["brand"], mission, product)
        assert score > 0.0


class TestTravelIntent:
    def test_travel_products_score_higher(self):
        mission = _make_mission("travel")
        travel_scores = [
            compute_intent_score(p["category"], p["brand"], mission, p)
            for p in TRAVEL_PRODUCTS.values()
        ]
        non_travel = {
            "category": "gym", "brand": "Under Armour", "title": "PowerLift Training Gloves",
            "description": "Breathable training gloves for gym workouts.",
            "properties": {"style": "sporty", "use_cases": ["gym", "weightlifting"]},
        }
        non_score = compute_intent_score(non_travel["category"], non_travel["brand"], mission, non_travel)
        assert min(travel_scores) > non_score


class TestGymIntent:
    def test_gym_products_score_higher(self):
        mission = _make_mission("gym")
        gym_scores = [
            compute_intent_score(p["category"], p["brand"], mission, p)
            for p in GYM_PRODUCTS.values()
        ]
        non_gym = {
            "category": "accessories", "brand": "Ray-Ban", "title": "SunGuard Sunglasses",
            "description": "UV-protective sunglasses for beach outings.",
            "properties": {"style": "stylish", "use_cases": ["beach", "travel"]},
        }
        non_score = compute_intent_score(non_gym["category"], non_gym["brand"], mission, non_gym)
        assert min(gym_scores) > non_score


class TestAllOccasionsNonZero:
    """Verify intent_score is never 0 for any occasion when metadata matches."""

    def _check_occasion_matches_something(self, occasion, products):
        mission = _make_mission(occasion)
        scores = []
        for pid, product in products.items():
            score = compute_intent_score(
                product["category"], product["brand"], mission, product
            )
            scores.append((pid, score))
        assert any(s > 0.0 for _, s in scores), (
            f"Occasion '{occasion}' should match at least one product. Scores: {scores}"
        )

    def test_beach_nonzero(self):
        self._check_occasion_matches_something("beach", BEACH_PRODUCTS)

    def test_party_nonzero(self):
        self._check_occasion_matches_something("party", PARTY_PRODUCTS)

    def test_college_nonzero(self):
        self._check_occasion_matches_something("college", COLLEGE_PRODUCTS)

    def test_office_nonzero(self):
        self._check_occasion_matches_something("office", OFFICE_PRODUCTS)

    def test_casual_nonzero(self):
        self._check_occasion_matches_something("casual", CASUAL_PRODUCTS)

    def test_travel_nonzero(self):
        self._check_occasion_matches_something("travel", TRAVEL_PRODUCTS)

    def test_gym_nonzero(self):
        self._check_occasion_matches_something("gym", GYM_PRODUCTS)


class TestDifferentOccasionsDifferentScores:
    """Different occasions should produce different scores for the same product."""

    def test_beach_vs_party_on_party_product(self):
        product = PARTY_PRODUCTS["P017"]
        beach_mission = _make_mission("beach")
        party_mission = _make_mission("party")
        beach_score = compute_intent_score(product["category"], product["brand"], beach_mission, product)
        party_score = compute_intent_score(product["category"], product["brand"], party_mission, product)
        assert party_score > beach_score

    def test_gym_vs_beach_on_gym_product(self):
        product = GYM_PRODUCTS["P025"]
        gym_mission = _make_mission("gym")
        beach_mission = _make_mission("beach")
        gym_score = compute_intent_score(product["category"], product["brand"], gym_mission, product)
        beach_score = compute_intent_score(product["category"], product["brand"], beach_mission, product)
        assert gym_score > beach_score


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
