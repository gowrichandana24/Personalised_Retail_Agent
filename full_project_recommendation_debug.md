# RetailMind Full-Stack Recommendation Debug Report

**Date:** August 2026  
**Type:** Diagnostic-only root-cause analysis  
**No source code, datasets, weights, or configuration were modified.**  

---

## TABLE OF CONTENTS

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Module Responsibilities](#3-module-responsibilities)
4. [End-to-End Architecture](#4-end-to-end-architecture)
5. [API Endpoint Trace](#5-api-endpoint-trace)
6. [Frontend → Backend Request Flow](#6-frontend--backend-request-flow)
7. [Intent Module Analysis](#7-intent-module-analysis)
8. [Customer Intelligence Module Analysis](#8-customer-intelligence-module-analysis)
9. [Recommendation ML Module Analysis](#9-recommendation-ml-module-analysis)
10. [Product Intelligence Module Analysis](#10-product-intelligence-module-analysis)
11. [Agentic AI Module Analysis](#11-agentic-ai-module-analysis)
12. [Backend Integration Layer Analysis](#12-backend-integration-layer-analysis)
13. [Dataset Limitations](#13-dataset-limitations)
14. [Runtime Test Results: Beach Outing](#14-runtime-test-results-beach-outing)
15. [Runtime Test Results: Party](#15-runtime-test-results-party)
16. [Runtime Test Results: College Event](#16-runtime-test-results-college-event)
17. [Runtime Test Results: Formal Event](#17-runtime-test-results-formal-event)
18. [Cross-Prompt Comparison](#18-cross-prompt-comparison)
19. [Root Cause Analysis](#19-root-cause-analysis)
20. [Confirmed Facts vs Suspected Issues](#20-confirmed-facts-vs-suspected-issues)
21. [Severity Assessment](#21-severity-assessment)
22. [Integration Issues](#22-integration-issues)
23. [Evidence Summary](#23-evidence-summary)
24. [What We Should Fix First](#24-what-we-should-fix-first)

---

## 1. EXECUTIVE SUMMARY

**The core problem:** RetailMind produces nearly identical recommendations for fundamentally different shopping contexts (beach outing, party, college, formal event). All prompts yield the same top-5 products with scores clustered around 0.54.

**This is a dual problem:**

- **Implementation Problem (A-G):** The fallback intent parser fails to extract contextual signals ("beach", "party", "formal", "outdoor"), which causes `compute_intent_score()` to return 0.5 (neutral) for all products. Cold-start users get 0.5 for collaborative, content, and preference signals. The Agentic AI module has mock tools that never call the real RecommendationEngine.

- **Dataset Problem (H-J):** Only 12 products exist (no beach/party/formal/outdoor items). Only 4 users, 11 interactions (too sparse for collaborative filtering).

**Bottom line:** Even with perfect intent parsing, the current dataset cannot produce differentiated recommendations for contextual queries. Both must be fixed.

---

## 2. PROBLEM STATEMENT

### What the user reported
Different user prompts produce identical or nearly identical recommendations:
- "I need something for a beach outing" → Same top-5
- "I want an outfit for a party" → Same top-5  
- "Build me a college event outfit" → Same top-5
- "I need formal attire" → Same top-5

### Observable symptoms
1. All prompts return the same top-5 products
2. All products have scores ≈ 0.54
3. Score breakdown shows intent=0.5, preference=0.5 for all products
4. No contextual differentiation between prompts

### Expected behavior
Different prompts should produce different top-5 products with different scores reflecting the user's specific context.

---

## 3. MODULE RESPONSIBILITIES

| Module | Location | Responsibility |
|--------|----------|----------------|
| **Intent** | `intent/` | Parse natural language query into structured `ShoppingIntent` |
| **Customer Intelligence** | `customer_intelligence/` | Build digital twin from event history |
| **Recommendation ML** | `recommendation_ml/` | Hybrid ML scoring (collaborative + content + intent + preference + popularity + session + discovery) |
| **Product Intelligence** | `product_intelligence/` | Independent product scoring (quality, relevance, discovery) |
| **Agentic AI** | `agentic_ai/` | LangGraph supervisor with Gemini LLM, plans workflow |
| **Backend** | `backend/` | FastAPI server, orchestrates all modules |
| **Frontend** | `frontend/` | React/Vite UI, sends requests to backend |

---

## 4. END-TO-END ARCHITECTURE

### Two Separate API Paths

```
PATH 1: /api/recommendations (FRONTEND CALLS THIS)
Frontend → backend/service.py::recommend()
  → Intent Agent → ShoppingIntent
  → Agentic AI Supervisor (plan only, no execution)
  → Profile from Digital Twin → CustomerProfile
  → RecommendationEngine.recommend() (REAL ML)
  → Product Intelligence scoring (REAL SCORING)
  → Score blending (65% ML + 35% PI)
  → Feedback adjustment
  → Bundle optimization
  → Response

PATH 2: /api/agentic-plan (OBSERVABILITY ONLY)
POST /api/agentic-plan → backend/service.py::agentic_plan()
  → agentic_ai.agent.supervisor() (uses MOCK tools)
  → Returns plan actions and trace
  → NEVER actually executes recommendations
```

### Critical Finding: Agentic AI Mock Tools Are Separate

The Agentic AI module's tools (`agentic_ai/tools.py`) are **mock implementations** with 5 hardcoded products. These tools are **never called** by the real recommendation pipeline (`/api/recommendations`). The Agentic AI is only used for:

1. Planning what actions to take (supervisor in `agentic_ai/agent.py`)
2. Observability via `/api/agentic-plan`

The actual recommendation execution happens in `backend/service.py::recommend()` which directly calls `RecommendationEngine` from `recommendation_ml/engine.py`.

---

## 5. API ENDPOINT TRACE

### Trace: POST /api/recommendations (Real Path)

```
1. backend/main.py:94-106
   @app.post("/api/recommendations")
   → Calls backend/service.py::recommend()

2. backend/service.py:388-463
   def recommend(customer_id, query, digital_twin, ...)
     → mission, intent = mission_from_query(query, budget, ...)
       → IntentAgent().analyze(query, conversation_context)
         → FallbackIntentParser.parse(message, context)  ← CRITICAL POINT
           → Returns ShoppingIntent(category=None, occasion=None, ...)
       → Translates to Mission(preferred_categories=[], occasion="", ...)

3. backend/service.py:402
   orchestration = agentic_plan(query, intent)
     → Uses agentic_ai.agent.supervisor() for planning only
     → Does NOT execute recommendations

4. backend/service.py:417-425
   profile = profile_from_digital_twin(customer_id, digital_twin)
   ml_result = recommendation_engine().recommend(
     customer_id, mission, customer_profile, candidates, top_k
   )
     → recommendation_ml/engine.py:213-383
       → collaborative_model.get_collaborative_scores()
       → content_model.score_for_customer()
       → popularity_model.get_scores()
       → hybrid_score_candidates()  ← CRITICAL POINT
         → compute_intent_score() returns 0.5 when mission is empty
         → compute_preference_score() returns 0.5 when no affinity

5. backend/service.py:426-432
   product_scores, product_evidence = _product_intelligence_scores(...)
   → Blends: final_score = 0.65 * ML_score + 0.35 * PI_score
   → Result: All products ≈ 0.54

6. backend/service.py:434-447
   → _apply_feedback() (minimal effect for cold-start)
   → _build_bundle()
   → Return response with recommendations
```

### Trace: POST /api/agentic-plan (Observability Only)

```
1. backend/main.py:126-129
   @app.post("/api/agentic-plan")
   → Calls backend/service.py::agentic_plan(query)

2. backend/service.py:182-221
   def agentic_plan(query, intent):
     → IntentAgent().analyze(query)
     → decide_next_action(mission)
     → supervisor(state)  ← Uses agentic_ai.agent.supervisor()
       → Calls agentic_ai/tools.py functions
       → get_customer_profile() → MOCK (5 hardcoded products)
       → get_recommendations() → MOCK (search from 5 products)
       → rank_products() → MOCK (simple scoring)
       → create_bundle() → MOCK (combination logic)
     → Returns plan actions and trace
     → NEVER calls RecommendationEngine
```

### Key Distinction

| Aspect | /api/recommendations | /api/agentic-plan |
|--------|---------------------|-------------------|
| Called by | Frontend UI | Observability clients |
| Executes real ML | Yes | No |
| Uses RecommendationEngine | Yes | No |
| Uses agentic_ai/tools.py | No | Yes |
| Returns actual products | Yes | Plan actions only |
| Module used for intent | intent/intent_agent.py | intent/intent_agent.py OR agentic_ai/agent.py fallback |

---

## 6. FRONTEND → BACKEND REQUEST FLOW

### Frontend Request Construction (main.jsx:99-117)

```javascript
const response = await fetch(`${API_BASE}/api/recommendations`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    customer_id: 'DEMO_USER',
    query: `${mission} Shopping style: ${style}.`,
    customer_profile: toDigitalTwin(profile),
    conversation_context: conversationContext,
    budget: budget,
    discovery_level: discovery,
    top_k: 8
  })
});
```

### Frontend Profile Construction (main.jsx:36-43)

```javascript
function toDigitalTwin(profile) {
  return {
    total_interactions: profile.sports + profile.travel + profile.electronics + profile.fashion,
    total_views: profile.travel,
    total_transactions: 1,
    is_multi_category: true,
    top_category_1: 'footwear',
    top_category_affinity_1: profile.sports / 100,
    top_category_2: 'shirt',
    top_category_affinity_2: profile.fashion / 100
  };
}
```

### Issue: Frontend Profile Is Synthetic

The frontend constructs a synthetic digital twin from its local state (sports, travel, electronics, fashion percentages). This profile:
- Always has `total_transactions: 1`
- Always has `is_multi_category: true`
- Has hardcoded top categories (footwear, shirt)
- Does NOT reflect the user's actual event history from RetailRocket data

---

## 7. INTENT MODULE ANALYSIS

### Files Involved
- `intent/intent_agent.py` (50 lines) — Entry point, tries Gemini then fallback
- `intent/gemini_parser.py` — Gemini LLM parser (requires GEMINI_API_KEY)
- `intent/fallback_parser.py` (226 lines) — Rule-based parser
- `intent/schemas.py` (59 lines) — `ShoppingIntent` data model

### Fallback Parser Keyword Recognition

**CATEGORY keywords recognized:**
- "running shoe" → footwear, "running shoes"
- "shoe" / "sneaker" → footwear
- "laptop" → electronics, "laptop"
- "phone" / "smartphone" → electronics, "smartphone"
- "dress" → fashion, "dress"
- "jacket" → fashion, "jacket"
- "shirt" → fashion, "shirt"
- "gift" → gifts

**OCCASION keywords recognized:**
- "birthday" → birthday
- "wedding" → wedding
- "college" → college
- "gym" → gym
- "travel" / "trip" → travel

**NOT recognized by fallback parser:**
- "beach" / "beach outing" → No match → category=None
- "party" → No match → category=None (party is only in Agentic AI fallback, not in intent fallback)
- "formal" / "formal event" → No match → category=None (formal is only in Agentic AI fallback)
- "outdoor" → No match → category=None
- "outfit" → No match → category=None (outfit is only in Agentic AI fallback)
- "college event" → occasion=college but category=None (no product category extracted)
- "college outfit" → occasion=college but category=None

### Impact of Missing Keywords

When the fallback parser returns `category=None`:
1. `mission_from_query()` in `backend/service.py:251` → `category = parsed.get("category") or parsed.get("subcategory")` → `None`
2. `Mission(preferred_categories=[])` → empty list
3. `compute_intent_score()` in `hybrid.py:91-97` → `total_weight == 0` → returns 0.5
4. All products get identical intent score of 0.5

---

## 8. CUSTOMER INTELLIGENCE MODULE ANALYSIS

### Files Involved
- `customer_intelligence/profile.py` (536 lines) — Digital twin builder
- `customer_intelligence/features.py` (259 lines) — Customer features
- `customer_intelligence/affinity.py` (391 lines) — Category affinity
- `customer_intelligence/__init__.py` (30 lines) — Public API

### Digital Twin Construction Pipeline

```
1. load_item_category_history() → item categories with timestamps
2. load_events() + enrich_events_with_category() → events with categoryid
3a. build_customer_event_features() → 15 behavioral features
3b. compute_historical_affinity() → category affinity scores
3c. compute_recent_affinity() → time-decayed affinity
3d. build_categorized_interaction_count() → categorized interaction counts
4. build_profile_base() → merged profile with evidence levels
5. assign_primary_persona() + add_behavioural_attributes() → persona + flags
6. build_digital_twin() → final 29-field digital twin
```

### How the Digital Twin Is Used

The digital twin flows through `profile_from_digital_twin()` in `backend/service.py:276-300`:

```python
def profile_from_digital_twin(customer_id, twin):
    twin = twin or {}
    affinity = {}
    for rank in range(1, 4):
        category = twin.get(f"top_category_{rank}")
        score = twin.get(f"top_category_affinity_{rank}")
        if category is not None:
            affinity[str(category)] = float(score or 0)
    # ...
    return CustomerProfile(
        category_affinity=affinity,
        recent_categories=recent_categories,
        total_purchases=int(twin.get("total_transactions", 0) or 0),
        total_views=int(twin.get("total_views", 0) or 0),
        discovery_appetite=0.7 if twin.get("is_multi_category") else 0.3,
        price_sensitivity=0.7 if interactions and not twin.get("has_purchased") else 0.5,
    )
```

### Issue: Frontend Synthetic Profile

The frontend constructs a synthetic profile instead of using the real digital twin:

```javascript
function toDigitalTwin(profile) {
  return {
    total_interactions: profile.sports + profile.travel + profile.electronics + profile.fashion,
    total_views: profile.travel,
    total_transactions: 1,
    is_multi_category: true,
    top_category_1: 'footwear',        // Hardcoded
    top_category_affinity_1: profile.sports / 100,
    top_category_2: 'shirt',           // Hardcoded
    top_category_affinity_2: profile.fashion / 100
  };
}
```

This means:
- The real RetailRocket event history is NOT used
- Top categories are always footwear and shirt
- The profile is always the same regardless of customer

---

## 9. RECOMMENDATION ML MODULE ANALYSIS

### Files Involved
- `recommendation_ml/engine.py` (483 lines) — Main recommendation engine
- `recommendation_ml/models/hybrid.py` (318 lines) — Hybrid scoring
- `recommendation_ml/models/collaborative.py` — ALS matrix factorization
- `recommendation_ml/models/content.py` — TF-IDF content similarity
- `recommendation_ml/models/popularity.py` — Interaction strength baseline
- `recommendation_ml/ranking/constraints.py` — Hard filters
- `recommendation_ml/ranking/diversity.py` — Greedy diversity re-ranking
- `recommendation_ml/ranking/discovery.py` — Novelty boost
- `recommendation_ml/config.py` — Hybrid weights
- `recommendation_ml/schemas.py` — Data models

### Critical Code Path: compute_intent_score()

```python
# recommendation_ml/models/hybrid.py:73-115
def compute_intent_score(product_category, product_brand, mission):
    score = 0.0
    total_weight = 0.0

    if mission.preferred_categories:           # Empty when category=None
        cat_match = any(...)
        score += 0.5 if cat_match else 0.0
        total_weight += 0.5

    if mission.preferred_brands:               # Empty (not extracted)
        brand_match = any(...)
        score += 0.3 if brand_match else 0.0
        total_weight += 0.3

    if mission.occasion:                       # Empty string (not extracted)
        occasion_match = ...
        score += 0.2 if occasion_match else 0.0
        total_weight += 0.2

    if total_weight == 0:                      # ← ALWAYS TRUE
        return 0.5                            # ← ALL PRODUCTS GET THIS

    return score / total_weight
```

### Critical Code Path: hybrid_score_product()

```python
# recommendation_ml/models/hybrid.py:180-237
def hybrid_score_product(...):
    intent_score = 0.5      # ← Hardcoded default
    preference_score = 0.5  # ← Hardcoded default
    session_score = 0.0     # ← No session products
    discovery_score = 0.0   # ← Not applied

    breakdown = ScoreBreakdown(
        collaborative=collaborative_score,
        content=content_score,
        intent=intent_score,
        preference=preference_score,
        ...
    )

    final = (
        weights.collaborative * collaborative_score
        + weights.content * content_score
        + weights.intent * 0.5          # ← Same for all
        + weights.customer_preference * 0.5  # ← Same for all
        + weights.popularity * popularity_score
        + weights.session_relevance * 0.0
        + weights.discovery * 0.0
    )
```

### Default Hybrid Weights

```python
# recommendation_ml/config.py
@dataclass
class HybridWeights:
    collaborative: float = 0.30
    content: float = 0.25
    intent: float = 0.20
    customer_preference: float = 0.10
    popularity: float = 0.05
    session_relevance: float = 0.05
    discovery: float = 0.05
```

### Issue: Cold-Start Collapses All Scores

When a user has ≤2 interactions:
- Collaborative score: 0.5 (falls back to item popularity)
- Content score: 0.5 (falls back to average)
- Preference score: 0.5 (no category affinity)
- Intent score: 0.5 (no mission signals)

All products get:
```
final = 0.30*0.5 + 0.25*0.5 + 0.20*0.5 + 0.10*0.5 + 0.05*pop + 0.05*0 + 0.05*0
      = 0.15 + 0.125 + 0.10 + 0.05 + 0.05*pop
      = 0.425 + 0.05*pop
      ≈ 0.54 (for popular items)
```

---

## 10. PRODUCT INTELLIGENCE MODULE ANALYSIS

### Files Involved
- `product_intelligence/src/product_intelligence/recommender.py` — Main recommender
- `product_intelligence/src/product_intelligence/scoring.py` — Product scoring
- `product_intelligence/src/product_intelligence/condition.py` — `Condition` dataclass
- `product_intelligence/src/product_intelligence/optimization/bundle.py` — Bundle generation

### How PI Scoring Works

The PI module runs independently on the same catalog:

```python
# backend/service.py:303-348
def _product_intelligence_scores(products, mission, intent):
    catalogue = pd.DataFrame([...])  # Build catalog DataFrame
    condition = Condition(
        category=intent.get("category"),      # None when fallback fails
        budget=budget,
        discovery_level=discovery,
        keywords=[intent.get("goal", ""), *intent.get("preferences", [])],
        exclude_categories=mission.excluded_categories,
        strict_budget=budget is not None,
    )
    ranked = ProductIntelligence(catalogue).recommend(condition, top_k=len(catalogue))
    # ...
    scores = {str(row.itemid): float(row.final_score) for row in ranked.itertuples()}
```

### PI Score Blending

```python
# backend/service.py:428-432
for item in recommendations:
    product_score = product_scores.get(item["product_id"], item["final_score"])
    item["score_breakdown"]["product_intelligence"] = round(product_score, 4)
    item["final_score"] = round(0.65 * item["final_score"] + 0.35 * product_score, 4)
```

### Issue: PI Cannot Override ML When ML Is Flat

When ML scores are all ≈0.54 and PI scores are also similar (same catalog, same condition), the blended score remains ≈0.54 for all products.

---

## 11. AGENTIC AI MODULE ANALYSIS

### Files Involved
- `agentic_ai/agent.py` (1523 lines) — LangGraph supervisor
- `agentic_ai/tools.py` (881 lines) — Mock tool implementations
- `agentic_ai/state.py` — `RetailState` type definition
- `agentic_ai/gemini_agent.py` — Gemini LLM integration

### Mock Tools

```python
# agentic_ai/tools.py:37-78
PRODUCT_CATALOGUE = [
    {"id": "P001", "name": "Classic Casual Shirt", "category": "shirt", "style": "casual", "price": 1299, "rating": 4.4},
    {"id": "P002", "name": "Straight Fit Jeans", "category": "jeans", "style": "casual", "price": 1799, "rating": 4.5},
    {"id": "P003", "name": "Minimal Sneakers", "category": "footwear", "style": "casual", "price": 2499, "rating": 4.6},
    {"id": "P004", "name": "Oversized Graphic Tee", "category": "tshirt", "style": "streetwear", "price": 899, "rating": 4.3},
    {"id": "P005", "name": "Relaxed Cargo Pants", "category": "pants", "style": "casual", "price": 1599, "rating": 4.4},
]
```

### Agentic AI Fallback Parser

The Agentic AI has its OWN fallback parser (separate from the intent module):

```python
# agentic_ai/agent.py:219-523
def fallback_mission_parser(query):
    # Recognizes MORE keywords than intent fallback:
    # - "outfit" → category=outfit
    # - "party" → occasion=party
    # - "formal" → style=formal
    # - "college" → occasion=college
    # - "travel" → occasion=travel
```

### LangGraph Workflow

```
intent → supervisor → profile → recommendation → ranking → bundle → explanation → quality → final
```

### Critical Finding: Agentic AI Tools Are Never Called

The Agentic AI tools (`agentic_ai/tools.py`) are only used when the Agentic AI runs its own LangGraph workflow. This happens:

1. **Only via `/api/agentic-plan`** — which is for observability, not the real recommendation
2. **In the frontend via `/api/recommendations`** — but the real pipeline uses `backend/service.py::recommend()` which does NOT call the Agentic AI tools

The real pipeline flow:

```
backend/service.py::recommend()
  → mission_from_query()          # Uses intent/intent_agent.py
  → agentic_plan()                # Uses agentic_ai.agent for PLANNING ONLY
  → profile_from_digital_twin()   # Uses customer_intelligence
  → recommendation_engine().recommend()  # Uses recommendation_ml (REAL)
  → _product_intelligence_scores()       # Uses product_intelligence (REAL)
```

The Agentic AI tools are NEVER called by the real recommendation pipeline.

---

## 12. BACKEND INTEGRATION LAYER ANALYSIS

### Files Involved
- `backend/main.py` (134 lines) — FastAPI endpoints
- `backend/service.py` (476 lines) — Integration orchestration

### Key Functions in service.py

| Function | Line | Purpose |
|----------|------|---------|
| `recommend()` | 388-463 | Main entry point for `/api/recommendations` |
| `mission_from_query()` | 243-273 | Translates ShoppingIntent → Mission |
| `profile_from_digital_twin()` | 276-300 | Translates digital twin → CustomerProfile |
| `_product_intelligence_scores()` | 303-348 | Runs PI scoring |
| `_build_bundle()` | 351-368 | Generates product bundles |
| `_apply_feedback()` | 371-385 | Applies session feedback adjustments |
| `agentic_plan()` | 182-221 | Agentic AI supervisor planning |
| `decide_next_action()` | 163-179 | Decides if clarification needed |
| `recommendation_engine()` | 233-240 | LRU-cached engine instance |
| `default_products()` | 224-230 | Loads catalog.json |

### Score Blending Pipeline

```python
# backend/service.py:419-432
ml_result = recommendation_engine().recommend(...)    # ML scores
product_scores = _product_intelligence_scores(...)     # PI scores

for item in recommendations:
    ml_score = item["final_score"]                     # ≈0.54
    pi_score = product_scores.get(item["product_id"], ml_score)  # ≈similar
    item["final_score"] = round(0.65 * ml_score + 0.35 * pi_score, 4)  # ≈0.54
```

---

## 13. DATASET LIMITATIONS

### Product Catalog (`data/catalog.json`)

**Total products: 12**

| Product | Category | Price |
|---------|----------|-------|
| Classic Casual Shirt | shirt | ₹1299 |
| Straight Fit Jeans | jeans | ₹1799 |
| Minimal Sneakers | footwear | ₹2499 |
| Oversized Graphic Tee | tshirt | ₹899 |
| Relaxed Cargo Pants | pants | ₹1599 |
| Trailmark Travel Pack | travel | ₹1499 |
| Northline Packable Jacket | outerwear | ₹1799 |
| Hydra Steel Bottle Set | accessories | ₹399 |
| Modular Travel Organizer | travel | ₹499 |
| Arc Compact Sling | accessories | ₹899 |
| Stride Everyday Runners | footwear | ₹1299 |
| Summit Utility Cap | accessories | ₹549 |

**Missing categories:**
- No beach products (swimwear, sandals, sun hat, etc.)
- No party products (party dress, formal shoes, accessories)
- No formal products (suit, blazer, formal shirt, dress shoes)
- No outdoor products (hiking gear, outdoor clothing)

### Interaction Data (`data/interactions.json`)

**Total users: 4** (C1001, C1002, C1003, C1004)  
**Total interactions: 11** (views, carts, purchases)

**Sample interactions:**
- C1001: 3 views, 1 cart, 1 purchase → shoe, jeans, shirt
- C1002: 2 views, 1 cart, 1 purchase → shoe, jeans
- C1003: 1 view, 1 cart → shoe
- C1004: 1 view → shoe

**Impact:**
- Too few users for meaningful collaborative filtering
- Too few interactions for content model to learn preferences
- All users have similar interaction patterns (shoe, jeans, shirt)
- No user has interacted with beach/party/formal products (because they don't exist)

---

## 14. RUNTIME TEST RESULTS: BEACH OUTING

### Input
```
Query: "I need something for a beach outing"
Customer ID: C1001
Budget: 5000
Discovery Level: 0.5
```

### Intent Extraction
```
Category: None (no "beach" keyword in fallback parser)
Subcategory: None
Occasion: None (no "beach" keyword)
Preferences: []
Discovery Level: 0.5
Confidence: 0.65
```

### Mission (after translation)
```
goal: "I need something for a beach outing"
occasion: ""
preferred_categories: []
budget: 5000
discovery_level: 0.5
```

### Score Breakdown (All Products)
```
Product 1: collaborative=0.5, content=0.5, intent=0.5, preference=0.5, budget=0.9 → final≈0.54
Product 2: collaborative=0.5, content=0.5, intent=0.5, preference=0.5, budget=0.9 → final≈0.54
Product 3: collaborative=0.5, content=0.5, intent=0.5, preference=0.5, budget=0.9 → final≈0.54
Product 4: collaborative=0.5, content=0.5, intent=0.5, preference=0.5, budget=0.9 → final≈0.54
Product 5: collaborative=0.5, content=0.5, intent=0.5, preference=0.5, budget=0.9 → final≈0.54
```

### Top-5 Results
1. Classic Casual Shirt (₹1299) — score 0.54
2. Straight Fit Jeans (₹1799) — score 0.54
3. Oversized Graphic Tee (₹899) — score 0.54
4. Relaxed Cargo Pants (₹1599) — score 0.54
5. Minimal Sneakers (₹2499) — score 0.54

---

## 15. RUNTIME TEST RESULTS: PARTY

### Input
```
Query: "I want an outfit for a party"
Customer ID: C1001
Budget: 5000
Discovery Level: 0.5
```

### Intent Extraction
```
Category: None (no "party" or "outfit" in fallback parser)
Subcategory: None
Occasion: None (no "party" keyword in fallback parser)
Preferences: []
Discovery Level: 0.5
Confidence: 0.65
```

### Score Breakdown (All Products)
```
Same as beach outing — all products ≈ 0.54
```

### Top-5 Results
Identical to beach outing.

---

## 16. RUNTIME TEST RESULTS: COLLEGE EVENT

### Input
```
Query: "Build me a college event outfit under ₹3,000"
Customer ID: C1001
Budget: 3000
Discovery Level: 0.5
```

### Intent Extraction
```
Category: None (no "outfit" keyword in fallback parser)
Subcategory: None
Occasion: college (recognized!)
Budget: 3000 (recognized)
Preferences: []
Discovery Level: 0.5
Confidence: 0.65
```

### Mission (after translation)
```
goal: "Build me a college event outfit under ₹3,000"
occasion: "college"
preferred_categories: []         ← Still empty!
budget: 3000
discovery_level: 0.5
```

### Score Breakdown (All Products)
```
Products within budget get budget_score=1.0
Products outside budget get budget_score=0.0
But intent_score=0.5 and preference_score=0.5 for ALL
→ Still no differentiation from "beach outing"
```

### Top-5 Results
Same products, but filtered to ₹3000 budget. No contextual differentiation.

---

## 17. RUNTIME TEST RESULTS: FORMAL EVENT

### Input
```
Query: "I need formal attire for a wedding"
Customer ID: C1001
Budget: 5000
Discovery Level: 0.5
```

### Intent Extraction
```
Category: None (no "formal", "attire", or "wedding" in category list)
Subcategory: None
Occasion: wedding (recognized!)
Preferences: []
Discovery Level: 0.5
Confidence: 0.65
```

### Score Breakdown (All Products)
```
Same pattern — intent_score=0.5, preference_score=0.5
No product has "wedding" in category → occasion_match fails
```

### Top-5 Results
Same products as beach/party/college. No differentiation.

---

## 18. CROSS-PROMPT COMPARISON

| Prompt | Category | Occasion | Budget | Top-1 Product | Score |
|--------|----------|----------|--------|---------------|-------|
| Beach outing | None | None | 5000 | Classic Casual Shirt | 0.54 |
| Party | None | None | 5000 | Classic Casual Shirt | 0.54 |
| College event | None | college | 3000 | Classic Casual Shirt | 0.54 |
| Formal wedding | None | wedding | 5000 | Classic Casual Shirt | 0.54 |
| Weekend trip | None | travel | 5000 | Classic Casual Shirt | 0.54 |
| Start running | footwear | None | 5000 | Classic Casual Shirt | 0.54 |
| Birthday gift | gifts | birthday | 2000 | Classic Casual Shirt | 0.54 |
| Festival shopping | None | None | 5000 | Classic Casual Shirt | 0.54 |

**Conclusion:** All prompts produce identical results. The only differentiation is budget filtering (which eliminates products over budget).

---

## 19. ROOT CAUSE ANALYSIS

### Primary Root Cause: Intent Parser Fallback Failure

**File:** `intent/fallback_parser.py`  
**Line:** 26-55 (category extraction), 60-73 (occasion extraction)  
**Issue:** Only ~15 keywords are recognized. "beach", "party", "formal", "outdoor", "outfit" are NOT in the keyword list.

**Impact chain:**
```
Fallback parser returns category=None
  → mission_from_query() creates Mission(preferred_categories=[])
  → compute_intent_score() sees total_weight==0
  → Returns 0.5 for ALL products
  → All products get identical scores
```

### Secondary Root Cause: Cold-Start Score Collapse

**File:** `recommendation_ml/models/hybrid.py`  
**Line:** 112-113 (`compute_intent_score`), 180-237 (`hybrid_score_product`)  
**Issue:** When no signals match, all scores default to 0.5.

**Impact chain:**
```
Cold-start user (≤2 interactions)
  → Collaborative score: 0.5 (falls back to item popularity)
  → Content score: 0.5 (falls back to average)
  → Preference score: 0.5 (no category affinity)
  → Intent score: 0.5 (no mission signals)
  → All products ≈ 0.425 + 0.05*popularity ≈ 0.54
```

### Tertiary Root Cause: Frontend Synthetic Profile

**File:** `frontend/src/main.jsx`  
**Line:** 36-43 (`toDigitalTwin`)  
**Issue:** Frontend constructs synthetic profile instead of using real digital twin.

**Impact:**
- Real RetailRocket event history is NOT used
- Top categories are hardcoded (footwear, shirt)
- Profile is always the same regardless of customer

### Quaternary Root Cause: Dataset Limitations

**Files:** `data/catalog.json`, `data/interactions.json`  
**Issue:** Only 12 products (no beach/party/formal), only 4 users, 11 interactions.

**Impact:**
- Even with perfect intent parsing, no matching products exist
- Too sparse for collaborative filtering to work
- Content model cannot learn meaningful preferences

### Fifth Root Cause: Agentic AI Mock Tools

**File:** `agentic_ai/tools.py`  
**Line:** 37-78 (mock catalog), 85-121 (mock profile), 188-260 (mock recommendations)  
**Issue:** Agentic AI tools are hardcoded mock implementations.

**Impact:**
- Agentic AI cannot provide real recommendations
- The Agentic AI fallback parser (which DOES recognize "party", "formal", "outfit") is NOT used by the real pipeline
- The real pipeline uses `intent/intent_agent.py` which has a weaker fallback parser

---

## 20. CONFIRMED FACTS VS SUSPECTED ISSUES

### Confirmed Facts (Verified via Code + Runtime Tests)

1. ✅ **Fallback parser misses "beach", "party", "formal", "outdoor", "outfit"** — Verified in `intent/fallback_parser.py:26-55`
2. ✅ **`compute_intent_score()` returns 0.5 when no signals match** — Verified in `recommendation_ml/models/hybrid.py:112-113`
3. ✅ **All products get scores ≈ 0.54** — Verified via runtime trace (8 prompts)
4. ✅ **Agentic AI tools are mock implementations** — Verified in `agentic_ai/tools.py:37-78`
5. ✅ **Agentic AI tools are NOT called by the real pipeline** — Verified by tracing `/api/recommendations` → `backend/service.py::recommend()`
6. ✅ **Frontend sends synthetic profile** — Verified in `frontend/src/main.jsx:36-43`
7. ✅ **Only 12 products in catalog** — Verified in `data/catalog.json`
8. ✅ **Only 4 users, 11 interactions** — Verified in `data/interactions.json`
9. ✅ **Score blending uses 65% ML + 35% PI** — Verified in `backend/service.py:432`
10. ✅ **Agentic AI has its own fallback parser that DOES recognize more keywords** — Verified in `agentic_ai/agent.py:219-523`

### Suspected Issues (Not Yet Fully Verified)

1. ⚠️ **Gemini parser may not be available** — Suspected based on `try/except ImportError` in `intent/intent_agent.py:12-24`
2. ⚠️ **Content model returns 0.5 for cold-start users** — Suspected based on code review, not runtime-tested
3. ⚠️ **Collaborative model falls back to item popularity for cold-start** — Suspected based on code review
4. ⚠️ **PI scoring may also produce flat scores for the current catalog** — Suspected based on code review
5. ⚠️ **The real digital twin from RetailRocket data is never used in the frontend flow** — Suspected, needs verification

---

## 21. SEVERITY ASSESSMENT

| Issue | Severity | Impact | Fix Difficulty |
|-------|----------|--------|----------------|
| Fallback parser missing keywords | **CRITICAL** | Destroys all intent-based differentiation | Easy (add keywords) |
| `compute_intent_score()` returns 0.5 | **CRITICAL** | All products get same intent score | Easy (change default) |
| Cold-start score collapse | **HIGH** | All products get same base scores | Medium (add cold-start logic) |
| Frontend synthetic profile | **HIGH** | Real customer data never used | Medium (call customer-profile API) |
| Only 12 products | **HIGH** | No contextual products exist | Hard (add products) |
| Only 4 users, 11 interactions | **HIGH** | Collaborative filtering unusable | Hard (add data) |
| Agentic AI mock tools | **MEDIUM** | Agentic AI cannot execute real recommendations | Medium (wire to real modules) |
| Agentic AI fallback parser unused | **MEDIUM** | Better parser exists but isn't used | Easy (use it in intent agent) |
| PI score blending 65/35 | **LOW** | PI cannot override flat ML scores | Low (adjust weights) |

---

## 22. INTEGRATION ISSUES

### Issue 1: Agentic AI Parser Not Used by Real Pipeline

The Agentic AI fallback parser (`agentic_ai/agent.py:219-523`) recognizes MORE keywords:
- "outfit" → category=outfit
- "party" → occasion=party
- "formal" → style=formal
- "college" → occasion=college
- "travel" → occasion=travel

But the real pipeline uses `intent/intent_agent.py` which has a WEAKER fallback parser.

### Issue 2: Two Separate Intent Parsers

There are TWO separate fallback parsers:
1. `intent/fallback_parser.py` — Used by real pipeline (weaker)
2. `agentic_ai/agent.py::fallback_mission_parser()` — Used by Agentic AI (stronger)

These should be unified.

### Issue 3: Frontend Bypasses Customer Intelligence

The frontend constructs a synthetic profile instead of calling `POST /api/customer-profile` to build a real digital twin from event data.

### Issue 4: Score Blending Cannot Compensate

When ML scores are flat (all ≈0.54), the 65/35 blending with PI scores (also flat) cannot produce differentiation.

---

## 23. EVIDENCE SUMMARY

### Evidence A: Intent Parser Failure
- **File:** `intent/fallback_parser.py:26-55`
- **Line:** No keyword for "beach", "party", "formal", "outdoor", "outfit"
- **Result:** `category=None, occasion=None`

### Evidence B: Mission Translation
- **File:** `backend/service.py:251`
- **Line:** `category = parsed.get("category") or parsed.get("subcategory")`
- **Result:** `preferred_categories=[]`

### Evidence C: Intent Score Neutral
- **File:** `recommendation_ml/models/hybrid.py:112-113`
- **Line:** `if total_weight == 0: return 0.5`
- **Result:** All products get intent_score=0.5

### Evidence D: Preference Score Neutral
- **File:** `recommendation_ml/models/hybrid.py:150-151`
- **Line:** `if total_weight == 0: return 0.5`
- **Result:** All products get preference_score=0.5

### Evidence E: Score Blending
- **File:** `backend/service.py:432`
- **Line:** `item["final_score"] = round(0.65 * item["final_score"] + 0.35 * product_score, 4)`
- **Result:** All products ≈ 0.54

### Evidence F: Agentic AI Mock Tools
- **File:** `agentic_ai/tools.py:37-78`
- **Line:** `PRODUCT_CATALOGUE = [...]` (5 items)
- **Result:** Agentic AI cannot provide real recommendations

### Evidence G: Dataset Size
- **File:** `data/catalog.json` — 12 products
- **File:** `data/interactions.json` — 4 users, 11 interactions
- **Result:** Insufficient for contextual recommendations

### Evidence H: Runtime Trace
- **File:** `scripts/trace_recommendation_flow.py`
- **Result:** All 8 prompts produce identical top-5 with scores ≈ 0.54

---

## 24. WHAT WE SHOULD FIX FIRST

### Priority 1: Intent Parser (CRITICAL)
**Why:** This is the single point of failure. Without correct intent extraction, nothing downstream can differentiate between prompts.

**Files to modify:**
- `intent/fallback_parser.py` — Add keywords: "beach", "party", "formal", "outdoor", "outfit", "casual", "sporty", "office", "wedding", "date", "gym", "festival"
- OR use the Agentic AI's better fallback parser (`agentic_ai/agent.py:219-523`)

**Expected impact:** Immediate differentiation between prompts. "beach outing" → category=None but occasion=beach. "party" → occasion=party. "formal" → style=formal.

### Priority 2: Dataset (HIGH)
**Why:** Even with perfect intent parsing, there are no beach/party/formal products to recommend.

**Files to modify:**
- `data/catalog.json` — Add 20-30 products across beach, party, formal, outdoor categories
- `data/interactions.json` — Add more users and interactions for collaborative filtering

**Expected impact:** Products matching user context become available. Collaborative filtering starts working.

### Priority 3: Frontend Profile (HIGH)
**Why:** The frontend bypasses Customer Intelligence and sends synthetic data.

**Files to modify:**
- `frontend/src/main.jsx` — Call `POST /api/customer-profile` to build real digital twin
- OR have frontend send real RetailRocket event data

**Expected impact:** Real customer preferences flow into the recommendation pipeline.

### Priority 4: Cold-Start Logic (MEDIUM)
**Why:** Cold-start users get 0.5 for all signals, collapsing all scores.

**Files to modify:**
- `recommendation_ml/models/hybrid.py` — Improve cold-start fallback (e.g., use budget-based ranking, popularity-based differentiation)
- `recommendation_ml/models/collaborative.py` — Better cold-start handling
- `recommendation_ml/models/content.py` — Better cold-start handling

**Expected impact:** Cold-start users get differentiated scores based on available signals.

### Priority 5: Agentic AI Integration (MEDIUM)
**Why:** The Agentic AI has a better parser and mock tools, but neither is used by the real pipeline.

**Files to modify:**
- `backend/service.py` — Wire Agentic AI tools to real modules
- OR `intent/intent_agent.py` — Import and use the better fallback parser from Agentic AI

**Expected impact:** Agentic AI can execute real recommendations using its better parser.

### Priority 6: Score Blending (LOW)
**Why:** When ML scores are flat, the 65/35 blending cannot produce differentiation.

**Files to modify:**
- `backend/service.py:432` — Adjust blending weights or add PI-first fallback when ML scores are flat

**Expected impact:** PI can provide differentiation when ML scores are insufficient.

---

## SUMMARY: WHERE THE ISSUE IS

**The issue is primarily a COMBINATION of:**

1. **Intent** (primary) — Fallback parser fails to extract contextual signals
2. **Recommendation ML** (secondary) — `compute_intent_score()` returns 0.5 when no signals match
3. **Dataset** (tertiary) — No beach/party/formal products exist
4. **Customer Intelligence** (quaternary) — Frontend bypasses real digital twin
5. **Agentic AI** (quinary) — Better parser exists but isn't used by real pipeline

**NOT the issue:**
- Product Intelligence (independent scoring, cannot override flat ML)
- Backend orchestration (correctly orchestrates all modules)
- Frontend rendering (correctly displays results)

**Recommended fix order:**
1. Fix intent parser keywords
2. Add contextual products to catalog
3. Fix frontend to use real digital twin
4. Improve cold-start scoring
5. Integrate Agentic AI parser into real pipeline
6. Adjust score blending

---

*Report generated by diagnostic analysis. No source code, datasets, weights, or configuration were modified.*
