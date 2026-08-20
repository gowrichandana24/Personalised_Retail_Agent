# Recommendation ML Module — RetailMind

## Overview

Hybrid recommendation engine for the RetailMind hackathon project. Combines collaborative filtering, content-based similarity, popularity, and mission/intent-aware ranking with diversity optimization and discovery support.

## Quick Start

```python
from recommendation_ml import RecommendationEngine, Mission, CustomerProfile
from recommendation_ml.data.synthetic import generate_test_scenario

# Generate test data
scenario = generate_test_scenario()

# Initialize and fit
engine = RecommendationEngine()
engine.fit(scenario["interactions"], scenario["products"])

# Create mission and profile
mission = Mission(
    goal="Weekend trip",
    budget=5000,
    preferred_categories=["Sports", "Clothing"],
    discovery_level=0.3,
)

profile = CustomerProfile(
    customer_id="10000",
    category_affinity={"Sports": 0.8, "Clothing": 0.6},
    preferred_brands=["Nike", "Adidas"],
)

# Get recommendations
result = engine.recommend(
    customer_id="10000",
    mission=mission,
    customer_profile=profile,
    top_k=5,
)

# Use results
for rec in result.recommendations:
    print(f"{rec.product_id}: {rec.final_score:.2f}")
    print(f"  Evidence: {rec.evidence}")
    print(f"  Breakdown: {rec.score_breakdown.to_dict()}")
```

## Installation

```bash
pip install numpy pandas scikit-learn scipy
```

## Module Structure

```
recommendation_ml/
├── __init__.py              # Public API exports
├── config.py                # Configurable weights and parameters
├── schemas.py               # Data schemas (Mission, Profile, Recommendation)
├── engine.py                # Main RecommendationEngine class
├── data/
│   ├── loader.py            # Data loading and preprocessing
│   └── synthetic.py         # Synthetic test data generator
├── models/
│   ├── popularity.py        # Popularity baseline
│   ├── content.py           # TF-IDF content-based model
│   ├── collaborative.py     # ALS collaborative filtering
│   └── hybrid.py            # Hybrid scoring logic
├── ranking/
│   ├── constraints.py       # Hard constraint filtering
│   ├── diversity.py         # Diversity-aware re-ranking
│   └── discovery.py         # Discovery/serendipity scoring
├── evaluation/
│   └── metrics.py           # Offline evaluation metrics
└── tests/
    └── test_recommendation.py  # 77 unit + integration tests
```

## Integration Guide

### Input Schemas

**Mission** (from Intent Agent):
```python
Mission(
    goal="Weekend trip",
    occasion="Travel",
    budget=5000,
    preferred_categories=["Sports", "Clothing"],
    excluded_brands=["Nike"],
    excluded_categories=[],
    discovery_level=0.3,
    urgency="medium",
    min_budget=0,
    preferred_brands=[],
    min_rating=0,
    session_product_ids=[],
)
```

**CustomerProfile** (from Customer Intelligence):
```python
CustomerProfile(
    customer_id="C001",
    category_affinity={"Sports": 0.8, "Electronics": 0.3},
    price_sensitivity=0.6,
    preferred_brands=["Nike", "Samsung"],
    average_spend=1500,
    recent_categories=["Sports", "Clothing"],
    recent_products=["P101", "P102"],
    discovery_appetite=0.4,
)
```

**Candidates** (from Product Intelligence):
```python
# Option 1: List of dicts
candidates = [
    {"product_id": "P101", "title": "...", "category": "Sports", "brand": "Nike", "price": 2500},
    {"product_id": "P102", "title": "...", "category": "Electronics", "brand": "Samsung", "price": 15000},
]

# Option 2: Just IDs (engine looks up metadata)
candidate_ids = ["P101", "P102", "P103"]

# Option 3: DataFrame
candidates_df = pd.DataFrame(candidates)
```

### Output Schema

```python
RecommendationResult:
  recommendations: [
    Recommendation:
      product_id: str
      final_score: float (0-1)
      score_breakdown: ScoreBreakdown
        collaborative: float
        content: float
        intent: float
        preference: float
        budget: float
        session: float
        popularity: float
        discovery: float
      evidence: [str, ...]
      confidence: float
      rank: int
      metadata: dict (title, category, brand, price)
  ]
  model_version: str
  candidate_count: int
  ranking_metadata: dict
  trace: [str, ...]
```

### API Reference

```python
engine = RecommendationEngine(config=None)

# Primary API
result = engine.recommend(
    customer_id="C001",
    mission=Mission(...),
    customer_profile=CustomerProfile(...),  # optional
    candidate_products=[...],               # optional
    candidate_ids=["P1", "P2"],            # optional
    session_context={...},                  # optional
    top_k=5,
    weights=HybridWeights(...),            # optional
)

# What-if re-ranking
reranked = engine.rerank_candidates(
    candidates=existing_candidates,
    customer_profile=profile,
    mission=new_mission,
    constraints={"budget": 3000},
    top_k=5,
)

# Individual model scores
popular = engine.get_popular_products(k=10)
content_scores = engine.get_content_scores("C001", ["P1", "P2"])
collab_scores = engine.get_collaborative_scores("C001", ["P1", "P2"])
```

### Configurable Weights

```python
from recommendation_ml.config import HybridWeights, RecommendationConfig

weights = HybridWeights(
    collaborative=0.30,
    content=0.25,
    intent=0.20,
    customer_preference=0.10,
    popularity=0.05,
    session_relevance=0.05,
    discovery=0.05,
)

config = RecommendationConfig(
    hybrid_weights=weights,
    diversity_weight=0.3,
    time_decay_half_life_days=30,
)

engine = RecommendationEngine(config=config)
```

## Running Tests

```bash
python -m pytest recommendation_ml/tests/ -v
```

## Evaluation

```python
from recommendation_ml.evaluation.metrics import evaluate_model, compare_models

# Evaluate a single model
metrics = evaluate_model(
    recommendations_per_user={"U1": ["P1", "P2"], "U2": ["P3"]},
    ground_truth_per_user={"U1": {"P1", "P5"}, "U2": {"P3"}},
    k=5,
)

# Compare multiple models
df = compare_models(
    model_results={
        "Popularity": pop_recs,
        "Content": content_recs,
        "Hybrid": hybrid_recs,
    },
    ground_truth=ground_truth,
    k=5,
)
print(df)
```

## Architecture Rules

- **No LLM scoring**: All product scores, prices, and evidence are ML/deterministic
- **No data leakage**: Time-aware splits only
- **No hallucination**: Evidence only claims what the model actually used
- **Configurable**: All weights and thresholds are configurable
- **Modular**: Each stage can be tested independently
- **Fast re-ranking**: What-if uses existing candidate sets
