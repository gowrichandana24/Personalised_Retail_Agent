"""Trace recommendation flow for different user prompts.
This script does NOT modify any project files. It only reads and analyzes.
"""

import sys
import json
from pathlib import Path
from collections import defaultdict

# Add project root to path
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

# Test prompts
test_prompts = [
    "I need an outfit for a beach outing",
    "I need an outfit for a party",
    "I need something for a beach outing",
    "I need something for a party",
    "I need something for college",
    "I need something for a formal office event",
    "Recommend something for a beach outing",
    "Recommend something for a casual outing",
]

# Create engine
engine = RecommendationEngine()
engine.fit(interactions, catalog)

# Create fallback parser
parser = FallbackIntentParser()

print("=" * 80)
print("RECOMMENDATION FLOW TRACE")
print("=" * 80)

# Track results for comparison
results_summary = defaultdict(list)

for prompt in test_prompts:
    print(f"\n{'='*80}")
    print(f"PROMPT: \"{prompt}\"")
    print("=" * 80)

    # Step 1: Parse intent
    intent = parser.parse(prompt)
    print(f"\n1. PARSED INTENT:")
    print(f"   goal: {intent.goal}")
    print(f"   category: {intent.category}")
    print(f"   subcategory: {intent.subcategory}")
    print(f"   occasion: {intent.occasion}")
    print(f"   budget: {intent.budget}")
    print(f"   preferences: {intent.preferences}")
    print(f"   exclusions: {intent.exclusions}")
    print(f"   discovery_level: {intent.discovery_level}")

    # Step 2: Create Mission (as backend/service.py does)
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

    print(f"\n2. MISSION OBJECT:")
    print(f"   goal: {mission.goal}")
    print(f"   occasion: {mission.occasion}")
    print(f"   budget: {mission.budget}")
    print(f"   preferred_categories: {mission.preferred_categories}")
    print(f"   preferred_brands: {mission.preferred_brands}")
    print(f"   excluded_brands: {mission.excluded_brands}")
    print(f"   excluded_categories: {mission.excluded_categories}")
    print(f"   discovery_level: {mission.discovery_level}")

    # Step 3: Create a dummy customer profile (no interaction history)
    profile = CustomerProfile(
        customer_id="test-user",
        category_affinity={},
        price_sensitivity=0.5,
        preferred_brands=[],
        recent_categories=[],
        recent_products=[],
        discovery_appetite=0.3,
    )

    # Step 4: Get recommendations
    result = engine.recommend(
        customer_id="test-user",
        mission=mission,
        customer_profile=profile,
        candidate_products=catalog,
        top_k=5,
    )

    print(f"\n3. RECOMMENDATIONS:")
    print(f"   Candidate count: {result.candidate_count}")
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
        print(f"        session: {breakdown.session:.4f}")
        print(f"        popularity: {breakdown.popularity:.4f}")
        print(f"        discovery: {breakdown.discovery:.4f}")
        print(f"      Evidence: {rec.evidence}")

    # Store for comparison
    rec_ids = [r.product_id for r in result.recommendations]
    results_summary[prompt] = rec_ids

    # Step 5: Show intent scoring for each product
    print(f"\n4. INTENT SCORES PER PRODUCT:")
    for product in catalog[:6]:  # Show first 6
        intent_score = compute_intent_score(
            product.get("category", ""),
            product.get("brand", ""),
            mission
        )
        print(f"   {product['product_id']} ({product['category']}): intent_score = {intent_score:.2f}")

print("\n\n" + "=" * 80)
print("COMPARISON SUMMARY")
print("=" * 80)

# Compare results
print("\nProduct IDs in top-5 for each prompt:")
for prompt, rec_ids in results_summary.items():
    print(f"\n  \"{prompt}\":")
    print(f"    {rec_ids}")

# Check how many unique recommendation sets exist
unique_sets = set(tuple(ids) for ids in results_summary.values())
print(f"\n\nUnique recommendation sets: {len(unique_sets)} out of {len(results_summary)} prompts")

# Analyze the catalog categories
print("\n\nCATALOG ANALYSIS:")
categories = defaultdict(list)
for product in catalog:
    categories[product.get("category", "unknown")].append(product['product_id'])

print("Categories in catalog:")
for cat, pids in categories.items():
    print(f"  {cat}: {pids}")

# Check if any product mentions beach or party
print("\n\nKEYWORD SEARCH IN CATALOG:")
keywords = ["beach", "party", "formal", "college", "casual", "outdoor"]
for keyword in keywords:
    matching = []
    for product in catalog:
        desc = product.get("description", "").lower()
        title = product.get("title", "").lower()
        props = str(product.get("properties", {})).lower()
        if keyword in desc or keyword in title or keyword in props:
            matching.append(product['product_id'])
    if matching:
        print(f"  '{keyword}' found in: {matching}")
    else:
        print(f"  '{keyword}' NOT FOUND in any product")
