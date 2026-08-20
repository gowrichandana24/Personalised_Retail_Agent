"""Hybrid scoring engine that combines multiple recommendation signals.

Normalizes individual scores and combines them using configurable weights.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from recommendation_ml.config import HybridWeights, RecommendationConfig
from recommendation_ml.schemas import Mission, CustomerProfile, ScoreBreakdown


def normalize_scores(scores: dict[str, float]) -> dict[str, float]:
    """Normalize scores to 0-1 range using min-max normalization.

    Args:
        scores: Dict of product_id -> raw score.

    Returns:
        Dict of product_id -> normalized score.
    """
    if not scores:
        return {}

    values = list(scores.values())
    min_val = min(values)
    max_val = max(values)
    val_range = max_val - min_val

    if val_range == 0:
        return {k: 0.5 for k in scores}

    return {k: (v - min_val) / val_range for k, v in scores.items()}


def compute_budget_score(price: float, budget: float, min_budget: float = 0.0) -> float:
    """Compute budget fit score.

    Products within budget get a score based on how well they fit.
    Products that are too expensive get 0.
    Products that are very cheap relative to budget also get slightly lower scores
    (they might be too cheap / low quality).

    Args:
        price: Product price.
        budget: Maximum budget.
        min_budget: Minimum budget if provided.

    Returns:
        Budget fit score between 0 and 1.
    """
    if price > budget:
        return 0.0

    if min_budget > 0 and price < min_budget:
        return 0.3

    if budget == 0:
        return 1.0

    budget_utilization = price / budget
    if budget_utilization <= 0.3:
        return 0.7
    elif budget_utilization <= 0.8:
        return 1.0
    else:
        return 0.9


def compute_intent_score(
    product_category: str,
    product_brand: str,
    mission: Mission,
) -> float:
    """Compute mission/intent fit score for a product.

    Args:
        product_category: Product's category.
        product_brand: Product's brand.
        mission: Current shopping mission.

    Returns:
        Intent match score between 0 and 1.
    """
    score = 0.0
    total_weight = 0.0

    if mission.preferred_categories:
        cat_match = any(
            c.lower() in product_category.lower()
            for c in mission.preferred_categories
        )
        score += 0.5 if cat_match else 0.0
        total_weight += 0.5

    if mission.preferred_brands:
        brand_match = any(
            b.lower() == product_brand.lower()
            for b in mission.preferred_brands
        )
        score += 0.3 if brand_match else 0.0
        total_weight += 0.3

    if mission.occasion:
        occasion_match = mission.occasion.lower() in product_category.lower()
        score += 0.2 if occasion_match else 0.0
        total_weight += 0.2

    if total_weight == 0:
        return 0.5

    return score / total_weight


def compute_preference_score(
    product_category: str,
    product_brand: str,
    profile: Optional[CustomerProfile],
) -> float:
    """Compute customer preference fit score.

    Args:
        product_category: Product's category.
        product_brand: Product's brand.
        profile: Customer digital twin.

    Returns:
        Preference score between 0 and 1.
    """
    if profile is None:
        return 0.5

    score = 0.0
    total_weight = 0.0

    if profile.category_affinity:
        cat_affinity = profile.category_affinity.get(product_category, 0.0)
        score += cat_affinity * 0.6
        total_weight += 0.6

    if profile.preferred_brands:
        brand_match = product_brand.lower() in [b.lower() for b in profile.preferred_brands]
        brand_score = 0.8 if brand_match else 0.2
        score += brand_score * 0.4
        total_weight += 0.4

    if total_weight == 0:
        return 0.5

    return score / total_weight


def compute_session_score(
    product_id: str,
    session_product_ids: list[str],
) -> float:
    """Compute session relevance score.

    Products similar to those in the current session get a boost.

    Args:
        product_id: Product to score.
        session_product_ids: Products already in the session.

    Returns:
        Session relevance score between 0 and 1.
    """
    if not session_product_ids:
        return 0.0

    if product_id in session_product_ids:
        return 0.8

    return 0.2


def hybrid_score_product(
    product_id: str,
    collaborative_score: float,
    content_score: float,
    popularity_score: float,
    mission: Mission,
    profile: Optional[CustomerProfile],
    session_product_ids: Optional[list[str]] = None,
    weights: Optional[HybridWeights] = None,
) -> tuple[float, ScoreBreakdown]:
    """Compute the hybrid score for a single product.

    Args:
        product_id: Product identifier.
        collaborative_score: Collaborative filtering score (0-1).
        content_score: Content-based score (0-1).
        popularity_score: Popularity score (0-1).
        mission: Current shopping mission.
        profile: Customer digital twin.
        session_product_ids: Products in the current session.
        weights: Configurable hybrid scoring weights.

    Returns:
        Tuple of (final_score, score_breakdown).
    """
    if weights is None:
        weights = HybridWeights()

    session_ids = session_product_ids or mission.session_product_ids

    budget_score = compute_budget_score(0.0, mission.budget, mission.min_budget)
    intent_score = 0.5
    preference_score = 0.5
    session_score = compute_session_score(product_id, session_ids)
    discovery_score = 0.0

    breakdown = ScoreBreakdown(
        collaborative=collaborative_score,
        content=content_score,
        intent=intent_score,
        preference=preference_score,
        budget=budget_score,
        session=session_score,
        popularity=popularity_score,
        discovery=discovery_score,
    )

    final = (
        weights.collaborative * collaborative_score
        + weights.content * content_score
        + weights.intent * intent_score
        + weights.customer_preference * preference_score
        + weights.popularity * popularity_score
        + weights.session_relevance * session_score
        + weights.discovery * discovery_score
    )

    return final, breakdown


def hybrid_score_candidates(
    candidate_ids: list[str],
    collaborative_scores: dict[str, float],
    content_scores: dict[str, float],
    popularity_scores: dict[str, float],
    product_metadata: dict[str, dict],
    mission: Mission,
    profile: Optional[CustomerProfile] = None,
    weights: Optional[HybridWeights] = None,
) -> list[dict]:
    """Score all candidate products using the hybrid model.

    Args:
        candidate_ids: List of candidate product IDs.
        collaborative_scores: Collaborative scores for candidates.
        content_scores: Content scores for candidates.
        popularity_scores: Popularity scores for candidates.
        product_metadata: Product metadata lookup.
        mission: Current shopping mission.
        profile: Customer digital twin.
        weights: Configurable hybrid weights.

    Returns:
        List of dicts with product_id, final_score, and score_breakdown.
    """
    if weights is None:
        weights = HybridWeights()
    weights.normalize()

    results = []

    for pid in candidate_ids:
        meta = product_metadata.get(pid, {})
        collab = collaborative_scores.get(pid, 0.0)
        content = content_scores.get(pid, 0.0)
        pop = popularity_scores.get(pid, 0.0)

        product_category = meta.get("category", "")
        product_brand = meta.get("brand", "")
        price = meta.get("price", 0.0)

        budget_score = compute_budget_score(price, mission.budget, mission.min_budget)
        intent_score = compute_intent_score(product_category, product_brand, mission)
        preference_score = compute_preference_score(product_category, product_brand, profile)
        session_score = compute_session_score(pid, mission.session_product_ids)

        breakdown = ScoreBreakdown(
            collaborative=collab,
            content=content,
            intent=intent_score,
            preference=preference_score,
            budget=budget_score,
            session=session_score,
            popularity=pop,
            discovery=0.0,
        )

        final = (
            weights.collaborative * collab
            + weights.content * content
            + weights.intent * intent_score
            + weights.customer_preference * preference_score
            + weights.popularity * pop
            + weights.session_relevance * session_score
            + weights.discovery * 0.0
        )

        results.append({
            "product_id": pid,
            "final_score": final,
            "score_breakdown": breakdown,
            "category": product_category,
            "brand": product_brand,
            "price": price,
            "title": meta.get("title", ""),
        })

    results.sort(key=lambda x: x["final_score"], reverse=True)
    return results
