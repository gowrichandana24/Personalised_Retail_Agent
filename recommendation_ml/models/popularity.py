"""Popularity baseline recommendation model.

Ranks products by weighted interaction popularity.
This provides a trivial baseline to demonstrate that personalization helps.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from recommendation_ml.config import RecommendationConfig
from recommendation_ml.schemas import Recommendation, ScoreBreakdown


class PopularityModel:
    """Simple popularity-based recommender.

    Products are ranked by total weighted interaction strength.
    """

    def __init__(self, config: Optional[RecommendationConfig] = None):
        self.config = config or RecommendationConfig()
        self._product_popularity: dict[str, float] = {}
        self._max_popularity: float = 1.0
        self._is_fitted = False

    def fit(self, interactions: pd.DataFrame) -> PopularityModel:
        """Compute product popularity from interaction data.

        Args:
            interactions: Preprocessed interactions with 'product_id' and 'strength' columns.

        Returns:
            self
        """
        if interactions.empty:
            self._is_fitted = True
            return self

        pop = interactions.groupby("product_id")["strength"].sum()
        self._product_popularity = pop.to_dict()
        self._max_popularity = pop.max() if len(pop) > 0 else 1.0
        self._is_fitted = True
        return self

    def get_popular_products(self, k: int = 10) -> list[Recommendation]:
        """Get the top-k most popular products.

        Args:
            k: Number of products to return.

        Returns:
            List of Recommendation objects sorted by popularity.
        """
        if not self._product_popularity:
            return []

        sorted_products = sorted(
            self._product_popularity.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:k]

        results = []
        for rank, (product_id, raw_score) in enumerate(sorted_products, 1):
            norm_score = raw_score / self._max_popularity if self._max_popularity > 0 else 0.0
            results.append(Recommendation(
                product_id=product_id,
                final_score=norm_score,
                score_breakdown=ScoreBreakdown(popularity=norm_score),
                evidence=["Popular among all customers"],
                confidence=norm_score,
                rank=rank,
            ))

        return results

    def recommend_popularity(
        self,
        customer_id: str,
        k: int = 10,
        exclude_ids: Optional[list[str]] = None,
    ) -> list[Recommendation]:
        """Get popularity-based recommendations for a specific customer.

        Note: This is still popularity-based, not personalized.
        The customer_id parameter is included for API consistency.

        Args:
            customer_id: Customer identifier (unused for popularity model).
            k: Number of products to return.
            exclude_ids: Product IDs to exclude from recommendations.

        Returns:
            List of Recommendation objects.
        """
        exclude_set = set(exclude_ids or [])
        all_recs = self.get_popular_products(k=k + len(exclude_set))
        return [r for r in all_recs if r.product_id not in exclude_set][:k]

    def get_score(self, product_id: str) -> float:
        """Get normalized popularity score for a single product."""
        if not self._product_popularity or self._max_popularity == 0:
            return 0.0
        raw = self._product_popularity.get(product_id, 0.0)
        return raw / self._max_popularity

    def get_scores(self, product_ids: list[str]) -> dict[str, float]:
        """Get normalized popularity scores for multiple products."""
        return {pid: self.get_score(pid) for pid in product_ids}

    @property
    def is_fitted(self) -> bool:
        return self._is_fitted
