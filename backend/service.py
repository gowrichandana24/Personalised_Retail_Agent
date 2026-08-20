"""Integration service for RetailMind's agent, ML and product modules."""

from __future__ import annotations

import sys
import json
from collections import defaultdict
from functools import lru_cache
from math import isinf
from pathlib import Path
from typing import Any

import pandas as pd

from customer_intelligence import (
    add_behavioural_attributes,
    assign_primary_persona,
    build_categorized_interaction_count,
    build_customer_event_features,
    build_digital_twin,
    build_profile_base,
    compute_historical_affinity,
    compute_recent_affinity,
    enrich_events_with_category,
)
from intent.intent_agent import IntentAgent
from recommendation_ml.engine import RecommendationEngine
from recommendation_ml.schemas import CustomerProfile, Mission

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PRODUCT_INTELLIGENCE_SRC = PROJECT_ROOT / "product_intelligence" / "src"
if str(PRODUCT_INTELLIGENCE_SRC) not in sys.path:
    sys.path.insert(0, str(PRODUCT_INTELLIGENCE_SRC))

from product_intelligence.condition import Condition
from product_intelligence.recommender import ProductIntelligence
from product_intelligence.optimization.bundle import (
    calculate_bundle_score,
    filter_bundles_by_budget,
    generate_bundles,
)


_feedback_events: dict[str, list[dict[str, str]]] = defaultdict(list)
_CATEGORY_ALIASES = {"shoe": "footwear", "shoes": "footwear", "sneaker": "footwear"}
CATALOG_PATH = PROJECT_ROOT / "data" / "catalog.json"
INTERACTIONS_PATH = PROJECT_ROOT / "data" / "interactions.json"


def _as_dict(model: Any) -> dict[str, Any]:
    """Support Pydantic v1 and v2 models."""
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()


def _to_datetime(values: pd.Series) -> pd.Series:
    """Convert epoch-millisecond or ISO timestamp values to datetimes."""
    numeric_values = pd.to_numeric(values, errors="coerce")
    if numeric_values.notna().all():
        return pd.to_datetime(numeric_values, unit="ms", errors="coerce")
    return pd.to_datetime(values, errors="coerce")


def _json_safe(value: Any) -> Any:
    """Convert pandas and NumPy values to values FastAPI can serialize."""
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        try:
            return value.item()
        except ValueError:
            pass
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def customer_profile_from_events(
    customer_id: str,
    events: list[dict[str, Any]],
    item_categories: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build one Customer Intelligence digital twin from raw interaction data.

    `events` follows the RetailRocket contract: timestamp, visitorid, event,
    itemid and optional transactionid. `item_categories` contains timestamp,
    itemid and categoryid. This function is the API boundary for the complete
    customer-intelligence pipeline, rather than requiring the frontend to
    construct an already-derived profile.
    """
    events_df = pd.DataFrame(events)
    required_events = {"timestamp", "visitorid", "event", "itemid"}
    missing_events = required_events - set(events_df.columns)
    if missing_events:
        raise ValueError(f"events missing required fields: {sorted(missing_events)}")
    if events_df.empty:
        raise ValueError("events must contain at least one interaction")

    events_df = events_df.copy()
    if "transactionid" not in events_df.columns:
        events_df["transactionid"] = None
    events_df["datetime"] = _to_datetime(events_df["timestamp"])
    if events_df["datetime"].isna().any():
        raise ValueError("events.timestamp must use ISO format or epoch milliseconds")

    customer_features = build_customer_event_features(events_df)
    category_df = pd.DataFrame(item_categories)
    required_categories = {"timestamp", "itemid", "categoryid"}

    if category_df.empty:
        # Return a valid cold-start twin when category metadata is unavailable.
        profile = customer_features.copy()
        profile["num_categories"] = 0
        profile["max_affinity"] = 0.0
        profile["max_recent_affinity"] = 0.0
        profile["has_purchased"] = (profile["total_transactions"] > 0).astype(int)
        profile["is_multi_category"] = False
        profile["primary_persona"] = "New / Unknown"
        profile["profile_evidence"] = "Low"
        profile["evidence_tier"] = "Cold / New"
        digital_twin = profile
    else:
        missing_categories = required_categories - set(category_df.columns)
        if missing_categories:
            raise ValueError(
                f"item_categories missing required fields: {sorted(missing_categories)}"
            )
        category_df = category_df.copy()
        category_df["timestamp"] = _to_datetime(category_df["timestamp"])
        if category_df["timestamp"].isna().any():
            raise ValueError("item_categories.timestamp must use ISO format or epoch milliseconds")

        enriched_events = enrich_events_with_category(events_df, category_df)
        if enriched_events["categoryid"].notna().any():
            historical_affinity = compute_historical_affinity(enriched_events)
            recent_affinity = compute_recent_affinity(enriched_events)
            categorized_interactions = build_categorized_interaction_count(enriched_events)
            profile = build_profile_base(
                customer_features,
                historical_affinity,
                recent_affinity,
                categorized_interactions,
            )
            profile = assign_primary_persona(profile)
            profile = add_behavioural_attributes(profile)
            digital_twin = build_digital_twin(profile, historical_affinity, recent_affinity)
        else:
            digital_twin = customer_features.copy()
            digital_twin["num_categories"] = 0
            digital_twin["max_affinity"] = 0.0
            digital_twin["max_recent_affinity"] = 0.0
            digital_twin["has_purchased"] = (digital_twin["total_transactions"] > 0).astype(int)
            digital_twin["is_multi_category"] = False
            digital_twin["primary_persona"] = "New / Unknown"
            digital_twin["profile_evidence"] = "Low"
            digital_twin["evidence_tier"] = "Cold / New"

    match = digital_twin[digital_twin["visitorid"].astype(str) == str(customer_id)]
    if match.empty:
        raise ValueError(f"customer_id {customer_id!r} was not found in events")
    return {key: _json_safe(value) for key, value in match.iloc[0].to_dict().items()}


def decide_next_action(intent: dict[str, Any]) -> dict[str, Any]:
    """Choose whether the request is actionable or needs clarification."""
    has_product_signal = any(
        intent.get(field)
        for field in ("category", "subcategory", "occasion", "preferences")
    )
    confidence = float(intent.get("confidence", 0.0) or 0.0)
    if not has_product_signal and confidence < 0.75:
        return {
            "action": "clarify",
            "reason": "The request does not identify a product or shopping context clearly enough.",
            "question": "What kind of product are you shopping for, and what will you use it for?",
        }
    return {
        "action": "recommend",
        "reason": "The intent contains enough product or use-case information to retrieve candidates.",
    }


def agentic_plan(query: str, intent: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run the Agentic AI supervisor to plan the real backend workflow.

    Product selection stays in the dedicated ML/Product Intelligence modules;
    the Agentic AI module supplies the mission-level plan and auditable trace.
    """
    try:
        from agentic_ai.agent import fallback_mission_parser, supervisor

        mission = intent or _as_dict(IntentAgent().analyze(query))
        decision = decide_next_action(mission)
        state: dict[str, Any] = {
            "mission": mission,
            "agent_trace": [],
        }
        if decision["action"] == "clarify":
            return {
                "mode": "agentic_ai_supervisor",
                "decision": decision,
                "mission": mission,
                "actions": ["intent", "clarification"],
                "trace": ["Supervisor: clarification required before retrieval"],
            }
        planned = supervisor(state)
        return {
            "mode": "agentic_ai_supervisor",
            "decision": decision,
            "mission": planned["mission"],
            "actions": planned["selected_actions"],
            "trace": planned["agent_trace"],
        }
    except Exception as error:
        # The deterministic recommendation pipeline remains usable if optional
        # LangGraph/Gemini dependencies are not installed yet.
        return {
            "mode": "deterministic_fallback",
            "mission": {},
            "actions": ["profile", "recommendation", "ranking", "explanation", "quality_check"],
            "trace": [f"Agentic AI unavailable: {type(error).__name__}"],
        }


def default_products() -> list[dict[str, Any]]:
    """Load the shared catalogue used by every recommendation request."""
    if not CATALOG_PATH.exists():
        raise FileNotFoundError(f"Product catalogue not found: {CATALOG_PATH}")
    with CATALOG_PATH.open(encoding="utf-8") as handle:
        products = json.load(handle)
    return [dict(product) for product in products]


@lru_cache(maxsize=1)
def recommendation_engine() -> RecommendationEngine:
    """Fit the hybrid model from the shared catalogue and interactions."""
    if not INTERACTIONS_PATH.exists():
        raise FileNotFoundError(f"Interaction data not found: {INTERACTIONS_PATH}")
    with INTERACTIONS_PATH.open(encoding="utf-8") as handle:
        interactions = json.load(handle)
    return RecommendationEngine().fit(interactions, default_products())


def mission_from_query(
    query: str,
    budget: float | None = None,
    discovery_level: float | None = None,
    conversation_context: dict[str, Any] | None = None,
) -> tuple[Mission, dict[str, Any]]:
    """Translate Intent Agent output to Recommendation ML's Mission schema."""
    parsed = _as_dict(IntentAgent().analyze(query, conversation_context))
    category = parsed.get("category") or parsed.get("subcategory")
    category = _CATEGORY_ALIASES.get(str(category).lower(), category) if category else None
    preferences = parsed.get("preferences") or []
    style_preference = ", ".join(preferences) if preferences else ""
    mission = Mission(
        goal=parsed.get("goal") or query,
        occasion=parsed.get("occasion") or "",
        budget=budget if budget is not None else (parsed.get("budget") or float("inf")),
        preferred_categories=[category] if category else [],
        excluded_brands=[
            value for value in parsed.get("exclusions", [])
            if str(value).lower() in {"nike", "adidas", "puma", "reebok"}
        ],
        excluded_categories=[
            value for value in parsed.get("exclusions", [])
            if str(value).lower() not in {"nike", "adidas", "puma", "reebok"}
        ],
        discovery_level=discovery_level if discovery_level is not None else parsed.get("discovery_level", 0.5),
        urgency=parsed.get("urgency") or "medium",
        style_preference=style_preference,
    )
    parsed["category"] = category
    parsed["budget"] = mission.budget
    parsed["discovery_level"] = mission.discovery_level
    return mission, parsed


def profile_from_digital_twin(customer_id: str, twin: dict[str, Any] | None) -> CustomerProfile:
    """Adapt Customer Intelligence's digital-twin fields for hybrid ranking."""
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


def _product_intelligence_scores(
    products: list[dict[str, Any]], mission: Mission, intent: dict[str, Any]
) -> tuple[dict[str, float], dict[str, list[str]]]:
    """Run the Product Intelligence filter/scoring engine on ML candidates."""
    catalogue = pd.DataFrame(
        [
            {
                "itemid": item["product_id"],
                "category": item.get("category", ""),
                "price": item.get("price", 0),
                "product_text": " ".join(
                    str(value)
                    for value in (item.get("title"), item.get("description"), item.get("category"))
                    if value
                ),
                "available": True,
                "views": max(1, int(float(item.get("rating", 0) or 0) * 100)),
                "smoothed_conversion": float(item.get("rating", 0) or 0) / 5,
            }
            for item in products
        ]
    )
    discovery = "high" if mission.discovery_level >= 0.67 else "low" if mission.discovery_level <= 0.33 else "medium"
    budget = mission.budget if not isinf(mission.budget) else None
    condition = Condition(
        category=intent.get("category"),
        budget=budget,
        discovery_level=discovery,
        keywords=[intent.get("goal", ""), *intent.get("preferences", [])],
        exclude_categories=mission.excluded_categories,
        strict_budget=budget is not None,
    )
    ranked = ProductIntelligence(catalogue).recommend(condition, top_k=len(catalogue))
    if ranked.empty and condition.category:
        condition.category = None
        ranked = ProductIntelligence(catalogue).recommend(condition, top_k=len(catalogue))

    scores = {str(row.itemid): float(row.final_score) for row in ranked.itertuples()}
    evidence = {
        str(row.itemid): [
            "Product Intelligence verified category and budget fit",
            "Product Intelligence applied transparent quality and discovery scoring",
        ]
        for row in ranked.itertuples()
    }
    return scores, evidence


def _build_bundle(recommendations: list[dict[str, Any]], budget: float) -> list[dict[str, Any]]:
    """Select the strongest multi-item bundle using Product Intelligence utilities."""
    if not recommendations or isinf(budget):
        return []
    candidates = [
        {
            "product_id": item["product_id"],
            "title": item.get("metadata", {}).get("title", item["product_id"]),
            "category": item.get("metadata", {}).get("category", ""),
            "price": float(item.get("metadata", {}).get("price", 0)),
            "score": float(item.get("final_score", 0)),
        }
        for item in recommendations
    ]
    bundles = filter_bundles_by_budget(generate_bundles(candidates, min_items=2, max_items=3), budget)
    if not bundles:
        return []
    return list(max(bundles, key=lambda bundle: calculate_bundle_score(bundle, budget)))


def _apply_feedback(customer_id: str, recommendations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Use current-session likes/skips as a lightweight online ranking signal."""
    actions = {event["product_id"]: event["action"] for event in _feedback_events[str(customer_id)]}
    for item in recommendations:
        action = actions.get(item["product_id"])
        if action == "like":
            item["final_score"] = round(min(1.0, item["final_score"] + 0.08), 4)
            item["evidence"] = [*item["evidence"], "Boosted by your positive feedback"]
        elif action == "skip":
            item["final_score"] = round(max(0.0, item["final_score"] - 0.12), 4)
            item["evidence"] = [*item["evidence"], "Deprioritized from your negative feedback"]
    recommendations.sort(key=lambda item: item["final_score"], reverse=True)
    for rank, item in enumerate(recommendations, start=1):
        item["rank"] = rank
    return recommendations


def recommend(
    customer_id: str,
    query: str,
    digital_twin: dict[str, Any] | None = None,
    candidate_products: list[dict[str, Any]] | None = None,
    top_k: int = 5,
    budget: float | None = None,
    discovery_level: float | None = None,
    conversation_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the complete production request pipeline used by the frontend."""
    mission, intent = mission_from_query(
        query, budget, discovery_level, conversation_context
    )
    orchestration = agentic_plan(query, intent)
    decision = orchestration.get("decision", decide_next_action(intent))
    if decision.get("action") == "clarify":
        return {
            "customer_id": str(customer_id),
            "query": query,
            "intent": intent,
            "mission": mission.to_dict(),
            "recommendations": [],
            "bundle": [],
            "needs_clarification": True,
            "clarification_question": decision["question"],
            "pipeline": ["Intent Agent", "Agentic Decision Layer"],
            "agentic_plan": orchestration,
        }
    profile = profile_from_digital_twin(customer_id, digital_twin)
    candidates = candidate_products or default_products()
    ml_result = recommendation_engine().recommend(
        customer_id=str(customer_id),
        mission=mission,
        customer_profile=profile,
        candidate_products=candidates,
        top_k=top_k,
    ).to_dict()
    product_scores, product_evidence = _product_intelligence_scores(candidates, mission, intent)

    recommendations = ml_result["recommendations"]
    for item in recommendations:
        product_score = product_scores.get(item["product_id"], item["final_score"])
        item["score_breakdown"]["product_intelligence"] = round(product_score, 4)
        item["final_score"] = round(0.65 * item["final_score"] + 0.35 * product_score, 4)
        item["evidence"] = list(dict.fromkeys([*item["evidence"], *product_evidence.get(item["product_id"], [])]))
    recommendations = _apply_feedback(customer_id, recommendations)

    response_mission = mission.to_dict()
    response_intent = dict(intent)
    if isinf(mission.budget):
        # JSON has no portable representation for infinity. Keep the internal
        # unbounded budget for ranking, but expose it as null to API clients.
        response_mission["budget"] = None
        response_intent["budget"] = None

    return {
        **ml_result,
        "recommendations": recommendations,
        "bundle": _build_bundle(recommendations, mission.budget),
        "customer_id": str(customer_id),
        "query": query,
        "intent": response_intent,
        "mission": response_mission,
        "customer_profile": profile.to_dict(),
        "pipeline": [
            "Agentic AI Supervisor",
            "Intent Agent",
            "Customer Intelligence",
            "Recommendation ML",
            "Product Intelligence",
            "Bundle Optimizer",
        ],
        "agentic_plan": orchestration,
        "feedback_events": len(_feedback_events[str(customer_id)]),
    }


def record_feedback(customer_id: str, product_id: str, action: str) -> dict[str, Any]:
    """Record a frontend feedback event for the active customer session."""
    allowed_actions = {"like", "save", "cart", "skip"}
    if action not in allowed_actions:
        raise ValueError(f"action must be one of {sorted(allowed_actions)}")
    event = {"product_id": product_id, "action": action}
    _feedback_events[str(customer_id)] = [
        item for item in _feedback_events[str(customer_id)] if item["product_id"] != product_id
    ]
    _feedback_events[str(customer_id)].append(event)
    return {"status": "recorded", "customer_id": str(customer_id), **event}


def get_digital_twin_for_customer(customer_id: str) -> dict[str, Any]:
    """Build a digital twin for a customer from the shared interactions dataset.

    Loads interactions from data/interactions.json, builds a Customer Intelligence
    digital twin, and returns it as a dictionary suitable for the recommendation
    pipeline.

    For customers not found in the dataset, returns a cold-start profile.
    """
    if not INTERACTIONS_PATH.exists():
        raise FileNotFoundError(f"Interaction data not found: {INTERACTIONS_PATH}")

    with INTERACTIONS_PATH.open(encoding="utf-8") as handle:
        interactions = json.load(handle)

    # Convert simplified interactions format to RetailRocket format
    events = []
    for interaction in interactions:
        events.append({
            "timestamp": interaction.get("timestamp", ""),
            "visitorid": interaction.get("customer_id", ""),
            "event": interaction.get("event_type", "view"),
            "itemid": interaction.get("product_id", ""),
            "transactionid": interaction.get("transactionid", None),
        })

    if not events:
        raise ValueError("No interactions found")

    # Build digital twin using Customer Intelligence
    events_df = pd.DataFrame(events)
    events_df["datetime"] = _to_datetime(events_df["timestamp"])

    customer_features = build_customer_event_features(events_df)

    # Build a minimal profile (no category enrichment from item_property files)
    profile = customer_features.copy()
    profile["num_categories"] = 0
    profile["max_affinity"] = 0.0
    profile["max_recent_affinity"] = 0.0
    profile["has_purchased"] = (profile["total_transactions"] > 0).astype(int)
    profile["is_multi_category"] = False
    profile["primary_persona"] = "New / Unknown"
    profile["profile_evidence"] = "Low"
    profile["evidence_tier"] = "Cold / New"

    # Look up the specific customer
    match = profile[profile["visitorid"].astype(str) == str(customer_id)]
    if match.empty:
        # Customer not in dataset — return cold-start profile
        return {
            "visitorid": str(customer_id),
            "primary_persona": "New / Unknown",
            "profile_evidence": "Low",
            "evidence_tier": "Cold / New",
            "total_interactions": 0,
            "total_views": 0,
            "total_cart_adds": 0,
            "total_transactions": 0,
            "unique_products": 0,
            "recency_days": None,
            "purchase_recency_days": None,
            "num_categories": 0,
            "max_affinity": 0.0,
            "max_recent_affinity": 0.0,
            "has_purchased": 0,
            "is_multi_category": False,
            "is_recently_active": False,
            "is_highly_active": False,
            "is_cart_heavy": False,
        }

    return {key: _json_safe(value) for key, value in match.iloc[0].to_dict().items()}
