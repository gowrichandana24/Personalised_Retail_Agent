"""Discovery / serendipity scoring for the recommendation pipeline.

Injects controlled novelty into recommendations by boosting
products that are relevant but less historically familiar to the customer.
"""

from __future__ import annotations

from typing import Optional

import numpy as np


def compute_novelty_score(
    product_id: str,
    interacted_products: set[str],
    total_products: int,
) -> float:
    """Compute novelty score for a product.

    Novelty is higher when the product has NOT been seen/interacted with.
    Uses inverse popularity as a proxy for novelty.

    Args:
        product_id: Product identifier.
        interacted_products: Set of product IDs the customer has interacted with.
        total_products: Total number of products in the catalogue.

    Returns:
        Novelty score between 0 and 1.
    """
    if product_id in interacted_products:
        return 0.0
    return 1.0


def compute_discovery_score(
    relevance_score: float,
    novelty_score: float,
    mission_fit: float,
    discovery_level: float = 0.3,
) -> float:
    """Compute discovery score combining relevance, novelty, and mission fit.

    Conceptually:
        DiscoveryScore = Relevance × Novelty × MissionFit

    With a configurable discovery_level that controls how much
    novelty is encouraged.

    Args:
        relevance_score: Base relevance score (0-1).
        novelty_score: Novelty score (0-1).
        mission_fit: Mission/category fit score (0-1).
        discovery_level: How much discovery is encouraged (0-1).

    Returns:
        Discovery score between 0 and 1.
    """
    if discovery_level <= 0:
        return 0.0

    raw_discovery = relevance_score * novelty_score * mission_fit
    weighted = raw_discovery * discovery_level
    return min(1.0, max(0.0, weighted))


def boost_discovery_candidates(
    candidates: list[dict],
    interacted_products: set[str],
    discovery_level: float = 0.3,
    discovery_weight: float = 0.4,
    score_col: str = "final_score",
    product_id_col: str = "product_id",
    category_col: str = "category",
    mission_categories: Optional[list[str]] = None,
) -> list[dict]:
    """Boost scores of discovery-worthy candidates.

    Products that are novel (not previously interacted with) and
    mission-relevant get a discovery bonus.

    Args:
        candidates: List of product dicts.
        interacted_products: Set of product IDs in customer history.
        discovery_level: Discovery preference (0-1).
        discovery_weight: Weight for discovery bonus in final score.
        score_col: Key for score in product dict.
        product_id_col: Key for product ID.
        category_col: Key for category.
        mission_categories: Categories relevant to the current mission.

    Returns:
        Updated list with discovery scores added.
    """
    if discovery_level <= 0 or not candidates:
        return candidates

    mission_cats = set(mission_categories or [])
    total = len(candidates) + len(interacted_products) + 1

    for candidate in candidates:
        pid = candidate.get(product_id_col, "")
        cat = candidate.get(category_col, "")
        base_score = candidate.get(score_col, 0.0)

        novelty = compute_novelty_score(pid, interacted_products, total)
        mission_fit = 1.0 if cat in mission_cats else 0.3

        discovery = compute_discovery_score(base_score, novelty, mission_fit, discovery_level)
        candidate["discovery_score"] = discovery

        if novelty > 0.5:
            boosted = base_score * (1 + discovery_weight * discovery_level)
            candidate[score_col] = min(1.0, boosted)

    return candidates


def get_discovery_candidates(
    all_products: list[dict],
    interacted_products: set[str],
    mission_categories: list[str],
    budget: float = float("inf"),
    top_k: int = 10,
    price_col: str = "price",
    category_col: str = "category",
) -> list[dict]:
    """Find discovery candidates from the full catalogue.

    Selects products the customer hasn't interacted with that match
    the mission's categories.

    Args:
        all_products: Full product catalogue as list of dicts.
        interacted_products: Set of product IDs in customer history.
        mission_categories: Categories relevant to the mission.
        budget: Maximum budget constraint.
        top_k: Number of candidates to return.
        price_col: Key for price.
        category_col: Key for category.

    Returns:
        List of discovery candidate dicts.
    """
    mission_cat_set = set(c.lower() for c in mission_categories)

    candidates = []
    for product in all_products:
        pid = product.get("product_id", "")
        if pid in interacted_products:
            continue

        price = product.get(price_col, 0)
        if price > budget:
            continue

        cat = product.get(category_col, "").lower()
        if mission_cat_set and cat in mission_cat_set:
            candidates.append(product)

    if len(candidates) > top_k:
        candidates = candidates[:top_k]

    return candidates
