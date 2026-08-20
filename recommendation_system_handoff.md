# Recommendation System -- RetailMind

## 1. My Contribution

I implemented the **Recommendation ML module** (`recommendation_ml/`), which is the core personalization engine of the RetailMind project. It takes a customer's shopping intent, their digital twin profile, and a product catalogue, then produces ranked, diversified, explainable product recommendations using a hybrid of collaborative filtering, content-based filtering, and popularity signals.

---

## 2. What the Recommendation System Does

The recommendation system solves one central problem: **given a customer who wants something, what products should we show them and in what order?**

It does this by:

1. Receiving structured input (shopping mission + customer profile + candidate products)
2. Filtering out products that don't meet hard constraints (budget, excluded brands, etc.)
3. Scoring every remaining product using 7 different signals
4. Combining those signals with configurable weights
5. Boosting novel products the customer hasn't seen
6. Re-ranking to ensure category and brand diversity
7. Generating human-readable evidence for why each product was recommended
8. Returning a `RecommendationResult` with ranked products, scores, and trace

---

## 3. Why We Need It

Without this module, RetailMind would have no data-driven personalization. The Agentic AI module has a mock tool layer (`agentic_ai/tools.py`) with 5 hardcoded products and simple rule-based sorting -- it cannot scale. The Intent module tells us *what* the customer wants, and Customer Intelligence tells us *who* the customer is, but neither can score and rank products. The Recommendation System is where those inputs become actual ranked product lists.

---

## 4. Architecture

```
Mission (from Intent)  +  CustomerProfile (from Customer Intelligence)  +  Candidates (from catalogue)
                                        |
                                        v
                          +---------------------------+
                          |   RecommendationEngine    |
                          |        .recommend()       |
                          +---------------------------+
                                        |
                    +-------------------+-------------------+
                    |                   |                   |
                    v                   v                   v
            Collaborative         Content-Based        Popularity
            (ALS Matrix           (TF-IDF +            (Interaction
             Factorization)       Cosine Sim)           Strength Sum)
                    |                   |                   |
                    v                   v                   v
                    +-------------------+-------------------+
                                        |
                                        v
                            normalize_scores()
                                        |
                                        v
                        hybrid_score_candidates()
                        (7-signal weighted sum)
                                        |
                                        v
                        boost_discovery_candidates()
                                        |
                                        v
                        diversify_recommendations()
                                        |
                                        v
                        _generate_evidence()
                                        |
                                        v
                              RecommendationResult
```

---

## 5. Complete Recommendation Pipeline

### Stage 1: Input

The `RecommendationEngine.recommend()` method receives:

| Parameter | Type | Source |
|-----------|------|--------|
| `customer_id` | `str` | Frontend / API request |
| `mission` | `Mission` | Intent Agent -> `backend/service.py::mission_from_query()` |
| `customer_profile` | `CustomerProfile` | Customer Intelligence -> `backend/service.py::profile_from_digital_twin()` |
| `candidate_products` | `list[dict]` | Catalogue (`data/catalog.json`) or frontend |
| `top_k` | `int` | Default 5 |
| `weights` | `HybridWeights` | Optional override of defaults |

### Stage 2: Candidate Preparation

```
_build_candidate_df(candidate_products)
    -> merges external candidates with trained product metadata
    -> fills missing columns (title, category, brand, price, etc.)
    -> returns pd.DataFrame
```

### Stage 3: Hard Constraint Filtering

```
apply_constraints(candidates, mission)
    -> filter_by_budget(candidates, mission)       # price <= budget
    -> filter_by_excluded_brands(candidates, mission)  # case-insensitive brand exclusion
    -> filter_by_excluded_categories(candidates, mission)  # case-insensitive category exclusion
    -> filter_by_rating(candidates, mission)        # rating >= min_rating
    -> returns filtered DataFrame
```

Products removed at this stage are gone permanently -- they never reach scoring.

### Stage 4: Model Scoring

Three independent models score every surviving candidate:

```
collaborative_scores = collaborative_model.get_collaborative_scores(customer_id, candidate_ids)
content_scores = content_model.score_for_customer(customer_profile, candidate_ids, interactions)
popularity_scores = popularity_model.get_scores(candidate_ids)
```

Each returns `dict[str, float]` with scores in [0, 1].

### Stage 5: Score Normalization

```
collaborative_scores = normalize_scores(collaborative_scores)
content_scores = normalize_scores(content_scores)
popularity_scores = normalize_scores(popularity_scores)
```

Min-max normalization to [0, 1]. Returns 0.5 for all if range is 0.

### Stage 6: Hybrid Scoring

For each candidate product:

```
intent_score = compute_intent_score(product.category, product.brand, mission)
preference_score = compute_preference_score(product.category, product.brand, customer_profile)
session_score = compute_session_score(product_id, mission.session_product_ids)
budget_score = compute_budget_score(product.price, mission.budget, mission.min_budget)

final_score = (
    W_collaborative * collaborative_score
    + W_content * content_score
    + W_intent * intent_score
    + W_preference * preference_score
    + W_popularity * popularity_score
    + W_session * session_score
    + W_discovery * 0.0
)
```

Default weights (normalized to sum to 1.0):

| Signal | Weight |
|--------|--------|
| Collaborative | 0.30 |
| Content | 0.25 |
| Intent | 0.20 |
| Customer Preference | 0.10 |
| Popularity | 0.05 |
| Session Relevance | 0.05 |
| Discovery | 0.05 |

### Stage 7: Discovery Boost

If `mission.discovery_level > 0`:

```
novelty = 1.0 if product not in customer's interaction history, else 0.0
mission_fit = 1.0 if category in mission.preferred_categories, else 0.3
discovery_score = relevance * novelty * mission_fit * discovery_level

if novelty > 0.5:
    boosted_score = base_score * (1 + discovery_weight * discovery_level)
    final_score = min(1.0, boosted_score)
```

### Stage 8: Diversity Re-ranking

Greedy selection with diversity bonus:

```
diversity_bonus = (category_diversity_score + brand_diversity_score) / 2.0
combined = (1 - diversity_weight) * base_score + diversity_weight * diversity_bonus
```

Where:
- `category_diversity_score` = 1.0 if category is new in the result list, `1/(1+count)` if repeated
- `brand_diversity_score` = 1.0 if brand is new, `1/(1+count)` if repeated
- `diversity_weight` = 0.3 (default)

### Stage 9: Evidence Generation

For each product, rule-based evidence strings are generated from the score breakdown:

- High collaborative score -> "Similar users purchased this product"
- High content score -> "Matches your preference for [category]"
- High intent score -> "Directly matches your shopping goal"
- High preference score -> "Aligned with your category interests"
- Budget fit -> "Within your budget"
- Novelty -> "New product you haven't explored"

### Stage 10: Output

Returns `RecommendationResult` containing:
- `recommendations`: list of `Recommendation` objects
- `model_version`: "1.0.0"
- `candidate_count`: number of products considered
- `ranking_metadata`: metadata about the ranking process
- `trace`: list of strings documenting what happened

---

## 6. Algorithms Used

### 6.1 Collaborative Filtering (ALS Matrix Factorization)

**File:** `recommendation_ml/models/collaborative.py`
**Class:** `CollaborativeModel`

**What it does:** Finds patterns in user-item interaction history. Users who interacted with similar products get similar recommendations.

**Algorithm:** Alternating Least Squares (ALS) matrix factorization with confidence weighting.

**How it works:**
1. Build user-item interaction matrix from interaction data
2. Apply confidence weighting: `confidence = 1 + alpha * matrix` where `alpha = 1.0`
3. Factorize into user factors and item factors (latent dimensions)
4. Config: 50 latent components, regularization = 0.02, 20 iterations
5. Score: `raw_score = user_factors[user] . item_factors[item]`
6. Normalize to [0, 1] via min-max

**Cold-start fallback:** If user not in training data, falls back to item popularity scores.

**Input:** User ID + candidate product IDs
**Output:** `dict[str, float]` -- product_id -> score in [0, 1]

### 6.2 Content-Based Filtering (TF-IDF + Cosine Similarity)

**File:** `recommendation_ml/models/content.py`
**Class:** `ContentModel`

**What it does:** Matches product text content (title, category, brand, description) to a customer's preference profile built from their interaction history.

**Algorithm:**
1. Build TF-IDF vectors for all products (max 5000 features, unigrams+bigrams)
2. Build customer preference vector: weighted average of TF-IDF vectors of products the customer interacted with (weights from event strength)
3. Score: `cosine_similarity(preference_vector, product_vector)` clamped to [0, 1]

**Product text construction:** Concatenates title + category + brand + description + property key-value pairs.

**Input:** Customer profile + candidate product IDs + interactions
**Output:** `dict[str, float]` -- product_id -> score in [0, 1]

### 6.3 Popularity Model

**File:** `recommendation_ml/models/popularity.py`
**Class:** `PopularityModel`

**What it does:** Ranks products by total interaction strength. Used as a baseline and cold-start fallback.

**Algorithm:**
1. Sum interaction strengths per product (view=1, addtocart=3, transaction=5, like=4, skip=-2)
2. Normalize: `score = raw_sum / max_sum`

**Input:** Candidate product IDs
**Output:** `dict[str, float]` -- product_id -> score in [0, 1]

### 6.4 Hybrid Scoring

**File:** `recommendation_ml/models/hybrid.py`
**Functions:** `hybrid_score_candidates()`, `hybrid_score_product()`

**What it does:** Combines all 7 scoring signals into a single weighted score per product.

**The 7 signals:**

| Signal | Source | Default Weight |
|--------|--------|---------------|
| Collaborative | `CollaborativeModel` | 0.30 |
| Content | `ContentModel` | 0.25 |
| Intent | `compute_intent_score()` | 0.20 |
| Customer Preference | `compute_preference_score()` | 0.10 |
| Popularity | `PopularityModel` | 0.05 |
| Session Relevance | `compute_session_score()` | 0.05 |
| Discovery | Hardcoded 0.0 (boosted later) | 0.05 |

**Final formula:**
```
final = W_c * collab + W_ct * content + W_i * intent + W_p * preference + W_po * popularity + W_s * session + W_d * discovery
```

Weights are normalized by `HybridWeights.normalize()` so they sum to exactly 1.0.

---

## 7. Collaborative Filtering

Detailed in Section 6.1 above.

Key parameters:
- `n_components = 50` (latent dimensions)
- `learning_rate = 0.01` (unused in current ALS, kept for future SGD variant)
- `regularization = 0.02`
- `iterations = 20`
- `alpha = 1.0` (confidence scaling)
- `random_seed = 42`

The model stores `_user_factors` and `_item_factors` numpy arrays after fitting. Cold-start users (not in training data) get popularity-based scores instead.

---

## 8. Content-Based Filtering

Detailed in Section 6.2 above.

Key parameters:
- `max_features = 5000` (TF-IDF vocabulary size)
- `ngram_range = (1, 2)` (unigrams and bigrams)
- `stop_words = "english"`

The customer preference vector is a weighted average of interacted product vectors, where weights are event strengths (time-decayed). This means a product the customer purchased recently contributes more to their preference than one they only viewed once.

---

## 9. Popularity Model

Detailed in Section 6.3 above.

Simple but important. It:
1. Works for cold-start (no user history)
2. Provides a stable baseline
3. Gets a small weight (0.05) in the hybrid, so it rarely dominates but prevents obscure products from ranking too high

---

## 10. Hybrid Recommendation

Detailed in Section 6.4 above.

The key design decisions:
1. **Weights are configurable** via `HybridWeights` dataclass
2. **Weights are auto-normalized** to sum to 1.0
3. **Discovery gets 0.0 in the hybrid formula** but is boosted post-hoc via `boost_discovery_candidates()` -- this keeps discovery separate from the core scoring
4. **Intent and preference are separate signals** -- intent comes from the current query, preference comes from historical behavior

---

## 11. Ranking

### Pre-scoring ranking (hard constraints)

Applied before any scoring in `apply_constraints()`:

| Constraint | Function | Logic |
|------------|----------|-------|
| Budget | `filter_by_budget()` | `price <= budget` AND `price >= min_budget` |
| Excluded brands | `filter_by_excluded_brands()` | Remove if brand in `mission.excluded_brands` (case-insensitive) |
| Excluded categories | `filter_by_excluded_categories()` | Remove if category in `mission.excluded_categories` (case-insensitive) |
| Minimum rating | `filter_by_rating()` | `rating >= min_rating` |

### Post-scoring ranking (diversity)

Applied after hybrid scoring in `diversify_recommendations()`:

Greedy selection: at each position, pick the candidate with the highest combined score:
```
combined = (1 - 0.3) * base_score + 0.3 * diversity_bonus
```

Where `diversity_bonus = (category_diversity + brand_diversity) / 2`.

This prevents the top-5 from being 5 products from the same category/brand.

---

## 12. Diversity / Constraints

### Diversity

**File:** `recommendation_ml/ranking/diversity.py`

- **Category diversity:** 1.0 if new category in list, `1/(1+count)` if repeated
- **Brand diversity:** 1.0 if new brand in list, `1/(1+count)` if repeated
- **MMR (Maximal Marginal Relevance):** Available but not used in the main pipeline. The main pipeline uses greedy diversity instead.
- **`diversity_weight`:** 0.3 (30% diversity, 70% relevance)

### Discovery

**File:** `recommendation_ml/ranking/discovery.py`

- **Novelty:** Binary -- 1.0 if product not in interaction history, 0.0 if seen
- **Mission fit:** 1.0 if category matches mission preferences, 0.3 otherwise
- **Discovery score:** `relevance * novelty * mission_fit * discovery_level`
- **Boost:** If novelty > 0.5, `boosted = base * (1 + 0.4 * discovery_level)`, capped at 1.0

`discovery_level` is controlled by the frontend/API (default 0.5).

---

## 13. Personalization

Personalization comes from **three sources**:

### Source 1: Customer Profile (historical behavior)

From `CustomerProfile.category_affinity`:
- `compute_preference_score()` uses `profile.category_affinity[category] * 0.6` as a signal
- Products in categories the customer historically engages with score higher

From `CustomerProfile.preferred_brands`:
- Brand match contributes 0.4 to the preference score

From `CustomerProfile.recent_categories`:
- Available but not directly used in the current scoring functions

### Source 2: Intent (current query)

From `Mission.preferred_categories`:
- `compute_intent_score()` gives +0.5 if product category matches

From `Mission.preferred_brands`:
- +0.3 if product brand matches

From `Mission.occasion`:
- +0.2 if product category contains the occasion

### Source 3: Interaction History (via models)

- **Collaborative filtering** uses the full interaction matrix to find similar users
- **Content filtering** builds a preference vector from interacted products
- **Popularity** is not personalized (same for all users)
- **Session relevance** is personalized via `mission.session_product_ids`

### Source 4: Event Strengths (time-decayed)

Every interaction is weighted by event type and recency:
- `strength = event_weight * exp(-ln(2)/30 * days_ago)`
- Purchase = 5.0, Like/Save = 4.0, Add to Cart = 3.0, View = 1.0, Skip = -2.0
- Recent interactions matter more (30-day half-life)

---

## 14. Data Used

### Interaction Data (`data/interactions.json`)

Fields: `timestamp`, `visitorid` (customer), `event` (view/addtocart/transaction), `itemid` (product), optional `transactionid`

Preprocessing pipeline:
1. Column normalization (maps various column names to standard names)
2. ID normalization (numeric IDs -> strings, non-numeric -> MD5 hash)
3. Deduplication
4. Timestamp parsing (auto-detects epoch ms, epoch seconds, ISO strings)
5. Time decay computation: `days_ago = (now - timestamp).days`, `decay = exp(-ln(2)/30 * days_ago)`
6. Event strength: `strength = event_weight * decay`

### Product Data (`data/catalog.json`)

Fields: `product_id`, `title`, `category`, `brand`, `price`, `description`, `rating`, optional `properties`

### Internal Data Representation

After loading, data is stored as:
- `pd.DataFrame` for interactions and products
- `dict[str, dict]` for product metadata index (product_id -> metadata dict)
- `pd.DataFrame` for user-item matrix (customer_id x product_id with strength values)
- numpy arrays for collaborative filtering latent factors

---

## 15. Important Files

| File | Purpose |
|------|---------|
| `recommendation_ml/__init__.py` | Public API: exports `RecommendationEngine`, `Mission`, `CustomerProfile`, `Recommendation` |
| `recommendation_ml/config.py` | All configurable parameters: event weights, hybrid weights, model hyperparameters |
| `recommendation_ml/schemas.py` | 7 dataclasses: `Mission`, `CustomerProfile`, `ScoreBreakdown`, `Recommendation`, `RecommendationResult`, `Product`, `Interaction` |
| `recommendation_ml/engine.py` | **Main entry point**: `RecommendationEngine` class with `fit()`, `recommend()`, `rerank_candidates()` |
| `recommendation_ml/models/popularity.py` | `PopularityModel` -- interaction-strength-based baseline |
| `recommendation_ml/models/content.py` | `ContentModel` -- TF-IDF + cosine similarity |
| `recommendation_ml/models/collaborative.py` | `CollaborativeModel` -- ALS matrix factorization |
| `recommendation_ml/models/hybrid.py` | Hybrid scoring: `normalize_scores()`, `compute_*_score()`, `hybrid_score_candidates()` |
| `recommendation_ml/data/loader.py` | Data preprocessing: `load_interactions()`, `load_products()`, `build_user_item_matrix()`, `build_product_metadata_index()` |
| `recommendation_ml/data/synthetic.py` | Synthetic data generator for testing |
| `recommendation_ml/ranking/constraints.py` | Hard constraint filters: budget, brands, categories, rating |
| `recommendation_ml/ranking/diversity.py` | Diversity re-ranking: category/brand diversity, MMR |
| `recommendation_ml/ranking/discovery.py` | Discovery/serendipity: novelty, mission fit, boost |
| `recommendation_ml/evaluation/metrics.py` | Offline metrics: Precision@K, Recall@K, NDCG@K, Hit Rate, Coverage, Diversity |
| `recommendation_ml/tests/test_recommendation.py` | 60+ unit tests covering all components |
| `recommendation_ml/tests/test_integration_audit.py` | Integration audit: 15 end-to-end checks |

---

## 16. Important Functions and Classes

### `RecommendationEngine` (engine.py)

```python
class RecommendationEngine:
    def __init__(self, config: RecommendationConfig = None)
    def fit(self, interactions, products, column_map=None) -> RecommendationEngine
    def recommend(self, customer_id, mission, customer_profile=None,
                  candidate_products=None, candidate_ids=None,
                  session_context=None, top_k=5, weights=None) -> RecommendationResult
    def rerank_candidates(self, candidates, customer_profile=None, mission=None,
                          constraints=None, top_k=5, weights=None) -> list[dict]
    def get_popular_products(self, k=10) -> list[Recommendation]
    def get_content_scores(self, customer_id, candidate_product_ids) -> dict[str, float]
    def get_collaborative_scores(self, customer_id, candidate_product_ids) -> dict[str, float]
```

**`fit()`** -- Trains all 3 models from raw interaction and product data. Called once at startup (cached via `@lru_cache` in `backend/service.py`).

**`recommend()`** -- The main API. Returns `RecommendationResult` with ranked products, scores, evidence, and trace.

**`rerank_candidates()`** -- Re-scores existing candidates with different constraints/weights without retraining. Used for what-if scenarios.

### `Mission` (schemas.py)

```python
@dataclass
class Mission:
    goal: str = ""
    occasion: str = ""
    budget: float = float("inf")
    preferred_categories: list[str] = []
    excluded_brands: list[str] = []
    excluded_categories: list[str] = []
    discovery_level: float = 0.3
    urgency: str = "medium"
    min_budget: float = 0.0
    preferred_brands: list[str] = []
    min_rating: float = 0.0
    style_preference: str = ""
    session_product_ids: list[str] = []
```

### `CustomerProfile` (schemas.py)

```python
@dataclass
class CustomerProfile:
    customer_id: str = ""
    category_affinity: dict[str, float] = {}
    price_sensitivity: float = 0.5
    preferred_brands: list[str] = []
    average_spend: float = 0.0
    recent_categories: list[str] = []
    recent_products: list[str] = []
    discovery_appetite: float = 0.3
    total_purchases: int = 0
    total_views: int = 0
    avg_rating: float = 0.0
```

### `Recommendation` (schemas.py)

```python
@dataclass
class Recommendation:
    product_id: str = ""
    final_score: float = 0.0
    score_breakdown: ScoreBreakdown = ScoreBreakdown()
    evidence: list[str] = []
    confidence: float = 0.0
    rank: int = 0
    metadata: dict = {}
```

### `RecommendationResult` (schemas.py)

```python
@dataclass
class RecommendationResult:
    recommendations: list[Recommendation] = []
    model_version: str = "1.0.0"
    candidate_count: int = 0
    ranking_metadata: dict = {}
    trace: list[str] = []
```

---

## 17. Integration With the Rest of RetailMind

### Who calls the Recommendation System?

**Only one file imports from `recommendation_ml`:** `backend/service.py`

All other connections are mediated through `backend/service.py`.

### Integration diagram

```
[Frontend]
    |
    | POST /api/recommendations
    v
[backend/main.py]
    |
    | calls recommend()
    v
[backend/service.py::recommend()]
    |
    |---> [Intent Agent] -> ShoppingIntent
    |---> [mission_from_query()] -> Mission (recommendation_ml.schemas.Mission)
    |---> [Agentic AI supervisor] -> workflow plan
    |---> [Customer Intelligence] -> digital twin dict
    |---> [profile_from_digital_twin()] -> CustomerProfile (recommendation_ml.schemas.CustomerProfile)
    |---> [RecommendationEngine.recommend()] -> RecommendationResult
    |---> [Product Intelligence] -> independent product scores
    |---> [Score blending] -> 0.65 * ml_score + 0.35 * pi_score
    |---> [Feedback adjustment] -> like +0.08, skip -0.12
    |---> [Bundle Optimizer] -> multi-item bundles
    |
    v
[Response dict] -> JSON -> Frontend
```

### Data adapters (in `backend/service.py`)

| Adapter | What it does |
|---------|-------------|
| `mission_from_query()` | Translates `ShoppingIntent` (from Intent Agent) into `Mission` (recommendation_ml schema) |
| `profile_from_digital_twin()` | Translates digital twin dict (from Customer Intelligence) into `CustomerProfile` (recommendation_ml schema) |
| `recommendation_engine()` | Cached factory: loads `data/interactions.json` + `data/catalog.json`, fits `RecommendationEngine` once |
| `_product_intelligence_scores()` | Runs Product Intelligence independently on same candidates, returns per-product scores |
| `_apply_feedback()` | Adjusts scores based on session feedback (like/save/cart/skip) |
| `_build_bundle()` | Generates multi-item bundles from top recommendations within budget |

### Score blending (service.py line 432)

```python
item["final_score"] = round(0.65 * item["final_score"] + 0.35 * product_score, 4)
```

The ML module's score gets 65% weight, Product Intelligence gets 35%.

### Feedback adjustment (service.py lines 377-381)

```python
if action == "like":
    item["final_score"] = round(min(1.0, item["final_score"] + 0.08), 4)
elif action == "skip":
    item["final_score"] = round(max(0.0, item["final_score"] - 0.12), 4)
```

---

## 18. End-to-End Data Flow

### Example: User says "I want affordable running shoes under 3000"

**Step 1: Frontend sends request**
```
POST /api/recommendations
{
    "customer_id": "42",
    "query": "I want affordable running shoes under 3000",
    "budget": 3000
}
```

**Step 2: `backend/main.py::get_recommendations()`**
- Calls `backend/service.py::recommend()`

**Step 3: `service.py::mission_from_query()`**
- Intent Agent parses query -> `{goal: "running shoes", category: "Sports", budget: 3000, ...}`
- Creates `Mission(goal="running shoes", budget=3000, preferred_categories=["Sports"], ...)`

**Step 4: `service.py::agentic_plan()`**
- Agentic AI supervisor plans: intent -> profile -> recommendation -> ranking -> bundle -> explanation

**Step 5: `service.py::profile_from_digital_twin()`**
- Digital twin -> `CustomerProfile(category_affinity={"Sports": 0.8, "Clothing": 0.6}, ...)`

**Step 6: `RecommendationEngine.recommend()`**
- `apply_constraints()`: removes products > 3000, excluded brands/categories
- `collaborative_model.get_collaborative_scores()`: scores based on similar users
- `content_model.score_for_customer()`: scores based on Sports/Clothing text match
- `popularity_model.get_scores()`: scores based on overall popularity
- `normalize_scores()`: all to [0, 1]
- `hybrid_score_candidates()`: weighted combination
- `boost_discovery_candidates()`: boost novel products
- `diversify_recommendations()`: ensure category/brand diversity
- `_generate_evidence()`: human-readable explanations
- Returns `RecommendationResult`

**Step 7: `service.py::_product_intelligence_scores()`**
- Product Intelligence independently scores same candidates
- Returns per-product PI scores

**Step 8: Score blending**
- `final_score = 0.65 * ml_score + 0.35 * pi_score`

**Step 9: Feedback adjustment**
- Applies any session feedback (like/skip)

**Step 10: Bundle building**
- `_build_bundle()` generates multi-item bundles within budget

**Step 11: Response**
```json
{
    "recommendations": [
        {
            "product_id": "P003",
            "final_score": 0.87,
            "score_breakdown": {...},
            "evidence": ["Directly matches your shopping goal", "Within your budget", ...],
            "rank": 1,
            "metadata": {"title": "Nike Running Shoes", "price": 2499, ...}
        },
        ...
    ],
    "mission": {...},
    "bundle": [...],
    "pipeline": ["Agentic AI Supervisor", "Intent Agent", "Customer Intelligence",
                 "Recommendation ML", "Product Intelligence", "Bundle Optimizer"]
}
```

---

## 19. Input / Output

### Input to `RecommendationEngine.recommend()`

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `customer_id` | `str` | Yes | - |
| `mission` | `Mission` | Yes | - |
| `customer_profile` | `CustomerProfile` | No | `None` |
| `candidate_products` | `list[dict]` | No | `None` (uses trained catalogue) |
| `candidate_ids` | `list[str]` | No | `None` |
| `session_context` | `dict` | No | `None` |
| `top_k` | `int` | No | `5` |
| `weights` | `HybridWeights` | No | `None` (uses config defaults) |

### Output: `RecommendationResult`

```python
RecommendationResult(
    recommendations=[
        Recommendation(
            product_id="P001",
            final_score=0.87,
            score_breakdown=ScoreBreakdown(
                collaborative=0.82,
                content=0.75,
                intent=0.90,
                preference=0.60,
                budget=0.0,
                session=0.0,
                popularity=0.45,
                discovery=0.0
            ),
            evidence=["Similar users purchased this product", "Directly matches your shopping goal"],
            confidence=0.957,
            rank=1,
            metadata={"title": "Nike Running Shoes", "price": 2499, "category": "Sports", "brand": "Nike"}
        ),
        ...
    ],
    model_version="1.0.0",
    candidate_count=12,
    ranking_metadata={},
    trace=["Applied budget constraint: 12 candidates", "Generated 5 recommendations"]
)
```

---

## 20. Testing and Evaluation

### Test suite (`recommendation_ml/tests/test_recommendation.py`)

60+ tests across 14 test classes:

| Test Class | Tests | What it covers |
|------------|-------|----------------|
| `TestSchemas` | 6 | Serialization/deserialization of all dataclasses |
| `TestDataLoading` | 7 | Column normalization, ID normalization, data loading, matrix building |
| `TestSyntheticData` | 2 | Synthetic data generation |
| `TestPopularityModel` | 4 | Fit, score, recommendations with exclusions |
| `TestContentModel` | 5 | TF-IDF vectors, cosine similarity, preference vectors |
| `TestCollaborativeModel` | 4 | ALS fitting, scoring, cold-start fallback |
| `TestHybridScoring` | 8 | Normalization, budget/intent/preference/session scoring |
| `TestConstraints` | 5 | Budget, brand, category filtering |
| `TestDiversity` | 4 | Category/brand diversity, diversity re-ranking |
| `TestDiscovery` | 5 | Novelty, discovery scoring, boost |
| `TestEvaluation` | 8 | Precision@K, Recall@K, NDCG@K, Coverage, Diversity |
| `TestColdStart` | 2 | Unknown user handling |
| `TestRecommendationEngine` | 9 | Full engine: fit, recommend, rerank, pop/content/collab scores |
| `TestEndToEnd` | 3 | Full pipeline, what-if pipeline, diversity pipeline |

### Integration audit (`recommendation_ml/tests/test_integration_audit.py`)

15 audit checks that verify:
- API contract correctness
- Engine fits realistic data
- Recommendations have required fields
- Budget filtering works
- Brand exclusion works
- Cold-start works
- Diversity is present
- Discovery level affects results
- Scores are normalized
- Reranking works
- No data leakage
- Empty candidates handled

### Evaluation metrics (`recommendation_ml/evaluation/metrics.py`)

| Metric | What it measures |
|--------|-----------------|
| Precision@K | Fraction of top-K that are relevant |
| Recall@K | Fraction of relevant items found in top-K |
| Hit Rate@K | Binary: any relevant item in top-K? |
| NDCG@K | Ranking quality (position-weighted relevance) |
| Catalog Coverage | Fraction of catalogue appearing in recommendations |
| Intra-list Diversity | Category diversity within a recommendation list |

### Running tests

```bash
python -m pytest recommendation_ml/tests/test_recommendation.py -v
python recommendation_ml/tests/test_integration_audit.py  # standalone audit
```

---

## 21. Current Implementation Status

### IMPLEMENTED

- `RecommendationEngine` with `fit()`, `recommend()`, `rerank_candidates()`
- `PopularityModel` -- fully working
- `ContentModel` -- TF-IDF + cosine similarity, fully working
- `CollaborativeModel` -- ALS matrix factorization, fully working with cold-start fallback
- Hybrid scoring -- 7-signal weighted combination
- Hard constraint filtering -- budget, brands, categories, rating
- Diversity re-ranking -- greedy category/brand diversity
- Discovery/serendipity -- novelty boost
- Evidence generation -- rule-based explanations
- All 7 data schemas with serialization
- Data loading pipeline -- column normalization, time decay, event strength
- Synthetic data generator
- Evaluation metrics
- 60+ unit tests + integration audit
- Backend integration via `backend/service.py`
- Product Intelligence score blending (65/35)
- Session feedback adjustment (like +0.08, skip -0.12)
- Bundle generation from top recommendations

### PARTIALLY IMPLEMENTED

- `rerank_candidates()` -- exists and works but uses a simpler formula than `recommend()`. In `recommend()`, hybrid scoring uses the full 7-signal formula. In `rerank_candidates()`, it uses a simplified blend with base_score * 0.5 for collaborative and content.

### NOT IMPLEMENTED / PLACEHOLDER

- The `session_context` parameter in `recommend()` is accepted but **not used** in the current scoring pipeline. Session relevance only uses `mission.session_product_ids`.
- The `weights` parameter in `recommend()` is accepted but the current implementation always uses the config defaults. Custom per-request weight overrides are not wired through.
- MMR diversification (`mmr_diversify()` in `diversity.py`) is implemented but **not called** by the main pipeline. The pipeline uses greedy diversity instead.
- The `learning_rate` config parameter is defined but unused (ALS uses analytical solve, not gradient descent).

---

## 22. Known Issues / Limitations

### MEDIUM

1. **Duplicate key in `EventWeights.get()`** -- `config.py` line 36 has `"addtocart"` mapped twice (duplicate dict key). The second one overwrites the first, but since both are `self.addtocart`, it's functionally harmless. Still, it's a code smell.

2. **`rerank_candidates()` uses different scoring than `recommend()`** -- The rerank formula is simpler: `0.5 * base * collab + 0.5 * base * content + ...`. This means reranking produces different score distributions than the initial recommend call. If a teammate calls `recommend()` then `rerank_candidates()`, the scores are not directly comparable.

3. **Discovery score is hardcoded to 0.0 in hybrid formula** -- In `hybrid_score_candidates()`, the discovery component is always `weights.discovery * 0.0 = 0.0`. Discovery is only applied post-hoc via `boost_discovery_candidates()`. This means the `HybridWeights.discovery` weight has no effect on the base hybrid score.

### LOW

4. **`session_context` parameter is unused** -- Accepted by `recommend()` but never read by any scoring function.

5. **`weights` override not wired** -- `recommend()` accepts `weights` parameter but always uses `self.config.hybrid_weights`.

6. **Cold-start collaborative falls back to popularity** -- When a new user has no interaction history, collaborative scores default to popularity. This means collaborative and popularity signals become identical for cold-start users, effectively reducing the hybrid to 6 signals.

7. **No product-level cold-start** -- If a product has no interactions, it gets a collaborative score of 0.0. For new products in the catalogue, this may unfairly penalize them.

---

## 23. How Teammates Can Use the Recommendation System

### Basic usage

```python
from recommendation_ml import RecommendationEngine, Mission, CustomerProfile

# 1. Create and fit engine
engine = RecommendationEngine()
engine.fit(interactions_data, products_data)

# 2. Create mission
mission = Mission(
    goal="running shoes",
    budget=3000,
    preferred_categories=["Sports"],
    excluded_brands=["Nike"],
    discovery_level=0.3,
)

# 3. Create customer profile
profile = CustomerProfile(
    customer_id="42",
    category_affinity={"Sports": 0.8, "Clothing": 0.6},
    preferred_brands=["Adidas"],
)

# 4. Get recommendations
result = engine.recommend(
    customer_id="42",
    mission=mission,
    customer_profile=profile,
    candidate_products=catalogue,
    top_k=5,
)

# 5. Use results
for rec in result.recommendations:
    print(f"{rec.rank}. {rec.product_id} (score={rec.final_score})")
    print(f"   Evidence: {rec.evidence}")
    print(f"   Breakdown: {rec.score_breakdown.to_dict()}")
```

### Getting scores for specific models

```python
# Content scores only
content_scores = engine.get_content_scores("42", ["P001", "P002", "P003"])

# Collaborative scores only
collab_scores = engine.get_collaborative_scores("42", ["P001", "P002", "P003"])

# Popularity baseline
popular = engine.get_popular_products(k=5)
```

### Re-ranking without retraining

```python
reranked = engine.rerank_candidates(
    candidates=existing_candidates,
    mission=new_mission,  # different budget, different exclusions
    top_k=3,
)
```

---

## 24. How Teammates Can Modify It Safely

### Changing weights

Edit `recommendation_ml/config.py` -> `HybridWeights` dataclass defaults. The `normalize()` method ensures they always sum to 1.0.

### Changing event strengths

Edit `recommendation_ml/config.py` -> `EventWeights` dataclass defaults.

### Adding a new scoring signal

1. Add a new weight field to `HybridWeights` in `config.py`
2. Add a new field to `ScoreBreakdown` in `schemas.py`
3. Compute the new score in `engine.py::recommend()`
4. Pass it to `hybrid_score_candidates()` in `hybrid.py`
5. Update the weighted sum formula in `hybrid_score_candidates()`
6. Add evidence generation in `engine.py::_generate_evidence()`
7. Update tests in `test_recommendation.py`

### Adding a new constraint

1. Add a new filter function in `ranking/constraints.py`
2. Call it in `apply_constraints()` in the same file
3. Add the corresponding field to `Mission` in `schemas.py` if needed

### Modifying the data pipeline

Edit `data/loader.py`. The key functions are `load_interactions()` and `load_products()`. Both accept column mappings, so they work with different data formats.

### Important: Do NOT modify

- `engine.py::recommend()` signature without updating `backend/service.py`
- `schemas.py` field names without updating `backend/service.py` adapters
- `config.py` defaults without re-running tests

---

## 25. Technical Summary

| Aspect | Detail |
|--------|--------|
| **Language** | Python 3.10+ |
| **Key libraries** | numpy, pandas, scikit-learn (TF-IDF, cosine similarity) |
| **Models** | Collaborative (ALS), Content (TF-IDF), Popularity (strength sum) |
| **Scoring** | 7-signal weighted hybrid |
| **Ranking** | Hard constraints -> hybrid score -> discovery boost -> diversity |
| **Cold-start** | Collaborative falls back to popularity |
| **Evaluation** | Precision@K, Recall@K, NDCG@K, Hit Rate, Coverage, Diversity |
| **Tests** | 60+ unit tests + 15 integration audits |
| **Data** | JSON files, loaded once at startup, cached |
| **Integration** | Single entry point: `backend/service.py` |
| **Configuration** | All tunable via `config.py` dataclasses |

---

# TL;DR FOR THE TEAM

## 30-second explanation

I built the recommendation engine for RetailMind. It takes a customer's shopping intent and profile, scores every product using collaborative filtering (similar users), content matching (similar products), and popularity, combines those scores with configurable weights, then re-ranks for diversity and boosts novel products. The result is a ranked list of personalized product recommendations with human-readable explanations.

## 1-minute technical explanation

The `recommendation_ml` module implements a hybrid recommendation system. When a request comes in, `RecommendationEngine.recommend()` first applies hard constraints (budget, excluded brands/categories, minimum rating) to filter the product catalogue. Then three models independently score every surviving product: **Collaborative Filtering** (ALS matrix factorization finding similar users), **Content-Based Filtering** (TF-IDF vectors + cosine similarity matching product text to customer preferences), and **Popularity** (total interaction strength). These scores are normalized to [0,1] and combined with four additional signals -- intent match, customer preference, session relevance, and discovery -- using a 7-signal weighted sum. The default weights are collaborative=0.30, content=0.25, intent=0.20, preference=0.10, popularity=0.05, session=0.05, discovery=0.05. After scoring, novel products get a discovery boost, then a greedy diversity re-ranking ensures the top-5 list isn't all from the same category or brand. Finally, rule-based evidence strings are generated for each recommendation. The module is called exclusively through `backend/service.py`, which also blends the ML scores with Product Intelligence scores (65/35 split) and applies session feedback adjustments.

## What files should a developer look at first?

1. `recommendation_ml/engine.py` -- the main `RecommendationEngine` class
2. `recommendation_ml/config.py` -- all configurable parameters
3. `recommendation_ml/schemas.py` -- all data structures
4. `recommendation_ml/models/hybrid.py` -- the hybrid scoring formulas
5. `backend/service.py` -- how the engine is called in production

## What should a developer know before changing this code?

- The `recommend()` method is the core API. Changing its signature breaks `backend/service.py`.
- The `Mission` and `CustomerProfile` schemas are the interface contracts with Intent and Customer Intelligence modules.
- The `HybridWeights` in `config.py` are auto-normalized to sum to 1.0 -- you can change individual weights and the system adapts.
- Collaborative filtering needs sufficient interaction data. With very few users/products, it degrades to popularity.
- The discovery score is hardcoded to 0.0 in the hybrid formula -- it's applied post-hoc via `boost_discovery_candidates()`.
- The `rerank_candidates()` method uses a simpler formula than `recommend()` -- scores from the two are not directly comparable.
- All tests are in `recommendation_ml/tests/test_recommendation.py`. Run them with `pytest`.
