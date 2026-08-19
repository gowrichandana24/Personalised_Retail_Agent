import pandas as pd

from src.product_intelligence import (
    Condition,
    ProductIntelligence
)


def create_test_catalog():

    return pd.DataFrame({

        "itemid": [
            "1001",
            "1002",
            "1003",
            "1004"
        ],

        "category": [
            "fashion",
            "fashion",
            "electronics",
            "fashion"
        ],

        "price": [
            1500,
            2500,
            1800,
            1000
        ],

        "product_text": [
            "stylish casual summer fashion dress",
            "premium stylish fashion jacket",
            "wireless electronic headphones",
            "casual unique cotton fashion shirt"
        ],

        "views": [
            1000,
            500,
            800,
            100
        ],

        "add_to_cart": [
            100,
            50,
            80,
            20
        ],

        "transactions": [
            50,
            20,
            40,
            10
        ],

        "conversion_rate": [
            0.05,
            0.04,
            0.05,
            0.10
        ],

        "smoothed_conversion": [
            0.05,
            0.04,
            0.05,
            0.09
        ],

        "available": [
            True,
            True,
            True,
            True
        ]
    })


def test_condition_creation():

    condition = Condition(
        category="Fashion",
        budget=2000,
        discovery_level="high",
        keywords=[
            "stylish",
            "casual"
        ]
    )

    assert condition.category == "fashion"
    assert condition.budget == 2000
    assert condition.discovery_level == "high"
    assert "stylish" in condition.keywords


def test_recommendation_generation():

    catalog = create_test_catalog()

    engine = ProductIntelligence(
        catalog
    )

    condition = Condition(
        category="fashion",
        budget=2000,
        discovery_level="high",
        keywords=[
            "stylish",
            "casual"
        ]
    )

    results = engine.recommend(
        condition,
        top_k=3
    )

    assert not results.empty

    assert len(results) <= 3

    assert "final_score" in results.columns

    assert "rank" in results.columns


def test_category_filtering():

    catalog = create_test_catalog()

    engine = ProductIntelligence(
        catalog
    )

    condition = Condition(
        category="fashion",
        budget=2000,
        discovery_level="medium",
        keywords=[
            "casual"
        ]
    )

    results = engine.recommend(
        condition,
        top_k=10
    )

    assert all(
        results["category"]
        .str.lower()
        .eq("fashion")
    )


def test_score_contributions():

    catalog = create_test_catalog()

    engine = ProductIntelligence(
        catalog
    )

    condition = Condition(
        category="fashion",
        budget=2000,
        discovery_level="high",
        keywords=[
            "stylish",
            "casual"
        ]
    )

    results = engine.recommend(
        condition,
        top_k=3
    )

    for _, product in results.iterrows():

        contribution_sum = (
            product["category_contribution"]
            +
            product["budget_contribution"]
            +
            product["semantic_contribution"]
            +
            product["quality_contribution"]
            +
            product["discovery_contribution"]
        )

        assert abs(
            contribution_sum
            -
            product["final_score"]
        ) < 1e-6


def test_ranking_order():

    catalog = create_test_catalog()

    engine = ProductIntelligence(
        catalog
    )

    condition = Condition(
        category="fashion",
        budget=2000,
        discovery_level="high",
        keywords=[
            "stylish",
            "casual"
        ]
    )

    results = engine.recommend(
        condition,
        top_k=4
    )

    scores = (
        results["final_score"]
        .tolist()
    )

    assert scores == sorted(
        scores,
        reverse=True
    )


def test_strict_budget():

    catalog = create_test_catalog()

    engine = ProductIntelligence(
        catalog
    )

    condition = Condition(
        category="fashion",
        budget=2000,
        discovery_level="medium",
        keywords=[
            "fashion"
        ],
        strict_budget=True
    )

    results = engine.recommend(
        condition,
        top_k=10
    )

    assert all(
        results["price"] <= 2000
    )


def test_explanation():

    catalog = create_test_catalog()

    engine = ProductIntelligence(
        catalog
    )

    condition = Condition(
        category="fashion",
        budget=2000,
        discovery_level="high",
        keywords=[
            "stylish",
            "casual"
        ]
    )

    results = engine.recommend(
        condition,
        top_k=1
    )

    explanation = engine.explain(
        results.iloc[0],
        condition
    )

    assert "final_score" in explanation
    assert "components" in explanation
    assert "weights" in explanation
    assert "contributions" in explanation

    assert abs(
        sum(
            explanation[
                "contributions"
            ].values()
        )
        -
        explanation[
            "final_score"
        ]
    ) < 1e-6