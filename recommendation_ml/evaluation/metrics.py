"""Offline evaluation metrics for the recommendation pipeline.

Computes Precision@K, Recall@K, HitRate@K, NDCG@K,
catalog coverage, and intra-list diversity.
"""

from __future__ import annotations

import math
from typing import Optional

import numpy as np
import pandas as pd


def precision_at_k(recommended: list[str], relevant: set[str], k: int) -> float:
    """Fraction of top-K recommendations that are relevant."""
    if k == 0:
        return 0.0
    top_k = recommended[:k]
    hits = sum(1 for item in top_k if item in relevant)
    return hits / k


def recall_at_k(recommended: list[str], relevant: set[str], k: int) -> float:
    """Fraction of relevant items that appear in top-K."""
    if not relevant:
        return 0.0
    top_k = recommended[:k]
    hits = sum(1 for item in top_k if item in relevant)
    return hits / len(relevant)


def hit_rate_at_k(recommended: list[str], relevant: set[str], k: int) -> float:
    """Binary: 1 if any relevant item is in top-K, else 0."""
    top_k = recommended[:k]
    return 1.0 if any(item in relevant for item in top_k) else 0.0


def ndcg_at_k(recommended: list[str], relevant: set[str], k: int) -> float:
    """Normalized Discounted Cumulative Gain at K."""
    if k == 0 or not relevant:
        return 0.0

    top_k = recommended[:k]
    dcg = 0.0
    for i, item in enumerate(top_k):
        if item in relevant:
            dcg += 1.0 / math.log2(i + 2)

    ideal_hits = min(len(relevant), k)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_hits))

    if idcg == 0:
        return 0.0

    return dcg / idcg


def catalog_coverage(
    all_recommendations: list[list[str]],
    total_catalog_size: int,
) -> float:
    """Fraction of the catalog that appears in any recommendation list."""
    recommended_items = set()
    for rec_list in all_recommendations:
        recommended_items.update(rec_list)

    if total_catalog_size == 0:
        return 0.0

    return len(recommended_items) / total_catalog_size


def intra_list_diversity(
    recommended_categories: list[str],
) -> float:
    """Intra-list diversity as 1 - fraction of most common category."""
    if not recommended_categories:
        return 0.0

    from collections import Counter
    counts = Counter(recommended_categories)
    most_common_count = counts.most_common(1)[0][1]

    return 1.0 - (most_common_count / len(recommended_categories))


def evaluate_model(
    recommendations_per_user: dict[str, list[str]],
    ground_truth_per_user: dict[str, set[str]],
    k: int = 5,
    product_categories: Optional[dict[str, str]] = None,
) -> dict[str, float]:
    """Run full evaluation for a recommendation model.

    Args:
        recommendations_per_user: Dict of user_id -> list of recommended product IDs.
        ground_truth_per_user: Dict of user_id -> set of relevant product IDs.
        k: Evaluation cutoff.
        product_categories: Optional product_id -> category mapping for diversity.

    Returns:
        Dict of metric_name -> value.
    """
    precisions = []
    recalls = []
    hit_rates = []
    ndcgs = []
    all_rec_lists = []

    for user_id, recommended in recommendations_per_user.items():
        relevant = ground_truth_per_user.get(user_id, set())
        precisions.append(precision_at_k(recommended, relevant, k))
        recalls.append(recall_at_k(recommended, relevant, k))
        hit_rates.append(hit_rate_at_k(recommended, relevant, k))
        ndcgs.append(ndcg_at_k(recommended, relevant, k))
        all_rec_lists.append(recommended[:k])

    metrics = {
        f"precision@{k}": np.mean(precisions) if precisions else 0.0,
        f"recall@{k}": np.mean(recalls) if recalls else 0.0,
        f"hit_rate@{k}": np.mean(hit_rates) if hit_rates else 0.0,
        f"ndcg@{k}": np.mean(ndcgs) if ndcgs else 0.0,
    }

    all_product_ids = set()
    for recs in recommendations_per_user.values():
        all_product_ids.update(recs)
    total_catalog = len(all_product_ids) + 50
    metrics["catalog_coverage"] = catalog_coverage(all_rec_lists, total_catalog)

    if product_categories:
        diversities = []
        for rec_list in all_rec_lists:
            cats = [product_categories.get(pid, "unknown") for pid in rec_list]
            diversities.append(intra_list_diversity(cats))
        metrics["intra_list_diversity"] = np.mean(diversities) if diversities else 0.0
    else:
        metrics["intra_list_diversity"] = 0.0

    return metrics


def compare_models(
    model_results: dict[str, dict[str, list[str]]],
    ground_truth: dict[str, set[str]],
    k: int = 5,
    product_categories: Optional[dict[str, str]] = None,
) -> pd.DataFrame:
    """Compare multiple models side by side.

    Args:
        model_results: Dict of model_name -> {user_id: [recommended_ids]}.
        ground_truth: Dict of user_id -> set of relevant product IDs.
        k: Evaluation cutoff.
        product_categories: Optional category mapping.

    Returns:
        DataFrame with model names as rows and metrics as columns.
    """
    rows = []
    for model_name, recs in model_results.items():
        metrics = evaluate_model(recs, ground_truth, k, product_categories)
        metrics["model"] = model_name
        rows.append(metrics)

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.set_index("model")
        df = df.round(4)

    return df
