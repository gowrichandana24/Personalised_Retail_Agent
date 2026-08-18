"""Comprehensive test suite for the recommendation ML module.

Run with: python -m pytest recommendation_ml/tests/ -v
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import numpy as np
import pandas as pd
import pytest

from recommendation_ml.config import EventWeights, HybridWeights, RecommendationConfig
from recommendation_ml.data.loader import (
    build_product_metadata_index,
    build_user_item_matrix,
    load_interactions,
    load_products,
    normalize_columns,
    normalize_id,
    time_aware_split,
)
from recommendation_ml.data.synthetic import generate_interactions, generate_test_scenario
from recommendation_ml.engine import RecommendationEngine
from recommendation_ml.evaluation.metrics import (
    catalog_coverage,
    compare_models,
    evaluate_model,
    hit_rate_at_k,
    intra_list_diversity,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)
from recommendation_ml.models.collaborative import CollaborativeModel
from recommendation_ml.models.content import ContentModel
from recommendation_ml.models.hybrid import (
    compute_budget_score,
    compute_intent_score,
    compute_preference_score,
    compute_session_score,
    hybrid_score_candidates,
    normalize_scores,
)
from recommendation_ml.models.popularity import PopularityModel
from recommendation_ml.ranking.constraints import (
    apply_constraints,
    filter_by_budget,
    filter_by_excluded_brands,
    filter_by_excluded_categories,
)
from recommendation_ml.ranking.discovery import (
    boost_discovery_candidates,
    compute_discovery_score,
    compute_novelty_score,
)
from recommendation_ml.ranking.diversity import (
    brand_diversity_score,
    category_diversity_score,
    diversify_recommendations,
)
from recommendation_ml.schemas import (
    CustomerProfile,
    Mission,
    Recommendation,
    RecommendationResult,
    ScoreBreakdown,
)


# ============================================================
# TEST DATA FIXTURES
# ============================================================

@pytest.fixture
def sample_products():
    return pd.DataFrame([
        {"product_id": "1", "title": "Nike Running Shoes", "category": "Sports", "brand": "Nike", "price": 2500, "description": "Running shoes for training", "rating": 4.5},
        {"product_id": "2", "title": "Samsung Galaxy Phone", "category": "Electronics", "brand": "Samsung", "price": 15000, "description": "Smart phone with great camera", "rating": 4.2},
        {"product_id": "3", "title": "Levi's Denim Jeans", "category": "Clothing", "brand": "Levi's", "price": 1800, "description": "Classic denim jeans", "rating": 4.0},
        {"product_id": "4", "title": "Puma Sports Bag", "category": "Sports", "brand": "Puma", "price": 800, "description": "Sports travel bag", "rating": 3.8},
        {"product_id": "5", "title": "Adidas Training Shirt", "category": "Sports", "brand": "Adidas", "price": 1200, "description": "Training t-shirt", "rating": 4.1},
        {"product_id": "6", "title": "Sony Wireless Earbuds", "category": "Electronics", "brand": "Sony", "price": 3500, "description": "Wireless earbuds with noise canceling", "rating": 4.3},
        {"product_id": "7", "title": "H&M Casual Jacket", "category": "Clothing", "brand": "H&M", "price": 1500, "description": "Casual jacket for travel", "rating": 3.9},
        {"product_id": "8", "title": "Apple iPad Tablet", "category": "Electronics", "brand": "Apple", "price": 25000, "description": "Tablet for entertainment", "rating": 4.6},
        {"product_id": "9", "title": "Bajaj Kitchen Mixer", "category": "Home & Kitchen", "brand": "Bajaj", "price": 2000, "description": "Mixer grinder for kitchen", "rating": 4.0},
        {"product_id": "10", "title": "Yonex Badminton Racket", "category": "Sports", "brand": "Yonex", "price": 1800, "description": "Professional badminton racket", "rating": 4.4},
    ])


@pytest.fixture
def sample_interactions():
    rows = []
    customers = ["C1", "C2", "C3"]
    product_weights = {
        "C1": [("1", 5), ("3", 3), ("5", 4), ("7", 2)],
        "C2": [("2", 5), ("6", 4), ("8", 3)],
        "C3": [("4", 3), ("5", 4), ("10", 5)],
    }
    for cust, prods in product_weights.items():
        for pid, strength in prods:
            for _ in range(strength):
                rows.append({
                    "customer_id": cust,
                    "product_id": pid,
                    "event_type": "view",
                    "timestamp": "2024-06-01T10:00:00",
                    "strength": strength,
                })
    return pd.DataFrame(rows)


@pytest.fixture
def sample_mission():
    return Mission(
        goal="Weekend trip",
        occasion="Travel",
        budget=5000,
        preferred_categories=["Sports", "Clothing"],
        excluded_brands=[],
        discovery_level=0.3,
    )


@pytest.fixture
def sample_profile():
    return CustomerProfile(
        customer_id="C1",
        category_affinity={"Sports": 0.8, "Clothing": 0.6, "Electronics": 0.3},
        price_sensitivity=0.6,
        preferred_brands=["Nike", "Adidas"],
        average_spend=1500,
        recent_categories=["Sports", "Clothing"],
        discovery_appetite=0.3,
    )


@pytest.fixture
def engine(sample_interactions, sample_products):
    eng = RecommendationEngine()
    eng.fit(sample_interactions, sample_products)
    return eng


# ============================================================
# SCHEMA TESTS
# ============================================================

class TestSchemas:
    def test_mission_from_dict(self):
        data = {"goal": "Trip", "budget": 3000, "discovery_level": 0.5}
        m = Mission.from_dict(data)
        assert m.goal == "Trip"
        assert m.budget == 3000
        assert m.discovery_level == 0.5

    def test_mission_to_dict(self):
        m = Mission(goal="Gift", budget=2000)
        d = m.to_dict()
        assert d["goal"] == "Gift"
        assert d["budget"] == 2000

    def test_customer_profile_from_dict(self):
        data = {"customer_id": "C1", "price_sensitivity": 0.7}
        p = CustomerProfile.from_dict(data)
        assert p.customer_id == "C1"
        assert p.price_sensitivity == 0.7

    def test_score_breakdown_to_dict(self):
        sb = ScoreBreakdown(collaborative=0.8, content=0.6)
        d = sb.to_dict()
        assert d["collaborative"] == 0.8
        assert d["content"] == 0.6

    def test_recommendation_to_dict(self):
        rec = Recommendation(
            product_id="P1",
            final_score=0.9,
            score_breakdown=ScoreBreakdown(collaborative=0.8),
            evidence=["test"],
        )
        d = rec.to_dict()
        assert d["product_id"] == "P1"
        assert d["final_score"] == 0.9
        assert len(d["evidence"]) == 1

    def test_recommendation_result_to_dict(self):
        result = RecommendationResult(
            recommendations=[Recommendation(product_id="P1")],
            candidate_count=10,
        )
        d = result.to_dict()
        assert len(d["recommendations"]) == 1
        assert d["candidate_count"] == 10


# ============================================================
# DATA LOADING TESTS
# ============================================================

class TestDataLoading:
    def test_normalize_columns(self):
        df = pd.DataFrame({"VisitorID": ["A"], "ItemId": ["1"], "Event": ["view"]})
        result = normalize_columns(df)
        assert "customer_id" in result.columns
        assert "product_id" in result.columns
        assert "event_type" in result.columns

    def test_normalize_id_numeric(self):
        assert normalize_id(123) == "123"
        assert normalize_id(123.0) == "123"

    def test_normalize_id_string(self):
        assert normalize_id("ABC") != ""

    def test_normalize_id_nan(self):
        assert normalize_id(float("nan")) == ""

    def test_load_interactions_from_dataframe(self):
        df = pd.DataFrame({
            "customer_id": ["C1", "C1"],
            "product_id": ["P1", "P2"],
            "event_type": ["view", "purchase"],
            "timestamp": ["2024-01-01", "2024-01-02"],
        })
        result = load_interactions(df)
        assert len(result) == 2
        assert "strength" in result.columns
        assert "time_decay" in result.columns

    def test_load_products_from_dataframe(self):
        df = pd.DataFrame({
            "product_id": ["P1", "P2"],
            "title": ["Product A", "Product B"],
            "category": ["Cat1", "Cat2"],
            "price": [100, 200],
        })
        result = load_products(df)
        assert len(result) == 2
        assert "product_id" in result.columns

    def test_build_user_item_matrix(self, sample_interactions):
        matrix = build_user_item_matrix(sample_interactions)
        assert not matrix.empty
        assert "C1" in matrix.index

    def test_build_product_metadata_index(self, sample_products):
        index = build_product_metadata_index(sample_products)
        assert "1" in index
        assert index["1"]["brand"] == "Nike"

    def test_time_aware_split(self, sample_interactions):
        train, val, test = time_aware_split(sample_interactions)
        assert len(train) > 0
        assert len(train) >= len(val)
        assert len(train) >= len(test)


# ============================================================
# SYNTHETIC DATA TESTS
# ============================================================

class TestSyntheticData:
    def test_generate_interactions(self):
        interactions, products, profiles = generate_interactions(
            n_customers=10, n_products=20, n_interactions=100, seed=42
        )
        assert len(interactions) > 0
        assert len(products) == 20
        assert len(profiles) == 10
        assert "customer_id" in interactions.columns
        assert "product_id" in interactions.columns

    def test_generate_test_scenario(self):
        scenario = generate_test_scenario()
        assert "interactions" in scenario
        assert "products" in scenario
        assert "customer_profiles" in scenario
        assert "mission" in scenario
        assert "test_customer" in scenario


# ============================================================
# POPULARITY MODEL TESTS
# ============================================================

class TestPopularityModel:
    def test_fit_and_get_popular(self, sample_interactions):
        model = PopularityModel()
        model.fit(sample_interactions)
        assert model.is_fitted
        popular = model.get_popular_products(k=5)
        assert len(popular) > 0
        assert popular[0].final_score >= popular[-1].final_score

    def test_empty_fit(self):
        model = PopularityModel()
        model.fit(pd.DataFrame())
        assert model.is_fitted
        assert model.get_popular_products() == []

    def test_get_score(self, sample_interactions):
        model = PopularityModel()
        model.fit(sample_interactions)
        score = model.get_score("1")
        assert 0 <= score <= 1

    def test_recommend_popularity_excludes(self, sample_interactions):
        model = PopularityModel()
        model.fit(sample_interactions)
        recs = model.recommend_popularity("C1", k=3, exclude_ids=["1"])
        rec_ids = [r.product_id for r in recs]
        assert "1" not in rec_ids


# ============================================================
# CONTENT MODEL TESTS
# ============================================================

class TestContentModel:
    def test_fit(self, sample_products):
        model = ContentModel()
        model.fit(sample_products)
        assert model.is_fitted
        assert model.vocabulary_size > 0

    def test_get_product_vector(self, sample_products):
        model = ContentModel()
        model.fit(sample_products)
        vec = model.get_product_vector("1")
        assert vec is not None
        assert len(vec) > 0

    def test_get_content_scores(self, sample_products):
        model = ContentModel()
        model.fit(sample_products)
        pref_vec = model.get_product_vector("1")
        scores = model.get_content_scores(pref_vec, ["2", "3", "4"])
        assert len(scores) == 3
        for score in scores.values():
            assert 0 <= score <= 1

    def test_build_customer_preference_vector(self, sample_products):
        model = ContentModel()
        model.fit(sample_products)
        vec = model.build_customer_preference_vector(["1", "5"])
        assert vec is not None

    def test_empty_candidates(self, sample_products):
        model = ContentModel()
        model.fit(sample_products)
        scores = model.get_content_scores(None, [])
        assert scores == {}


# ============================================================
# COLLABORATIVE MODEL TESTS
# ============================================================

class TestCollaborativeModel:
    def test_fit(self, sample_interactions):
        model = CollaborativeModel()
        model.fit(sample_interactions)
        assert model.is_fitted
        assert model.n_users > 0
        assert model.n_items > 0

    def test_get_collaborative_scores(self, sample_interactions):
        model = CollaborativeModel()
        model.fit(sample_interactions)
        scores = model.get_collaborative_scores("C1", ["1", "2", "3"])
        assert len(scores) == 3
        for score in scores.values():
            assert 0 <= score <= 1

    def test_cold_start_user(self, sample_interactions):
        model = CollaborativeModel()
        model.fit(sample_interactions)
        scores = model.get_collaborative_scores("UNKNOWN", ["1", "2"])
        assert len(scores) == 2
        for score in scores.values():
            assert 0 <= score <= 1

    def test_empty_fit(self):
        model = CollaborativeModel()
        model.fit(pd.DataFrame())
        assert model.is_fitted
        scores = model.get_collaborative_scores("C1", ["P1"])
        assert scores["P1"] == 0.0


# ============================================================
# HYBRID SCORING TESTS
# ============================================================

class TestHybridScoring:
    def test_normalize_scores(self):
        scores = {"A": 0.5, "B": 1.0, "C": 0.0}
        normalized = normalize_scores(scores)
        assert normalized["B"] == 1.0
        assert normalized["C"] == 0.0
        assert 0 <= normalized["A"] <= 1

    def test_normalize_empty(self):
        assert normalize_scores({}) == {}

    def test_normalize_equal(self):
        scores = {"A": 0.5, "B": 0.5}
        normalized = normalize_scores(scores)
        assert all(v == 0.5 for v in normalized.values())

    def test_budget_score(self):
        assert compute_budget_score(100, 500) == 0.7  # budget_utilization=0.2, low
        assert compute_budget_score(350, 500) == 1.0  # budget_utilization=0.7, sweet spot
        assert compute_budget_score(600, 500) == 0.0  # over budget
        assert compute_budget_score(100, 500, min_budget=200) == 0.3  # below min

    def test_intent_score(self):
        m = Mission(preferred_categories=["Sports"])
        assert compute_intent_score("Sports", "Nike", m) > 0.5
        assert compute_intent_score("Electronics", "Samsung", m) < 0.5

    def test_preference_score(self, sample_profile):
        assert compute_preference_score("Sports", "Nike", sample_profile) > 0.5
        assert compute_preference_score("Electronics", "Sony", sample_profile) < 0.5

    def test_preference_score_no_profile(self):
        score = compute_preference_score("Sports", "Nike", None)
        assert score == 0.5

    def test_session_score(self):
        assert compute_session_score("P1", ["P1", "P2"]) == 0.8
        assert compute_session_score("P3", ["P1", "P2"]) == 0.2
        assert compute_session_score("P1", []) == 0.0


# ============================================================
# CONSTRAINT FILTERING TESTS
# ============================================================

class TestConstraints:
    def test_filter_by_budget(self, sample_products):
        mission = Mission(budget=3000)
        filtered = filter_by_budget(sample_products, mission)
        assert all(filtered["price"] <= 3000)

    def test_filter_by_excluded_brands(self, sample_products):
        mission = Mission(excluded_brands=["Nike"])
        filtered = filter_by_excluded_brands(sample_products, mission)
        assert all(b != "Nike" for b in filtered["brand"])

    def test_filter_by_excluded_categories(self, sample_products):
        mission = Mission(excluded_categories=["Electronics"])
        filtered = filter_by_excluded_categories(sample_products, mission)
        assert all(c != "Electronics" for c in filtered["category"])

    def test_apply_all_constraints(self, sample_products):
        mission = Mission(budget=3000, excluded_brands=["Nike"])
        filtered = apply_constraints(sample_products, mission)
        assert all(filtered["price"] <= 3000)
        assert all(b != "Nike" for b in filtered["brand"])

    def test_empty_candidates(self):
        mission = Mission(budget=1000)
        filtered = apply_constraints(pd.DataFrame(), mission)
        assert filtered.empty


# ============================================================
# DIVERSITY TESTS
# ============================================================

class TestDiversity:
    def test_category_diversity_new(self):
        assert category_diversity_score(["A", "B"], "C") == 1.0

    def test_category_diversity_repeat(self):
        score = category_diversity_score(["A", "A"], "A")
        assert score < 1.0

    def test_brand_diversity(self):
        assert brand_diversity_score([], "Nike") == 1.0
        assert brand_diversity_score(["Nike"], "Nike") < 1.0

    def test_diversify_recommendations(self):
        products = [
            {"product_id": "1", "final_score": 0.9, "category": "Sports", "brand": "Nike"},
            {"product_id": "2", "final_score": 0.85, "category": "Sports", "brand": "Adidas"},
            {"product_id": "3", "final_score": 0.8, "category": "Electronics", "brand": "Samsung"},
            {"product_id": "4", "final_score": 0.75, "category": "Clothing", "brand": "Levi's"},
        ]
        result = diversify_recommendations(products, top_k=3, diversity_weight=0.5)
        assert len(result) == 3
        categories = [r["category"] for r in result]
        assert len(set(categories)) > 1


# ============================================================
# DISCOVERY TESTS
# ============================================================

class TestDiscovery:
    def test_novelty_score_new(self):
        assert compute_novelty_score("P1", {"P2", "P3"}, 10) == 1.0

    def test_novelty_score_seen(self):
        assert compute_novelty_score("P1", {"P1", "P2"}, 10) == 0.0

    def test_discovery_score(self):
        score = compute_discovery_score(0.8, 1.0, 0.9, 0.5)
        assert 0 <= score <= 1

    def test_discovery_score_zero_level(self):
        score = compute_discovery_score(0.8, 1.0, 0.9, 0.0)
        assert score == 0.0

    def test_boost_discovery_candidates(self):
        candidates = [
            {"product_id": "P1", "final_score": 0.5, "category": "Sports"},
            {"product_id": "P2", "final_score": 0.4, "category": "Sports"},
        ]
        result = boost_discovery_candidates(
            candidates,
            interacted_products={"P1"},
            discovery_level=0.5,
            mission_categories=["Sports"],
        )
        assert result[1]["discovery_score"] > 0


# ============================================================
# EVALUATION METRICS TESTS
# ============================================================

class TestEvaluation:
    def test_precision_at_k(self):
        recs = ["A", "B", "C", "D", "E"]
        relevant = {"A", "B", "F"}
        assert precision_at_k(recs, relevant, 3) == pytest.approx(2 / 3)
        assert precision_at_k(recs, relevant, 5) == pytest.approx(2 / 5)

    def test_recall_at_k(self):
        recs = ["A", "B", "C"]
        relevant = {"A", "B", "D"}
        assert recall_at_k(recs, relevant, 3) == pytest.approx(2 / 3)

    def test_hit_rate(self):
        assert hit_rate_at_k(["A", "B"], {"A"}, 2) == 1.0
        assert hit_rate_at_k(["C", "D"], {"A"}, 2) == 0.0

    def test_ndcg(self):
        recs = ["A", "B", "C"]
        relevant = {"A", "B"}
        score = ndcg_at_k(recs, relevant, 3)
        assert 0 < score <= 1

    def test_ndcg_empty(self):
        assert ndcg_at_k([], set(), 5) == 0.0

    def test_catalog_coverage(self):
        all_recs = [["A", "B"], ["B", "C"]]
        coverage = catalog_coverage(all_recs, 5)
        assert coverage == 3 / 5

    def test_intra_list_diversity(self):
        assert intra_list_diversity(["A", "B", "C"]) > 0.5
        assert intra_list_diversity(["A", "A", "A"]) == 0.0

    def test_evaluate_model(self):
        recs = {"U1": ["A", "B", "C"], "U2": ["D", "E", "F"]}
        truth = {"U1": {"A", "X"}, "U2": {"D", "Y"}}
        metrics = evaluate_model(recs, truth, k=3)
        assert "precision@3" in metrics
        assert "recall@3" in metrics
        assert "hit_rate@3" in metrics
        assert "ndcg@3" in metrics

    def test_compare_models(self):
        model_a = {"U1": ["A", "B"]}
        model_b = {"U1": ["C", "D"]}
        truth = {"U1": {"A"}}
        df = compare_models({"Popularity": model_a, "Content": model_b}, truth, k=2)
        assert len(df) == 2
        assert "precision@2" in df.columns


# ============================================================
# COLD START TESTS
# ============================================================

class TestColdStart:
    def test_unknown_user_returns_results(self, engine):
        mission = Mission(budget=5000)
        result = engine.recommend("UNKNOWN_USER", mission, top_k=3)
        assert isinstance(result, RecommendationResult)

    def test_new_user_with_profile(self, engine, sample_profile):
        mission = Mission(budget=5000)
        result = engine.recommend(
            "UNKNOWN_USER", mission, customer_profile=sample_profile, top_k=3
        )
        assert isinstance(result, RecommendationResult)


# ============================================================
# MAIN ENGINE TESTS
# ============================================================

class TestRecommendationEngine:
    def test_fit(self, engine):
        assert engine.is_fitted

    def test_recommend_basic(self, engine, sample_mission, sample_profile):
        result = engine.recommend(
            customer_id="C1",
            mission=sample_mission,
            customer_profile=sample_profile,
            top_k=3,
        )
        assert isinstance(result, RecommendationResult)
        assert len(result.recommendations) <= 3
        assert result.candidate_count > 0
        assert len(result.trace) > 0

    def test_recommend_has_scores(self, engine, sample_mission, sample_profile):
        result = engine.recommend("C1", sample_mission, sample_profile, top_k=3)
        for rec in result.recommendations:
            assert 0 <= rec.final_score <= 1
            assert rec.score_breakdown is not None
            assert len(rec.evidence) > 0

    def test_recommend_with_candidates(self, engine, sample_mission, sample_products):
        candidates = sample_products.to_dict("records")
        result = engine.recommend(
            "C1", sample_mission, candidate_products=candidates, top_k=3
        )
        assert len(result.recommendations) <= 3

    def test_recommend_with_budget_constraint(self, engine):
        mission = Mission(budget=2000)
        result = engine.recommend("C1", mission, top_k=5)
        for rec in result.recommendations:
            price = rec.metadata.get("price", 0)
            assert price <= 2000

    def test_recommend_with_brand_exclusion(self, engine):
        mission = Mission(budget=50000, excluded_brands=["Nike"])
        result = engine.recommend("C1", mission, top_k=5)
        for rec in result.recommendations:
            assert rec.metadata.get("brand", "") != "Nike"

    def test_recommend_empty_candidates(self, engine, sample_mission):
        result = engine.recommend(
            "C1", sample_mission, candidate_ids=[], top_k=5
        )
        assert len(result.recommendations) == 0

    def test_rerank_candidates(self, engine, sample_products):
        candidates = [
            {"product_id": "1", "final_score": 0.8, "price": 2500},
            {"product_id": "2", "final_score": 0.7, "price": 15000},
            {"product_id": "3", "final_score": 0.6, "price": 1800},
        ]
        mission = Mission(budget=3000)
        reranked = engine.rerank_candidates(candidates, mission=mission, top_k=2)
        assert len(reranked) == 2
        assert all(c["price"] <= 3000 for c in reranked)

    def test_get_popular_products(self, engine):
        popular = engine.get_popular_products(k=5)
        assert len(popular) > 0
        assert all(isinstance(r, Recommendation) for r in popular)

    def test_get_content_scores(self, engine):
        scores = engine.get_content_scores("C1", ["1", "2", "3"])
        assert len(scores) == 3

    def test_get_collaborative_scores(self, engine):
        scores = engine.get_collaborative_scores("C1", ["1", "2", "3"])
        assert len(scores) == 3


# ============================================================
# END-TO-END TEST
# ============================================================

class TestEndToEnd:
    def test_full_pipeline(self):
        scenario = generate_test_scenario()

        engine = RecommendationEngine()
        engine.fit(scenario["interactions"], scenario["products"])

        customer = scenario["test_customer"]
        mission = Mission(**scenario["mission"])

        profile = CustomerProfile(**customer)

        result = engine.recommend(
            customer_id=profile.customer_id,
            mission=mission,
            customer_profile=profile,
            top_k=5,
        )

        assert isinstance(result, RecommendationResult)
        assert len(result.recommendations) <= 5
        assert result.model_version == "1.0.0"
        assert len(result.trace) > 0

        for rec in result.recommendations:
            assert rec.product_id != ""
            assert 0 <= rec.final_score <= 1
            assert rec.score_breakdown is not None
            assert len(rec.evidence) > 0
            assert 0 <= rec.confidence <= 1
            assert rec.rank > 0

        result_dict = result.to_dict()
        assert "recommendations" in result_dict
        assert "model_version" in result_dict
        assert "candidate_count" in result_dict
        assert "trace" in result_dict

    def test_whatif_pipeline(self):
        scenario = generate_test_scenario()
        engine = RecommendationEngine()
        engine.fit(scenario["interactions"], scenario["products"])

        candidates = [
            {"product_id": "1000", "final_score": 0.8, "price": 2000},
            {"product_id": "1001", "final_score": 0.7, "price": 4000},
            {"product_id": "1002", "final_score": 0.6, "price": 1500},
        ]
        mission = Mission(budget=3000)
        reranked = engine.rerank_candidates(candidates, mission=mission, top_k=2)
        assert len(reranked) == 2

    def test_diversity_pipeline(self):
        scenario = generate_test_scenario()
        engine = RecommendationEngine()
        engine.fit(scenario["interactions"], scenario["products"])

        mission = Mission(
            budget=10000,
            preferred_categories=["Electronics", "Sports", "Clothing"],
        )
        result = engine.recommend(
            customer_id=scenario["test_customer"]["customer_id"],
            mission=mission,
            top_k=5,
        )

        categories = [r.metadata.get("category", "") for r in result.recommendations]
        unique_cats = set(c for c in categories if c)
        assert len(unique_cats) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
