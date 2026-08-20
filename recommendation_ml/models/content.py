"""Content-based recommendation model using TF-IDF.

Uses product metadata (title, category, brand, description) to compute
similarity between customer preference vectors and candidate products.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from recommendation_ml.config import RecommendationConfig
from recommendation_ml.schemas import Recommendation, ScoreBreakdown, CustomerProfile


def _build_product_text(row: pd.Series) -> str:
    """Build a text representation from product metadata."""
    parts = []
    for field in ["title", "category", "brand", "description"]:
        val = str(row.get(field, "")).strip()
        if val and val.lower() not in ("", "nan", "none"):
            parts.append(val)
    props = row.get("properties", {})
    if isinstance(props, dict):
        for k, v in props.items():
            parts.append(f"{k} {v}")
    return " ".join(parts)


class ContentModel:
    """Content-based recommender using TF-IDF + cosine similarity.

    Builds a TF-IDF matrix over product metadata and computes
    customer preference vectors from their interaction history.
    """

    def __init__(self, config: Optional[RecommendationConfig] = None):
        self.config = config or RecommendationConfig()
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._product_tfidf: Optional[np.ndarray] = None
        self._product_ids: list[str] = []
        self._is_fitted = False

    def fit(self, products: pd.DataFrame) -> ContentModel:
        """Fit the TF-IDF model on product metadata.

        Args:
            products: Product DataFrame with at least 'product_id' and text fields.

        Returns:
            self
        """
        if products.empty:
            self._is_fitted = True
            return self

        self._product_ids = products["product_id"].tolist()
        texts = products.apply(_build_product_text, axis=1).tolist()

        self._vectorizer = TfidfVectorizer(
            max_features=self.config.tfidf_max_features,
            ngram_range=self.config.tfidf_ngram_range,
            stop_words="english",
            lowercase=True,
        )
        self._product_tfidf = self._vectorizer.fit_transform(texts).toarray()
        self._is_fitted = True
        return self

    def _get_product_index(self, product_id: str) -> Optional[int]:
        """Get the index of a product in the TF-IDF matrix."""
        try:
            return self._product_ids.index(product_id)
        except ValueError:
            return None

    def get_product_vector(self, product_id: str) -> Optional[np.ndarray]:
        """Get the TF-IDF vector for a single product."""
        idx = self._get_product_index(product_id)
        if idx is None or self._product_tfidf is None:
            return None
        return self._product_tfidf[idx]

    def build_customer_preference_vector(
        self,
        interacted_product_ids: list[str],
        weights: Optional[list[float]] = None,
    ) -> Optional[np.ndarray]:
        """Build a customer preference vector from their interacted products.

        Args:
            interacted_product_ids: List of product IDs the customer interacted with.
            weights: Optional interaction strength weights for each product.

        Returns:
            Weighted average TF-IDF vector representing customer preferences.
        """
        if not interacted_product_ids or self._product_tfidf is None:
            return None

        vectors = []
        actual_weights = []

        for i, pid in enumerate(interacted_product_ids):
            vec = self.get_product_vector(pid)
            if vec is not None:
                vectors.append(vec)
                if weights and i < len(weights):
                    actual_weights.append(max(weights[i], 0.01))
                else:
                    actual_weights.append(1.0)

        if not vectors:
            return None

        vectors = np.array(vectors)
        actual_weights = np.array(actual_weights)
        actual_weights = actual_weights / actual_weights.sum()

        preference = np.average(vectors, axis=0, weights=actual_weights)
        return preference

    def get_content_scores(
        self,
        customer_preference_vector: Optional[np.ndarray],
        candidate_product_ids: list[str],
    ) -> dict[str, float]:
        """Compute content similarity scores for candidate products.

        Args:
            customer_preference_vector: Customer's preference TF-IDF vector.
            candidate_product_ids: List of candidate product IDs to score.

        Returns:
            Dict mapping product_id to normalized similarity score (0-1).
        """
        if customer_preference_vector is None or not candidate_product_ids:
            return {pid: 0.0 for pid in candidate_product_ids}

        scores = {}
        for pid in candidate_product_ids:
            prod_vec = self.get_product_vector(pid)
            if prod_vec is None:
                scores[pid] = 0.0
            else:
                sim = cosine_similarity(
                    customer_preference_vector.reshape(1, -1),
                    prod_vec.reshape(1, -1),
                )[0, 0]
                scores[pid] = max(0.0, min(1.0, float(sim)))

        return scores

    def score_for_customer(
        self,
        customer_profile: CustomerProfile,
        candidate_product_ids: list[str],
        interactions: Optional[pd.DataFrame] = None,
    ) -> dict[str, float]:
        """Score candidates using customer profile and interaction history.

        Args:
            customer_profile: Customer digital twin.
            candidate_product_ids: Products to score.
            interactions: Optional interaction data for building preference vector.

        Returns:
            Dict mapping product_id to content score (0-1).
        """
        interacted_ids = []
        interacted_weights = []

        if interactions is not None and not interactions.empty:
            cust_interactions = interactions[interactions["customer_id"] == customer_profile.customer_id]
            if not cust_interactions.empty:
                agg = cust_interactions.groupby("product_id")["strength"].sum()
                interacted_ids = agg.index.tolist()
                interacted_weights = agg.values.tolist()

        if not interacted_ids and customer_profile.recent_products:
            interacted_ids = customer_profile.recent_products

        pref_vec = self.build_customer_preference_vector(interacted_ids, interacted_weights)
        return self.get_content_scores(pref_vec, candidate_product_ids)

    @property
    def is_fitted(self) -> bool:
        return self._is_fitted

    @property
    def vocabulary_size(self) -> int:
        if self._vectorizer is None:
            return 0
        return len(self._vectorizer.vocabulary_)
