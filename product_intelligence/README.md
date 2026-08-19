# Product Intelligence Engine

An interpretable, condition-aware product recommendation engine built using the RetailRocket dataset.

The Product Intelligence layer receives a structured shopping condition from an NLP chatbot / Intent Agent and evaluates eligible products using transparent, interpretable scoring components.

---

## Architecture

The overall system is:

User
  ↓
NLP Chatbot / Intent Agent
  ↓
Structured Condition
  ↓
Product Intelligence Engine
  ↓
Hard Filtering
  ↓
Component Scoring
  ↓
Dynamic Weight Selection
  ↓
Transparent Weighted Score
  ↓
Ranking
  ↓
Recommendations + Explanation


The Product Intelligence engine is implemented as:

src/
└── product_intelligence/
    ├── __init__.py
    ├── condition.py
    ├── filtering.py
    ├── scoring.py
    ├── ranking.py
    └── recommender.py

---

## Core Idea

The system does not use a black-box recommendation model.

Instead, each product receives five interpretable component scores:

1. Category Match
2. Budget Fit
3. Semantic / Style Fit
4. Quality
5. Discovery / Novelty

The final Product Intelligence score is:

PI Score =

    w_category × Category Match
  + w_budget × Budget Fit
  + w_semantic × Semantic Fit
  + w_quality × Quality
  + w_discovery × Discovery

The weights change according to the user's intent.

For example:

A budget-focused request:

    Budget → high importance

A "surprise me" / discovery-focused request:

    Discovery → high importance

This makes the recommendation process both condition-aware and explainable.

---

## Components

### 1. Category Match

Measures whether the product belongs to the requested category.

Score range:

    0 → 1

---

### 2. Budget Fit

Measures how well the product price fits within the user's budget.

Products within the budget receive the highest score.

Products above the budget receive a decreasing score.

Budget can also act as a hard constraint when:

    strict_budget = True

---

### 3. Semantic / Style Fit

Measures how closely the product attributes match the user's keywords.

Example condition:

    keywords = [
        "stylish",
        "casual",
        "unique"
    ]

The current implementation uses TF-IDF and cosine similarity.

---

### 4. Quality

Quality is derived from product interaction behavior in RetailRocket.

Signals include:

- Views
- Add-to-cart events
- Transactions
- Conversion rate

A smoothed conversion measure is used to reduce instability from products with very few interactions.

---

### 5. Discovery

Discovery favors products that are less popular / less frequently viewed.

This allows the engine to surface less obvious products when the user requests discovery.

---

## Dynamic Weight Profiles

### Budget-focused

```text
Category      0.20
Budget        0.45
Semantic      0.20
Quality       0.10
Discovery     0.05