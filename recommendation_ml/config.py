"""Configuration for the recommendation ML module."""

from dataclasses import dataclass, field


@dataclass
class EventWeights:
    """Configurable interaction strength weights."""
    view: float = 1.0
    addtocart: float = 3.0
    transaction: float = 5.0
    purchase: float = 5.0
    like: float = 4.0
    save: float = 4.0
    skip: float = -2.0
    default: float = 1.0

    def get(self, event_type: str) -> float:
        normalized = event_type.lower().replace(" ", "").replace("-", "")
        mapping = {
            "view": self.view,
            "addtocart": self.addtocart,
            "addtocart": self.addtocart,
            "transaction": self.transaction,
            "purchase": self.purchase,
            "like": self.like,
            "save": self.save,
            "skip": self.skip,
        }
        return mapping.get(normalized, self.default)


@dataclass
class HybridWeights:
    """Configurable hybrid scoring weights."""
    collaborative: float = 0.30
    content: float = 0.25
    intent: float = 0.20
    customer_preference: float = 0.10
    popularity: float = 0.05
    session_relevance: float = 0.05
    discovery: float = 0.05

    def normalize(self):
        total = sum([
            self.collaborative, self.content, self.intent,
            self.customer_preference, self.popularity,
            self.session_relevance, self.discovery
        ])
        if total > 0:
            self.collaborative /= total
            self.content /= total
            self.intent /= total
            self.customer_preference /= total
            self.popularity /= total
            self.session_relevance /= total
            self.discovery /= total


@dataclass
class RecommendationConfig:
    """Master configuration for the recommendation engine."""
    event_weights: EventWeights = field(default_factory=EventWeights)
    hybrid_weights: HybridWeights = field(default_factory=HybridWeights)
    time_decay_half_life_days: float = 30.0
    min_interaction_strength: float = 0.1
    tfidf_max_features: int = 5000
    tfidf_ngram_range: tuple = (1, 2)
    collaborative_n_components: int = 50
    collaborative_learning_rate: float = 0.01
    collaborative_regularization: float = 0.02
    collaborative_iterations: int = 20
    diversity_weight: float = 0.3
    discovery_novelty_weight: float = 0.4
    default_top_k: int = 5
    min_rating_threshold: float = 0.0
    cold_start_popularity_k: int = 20
    random_seed: int = 42
