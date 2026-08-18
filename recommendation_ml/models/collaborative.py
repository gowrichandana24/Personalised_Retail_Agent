"""Collaborative filtering recommendation model.

Uses a lightweight matrix factorization approach (ALS-style) for
implicit feedback collaborative filtering.

Falls back to user-item similarity when factorization is not feasible.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from recommendation_ml.config import RecommendationConfig
from recommendation_ml.schemas import Recommendation, ScoreBreakdown


class CollaborativeModel:
    """Lightweight collaborative filtering model.

    Uses ALS-style matrix factorization for implicit feedback data.
    Falls back to user-based similarity for cold-start cases.
    """

    def __init__(self, config: Optional[RecommendationConfig] = None):
        self.config = config or RecommendationConfig()
        self._user_factors: Optional[np.ndarray] = None
        self._item_factors: Optional[np.ndarray] = None
        self._user_index: dict[str, int] = {}
        self._item_index: dict[str, int] = {}
        self._item_popularity: dict[str, float] = {}
        self._user_item_matrix: Optional[np.ndarray] = None
        self._is_fitted = False

    def fit(self, interactions: pd.DataFrame) -> CollaborativeModel:
        """Fit the collaborative model from interaction data.

        Args:
            interactions: Preprocessed interactions with customer_id, product_id, strength.

        Returns:
            self
        """
        if interactions.empty:
            self._is_fitted = True
            return self

        agg = interactions.groupby(["customer_id", "product_id"])["strength"].sum().reset_index()

        users = sorted(agg["customer_id"].unique())
        items = sorted(agg["product_id"].unique())

        self._user_index = {u: i for i, u in enumerate(users)}
        self._item_index = {p: i for i, p in enumerate(items)}

        n_users = len(users)
        n_items = len(items)

        matrix = np.zeros((n_users, n_items))
        for _, row in agg.iterrows():
            uid = self._user_index[row["customer_id"]]
            iid = self._item_index[row["product_id"]]
            matrix[uid, iid] = row["strength"]

        self._user_item_matrix = matrix

        pop = interactions.groupby("product_id")["strength"].sum()
        pop_max = pop.max() if len(pop) > 0 else 1.0
        self._item_popularity = {pid: pop.get(pid, 0.0) / pop_max for pid in items}

        self._fit_als(matrix)

        self._is_fitted = True
        return self

    def _fit_als(self, matrix: np.ndarray) -> None:
        """Fit ALS matrix factorization.

        Uses confidence-weighted ALS for implicit feedback.
        """
        n_users, n_items = matrix.shape
        k = min(self.config.collaborative_n_components, min(n_users, n_items) - 1)

        if k <= 0:
            self._user_factors = np.random.randn(n_users, 1) * 0.01
            self._item_factors = np.random.randn(n_items, 1) * 0.01
            return

        rng = np.random.RandomState(self.config.random_seed)
        self._user_factors = rng.randn(n_users, k) * 0.01
        self._item_factors = rng.randn(n_items, k) * 0.01

        alpha = 1.0
        lambda_reg = self.config.collaborative_regularization
        confidence = 1 + alpha * matrix

        for iteration in range(self.config.collaborative_iterations):
            for u in range(n_users):
                Cu = np.diag(confidence[u])
                YtY = self._item_factors.T @ self._item_factors
                A = YtY + self._item_factors.T @ Cu @ self._item_factors + lambda_reg * np.eye(k)
                b = self._item_factors.T @ Cu @ (matrix[u] > 0).astype(float)
                self._user_factors[u] = np.linalg.solve(A, b)

            for i in range(n_items):
                Ci = np.diag(confidence[:, i])
                XtX = self._user_factors.T @ self._user_factors
                A = XtX + self._user_factors.T @ Ci @ self._user_factors + lambda_reg * np.eye(k)
                b = self._user_factors.T @ Ci @ (matrix[:, i] > 0).astype(float)
                self._item_factors[i] = np.linalg.solve(A, b)

    def _predict_user_item(self, user_idx: int, item_idx: int) -> float:
        """Predict affinity score for a user-item pair."""
        if self._user_factors is None or self._item_factors is None:
            return 0.0
        score = self._user_factors[user_idx] @ self._item_factors[item_idx]
        return float(score)

    def get_collaborative_scores(
        self,
        user_id: str,
        candidate_product_ids: list[str],
    ) -> dict[str, float]:
        """Get collaborative filtering scores for candidate products.

        Args:
            user_id: Customer identifier.
            candidate_product_ids: Products to score.

        Returns:
            Dict mapping product_id to normalized score (0-1).
        """
        scores = {}

        if user_id not in self._user_index:
            for pid in candidate_product_ids:
                scores[pid] = self._item_popularity.get(pid, 0.0)
            return scores

        user_idx = self._user_index[user_id]
        raw_scores = []

        for pid in candidate_product_ids:
            if pid in self._item_index:
                item_idx = self._item_index[pid]
                raw_scores.append((pid, self._predict_user_item(user_idx, item_idx)))
            else:
                raw_scores.append((pid, 0.0))

        if not raw_scores:
            return scores

        vals = [s for _, s in raw_scores]
        min_val = min(vals)
        max_val = max(vals)
        val_range = max_val - min_val

        for pid, raw in raw_scores:
            if val_range > 0:
                scores[pid] = (raw - min_val) / val_range
            else:
                scores[pid] = 0.5

        return scores

    def get_user_similar_items(
        self,
        user_id: str,
        candidate_product_ids: list[str],
        interactions: Optional[pd.DataFrame] = None,
    ) -> dict[str, float]:
        """Fallback: compute item-item similarity from user's history.

        Used when ALS factorization is not available or for cold-start.
        """
        if user_id not in self._user_index or interactions is None:
            return {pid: 0.0 for pid in candidate_product_ids}

        user_idx = self._user_index[user_id]
        if self._user_item_matrix is None:
            return {pid: 0.0 for pid in candidate_product_ids}

        user_vector = self._user_item_matrix[user_idx]
        interacted_items = np.where(user_vector > 0)[0]

        if len(interacted_items) == 0:
            return {pid: 0.0 for pid in candidate_product_ids}

        item_vectors = self._user_item_matrix.T

        scores = {}
        for pid in candidate_product_ids:
            if pid not in self._item_index:
                scores[pid] = 0.0
                continue

            item_idx = self._item_index[pid]
            item_vec = item_vectors[item_idx]

            sims = []
            for int_idx in interacted_items:
                int_vec = item_vectors[int_idx]
                dot = np.dot(item_vec, int_vec)
                norm = np.linalg.norm(item_vec) * np.linalg.norm(int_vec)
                if norm > 0:
                    sims.append(dot / norm)

            scores[pid] = float(np.mean(sims)) if sims else 0.0

        min_s = min(scores.values()) if scores else 0
        max_s = max(scores.values()) if scores else 1
        rng = max_s - min_s
        if rng > 0:
            scores = {k: (v - min_s) / rng for k, v in scores.items()}
        else:
            scores = {k: 0.5 for k in scores}

        return scores

    @property
    def is_fitted(self) -> bool:
        return self._is_fitted

    @property
    def n_users(self) -> int:
        return len(self._user_index)

    @property
    def n_items(self) -> int:
        return len(self._item_index)
