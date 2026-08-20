"""Diversity-aware ranking for the recommendation pipeline.

Ensures the final recommendation list is not dominated by
products from a single category or brand.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from recommendation_ml.config import RecommendationConfig


def category_diversity_score(
    selected_categories: list[str],
    candidate_category: str,
) -> float:
    """Compute diversity bonus for adding a candidate from a new category.

    Returns a higher score when the candidate adds category diversity.
    """
    if not selected_categories:
        return 1.0

    if candidate_category not in selected_categories:
        return 1.0

    repetition_count = selected_categories.count(candidate_category)
    return 1.0 / (1.0 + repetition_count)


def brand_diversity_score(
    selected_brands: list[str],
    candidate_brand: str,
) -> float:
    """Compute diversity bonus for adding a candidate from a new brand."""
    if not selected_brands:
        return 1.0

    if candidate_brand not in selected_brands:
        return 1.0

    repetition_count = selected_brands.count(candidate_brand)
    return 1.0 / (1.0 + repetition_count)


def mmr_diversify(
    candidates: list[str],
    scores: dict[str, float],
    features: dict[str, np.ndarray],
    lambda_param: float = 0.7,
    top_k: int = 5,
) -> list[str]:
    """Maximal Marginal Relevance diversification.

    Balances relevance with diversity using a similarity-aware selection.

    Args:
        candidates: List of candidate product IDs.
        scores: Dict of product_id -> relevance score.
        features: Dict of product_id -> feature vector.
        lambda_param: Trade-off between relevance (1.0) and diversity (0.0).
        top_k: Number of items to select.

    Returns:
        Diversified list of product IDs.
    """
    if not candidates:
        return []

    selected = []
    remaining = list(candidates)

    while remaining and len(selected) < top_k:
        best_score = -float("inf")
        best_idx = 0

        for i, candidate in enumerate(remaining):
            relevance = scores.get(candidate, 0.0)

            max_sim = 0.0
            if selected and candidate in features:
                cand_feat = features[candidate]
                for sel in selected:
                    if sel in features:
                        sim = float(np.dot(cand_feat, features[sel]) / (
                            np.linalg.norm(cand_feat) * np.linalg.norm(features[sel]) + 1e-8
                        ))
                        max_sim = max(max_sim, sim)

            mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim

            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = i

        selected.append(remaining.pop(best_idx))

    return selected


def diversify_recommendations(
    ranked_products: list[dict],
    top_k: int = 5,
    diversity_weight: float = 0.3,
    category_col: str = "category",
    brand_col: str = "brand",
    score_col: str = "final_score",
) -> list[dict]:
    """Apply diversity-aware re-ranking to a sorted product list.

    Uses a greedy approach: each position considers both the original
    score and a diversity bonus for adding new categories/brands.

    Args:
        ranked_products: List of product dicts with scores and metadata.
        top_k: Number of products to return.
        diversity_weight: Weight for diversity bonus (0-1).
        category_col: Key for category in product dict.
        brand_col: Key for brand in product dict.
        score_col: Key for score in product dict.

    Returns:
        Re-ranked list of product dicts.
    """
    if not ranked_products:
        return []

    selected = []
    remaining = list(ranked_products)
    selected_categories = []
    selected_brands = []

    while remaining and len(selected) < top_k:
        best_score = -float("inf")
        best_idx = 0

        for i, product in enumerate(remaining):
            base_score = product.get(score_col, 0.0)

            cat = product.get(category_col, "")
            brand = product.get(brand_col, "")

            cat_div = category_diversity_score(selected_categories, cat)
            brand_div = brand_diversity_score(selected_brands, brand)
            diversity_bonus = (cat_div + brand_div) / 2.0

            combined = (1 - diversity_weight) * base_score + diversity_weight * diversity_bonus

            if combined > best_score:
                best_score = combined
                best_idx = i

        chosen = remaining.pop(best_idx)
        selected.append(chosen)
        selected_categories.append(chosen.get(category_col, ""))
        selected_brands.append(chosen.get(brand_col, ""))

    return selected
