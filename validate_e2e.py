"""Full End-to-End Validation of the RetailMind recommendation pipeline.

Tests the actual production pipeline used by the frontend — NOT isolated functions.
No code changes. Diagnosis/validation only.
"""

import sys
import json
from pathlib import Path
from math import isinf

PROJECT_ROOT = Path(__file__).resolve().parents[0]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.service import (
    mission_from_query,
    profile_from_digital_twin,
    get_digital_twin_for_customer,
    recommend,
    recommendation_engine,
    default_products,
    _product_intelligence_scores,
)
from recommendation_ml.schemas import Mission, CustomerProfile

QUERIES = [
    "I need something for a beach outing",
    "I need something for a party",
    "I need something for college",
    "I need something for a formal office event",
    "I need something casual for an outing",
    "I need something for travel",
    "I need something for the gym",
]

DIVIDER = "=" * 80

def trace_query(query, index):
    """Trace the full pipeline for a single query."""
    print(f"\n{DIVIDER}")
    print(f"QUERY {index}: {query}")
    print(DIVIDER)

    # --- Stage 1: Intent Parsing ---
    print("\n[STAGE 1] INTENT / MISSION PARSING")
    mission, parsed_intent = mission_from_query(query)
    print(f"  goal:              {mission.goal}")
    print(f"  occasion:          {mission.occasion}")
    print(f"  budget:            {mission.budget if not isinf(mission.budget) else 'inf'}")
    print(f"  preferred_categories: {mission.preferred_categories}")
    print(f"  style_preference:  {mission.style_preference}")
    print(f"  discovery_level:   {mission.discovery_level}")
    print(f"  urgency:           {mission.urgency}")
    print(f"  excluded_brands:   {mission.excluded_brands}")
    print(f"  excluded_categories: {mission.excluded_categories}")
    print(f"  Raw parsed intent: {json.dumps({k:v for k,v in parsed_intent.items() if k in ['goal','category','subcategory','occasion','budget','preferences','exclusions','urgency','discovery_level']}, indent=2)}")

    # --- Stage 2: Customer Intelligence ---
    print("\n[STAGE 2] CUSTOMER DIGITAL TWIN")
    twin = get_digital_twin_for_customer("DEMO_USER")
    print(f"  visitorid:         {twin.get('visitorid')}")
    print(f"  primary_persona:   {twin.get('primary_persona')}")
    print(f"  total_interactions: {twin.get('total_interactions')}")
    print(f"  total_views:       {twin.get('total_views')}")
    print(f"  total_transactions: {twin.get('total_transactions')}")
    print(f"  evidence_tier:     {twin.get('evidence_tier')}")

    profile = profile_from_digital_twin("DEMO_USER", twin)
    print(f"  CustomerProfile:")
    print(f"    category_affinity: {profile.category_affinity}")
    print(f"    discovery_appetite: {profile.discovery_appetite}")
    print(f"    price_sensitivity: {profile.price_sensitivity}")
    print(f"    total_purchases:  {profile.total_purchases}")

    # --- Stage 3: Full Pipeline ---
    print("\n[STAGE 3] FULL PIPELINE (via recommend())")
    result = recommend(
        customer_id="DEMO_USER",
        query=query,
        digital_twin=twin,
        top_k=5,
        budget=None,
        discovery_level=None,
    )

    recs = result.get("recommendations", [])
    print(f"  Pipeline stages:   {result.get('pipeline', [])}")
    print(f"  Recommendations:   {len(recs)} items")

    print(f"\n  TOP 5 RECOMMENDATIONS:")
    for rank, rec in enumerate(recs[:5], 1):
        meta = rec.get("metadata", {})
        breakdown = rec.get("score_breakdown", {})
        pi_score = breakdown.get("product_intelligence", "N/A")
        print(f"    #{rank} [{rec['product_id']}] {meta.get('title', 'N/A')}")
        print(f"       Category: {meta.get('category', 'N/A')}  |  Price: {meta.get('price', 0)}")
        print(f"       Final Score: {rec['final_score']:.4f}  |  ML contrib: {rec['final_score'] - float(pi_score or 0) * 0.35:.4f}  |  PI Score: {pi_score}")
        print(f"       Score Breakdown: {json.dumps({k:v for k,v in breakdown.items() if k != 'product_intelligence'}, indent=2)}")
        print(f"       Evidence: {rec.get('evidence', [])}")

    return {
        "query": query,
        "mission": mission.to_dict(),
        "intent": parsed_intent,
        "twin": twin,
        "profile": {
            "category_affinity": profile.category_affinity,
            "discovery_appetite": profile.discovery_appetite,
        },
        "recommendations": [
            {
                "product_id": r["product_id"],
                "title": r.get("metadata", {}).get("title", ""),
                "category": r.get("metadata", {}).get("category", ""),
                "final_score": r["final_score"],
                "pi_score": r.get("score_breakdown", {}).get("product_intelligence"),
            }
            for r in recs[:5]
        ],
        "all_product_ids": [r["product_id"] for r in recs],
    }


def validate_agentic_ai():
    """Verify Agentic AI integration."""
    print(f"\n\n{DIVIDER}")
    print("AGENTIC AI INTEGRATION VERIFICATION")
    print(DIVIDER)

    # Check agentic_ai/tools.py mock tools
    print("\n[1] agentic_ai/tools.py — Mock tools")
    try:
        from agentic_ai.tools import search_products, get_customer_profile
        from agentic_ai.agent import build_graph
        print("  agentic_ai module: importable")

        # Check if mock tools return hardcoded data
        mock_result = search_products("beach")
        print(f"  search_products('beach') returns: {len(mock_result.get('results', []))} items")
        if mock_result.get("results"):
            print(f"    First result: {mock_result['results'][0]}")

        mock_profile = get_customer_profile("DEMO_USER")
        print(f"  get_customer_profile('DEMO_USER'): {mock_profile}")
    except Exception as e:
        print(f"  Error importing agentic_ai: {e}")

    # Check which endpoint frontend calls
    print("\n[2] Frontend endpoint mapping")
    print("  frontend/src/main.jsx → POST /api/recommendations")
    print("  (This is the production pipeline, NOT agentic_ai)")

    # Check agentic endpoints
    print("\n[3] Backend agentic endpoints")
    try:
        from backend.main import app
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        print(f"  Registered routes: {routes}")
    except Exception as e:
        print(f"  Error: {e}")


def compare_results(all_results):
    """Compare recommendation sets across queries."""
    print(f"\n\n{DIVIDER}")
    print("COMPARISON ANALYSIS")
    print(DIVIDER)

    # Build comparison table
    print("\n[1] RECOMMENDATION SETS BY QUERY")
    print("-" * 80)
    for r in all_results:
        ids = r["all_product_ids"][:5]
        print(f"  Q: {r['query'][:50]}")
        print(f"     Mission: category={r['mission']['preferred_categories']}, occasion={r['mission']['occasion']}")
        print(f"     Products: {ids}")
        print()

    # Check uniqueness
    sets = [tuple(r["all_product_ids"][:5]) for r in all_results]
    unique_sets = set(sets)
    print(f"\n[2] UNIQUE RECOMMENDATION SET COUNT: {len(unique_sets)} out of {len(sets)} queries")

    # Pairwise comparisons
    print("\n[3] PAIRWISE COMPARISONS")
    comparisons = [
        (0, 1, "Beach vs Party"),
        (1, 2, "Party vs College"),
        (2, 3, "College vs Formal"),
        (3, 4, "Formal vs Casual"),
        (4, 5, "Casual vs Travel"),
        (5, 6, "Travel vs Gym"),
        (0, 6, "Beach vs Gym"),
    ]
    for i, j, label in comparisons:
        set_i = set(all_results[i]["all_product_ids"][:5])
        set_j = set(all_results[j]["all_product_ids"][:5])
        overlap = set_i & set_j
        unique_i = set_i - set_j
        unique_j = set_j - set_i
        status = "DIFFERENT" if set_i != set_j else "IDENTICAL"
        print(f"  {label}: {status}")
        print(f"    Overlap: {len(overlap)} items")
        if unique_i:
            print(f"    Only in {all_results[i]['query'][:20]}: {unique_i}")
        if unique_j:
            print(f"    Only in {all_results[j]['query'][:20]}: {unique_j}")

    # Check if different occasions produce different results
    print("\n[4] OCCASION DIFFERENTIATION")
    occasion_products = {}
    for r in all_results:
        occ = r["mission"]["occasion"]
        if occ not in occasion_products:
            occasion_products[occ] = set()
        occasion_products[occ].update(r["all_product_ids"][:3])

    for occ, prods in sorted(occasion_products.items()):
        print(f"  {occ}: {prods}")

    # Check PI impact
    print("\n[5] PRODUCT INTELLIGENCE IMPACT")
    pi_changes = 0
    for r in all_results:
        for rec in r["recommendations"]:
            if rec["pi_score"] is not None and rec["pi_score"] != "N/A":
                pi_changes += 1
    print(f"  Total recommendations with PI scores: {pi_changes}")


if __name__ == "__main__":
    print("RETAILMIND FULL END-TO-END VALIDATION")
    print(f"Testing {len(QUERIES)} queries through the production pipeline")
    print(f"Data: {PROJECT_ROOT / 'data'}")
    print(f"Catalog: {PROJECT_ROOT / 'data' / 'catalog.json'}")

    all_results = []
    for i, query in enumerate(QUERIES, 1):
        result = trace_query(query, i)
        all_results.append(result)

    compare_results(all_results)
    validate_agentic_ai()

    print(f"\n\n{DIVIDER}")
    print("VALIDATION COMPLETE")
    print(DIVIDER)
