"""Quick demo of the Recommendation ML module.

Run: python demo_recommendation.py
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(__file__))

from recommendation_ml import RecommendationEngine, Mission, CustomerProfile
from recommendation_ml.data.synthetic import generate_test_scenario
from recommendation_ml.evaluation.metrics import evaluate_model, compare_models


def main():
    print("=" * 60)
    print("RetailMind — Recommendation ML Module Demo")
    print("=" * 60)

    # 1. Generate synthetic data
    print("\n[1] Generating synthetic data...")
    scenario = generate_test_scenario()
    print(f"    Interactions: {len(scenario['interactions'])}")
    print(f"    Products: {len(scenario['products'])}")
    print(f"    Customers: {len(scenario['customer_profiles'])}")

    # 2. Initialize and fit engine
    print("\n[2] Fitting recommendation engine...")
    engine = RecommendationEngine()
    engine.fit(scenario["interactions"], scenario["products"])
    print(f"    Model version: {engine.model_version}")
    print(f"    Users: {engine.collaborative_model.n_users}")
    print(f"    Items: {engine.collaborative_model.n_items}")

    # 3. Create a shopping mission
    print("\n[3] Creating shopping mission...")
    mission = Mission(
        goal="Weekend trip",
        occasion="Travel",
        budget=5000,
        preferred_categories=["Sports", "Clothing"],
        excluded_brands=[],
        discovery_level=0.3,
        urgency="medium",
    )
    print(f"    Goal: {mission.goal}")
    print(f"    Budget: Rs.{mission.budget}")
    print(f"    Categories: {mission.preferred_categories}")

    # 4. Create customer profile
    print("\n[4] Loading customer profile...")
    test_customer = scenario["test_customer"]
    profile = CustomerProfile(**test_customer)
    print(f"    Customer: {profile.customer_id}")
    print(f"    Category affinity: {dict(list(profile.category_affinity.items())[:3])}")
    print(f"    Discovery appetite: {profile.discovery_appetite}")

    # 5. Get recommendations
    print("\n[5] Generating recommendations...")
    result = engine.recommend(
        customer_id=profile.customer_id,
        mission=mission,
        customer_profile=profile,
        top_k=5,
    )
    print(f"    Candidates considered: {result.candidate_count}")
    print(f"    Recommendations returned: {len(result.recommendations)}")

    # 6. Display results
    print("\n[6] Recommendations:")
    print("-" * 60)
    for rec in result.recommendations:
        meta = rec.metadata
        print(f"  #{rec.rank} {meta.get('title', 'Unknown')}")
        print(f"     Price: Rs.{meta.get('price', 0):.0f} | "
              f"Category: {meta.get('category', '')} | "
              f"Brand: {meta.get('brand', '')}")
        print(f"     Score: {rec.final_score:.3f} | "
              f"Confidence: {rec.confidence:.3f}")
        print(f"     Evidence: {'; '.join(rec.evidence)}")
        breakdown = rec.score_breakdown.to_dict()
        scores_str = " | ".join(f"{k}={v:.2f}" for k, v in breakdown.items() if v > 0)
        print(f"     Breakdown: {scores_str}")
        print()

    # 7. Decision trace
    print("[7] Decision Trace:")
    print("-" * 60)
    for step in result.trace:
        print(f"    -> {step}")

    # 8. What-if scenario
    print("\n[8] What-If: Budget changed to Rs.3000")
    print("-" * 60)
    candidates_for_rerank = [
        {"product_id": rec.product_id, "final_score": rec.final_score,
         "price": rec.metadata.get("price", 0), "category": rec.metadata.get("category", ""),
         "brand": rec.metadata.get("brand", "")}
        for rec in result.recommendations
    ]
    new_mission = Mission(budget=3000, goal="Weekend trip", preferred_categories=["Sports", "Clothing"])
    reranked = engine.rerank_candidates(candidates_for_rerank, mission=new_mission, top_k=3)
    for i, item in enumerate(reranked, 1):
        print(f"  #{i} {item['product_id']}: score={item['final_score']:.3f}, price=Rs.{item['price']:.0f}")

    # 9. Popularity baseline comparison
    print("\n[9] Popularity Baseline (for comparison):")
    print("-" * 60)
    popular = engine.get_popular_products(k=3)
    for rec in popular:
        print(f"    {rec.product_id}: popularity={rec.final_score:.3f}")

    # 10. Evaluation
    print("\n[10] Offline Evaluation:")
    print("-" * 60)

    customers = [p["customer_id"] for p in scenario["customer_profiles"][:20]]
    ground_truth = {}
    recs_pop = {}
    recs_hybrid = {}

    for cid in customers:
        pop_result = engine.recommend_popularity(cid, k=5) if hasattr(engine, 'recommend_popularity') else engine.get_popular_products(k=5)
        pop_ids = [r.product_id for r in pop_result[:5]]
        recs_pop[cid] = pop_ids

        hybrid_result = engine.recommend(cid, mission, top_k=5)
        hybrid_ids = [r.product_id for r in hybrid_result.recommendations[:5]]
        recs_hybrid[cid] = hybrid_ids

        customer_interactions = scenario["interactions"][scenario["interactions"]["customer_id"] == cid]
        if not customer_interactions.empty:
            relevant = set(customer_interactions["product_id"].head(5).tolist())
            ground_truth[cid] = relevant

    if ground_truth:
        comparison = compare_models(
            {"Popularity": recs_pop, "Hybrid": recs_hybrid},
            ground_truth,
            k=5,
        )
        print(comparison.to_string())
    else:
        print("    No ground truth available for evaluation")

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
