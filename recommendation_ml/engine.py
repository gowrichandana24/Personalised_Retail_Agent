"""Main Recommendation Engine for RetailMind.

This is the primary entry point for the recommendation ML module.
It orchestrates the full pipeline from data loading through
scoring, ranking, constraint filtering, diversity, and evidence generation.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from recommendation_ml.config import HybridWeights, RecommendationConfig
from recommendation_ml.data.loader import (
    build_product_metadata_index,
    build_user_item_matrix,
    load_interactions,
    load_products,
    time_aware_split,
)
from recommendation_ml.models.collaborative import CollaborativeModel
from recommendation_ml.models.content import ContentModel
from recommendation_ml.models.hybrid import (
    compute_budget_score,
    compute_intent_score,
    compute_preference_score,
    compute_session_score,
    hybrid_score_candidates,
    normalize_scores,
)
from recommendation_ml.models.popularity import PopularityModel
from recommendation_ml.ranking.constraints import apply_constraints
from recommendation_ml.ranking.discovery import boost_discovery_candidates
from recommendation_ml.ranking.diversity import diversify_recommendations
from recommendation_ml.schemas import (
    CustomerProfile,
    Mission,
    Recommendation,
    RecommendationResult,
    ScoreBreakdown,
)


class RecommendationEngine:
    """Hybrid recommendation engine with mission-aware ranking.

    Orchestrates: data loading, model training, candidate scoring,
    constraint filtering, diversity optimization, and evidence generation.

    Usage:
        engine = RecommendationEngine()
        engine.fit(interactions_df, products_df)
        result = engine.recommend(customer_id, mission, profile, candidates)
    """

    def __init__(self, config: Optional[RecommendationConfig] = None):
        self.config = config or RecommendationConfig()
        self.popularity_model = PopularityModel(self.config)
        self.content_model = ContentModel(self.config)
        self.collaborative_model = CollaborativeModel(self.config)

        self._interactions: Optional[pd.DataFrame] = None
        self._products: Optional[pd.DataFrame] = None
        self._product_metadata: dict[str, dict] = {}
        self._user_item_matrix: Optional[pd.DataFrame] = None
        self._is_fitted = False

        self._version = "1.0.0"

    def fit(
        self,
        interactions: pd.DataFrame | list[dict] | str,
        products: pd.DataFrame | list[dict] | str,
        column_map: Optional[dict] = None,
    ) -> RecommendationEngine:
        """Fit all models on interaction and product data.

        Args:
            interactions: Interaction data (DataFrame, list of dicts, or file path).
            products: Product catalogue data.
            column_map: Optional column name mapping.

        Returns:
            self
        """
        if isinstance(interactions, (list, str)):
            interactions = load_interactions(interactions, column_map=column_map)
        elif isinstance(interactions, pd.DataFrame):
            if "strength" not in interactions.columns:
                interactions = load_interactions(interactions, column_map=column_map)

        if isinstance(products, (list, str)):
            products = load_products(products, column_map=column_map)
        elif isinstance(products, pd.DataFrame):
            if "product_id" in products.columns:
                products = load_products(products, column_map=column_map)

        self._interactions = interactions
        self._products = products
        self._product_metadata = build_product_metadata_index(products)

        self.popularity_model.fit(interactions)
        self.content_model.fit(products)
        self.collaborative_model.fit(interactions)

        self._user_item_matrix = build_user_item_matrix(interactions)
        self._is_fitted = True

        return self

    def _get_candidate_ids(
        self,
        candidate_products: Optional[list[dict] | pd.DataFrame] = None,
        candidate_ids: Optional[list[str]] = None,
    ) -> list[str]:
        """Extract candidate product IDs from various input formats."""
        if candidate_ids is not None:
            return candidate_ids

        if candidate_products is not None:
            if isinstance(candidate_products, pd.DataFrame):
                if "product_id" in candidate_products.columns:
                    return candidate_products["product_id"].tolist()
            elif isinstance(candidate_products, list):
                return [p.get("product_id", p.get("product_id", "")) for p in candidate_products]

        if self._products is not None:
            return self._products["product_id"].tolist()

        return []

    def _build_candidate_df(
        self,
        candidate_products: Optional[list[dict] | pd.DataFrame] = None,
        candidate_ids: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """Build a candidate DataFrame from available inputs."""
        if candidate_products is not None:
            if isinstance(candidate_products, pd.DataFrame):
                return candidate_products.copy()
            elif isinstance(candidate_products, list):
                return pd.DataFrame(candidate_products)

        ids = self._get_candidate_ids(candidate_products, candidate_ids)
        if not ids:
            return pd.DataFrame()

        rows = []
        for pid in ids:
            meta = self._product_metadata.get(pid, {})
            rows.append({
                "product_id": pid,
                "title": meta.get("title", ""),
                "category": meta.get("category", ""),
                "brand": meta.get("brand", ""),
                "price": meta.get("price", 0.0),
                "description": meta.get("description", ""),
                "rating": meta.get("rating", 0.0),
            })
        return pd.DataFrame(rows)

    def _generate_evidence(
        self,
        product_id: str,
        score_breakdown: ScoreBreakdown,
        mission: Mission,
        profile: Optional[CustomerProfile],
        meta: dict,
    ) -> list[str]:
        """Generate structured evidence for a recommendation.

        This evidence is consumed by the Explanation Agent.
        Never invents evidence — only reports what the model actually used.
        """
        evidence = []

        if score_breakdown.intent > 0.6:
            evidence.append("Matches current shopping mission")

        if score_breakdown.budget > 0.8:
            evidence.append("Within stated budget")
        elif score_breakdown.budget > 0:
            evidence.append("Fits budget range")

        if score_breakdown.collaborative > 0.5:
            evidence.append("Similar customers showed strong interest")

        if score_breakdown.content > 0.6:
            evidence.append("Matches your preference profile")

        if score_breakdown.preference > 0.6:
            cat = meta.get("category", "")
            if cat and profile and profile.category_affinity:
                if profile.category_affinity.get(cat, 0) > 0.5:
                    evidence.append(f"Matches preferred category: {cat}")

        if score_breakdown.session > 0.5:
            evidence.append("Related to current session")

        if score_breakdown.popularity > 0.7:
            evidence.append("Popular product")

        if score_breakdown.discovery > 0.3:
            evidence.append("Adds novelty to recommendations")

        if not evidence:
            evidence.append("Relevant based on combined signals")

        return evidence

    def recommend(
        self,
        customer_id: str,
        mission: Mission,
        customer_profile: Optional[CustomerProfile] = None,
        candidate_products: Optional[list[dict] | pd.DataFrame] = None,
        candidate_ids: Optional[list[str]] = None,
        session_context: Optional[dict] = None,
        top_k: int = 5,
        weights: Optional[HybridWeights] = None,
    ) -> RecommendationResult:
        """Generate personalized recommendations.

        This is the primary API entry point.

        Args:
            customer_id: Customer identifier.
            mission: Structured shopping mission from Intent Agent.
            customer_profile: Customer digital twin from Persona Agent.
            candidate_products: Candidate products from Retrieval Agent.
            candidate_ids: Alternative: just product IDs.
            session_context: Optional session context.
            top_k: Number of recommendations to return.
            weights: Optional custom hybrid weights.

        Returns:
            RecommendationResult with top-K recommendations and metadata.
        """
        trace = []
        trace.append(f"Starting recommendation for customer {customer_id}")

        candidate_df = self._build_candidate_df(candidate_products, candidate_ids)
        trace.append(f"Candidate count: {len(candidate_df)}")

        # Build effective metadata: merge external candidate metadata with trained metadata
        effective_metadata = dict(self._product_metadata)
        for _, row in candidate_df.iterrows():
            pid = row.get("product_id", "")
            if pid and pid not in effective_metadata:
                effective_metadata[pid] = {
                    "title": row.get("title", ""),
                    "category": row.get("category", ""),
                    "brand": row.get("brand", ""),
                    "price": row.get("price", 0.0),
                    "description": row.get("description", ""),
                    "rating": row.get("rating", 0.0),
                    "properties": row.get("properties", {}),
                }
            elif pid:
                # Merge: use candidate data for fields, fallback to trained metadata
                existing = effective_metadata[pid]
                for field in ["title", "category", "brand", "price", "description", "rating"]:
                    val = row.get(field, None)
                    if val is not None and val != "" and val != 0.0:
                        existing[field] = val

        candidate_df = apply_constraints(candidate_df, mission, effective_metadata)
        trace.append(f"After constraint filtering: {len(candidate_df)}")

        if candidate_df.empty:
            trace.append("No candidates remain after filtering")
            return RecommendationResult(
                recommendations=[],
                candidate_count=0,
                ranking_metadata={"filtered_out": True},
                trace=trace,
            )

        candidate_ids_list = candidate_df["product_id"].tolist()

        collab_scores = self.collaborative_model.get_collaborative_scores(
            customer_id, candidate_ids_list
        )
        content_scores = self.content_model.score_for_customer(
            customer_profile or CustomerProfile(customer_id=customer_id),
            candidate_ids_list,
            self._interactions,
        )
        pop_scores = self.popularity_model.get_scores(candidate_ids_list)

        collab_scores = normalize_scores(collab_scores)
        content_scores = normalize_scores(content_scores)
        pop_scores = normalize_scores(pop_scores)

        trace.append("Computed collaborative, content, and popularity scores")

        scored = hybrid_score_candidates(
            candidate_ids=candidate_ids_list,
            collaborative_scores=collab_scores,
            content_scores=content_scores,
            popularity_scores=pop_scores,
            product_metadata=effective_metadata,
            mission=mission,
            profile=customer_profile,
            weights=weights or self.config.hybrid_weights,
        )

        if mission.discovery_level > 0 and self._products is not None:
            interacted = set()
            if customer_profile and customer_profile.recent_products:
                interacted = set(customer_profile.recent_products)
            elif self._interactions is not None:
                cust_int = self._interactions[self._interactions["customer_id"] == customer_id]
                interacted = set(cust_int["product_id"].tolist())

            scored = boost_discovery_candidates(
                scored,
                interacted,
                discovery_level=mission.discovery_level,
                mission_categories=mission.preferred_categories,
            )
            trace.append(f"Applied discovery boost (level={mission.discovery_level})")

        scored = diversify_recommendations(
            scored,
            top_k=top_k,
            diversity_weight=self.config.diversity_weight,
        )
        trace.append(f"Diversified to top {top_k}")

        recommendations = []
        for rank, item in enumerate(scored[:top_k], 1):
            pid = item["product_id"]
            meta = effective_metadata.get(pid, {})
            breakdown = item.get("score_breakdown", ScoreBreakdown())

            evidence = self._generate_evidence(pid, breakdown, mission, customer_profile, meta)

            confidence = min(1.0, item["final_score"] * 1.1)

            rec = Recommendation(
                product_id=pid,
                final_score=item["final_score"],
                score_breakdown=breakdown,
                evidence=evidence,
                confidence=confidence,
                rank=rank,
                metadata={
                    "title": meta.get("title", ""),
                    "category": meta.get("category", ""),
                    "brand": meta.get("brand", ""),
                    "price": meta.get("price", 0.0),
                },
            )
            recommendations.append(rec)

        result = RecommendationResult(
            recommendations=recommendations,
            model_version=self._version,
            candidate_count=len(candidate_df),
            ranking_metadata={
                "customer_id": customer_id,
                "mission_goal": mission.goal,
                "budget": mission.budget,
                "discovery_level": mission.discovery_level,
                "top_k": top_k,
                "weights": {
                    "collaborative": self.config.hybrid_weights.collaborative,
                    "content": self.config.hybrid_weights.content,
                    "intent": self.config.hybrid_weights.intent,
                    "customer_preference": self.config.hybrid_weights.customer_preference,
                    "popularity": self.config.hybrid_weights.popularity,
                    "session_relevance": self.config.hybrid_weights.session_relevance,
                    "discovery": self.config.hybrid_weights.discovery,
                },
            },
            trace=trace,
        )

        trace.append(f"Generated {len(recommendations)} recommendations")
        return result

    def rerank_candidates(
        self,
        candidates: list[dict],
        customer_profile: Optional[CustomerProfile] = None,
        mission: Optional[Mission] = None,
        constraints: Optional[dict] = None,
        top_k: int = 5,
        weights: Optional[HybridWeights] = None,
    ) -> list[dict]:
        """Re-rank an existing candidate set with new constraints.

        Used for what-if scenarios: keeps the candidate set,
        recomputes scores under new constraints.

        Args:
            candidates: Existing candidate products with scores.
            customer_profile: Updated customer profile.
            mission: Updated mission (e.g., new budget).
            constraints: Additional constraint overrides.
            top_k: Number of results to return.
            weights: Optional custom weights.

        Returns:
            Re-ranked list of product dicts.
        """
        if not candidates:
            return []

        if mission is None:
            mission = Mission()

        if constraints:
            if "budget" in constraints:
                mission.budget = constraints["budget"]
            if "excluded_brands" in constraints:
                mission.excluded_brands = constraints["excluded_brands"]
            if "discovery_level" in constraints:
                mission.discovery_level = constraints["discovery_level"]

        for candidate in candidates:
            pid = candidate.get("product_id", "")
            meta = self._product_metadata.get(pid, {})
            price = candidate.get("price", meta.get("price", 0.0))
            category = candidate.get("category", meta.get("category", ""))
            brand = candidate.get("brand", meta.get("brand", ""))

            budget_score = compute_budget_score(price, mission.budget, mission.min_budget)
            intent_score = compute_intent_score(category, brand, mission)
            preference_score = compute_preference_score(category, brand, customer_profile)

            w = weights or self.config.hybrid_weights
            w.normalize()

            base_score = candidate.get("final_score", 0.5)
            new_score = (
                w.collaborative * base_score * 0.5
                + w.content * base_score * 0.5
                + w.intent * intent_score
                + w.customer_preference * preference_score
                + w.popularity * candidate.get("popularity_score", 0.0)
                + w.session_relevance * candidate.get("session_score", 0.0)
                + 0.1 * budget_score
            )

            candidate["final_score"] = new_score
            candidate["budget_score"] = budget_score
            candidate["intent_score"] = intent_score

        candidates.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        return candidates[:top_k]

    def get_popular_products(self, k: int = 10) -> list[Recommendation]:
        """Get popular products (baseline)."""
        return self.popularity_model.get_popular_products(k)

    def get_content_scores(
        self,
        customer_id: str,
        candidate_product_ids: list[str],
    ) -> dict[str, float]:
        """Get content-based scores for candidates."""
        profile = CustomerProfile(customer_id=customer_id)
        return self.content_model.score_for_customer(profile, candidate_product_ids, self._interactions)

    def get_collaborative_scores(
        self,
        customer_id: str,
        candidate_product_ids: list[str],
    ) -> dict[str, float]:
        """Get collaborative filtering scores for candidates."""
        return self.collaborative_model.get_collaborative_scores(customer_id, candidate_product_ids)

    @property
    def is_fitted(self) -> bool:
        return self._is_fitted

    @property
    def model_version(self) -> str:
        return self._version
