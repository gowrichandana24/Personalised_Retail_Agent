"""Adapters that connect the intent, customer, and recommendation modules."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from agentic_ai.tools import PRODUCT_CATALOGUE
from intent.intent_agent import IntentAgent
from recommendation_ml.engine import RecommendationEngine
from recommendation_ml.schemas import CustomerProfile, Mission


def _as_dict(model: Any) -> dict[str, Any]:
    """Support both Pydantic v1 and v2 models."""
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def default_products() -> list[dict[str, Any]]:
    """Expose the existing catalogue in the ML module's product contract."""
    return [
        {
            "product_id": product["id"],
            "title": product["name"],
            "category": product["category"],
            "brand": "RetailMind",
            "price": product["price"],
            "rating": product["rating"],
            "description": f"{product['style']} {product['category']}",
            "properties": {"style": product["style"]},
        }
        for product in PRODUCT_CATALOGUE
    ]


@lru_cache(maxsize=1)
def recommendation_engine() -> RecommendationEngine:
    """Train once on the bundled sample catalogue for a runnable default.

    Production callers can replace this seed data with their product catalogue
    and event feed without changing the API contract.
    """
    products = default_products()
    interactions = [
        {"customer_id": "seed-1", "product_id": "P001", "event_type": "view", "timestamp": 1720000000000},
        {"customer_id": "seed-1", "product_id": "P002", "event_type": "transaction", "timestamp": 1720100000000},
        {"customer_id": "seed-2", "product_id": "P003", "event_type": "view", "timestamp": 1720200000000},
        {"customer_id": "seed-2", "product_id": "P004", "event_type": "addtocart", "timestamp": 1720300000000},
        {"customer_id": "seed-3", "product_id": "P005", "event_type": "transaction", "timestamp": 1720400000000},
    ]
    return RecommendationEngine().fit(interactions, products)


def mission_from_query(query: str) -> tuple[Mission, dict[str, Any]]:
    """Translate Intent Agent output to Recommendation ML's Mission schema."""
    parsed = _as_dict(IntentAgent().analyze(query))
    category = parsed.get("category")
    mission = Mission(
        goal=parsed.get("goal") or query,
        occasion=parsed.get("occasion") or "",
        budget=parsed.get("budget") if parsed.get("budget") is not None else float("inf"),
        preferred_categories=[category] if category else [],
        excluded_categories=parsed.get("exclusions", []),
        discovery_level=parsed.get("discovery_level", 0.5),
        urgency=parsed.get("urgency") or "medium",
        style_preference=(parsed.get("preferences") or [""])[0],
    )
    return mission, parsed


def profile_from_digital_twin(customer_id: str, twin: dict[str, Any] | None) -> CustomerProfile:
    """Adapt Customer Intelligence's digital-twin fields for ML ranking."""
    twin = twin or {}
    affinity: dict[str, float] = {}
    recent_categories: list[str] = []
    for rank in range(1, 4):
        category = twin.get(f"top_category_{rank}")
        score = twin.get(f"top_category_affinity_{rank}")
        if category is not None:
            affinity[str(category)] = float(score or 0)
    for rank in range(1, 3):
        category = twin.get(f"recent_category_{rank}")
        if category is not None:
            recent_categories.append(str(category))

    interactions = float(twin.get("total_interactions", 0) or 0)
    return CustomerProfile(
        customer_id=str(customer_id),
        category_affinity=affinity,
        recent_categories=recent_categories,
        total_purchases=int(twin.get("total_transactions", 0) or 0),
        total_views=int(twin.get("total_views", 0) or 0),
        discovery_appetite=0.7 if twin.get("is_multi_category") else 0.3,
        price_sensitivity=0.7 if interactions and not twin.get("has_purchased") else 0.5,
    )


def recommend(
    customer_id: str,
    query: str,
    digital_twin: dict[str, Any] | None = None,
    candidate_products: list[dict[str, Any]] | None = None,
    top_k: int = 5,
) -> dict[str, Any]:
    mission, intent = mission_from_query(query)
    profile = profile_from_digital_twin(customer_id, digital_twin)
    candidates = candidate_products or default_products()
    result = recommendation_engine().recommend(
        customer_id=str(customer_id),
        mission=mission,
        customer_profile=profile,
        candidate_products=candidates,
        top_k=top_k,
    )
    payload = result.to_dict()
    payload.update(
        {
            "customer_id": str(customer_id),
            "query": query,
            "intent": intent,
            "mission": mission.to_dict(),
            "customer_profile": profile.to_dict(),
        }
    )
    return payload
