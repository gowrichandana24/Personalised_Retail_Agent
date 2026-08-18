"""Hard constraint filtering for the recommendation pipeline.

Filters candidates based on budget, brand exclusions, category exclusions,
and other hard constraints before ranking.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from recommendation_ml.schemas import Mission, Product


def filter_by_budget(
    candidates: pd.DataFrame,
    mission: Mission,
    price_col: str = "price",
) -> pd.DataFrame:
    """Filter candidates by budget constraints.

    Args:
        candidates: Product DataFrame with a price column.
        mission: Shopping mission with budget constraints.
        price_col: Name of the price column.

    Returns:
        Filtered DataFrame within budget.
    """
    if candidates.empty or mission.budget == float("inf"):
        return candidates

    mask = candidates[price_col] <= mission.budget

    if mission.min_budget > 0:
        mask = mask & (candidates[price_col] >= mission.min_budget)

    return candidates[mask].copy()


def filter_by_excluded_brands(
    candidates: pd.DataFrame,
    mission: Mission,
    brand_col: str = "brand",
) -> pd.DataFrame:
    """Remove products from excluded brands."""
    if candidates.empty or not mission.excluded_brands:
        return candidates

    excluded = set(b.lower() for b in mission.excluded_brands)
    mask = ~candidates[brand_col].str.lower().isin(excluded)
    return candidates[mask].copy()


def filter_by_excluded_categories(
    candidates: pd.DataFrame,
    mission: Mission,
    category_col: str = "category",
) -> pd.DataFrame:
    """Remove products from excluded categories."""
    if candidates.empty or not mission.excluded_categories:
        return candidates

    excluded = set(c.lower() for c in mission.excluded_categories)
    mask = ~candidates[category_col].str.lower().isin(excluded)
    return candidates[mask].copy()


def filter_by_rating(
    candidates: pd.DataFrame,
    min_rating: float = 0.0,
    rating_col: str = "rating",
) -> pd.DataFrame:
    """Filter products below minimum rating threshold."""
    if candidates.empty or min_rating <= 0:
        return candidates

    return candidates[candidates[rating_col] >= min_rating].copy()


def apply_constraints(
    candidates: pd.DataFrame,
    mission: Mission,
    product_metadata: Optional[dict[str, dict]] = None,
) -> pd.DataFrame:
    """Apply all hard constraints to candidate products.

    This is the main entry point for constraint filtering.

    Args:
        candidates: DataFrame or list of product dicts to filter.
        mission: Shopping mission with constraints.
        product_metadata: Optional product metadata lookup for price/brand info.

    Returns:
        Filtered DataFrame passing all constraints.
    """
    if candidates.empty:
        return candidates

    result = candidates.copy()

    if "price" in result.columns:
        result = filter_by_budget(result, mission)

    if "brand" in result.columns:
        result = filter_by_excluded_brands(result, mission)

    if "category" in result.columns:
        result = filter_by_excluded_categories(result, mission)

    if "rating" in result.columns and mission.min_rating > 0:
        result = filter_by_rating(result, mission.min_rating)

    if product_metadata and "product_id" in result.columns:
        for col in ["price", "brand", "category", "rating"]:
            if col not in result.columns:
                result[col] = result["product_id"].map(
                    lambda pid, c=col: product_metadata.get(pid, {}).get(c, 0.0 if c in ("price", "rating") else "")
                )
        result = filter_by_budget(result, mission)
        result = filter_by_excluded_brands(result, mission)
        result = filter_by_excluded_categories(result, mission)

    return result
