"""Trace recommendation flow WITH user interaction history.
This shows how the system behaves when user data IS available.
"""

import sys
import json
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from intent.fallback_parser import FallbackIntentParser
from recommendation_ml.schemas import Mission, CustomerProfile
from recommendation_ml.engine import RecommendationEngine
from recommendation_ml.models.hybrid import compute_intent_score, compute_preference_score
from recommendation_ml.config import HybridWeights

# Load actual data
CATALOG_PATH = PROJECT_ROOT / "data" / "catalog.json"
INTERACTIONS_PATH = PROJECT_ROOT / "data" / "interactions.json"

with open(CATALOG_PATH, encoding="utf-8") as f:
    catalog = json.load(f)

with open(INTERACTIONS_PATH, encoding="utf-8") as f:
    interactions = json.load(f)

# Create engine
engine = RecommendationEngine()
engine.fit(interactions, catalog)

# Create a customer profile with actual affinity data
# This simulates what Customer Intelligence would produce
profile_with_history = CustomerProfile(
    customer_id="seed-1",  # This user interacted with P001, P002, P008
    category_affinity={"bags": 0.8, "clothing": 0.6, "electronics": 0.3},
    price_sensitivity=0.5,
    preferred_brands=["Wildcraft", "Allen Solly"],
    recent_categories=["bags", "clothing"],
    recent_products=["P001", "P002", "P008"],
    discovery_appetite=0.3,
    total_purchases=1,
    total_views=2,
)

# Test prompts
test_prompts = [
    "I need an outfit for a beach outing",
    "I need an outfit for a party",
    "I need something for college",
    "I need something for a formal office event",
]

parser = FallbackIntentParser()

print("=" * 80)
print("RECOMMENDATION FLOW TRACE - WITH USER HISTORY")
print("=" * 80)

for prompt in test_prompts:
    print(f"\n{'='*80}")
    print(f"PROMPT: \"{prompt}\"")
    print("=" * 80)

    # Parse intent
    intent = parser.parse(prompt)
    print(f"\n1. PARSED INTENT:")
    print(f"   category: {intent.category}")
    print(f"   occasion: {intent.occasion}")
    print(f"   preferences: {intent.preferences}")

    # Create Mission
    mission = Mission(
        goal=intent.goal or prompt,
        occasion=intent.occasion or "",
        budget=intent.budget if intent.budget is not None else float("inf"),
        preferred_categories=[intent.category] if intent.category else [],
        excluded_brands=[],
        excluded_categories=[],
        discovery_level=intent.discovery_level,
        urgency=intent.urgency or "medium",
        style_preference=(intent.preferences or [""])[0] if intent.preferences else "",
    )

    # Get recommendations WITH profile
    result = engine.recommend(
        customer_id="seed-1",
        mission=mission,
        customer_profile=profile_with_history,
        candidate_products=catalog,
        top_k=5,
    )

    print(f"\n2. RECOMMENDATIONS (with user history):")
    for rec in result.recommendations:
        breakdown = rec.score_breakdown
        print(f"\n   Rank {rec.rank}: {rec.product_id} - {rec.metadata.get('title', 'N/A')}")
        print(f"      Final Score: {rec.final_score:.4f}")
        print(f"      Score Breakdown:")
        print(f"        collaborative: {breakdown.collaborative:.4f}")
        print(f"        content: {breakdown.content:.4f}")
        print(f"        intent: {breakdown.intent:.4f}")
        print(f"        preference: {breakdown.preference:.4f}")
        print(f"        budget: {breakdown.budget:.4f}")
        print(f"        popularity: {breakdown.popularity:.4f}")
        print(f"      Evidence: {rec.evidence}")

    # Show intent scoring detail
    print(f"\n3. INTENT SCORE DETAIL:")
    for product in catalog[:6]:
        intent_score = compute_intent_score(
            product.get("category", ""),
            product.get("brand", ""),
            mission
        )
        pref_score = compute_preference_score(
            product.get("category", ""),
            product.get("brand", ""),
            profile_with_history
        )
        print(f"   {product['product_id']} ({product['category']}, {product['brand']}):")
        print(f"      intent_score = {intent_score:.2f}, preference_score = {pref_score:.2f}")


# Now test what happens with Gemini parser (if available)
print("\n\n" + "=" * 80)
print("TESTING GEMINI PARSER (if available)")
print("=" * 80)

try:
    from intent.gemini_parser import GeminiIntentParser
    gemini = GeminiIntentParser()
    
    test_prompts_gemini = [
        "I need an outfit for a beach outing",
        "I need an outfit for a party",
        "I need something for college",
    ]
    
    for prompt in test_prompts_gemini:
        print(f"\nPrompt: \"{prompt}\"")
        try:
            result = gemini.parse(prompt)
            print(f"  Gemini parsed: category={result.category}, occasion={result.occasion}")
            print(f"  preferences: {result.preferences}")
        except Exception as e:
            print(f"  Gemini error: {e}")
            
except Exception as e:
    print(f"Gemini not available: {e}")
