"""Data schemas for the recommendation ML module.

These schemas define the interfaces between the recommendation engine
and other team modules (Intent Agent, Customer Intelligence, Product
Intelligence, Backend, Frontend).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Mission:
    """Structured shopping mission from the Intent Agent.

    The Intent Agent converts natural language into this structured
    representation. The recommendation engine consumes this directly.
    """
    goal: str = ""
    occasion: str = ""
    budget: float = float("inf")
    preferred_categories: list[str] = field(default_factory=list)
    excluded_brands: list[str] = field(default_factory=list)
    excluded_categories: list[str] = field(default_factory=list)
    discovery_level: float = 0.3
    urgency: str = "medium"
    min_budget: float = 0.0
    preferred_brands: list[str] = field(default_factory=list)
    min_rating: float = 0.0
    style_preference: str = ""
    session_product_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "goal": self.goal,
            "occasion": self.occasion,
            "budget": self.budget,
            "preferred_categories": self.preferred_categories,
            "excluded_brands": self.excluded_brands,
            "excluded_categories": self.excluded_categories,
            "discovery_level": self.discovery_level,
            "urgency": self.urgency,
            "min_budget": self.min_budget,
            "preferred_brands": self.preferred_brands,
            "min_rating": self.min_rating,
            "style_preference": self.style_preference,
            "session_product_ids": self.session_product_ids,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Mission:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class CustomerProfile:
    """Customer digital twin from the Customer Intelligence module.

    The Persona Agent builds and maintains this profile. The
    recommendation engine consumes it for scoring.
    """
    customer_id: str = ""
    category_affinity: dict[str, float] = field(default_factory=dict)
    price_sensitivity: float = 0.5
    preferred_brands: list[str] = field(default_factory=list)
    average_spend: float = 0.0
    recent_categories: list[str] = field(default_factory=list)
    recent_products: list[str] = field(default_factory=list)
    discovery_appetite: float = 0.3
    total_purchases: int = 0
    total_views: int = 0
    avg_rating: float = 0.0

    def to_dict(self) -> dict:
        return {
            "customer_id": self.customer_id,
            "category_affinity": self.category_affinity,
            "price_sensitivity": self.price_sensitivity,
            "preferred_brands": self.preferred_brands,
            "average_spend": self.average_spend,
            "recent_categories": self.recent_categories,
            "recent_products": self.recent_products,
            "discovery_appetite": self.discovery_appetite,
            "total_purchases": self.total_purchases,
            "total_views": self.total_views,
            "avg_rating": self.avg_rating,
        }

    @classmethod
    def from_dict(cls, data: dict) -> CustomerProfile:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ScoreBreakdown:
    """Detailed score components for a single recommendation."""
    collaborative: float = 0.0
    content: float = 0.0
    intent: float = 0.0
    preference: float = 0.0
    budget: float = 0.0
    session: float = 0.0
    popularity: float = 0.0
    discovery: float = 0.0

    def to_dict(self) -> dict:
        return {
            "collaborative": round(self.collaborative, 4),
            "content": round(self.content, 4),
            "intent": round(self.intent, 4),
            "preference": round(self.preference, 4),
            "budget": round(self.budget, 4),
            "session": round(self.session, 4),
            "popularity": round(self.popularity, 4),
            "discovery": round(self.discovery, 4),
        }


@dataclass
class Recommendation:
    """A single recommendation with evidence and metadata."""
    product_id: str = ""
    final_score: float = 0.0
    score_breakdown: ScoreBreakdown = field(default_factory=ScoreBreakdown)
    evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0
    rank: int = 0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "product_id": self.product_id,
            "final_score": round(self.final_score, 4),
            "score_breakdown": self.score_breakdown.to_dict(),
            "evidence": self.evidence,
            "confidence": round(self.confidence, 4),
            "rank": self.rank,
            "metadata": self.metadata,
        }


@dataclass
class RecommendationResult:
    """Complete result from the recommendation engine."""
    recommendations: list[Recommendation] = field(default_factory=list)
    model_version: str = "1.0.0"
    candidate_count: int = 0
    ranking_metadata: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "recommendations": [r.to_dict() for r in self.recommendations],
            "model_version": self.model_version,
            "candidate_count": self.candidate_count,
            "ranking_metadata": self.ranking_metadata,
            "trace": self.trace,
        }


@dataclass
class Product:
    """Product in the catalogue."""
    product_id: str = ""
    title: str = ""
    category: str = ""
    brand: str = ""
    price: float = 0.0
    description: str = ""
    rating: float = 0.0
    properties: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "product_id": self.product_id,
            "title": self.title,
            "category": self.category,
            "brand": self.brand,
            "price": self.price,
            "description": self.description,
            "rating": self.rating,
            "properties": self.properties,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Product:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Interaction:
    """A single user-product interaction event."""
    customer_id: str = ""
    product_id: str = ""
    event_type: str = "view"
    timestamp: str = ""
    value: float = 0.0

    def to_dict(self) -> dict:
        return {
            "customer_id": self.customer_id,
            "product_id": self.product_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "value": self.value,
        }
