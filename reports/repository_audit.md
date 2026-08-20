# Repository Audit Report

_Generated: 2026-08-20T21:03:37.463071_

```
Repository: D:\sem_7\cog_hackathon\Personalised_Retail_Agent
Branch:     main
Commit:     a60e1c8
Remote:     https://github.com/gowrichandana24/Personalised_Retail_Agent.git
```

---

# 1. Repository Overview

**Path:** `D:\sem_7\cog_hackathon\Personalised_Retail_Agent`
**Branch:** `main`
**Commit:** `a60e1c8`
**Remote:** `https://github.com/gowrichandana24/Personalised_Retail_Agent.git`
**Commits:** 14
**Ahead of remote:** 0
**Behind remote:** 0
**Files:** 86
**Folders:** 27

## File counts by extension

| Extension | Count |
|-----------|-------|
| `.py` | 56 |
| `.md` | 7 |
| `.txt` | 6 |
| `.json` | 5 |
| `(none)` | 3 |
| `.ipynb` | 3 |
| `.ps1` | 2 |
| `.example` | 1 |
| `.html` | 1 |
| `.jsx` | 1 |
| `.css` | 1 |

## Approximate lines of code

| Language/Extension | Lines |
|--------------------|-------|
| `.py` | 9,584 |
| `.md` | 1,286 |
| `.json` | 1,267 |
| `.jsx` | 190 |
| `.txt` | 27 |
| `.ps1` | 10 |
| `.css` | 5 |
| `.html` | 1 |

---

# 2. Complete Directory Tree

```
Personalised_Retail_Agent/
├── agentic_ai/  # 6 Python files, The `agentic_ai` module is the Agentic AI orchestration layer of RetailMind.
│   ├── agent.py
│   ├── app.py
│   ├── config.py
│   ├── gemini_agent.py
│   ├── README.md
│   ├── requirements.txt
│   ├── state.py
│   └── tools.py
├── backend/  # 3 Python files, The FastAPI application exposes the single integration path used by the
│   ├── __init__.py
│   ├── main.py
│   ├── README.md
│   └── service.py
├── backend_package/  # This package makes the repository's existing modules work together:
│   ├── README.md
│   └── requirements-backend.txt
├── customer_intelligence/  # 4 Python files, 2 notebooks
│   ├──  notebooks/
│   │   └── 01_customer_exploration.ipynb
│   ├── notebooks/
│   │   └── 01_customer_exploration.ipynb
│   ├── __init__.py
│   ├── affinity.py
│   ├── features.py
│   └── profile.py
├── data/  # 2 JSON files
│   ├── catalog.json
│   └── interactions.json
├── frontend/  # 547 JS/TS files, 28 JSON files
│   ├── src/
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── .env.example
│   ├── index.html
│   ├── package-lock.json
│   └── package.json
├── intent/  # 7 Python files
│   ├── __init__.py
│   ├── fallback_parser.py
│   ├── gemini_parser.py
│   ├── intent_agent.py
│   ├── prompts.py
│   ├── schemas.py
│   └── test_intent.py
├── postman/  # 1 JSON files
│   └── RetailMind.postman_collection.json
├── product_intelligence/  # 12 Python files, 1 notebooks, An interpretable, condition-aware product recommendation engine built using the 
│   ├── data/  # 2 JSON files
│   ├── notebook/
│   │   └── product_engineering.ipynb
│   ├── Personalised_Retail_Agent/
│   ├── src/
│   │   ├── product_intelligence/  # 12 Python files, 1 notebooks, An interpretable, condition-aware product recommendation engine built using the 
│   │   │   ├── optimization/
│   │   │   ├── __init__.py
│   │   │   ├── condition.py
│   │   │   ├── filtering.py
│   │   │   ├── ranking.py
│   │   │   ├── recommender.py
│   │   │   └── scoring.py
│   │   └── __init__.py
│   ├── test/
│   │   └── test.py
│   ├── README.md
│   └── requirement.txt
├── recommendation_ml/  # 21 Python files, Hybrid recommendation engine for the RetailMind hackathon project. Combines coll
│   ├── data/  # 2 JSON files
│   │   ├── __init__.py
│   │   ├── loader.py
│   │   └── synthetic.py
│   ├── evaluation/
│   │   ├── __init__.py
│   │   └── metrics.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── collaborative.py
│   │   ├── content.py
│   │   ├── hybrid.py
│   │   └── popularity.py
│   ├── ranking/
│   │   ├── __init__.py
│   │   ├── constraints.py
│   │   ├── discovery.py
│   │   └── diversity.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_integration_audit.py
│   │   └── test_recommendation.py
│   ├── __init__.py
│   ├── config.py
│   ├── engine.py
│   ├── README.md
│   └── schemas.py
├── reports/
│   └── repository_audit.md
├── scripts/  # 2 Python files
│   ├── repo_audit.py
│   ├── run_backend.ps1
│   ├── run_frontend.ps1
│   └── smoke_test.py
├── demo_recommendation.py
├── README.md
├── requirements-backend.txt
└── requirements.txt
```

---

# 3. Project Components

| Component | Summary |
|-----------|---------|
| `agentic_ai` | 6 Python files -- The `agentic_ai` module is the Agentic AI orchestration layer of RetailMind. |
| `backend` | 3 Python files -- The FastAPI application exposes the single integration path used by the |
| `backend_package` | This package makes the repository's existing modules work together: |
| `customer_intelligence` | 4 Python files |
| `data` | Present |
| `frontend` | 269 JS/JSX files |
| `intent` | 7 Python files |
| `postman` | Present |
| `product_intelligence` | 12 Python files -- An interpretable, condition-aware product recommendation engine built using the RetailRocket dataset |
| `recommendation_ml` | 21 Python files -- Hybrid recommendation engine for the RetailMind hackathon project. Combines collaborative filtering, |
| `reports` | Present |
| `scripts` | 2 Python files |

---

# 4. Important Files

| File | Purpose |
|------|---------|
| `.gitignore` | Git ignore rules |
| `README.md` | Documentation |
| `agentic_ai\README.md` | Documentation |
| `agentic_ai\app.py` | Python application |
| `agentic_ai\requirements.txt` | Python dependencies |
| `backend\README.md` | Documentation |
| `backend\main.py` | Python entry point |
| `backend_package\README.md` | Documentation |
| `backend_package\requirements-backend.txt` | Backend Python dependencies |
| `frontend\.env.example` | Environment variable template |
| `frontend\.gitignore` | Git ignore rules |
| `frontend\package-lock.json` | Lockfile |
| `frontend\package.json` | Node.js dependencies/scripts |
| `product_intelligence\.gitignore` | Git ignore rules |
| `product_intelligence\README.md` | Documentation |
| `recommendation_ml\README.md` | Documentation |
| `requirements-backend.txt` | Backend Python dependencies |
| `requirements.txt` | Python dependencies |

### `README.md`

*(First 15 lines shown)*

# RetailMind — Personalised Retail Agent

RetailMind is a full-stack, explainable shopping-recommendation system. This
repository connects every project module through one FastAPI backend and a
React frontend.

## Connected architecture

```text
React frontend
  ├─ POST /api/recommendations
  └─ POST /api/feedback
          │
          ▼
FastAPI backend

### `agentic_ai\README.md`

*(First 15 lines shown)*

# RetailMind - Agentic AI

## Overview

The `agentic_ai` module is the Agentic AI orchestration layer of RetailMind.

It handles:

- Shopping intent understanding
- Shopping mission extraction
- Customer profile retrieval
- Personalized recommendation retrieval
- Product ranking
- Bundle creation
- Recommendation explanation

### `backend\README.md`

*(First 15 lines shown)*

# RetailMind connected backend

The FastAPI application exposes the single integration path used by the
React frontend:

```text
React UI -> Agentic AI -> Intent -> Customer Intelligence -> Recommendation ML
         -> Product Intelligence -> Bundle Optimizer -> JSON response
```

## Start locally

From the repository root:

```powershell

### `backend_package\README.md`

*(First 15 lines shown)*

# RetailMind backend integration

This package makes the repository's existing modules work together:

`frontend -> FastAPI -> Intent Agent -> Customer Digital Twin adapter -> Recommendation ML -> ranked response`

## Install and run

Copy `backend/` and `requirements-backend.txt` into the repository root, then run:

```bash
pip install -r requirements-backend.txt
uvicorn backend.main:app --reload
```


### `product_intelligence\README.md`

*(First 15 lines shown)*

# Product Intelligence Engine

An interpretable, condition-aware product recommendation engine built using the RetailRocket dataset.

The Product Intelligence layer receives a structured shopping condition from an NLP chatbot / Intent Agent and evaluates eligible products using transparent, interpretable scoring components.

---

## Architecture

The overall system is:

User
  ↓
NLP Chatbot / Intent Agent

### `recommendation_ml\README.md`

*(First 15 lines shown)*

# Recommendation ML Module — RetailMind

## Overview

Hybrid recommendation engine for the RetailMind hackathon project. Combines collaborative filtering, content-based similarity, popularity, and mission/intent-aware ranking with diversity optimization and discovery support.

## Quick Start

```python
from recommendation_ml import RecommendationEngine, Mission, CustomerProfile
from recommendation_ml.data.synthetic import generate_test_scenario

# Generate test data
scenario = generate_test_scenario()


### `requirements.txt`

**4 dependencies:**
- `numpy>=1.24.0`
- `pandas>=2.0.0`
- `scikit-learn>=1.3.0`
- `scipy>=1.10.0`

### `agentic_ai\requirements.txt`

**9 dependencies:**
- `fastapi`
- `uvicorn`
- `langgraph`
- `langchain`
- `langchain-core`
- `langchain-google-genai`
- `python-dotenv`
- `pydantic`
- `google-genai`

### `requirements-backend.txt`

**7 dependencies:**
- `-r requirements.txt`
- `fastapi>=0.110.0`
- `uvicorn[standard]>=0.27.0`
- `python-dotenv>=1.0.0`
- `pydantic>=2.0.0`
- `langgraph>=0.2.0`
- `google-genai>=1.0.0`

### `backend_package\requirements-backend.txt`

**4 dependencies:**
- `-r requirements.txt`
- `fastapi>=0.110.0`
- `uvicorn[standard]>=0.27.0`
- `python-dotenv>=1.0.0`

### `frontend\.env.example`

**Environment variable template:**
- `VITE_API_BASE_URL`

### `frontend\package.json`

**Name:** retailmind-frontend
**Version:** 1.0.0
**Description:** N/A

**npm scripts:**
- `dev`: `vite`
- `build`: `vite build`
- `preview`: `vite preview`

**Dependencies:** 5 packages

---

# 5. Python Analysis

**Total Python files:** 56

## Entry Points

- `demo_recommendation.py`
- `agentic_ai\agent.py`
- `agentic_ai\app.py`
- `scripts\repo_audit.py`
- `scripts\smoke_test.py`
- `recommendation_ml\tests\test_recommendation.py`
- `product_intelligence\src\product_intelligence\optimization\bundle.py`
- `product_intelligence\src\product_intelligence\optimization\optimizer.py`

## Inter-module Imports

- `backend\service.py` -> `customer_intelligence`
- `backend\service.py` -> `intent.intent_agent`
- `backend\service.py` -> `recommendation_ml.engine`
- `backend\service.py` -> `recommendation_ml.schemas`
- `backend\service.py` -> `product_intelligence.condition`
- `backend\service.py` -> `product_intelligence.recommender`
- `backend\service.py` -> `product_intelligence.optimization.bundle`
- `backend\service.py` -> `agentic_ai.agent`
- `demo_recommendation.py` -> `recommendation_ml`
- `demo_recommendation.py` -> `recommendation_ml.data.synthetic`
- `demo_recommendation.py` -> `recommendation_ml.evaluation.metrics`
- `scripts\smoke_test.py` -> `backend.service`

## Syntax Errors

_No syntax errors detected._

## TODO/FIXME Comments

- `agentic_ai\agent.py:73`: MAX_REPLAN_ATTEMPTS = 3
- `agentic_ai\agent.py:1205`: and count < MAX_REPLAN_ATTEMPTS
- `agentic_ai\gemini_agent.py:25`: - Resilient to temporary Gemini failures
- `agentic_ai\gemini_agent.py:165`: Gemini is retried automatically when temporary
- `agentic_ai\gemini_agent.py:168`: Non-temporary errors are raised immediately.
- `agentic_ai\gemini_agent.py:320`: for attempt in range(max_retries):
- `agentic_ai\gemini_agent.py:368`: # Temporary Gemini/API errors
- `agentic_ai\gemini_agent.py:369`: temporary_error = (
- `agentic_ai\gemini_agent.py:382`: if not temporary_error:
- `agentic_ai\gemini_agent.py:387`: # Last attempt
- `agentic_ai\gemini_agent.py:390`: if attempt == max_retries - 1:
- `agentic_ai\gemini_agent.py:393`: "Gemini is temporarily unavailable "
- `agentic_ai\gemini_agent.py:394`: "after multiple retry attempts."
- `agentic_ai\gemini_agent.py:401`: wait_time = 2 ** attempt
- `agentic_ai\gemini_agent.py:408`: f"Attempt {attempt + 1}/{max_retries} "
- `agentic_ai\gemini_agent.py:413`: f"Temporary Gemini error detected."
- `scripts\repo_audit.py:347`: (".env.example", "Environment variable template"),
- `scripts\repo_audit.py:423`: lines.append("**Environment variable template:**")
- `scripts\repo_audit.py:455`: todo_comments: List[str] = []
- `scripts\repo_audit.py:511`: # TODO/FIXME
- `scripts\repo_audit.py:513`: if re.search(r'(?i)(TODO|FIXME|HACK|XXX|TEMP)', ln):
- `scripts\repo_audit.py:514`: todo_comments.append(f"`{rel}:{i}`: {ln.strip()[:100]}")
- `scripts\repo_audit.py:549`: # TODOs
- `scripts\repo_audit.py:550`: lines.append("## TODO/FIXME Comments\n")
- `scripts\repo_audit.py:551`: if todo_comments:
- `scripts\repo_audit.py:552`: for tc in todo_comments:
- `scripts\repo_audit.py:576`: issues.extend([f"MEDIUM: TODO/FIXME in `{tc.split(':')[0]}`" for tc in todo_comments[:10]])
- `scripts\repo_audit.py:1227`: lines.append("Attempting frontend build check...\n")
- `scripts\repo_audit.py:1608`: ("intent/prompts.py", "LLM prompt templates"),
- `scripts\repo_audit.py:1638`: ("frontend/.env.example", "Environment variable template"),
- `recommendation_ml\data\synthetic.py:3`: Generates realistic retail interaction data for hackathon development
- `recommendation_ml\data\synthetic.py:34`: PRODUCT_TEMPLATES = {
- `recommendation_ml\data\synthetic.py:91`: template = rng.choice(PRODUCT_TEMPLATES.get(category, ["{brand} {product} {variant}"]))
- `recommendation_ml\data\synthetic.py:93`: title = template.format(brand=brand, product=product_name, variant=variant)
- `recommendation_ml\tests\test_integration_audit.py:440`: # Create a temporary engine with sparse data

## Duplicate Names (potential risk)

- **RecommendationRequest**: class in `agentic_ai\app.py`, class in `backend\main.py`
- **filter_by_budget**: function in `recommendation_ml\ranking\constraints.py`, function in `product_intelligence\src\product_intelligence\optimization\constraints.py`
- **fit**: function in `recommendation_ml\engine.py`, function in `recommendation_ml\models\collaborative.py`, function in `recommendation_ml\models\content.py`, function in `recommendation_ml\models\popularity.py`
- **from_dict**: function in `recommendation_ml\schemas.py`, function in `recommendation_ml\schemas.py`, function in `recommendation_ml\schemas.py`
- **get_collaborative_scores**: function in `recommendation_ml\engine.py`, function in `recommendation_ml\models\collaborative.py`
- **get_content_scores**: function in `recommendation_ml\engine.py`, function in `recommendation_ml\models\content.py`
- **get_customer_profile**: function in `agentic_ai\tools.py`, function in `customer_intelligence\profile.py`
- **get_popular_products**: function in `recommendation_ml\engine.py`, function in `recommendation_ml\models\popularity.py`
- **get_recommendations**: function in `agentic_ai\tools.py`, function in `backend\main.py`
- **is_fitted**: function in `recommendation_ml\engine.py`, function in `recommendation_ml\models\collaborative.py`, function in `recommendation_ml\models\content.py`, function in `recommendation_ml\models\popularity.py`
- **main**: function in `demo_recommendation.py`, function in `scripts\repo_audit.py`, function in `scripts\smoke_test.py`
- **parse**: function in `intent\fallback_parser.py`, function in `intent\gemini_parser.py`
- **rank_products**: function in `agentic_ai\tools.py`, function in `product_intelligence\src\product_intelligence\ranking.py`
- **recommend**: function in `agentic_ai\app.py`, function in `backend\service.py`, function in `recommendation_ml\engine.py`, function in `product_intelligence\src\product_intelligence\recommender.py`
- **test_empty_candidates**: function in `recommendation_ml\tests\test_recommendation.py`, function in `recommendation_ml\tests\test_recommendation.py`
- **test_empty_fit**: function in `recommendation_ml\tests\test_recommendation.py`, function in `recommendation_ml\tests\test_recommendation.py`
- **test_fit**: function in `recommendation_ml\tests\test_recommendation.py`, function in `recommendation_ml\tests\test_recommendation.py`, function in `recommendation_ml\tests\test_recommendation.py`
- **test_get_collaborative_scores**: function in `recommendation_ml\tests\test_recommendation.py`, function in `recommendation_ml\tests\test_recommendation.py`
- **test_get_content_scores**: function in `recommendation_ml\tests\test_recommendation.py`, function in `recommendation_ml\tests\test_recommendation.py`
- **to_dict**: function in `recommendation_ml\schemas.py`, function in `recommendation_ml\schemas.py`, function in `recommendation_ml\schemas.py`, function in `recommendation_ml\schemas.py`, function in `recommendation_ml\schemas.py`, function in `recommendation_ml\schemas.py`, function in `recommendation_ml\schemas.py`

---

# 6. Frontend Analysis

**Name:** `retailmind-frontend`
**Version:** `1.0.0`
**Description:** N/A

### npm scripts

- `dev`: `vite`
- `build`: `vite build`
- `preview`: `vite preview`

### Dependencies (5)

- `@vitejs/plugin-react`: `latest`
- `react`: `latest`
- `react-dom`: `latest`
- `typescript`: `latest`
- `vite`: `latest`

### Environment Variables

- `VITE_API_BASE_URL`

### Source Files

- JSX/TSX: 1
- JS/TS: 0
- CSS: 1

#### `frontend\src\main.jsx`

**API calls:** ${API_BASE}/api/feedback, ${API_BASE}/api/recommendations

### Build Output

Files in `dist/`: 4
_Build exists -- `npm run build` was previously executed._

### node_modules

**Installed packages:** 20
_node_modules present -- `npm install` was previously executed._

---

# 7. Backend / API Analysis

**Detected framework:** FastAPI

## API Endpoints

| Method | Endpoint | File | Function | Purpose |
|--------|----------|------|----------|---------|
| GET | `/` | `agentic_ai\app.py` | `health_check` |  |
| POST | `/recommend` | `agentic_ai\app.py` | `recommend` |  |
| GET | `/api/health` | `backend\main.py` | `health` |  |
| GET | `/api/modules` | `backend\main.py` | `modules` | Return the concrete module-to-backend integration map. |
| GET | `/api/catalog` | `backend\main.py` | `catalog` |  |
| POST | `/api/recommendations` | `backend\main.py` | `get_recommendations` |  |
| POST | `/api/customer-profile` | `backend\main.py` | `build_customer_profile` | Build a customer digital twin from raw events and category h |
| POST | `/api/agentic-plan` | `backend\main.py` | `get_agentic_plan` | Expose the Agentic AI supervisor plan for observability clie |
| POST | `/api/feedback` | `backend\main.py` | `feedback` |  |

## Backend Entry Points

- `agentic_ai\app.py` (has `__main__` block)
- `backend\main.py`

---

# 8. Database Analysis

### Data Files

- `data\catalog.json`: list with 12 items
- `data\interactions.json`: list with 11 items

### Database References Found

- `agentic_ai\tools.py`: MongoDB reference found
- `scripts\repo_audit.py`: MongoDB reference found
- `scripts\repo_audit.py`: SQL database reference found
- `scripts\repo_audit.py`: Redis/Celery reference found

---

# 9. AI / ML / Recommendation Analysis

### Agentic AI Module

#### `agentic_ai\agent.py`

**Functions:** extract_mission, fallback_mission_parser, supervisor, profile_node, recommendation_node, ranking_node, discovery_ranking, bundle_node, explanation_node, quality_node, replan, quality_router, final_response, build_agent, run_agent, discovery_score

#### `agentic_ai\app.py`

**Classes:** RecommendationRequest
**Functions:** health_check, recommend

#### `agentic_ai\gemini_agent.py`

**Classes:** ShoppingMission
**Functions:** get_gemini_client, understand_shopping_request

#### `agentic_ai\state.py`

**Classes:** RetailState

#### `agentic_ai\tools.py`

**Functions:** get_customer_profile, search_products, get_recommendations, rank_products, create_bundle, explain_recommendation, quality_check

### AI/ML Libraries Detected

| File | Library | Classification | Key Functions | Key Classes |
|------|---------|----------------|---------------|-------------|
| `agentic_ai\agent.py` | Gemini | recommendation/ranking | extract_mission, fallback_mission_parser, supervisor, profile_node, recommendation_node, ranking_node, discovery_ranking, bundle_node, explanation_node, quality_node | N/A |
| `agentic_ai\config.py` | Gemini | recommendation/ranking | N/A | N/A |
| `agentic_ai\gemini_agent.py` | Gemini | recommendation/ranking | get_gemini_client, understand_shopping_request | ShoppingMission |
| `backend\service.py` | Gemini | recommendation/ranking | _as_dict, _to_datetime, _json_safe, customer_profile_from_events, decide_next_action, agentic_plan, default_products, recommendation_engine, mission_from_query, profile_from_digital_twin | N/A |
| `backend\service.py` | NumPy | recommendation/ranking | _as_dict, _to_datetime, _json_safe, customer_profile_from_events, decide_next_action, agentic_plan, default_products, recommendation_engine, mission_from_query, profile_from_digital_twin | N/A |
| `backend\service.py` | Pandas | recommendation/ranking | _as_dict, _to_datetime, _json_safe, customer_profile_from_events, decide_next_action, agentic_plan, default_products, recommendation_engine, mission_from_query, profile_from_digital_twin | N/A |
| `customer_intelligence\affinity.py` | NumPy | recommendation/ranking | load_item_category_history, enrich_events_with_category, compute_historical_affinity, compute_recent_affinity | N/A |
| `customer_intelligence\affinity.py` | Pandas | recommendation/ranking | load_item_category_history, enrich_events_with_category, compute_historical_affinity, compute_recent_affinity | N/A |
| `customer_intelligence\features.py` | NumPy | unknown | load_events, build_customer_event_features, build_categorized_interaction_count | N/A |
| `customer_intelligence\features.py` | Pandas | unknown | load_events, build_customer_event_features, build_categorized_interaction_count | N/A |
| `customer_intelligence\profile.py` | NumPy | recommendation/ranking | build_profile_base, assign_primary_persona, add_behavioural_attributes, add_top_historical_categories, add_top_recent_categories, build_digital_twin, get_customer_profile, assign_evidence_level, assign_evidence_tier, persona | N/A |
| `customer_intelligence\profile.py` | Pandas | recommendation/ranking | build_profile_base, assign_primary_persona, add_behavioural_attributes, add_top_historical_categories, add_top_recent_categories, build_digital_twin, get_customer_profile, assign_evidence_level, assign_evidence_tier, persona | N/A |
| `intent\gemini_parser.py` | Gemini | trained ML | __init__, parse | GeminiIntentParser |
| `intent\intent_agent.py` | Gemini | LLM/agent-based | __init__, analyze | IntentAgent |
| `recommendation_ml\engine.py` | NumPy | recommendation/ranking | __init__, fit, _get_candidate_ids, _build_candidate_df, _generate_evidence, recommend, rerank_candidates, get_popular_products, get_content_scores, get_collaborative_scores | RecommendationEngine |
| `recommendation_ml\engine.py` | Pandas | recommendation/ranking | __init__, fit, _get_candidate_ids, _build_candidate_df, _generate_evidence, recommend, rerank_candidates, get_popular_products, get_content_scores, get_collaborative_scores | RecommendationEngine |
| `scripts\repo_audit.py` | Gemini | recommendation/ranking | safe_print, run, safe_read, is_ignored, count_lines, git_info, section_overview, section_tree, section_components, section_important_files | N/A |
| `scripts\repo_audit.py` | OpenAI | recommendation/ranking | safe_print, run, safe_read, is_ignored, count_lines, git_info, section_overview, section_tree, section_components, section_important_files | N/A |
| `scripts\repo_audit.py` | LangChain | recommendation/ranking | safe_print, run, safe_read, is_ignored, count_lines, git_info, section_overview, section_tree, section_components, section_important_files | N/A |
| `scripts\repo_audit.py` | scikit-learn | recommendation/ranking | safe_print, run, safe_read, is_ignored, count_lines, git_info, section_overview, section_tree, section_components, section_important_files | N/A |
| `scripts\repo_audit.py` | TensorFlow | recommendation/ranking | safe_print, run, safe_read, is_ignored, count_lines, git_info, section_overview, section_tree, section_components, section_important_files | N/A |
| `scripts\repo_audit.py` | PyTorch | recommendation/ranking | safe_print, run, safe_read, is_ignored, count_lines, git_info, section_overview, section_tree, section_components, section_important_files | N/A |
| `scripts\repo_audit.py` | NumPy | recommendation/ranking | safe_print, run, safe_read, is_ignored, count_lines, git_info, section_overview, section_tree, section_components, section_important_files | N/A |
| `scripts\repo_audit.py` | Pandas | recommendation/ranking | safe_print, run, safe_read, is_ignored, count_lines, git_info, section_overview, section_tree, section_components, section_important_files | N/A |
| `recommendation_ml\data\loader.py` | NumPy | recommendation/ranking | normalize_columns, normalize_id, parse_timestamps, compute_event_strength, load_interactions, load_products, build_user_item_matrix, build_product_metadata_index, time_aware_split | N/A |
| `recommendation_ml\data\loader.py` | Pandas | recommendation/ranking | normalize_columns, normalize_id, parse_timestamps, compute_event_strength, load_interactions, load_products, build_user_item_matrix, build_product_metadata_index, time_aware_split | N/A |
| `recommendation_ml\data\synthetic.py` | NumPy | trained ML | _generate_products, _generate_customer_profile, generate_interactions, generate_test_scenario | N/A |
| `recommendation_ml\data\synthetic.py` | Pandas | trained ML | _generate_products, _generate_customer_profile, generate_interactions, generate_test_scenario | N/A |
| `recommendation_ml\evaluation\metrics.py` | NumPy | recommendation/ranking | precision_at_k, recall_at_k, hit_rate_at_k, ndcg_at_k, catalog_coverage, intra_list_diversity, evaluate_model, compare_models | N/A |
| `recommendation_ml\evaluation\metrics.py` | Pandas | recommendation/ranking | precision_at_k, recall_at_k, hit_rate_at_k, ndcg_at_k, catalog_coverage, intra_list_diversity, evaluate_model, compare_models | N/A |
| `recommendation_ml\models\collaborative.py` | NumPy | recommendation/ranking | __init__, fit, _fit_als, _predict_user_item, get_collaborative_scores, get_user_similar_items, is_fitted, n_users, n_items | CollaborativeModel |
| `recommendation_ml\models\collaborative.py` | Pandas | recommendation/ranking | __init__, fit, _fit_als, _predict_user_item, get_collaborative_scores, get_user_similar_items, is_fitted, n_users, n_items | CollaborativeModel |
| `recommendation_ml\models\content.py` | scikit-learn | recommendation/ranking | _build_product_text, __init__, fit, _get_product_index, get_product_vector, build_customer_preference_vector, get_content_scores, score_for_customer, is_fitted, vocabulary_size | ContentModel |
| `recommendation_ml\models\content.py` | NumPy | recommendation/ranking | _build_product_text, __init__, fit, _get_product_index, get_product_vector, build_customer_preference_vector, get_content_scores, score_for_customer, is_fitted, vocabulary_size | ContentModel |
| `recommendation_ml\models\content.py` | Pandas | recommendation/ranking | _build_product_text, __init__, fit, _get_product_index, get_product_vector, build_customer_preference_vector, get_content_scores, score_for_customer, is_fitted, vocabulary_size | ContentModel |
| `recommendation_ml\models\hybrid.py` | NumPy | recommendation/ranking | normalize_scores, compute_budget_score, compute_intent_score, compute_preference_score, compute_session_score, hybrid_score_product, hybrid_score_candidates | N/A |
| `recommendation_ml\models\popularity.py` | NumPy | recommendation/ranking | __init__, fit, get_popular_products, recommend_popularity, get_score, get_scores, is_fitted | PopularityModel |
| `recommendation_ml\models\popularity.py` | Pandas | recommendation/ranking | __init__, fit, get_popular_products, recommend_popularity, get_score, get_scores, is_fitted | PopularityModel |
| `recommendation_ml\ranking\constraints.py` | Pandas | recommendation/ranking | filter_by_budget, filter_by_excluded_brands, filter_by_excluded_categories, filter_by_rating, apply_constraints | N/A |
| `recommendation_ml\ranking\discovery.py` | NumPy | recommendation/ranking | compute_novelty_score, compute_discovery_score, boost_discovery_candidates, get_discovery_candidates | N/A |
| `recommendation_ml\ranking\diversity.py` | NumPy | recommendation/ranking | category_diversity_score, brand_diversity_score, mmr_diversify, diversify_recommendations | N/A |
| `recommendation_ml\ranking\diversity.py` | Pandas | recommendation/ranking | category_diversity_score, brand_diversity_score, mmr_diversify, diversify_recommendations | N/A |
| `recommendation_ml\tests\test_integration_audit.py` | Pandas | recommendation/ranking | N/A | N/A |
| `recommendation_ml\tests\test_recommendation.py` | NumPy | recommendation/ranking | sample_products, sample_interactions, sample_mission, sample_profile, engine, test_mission_from_dict, test_mission_to_dict, test_customer_profile_from_dict, test_score_breakdown_to_dict, test_recommendation_to_dict | TestSchemas, TestDataLoading, TestSyntheticData, TestPopularityModel, TestContentModel |
| `recommendation_ml\tests\test_recommendation.py` | Pandas | recommendation/ranking | sample_products, sample_interactions, sample_mission, sample_profile, engine, test_mission_from_dict, test_mission_to_dict, test_customer_profile_from_dict, test_score_breakdown_to_dict, test_recommendation_to_dict | TestSchemas, TestDataLoading, TestSyntheticData, TestPopularityModel, TestContentModel |
| `product_intelligence\test\test.py` | Pandas | recommendation/ranking | create_test_catalog, test_condition_creation, test_recommendation_generation, test_category_filtering, test_score_contributions, test_ranking_order, test_strict_budget, test_explanation | N/A |
| `product_intelligence\src\product_intelligence\filtering.py` | Pandas | trained ML | filter_products | N/A |
| `product_intelligence\src\product_intelligence\ranking.py` | Pandas | recommendation/ranking | rank_products | N/A |
| `product_intelligence\src\product_intelligence\recommender.py` | Pandas | recommendation/ranking | __init__, recommend, explain | ProductIntelligence |
| `product_intelligence\src\product_intelligence\scoring.py` | scikit-learn | recommendation/ranking | minmax_normalize, calculate_budget_fit, calculate_category_match, calculate_semantic_scores, select_weights, calculate_component_scores, calculate_final_score | N/A |
| `product_intelligence\src\product_intelligence\scoring.py` | NumPy | recommendation/ranking | minmax_normalize, calculate_budget_fit, calculate_category_match, calculate_semantic_scores, select_weights, calculate_component_scores, calculate_final_score | N/A |
| `product_intelligence\src\product_intelligence\scoring.py` | Pandas | recommendation/ranking | minmax_normalize, calculate_budget_fit, calculate_category_match, calculate_semantic_scores, select_weights, calculate_component_scores, calculate_final_score | N/A |

### Recommendation ML Module

#### `recommendation_ml\config.py`

**Classes:** EventWeights, HybridWeights, RecommendationConfig
**Functions:** get, normalize

#### `recommendation_ml\data\loader.py`

**Functions:** normalize_columns, normalize_id, parse_timestamps, compute_event_strength, load_interactions, load_products, build_user_item_matrix, build_product_metadata_index, time_aware_split

#### `recommendation_ml\data\synthetic.py`

**Functions:** _generate_products, _generate_customer_profile, generate_interactions, generate_test_scenario

#### `recommendation_ml\engine.py`

**Classes:** RecommendationEngine
**Functions:** __init__, fit, _get_candidate_ids, _build_candidate_df, _generate_evidence, recommend, rerank_candidates, get_popular_products, get_content_scores, get_collaborative_scores, is_fitted, model_version

#### `recommendation_ml\evaluation\metrics.py`

**Functions:** precision_at_k, recall_at_k, hit_rate_at_k, ndcg_at_k, catalog_coverage, intra_list_diversity, evaluate_model, compare_models

#### `recommendation_ml\models\collaborative.py`

**Classes:** CollaborativeModel
**Functions:** __init__, fit, _fit_als, _predict_user_item, get_collaborative_scores, get_user_similar_items, is_fitted, n_users, n_items

#### `recommendation_ml\models\content.py`

**Classes:** ContentModel
**Functions:** _build_product_text, __init__, fit, _get_product_index, get_product_vector, build_customer_preference_vector, get_content_scores, score_for_customer, is_fitted, vocabulary_size

#### `recommendation_ml\models\hybrid.py`

**Functions:** normalize_scores, compute_budget_score, compute_intent_score, compute_preference_score, compute_session_score, hybrid_score_product, hybrid_score_candidates

#### `recommendation_ml\models\popularity.py`

**Classes:** PopularityModel
**Functions:** __init__, fit, get_popular_products, recommend_popularity, get_score, get_scores, is_fitted

#### `recommendation_ml\ranking\constraints.py`

**Functions:** filter_by_budget, filter_by_excluded_brands, filter_by_excluded_categories, filter_by_rating, apply_constraints

#### `recommendation_ml\ranking\discovery.py`

**Functions:** compute_novelty_score, compute_discovery_score, boost_discovery_candidates, get_discovery_candidates

#### `recommendation_ml\ranking\diversity.py`

**Functions:** category_diversity_score, brand_diversity_score, mmr_diversify, diversify_recommendations

#### `recommendation_ml\schemas.py`

**Classes:** Mission, CustomerProfile, ScoreBreakdown, Recommendation, RecommendationResult, Product, Interaction
**Functions:** to_dict, from_dict, to_dict, from_dict, to_dict, to_dict, to_dict, to_dict, from_dict, to_dict

#### `recommendation_ml\tests\test_recommendation.py`

**Classes:** TestSchemas, TestDataLoading, TestSyntheticData, TestPopularityModel, TestContentModel, TestCollaborativeModel, TestHybridScoring, TestConstraints, TestDiversity, TestDiscovery, TestEvaluation, TestColdStart, TestRecommendationEngine, TestEndToEnd
**Functions:** sample_products, sample_interactions, sample_mission, sample_profile, engine, test_mission_from_dict, test_mission_to_dict, test_customer_profile_from_dict, test_score_breakdown_to_dict, test_recommendation_to_dict, test_recommendation_result_to_dict, test_normalize_columns, test_normalize_id_numeric, test_normalize_id_string, test_normalize_id_nan, test_load_interactions_from_dataframe, test_load_products_from_dataframe, test_build_user_item_matrix, test_build_product_metadata_index, test_time_aware_split, test_generate_interactions, test_generate_test_scenario, test_fit_and_get_popular, test_empty_fit, test_get_score, test_recommend_popularity_excludes, test_fit, test_get_product_vector, test_get_content_scores, test_build_customer_preference_vector, test_empty_candidates, test_fit, test_get_collaborative_scores, test_cold_start_user, test_empty_fit, test_normalize_scores, test_normalize_empty, test_normalize_equal, test_budget_score, test_intent_score, test_preference_score, test_preference_score_no_profile, test_session_score, test_filter_by_budget, test_filter_by_excluded_brands, test_filter_by_excluded_categories, test_apply_all_constraints, test_empty_candidates, test_category_diversity_new, test_category_diversity_repeat, test_brand_diversity, test_diversify_recommendations, test_novelty_score_new, test_novelty_score_seen, test_discovery_score, test_discovery_score_zero_level, test_boost_discovery_candidates, test_precision_at_k, test_recall_at_k, test_hit_rate, test_ndcg, test_ndcg_empty, test_catalog_coverage, test_intra_list_diversity, test_evaluate_model, test_compare_models, test_unknown_user_returns_results, test_new_user_with_profile, test_fit, test_recommend_basic, test_recommend_has_scores, test_recommend_with_candidates, test_recommend_with_budget_constraint, test_recommend_with_brand_exclusion, test_recommend_empty_candidates, test_rerank_candidates, test_get_popular_products, test_get_content_scores, test_get_collaborative_scores, test_full_pipeline, test_whatif_pipeline, test_diversity_pipeline

### Product Intelligence Module

#### `product_intelligence\src\product_intelligence\condition.py`

**Classes:** Condition
**Functions:** __post_init__

#### `product_intelligence\src\product_intelligence\filtering.py`

**Functions:** filter_products

#### `product_intelligence\src\product_intelligence\optimization\bundle.py`

**Functions:** generate_bundles, filter_bundles_by_budget, calculate_bundle_score

#### `product_intelligence\src\product_intelligence\optimization\constraints.py`

**Functions:** filter_by_budget, filter_excluded_brands

#### `product_intelligence\src\product_intelligence\optimization\optimizer.py`

**Functions:** optimize_products

#### `product_intelligence\src\product_intelligence\ranking.py`

**Functions:** rank_products

#### `product_intelligence\src\product_intelligence\recommender.py`

**Classes:** ProductIntelligence
**Functions:** __init__, recommend, explain

#### `product_intelligence\src\product_intelligence\scoring.py`

**Functions:** minmax_normalize, calculate_budget_fit, calculate_category_match, calculate_semantic_scores, select_weights, calculate_component_scores, calculate_final_score

#### `product_intelligence\test\test.py`

**Functions:** create_test_catalog, test_condition_creation, test_recommendation_generation, test_category_filtering, test_score_contributions, test_ranking_order, test_strict_budget, test_explanation

---

# 10. Dependency Analysis

### `requirements.txt` (4 deps)

- `numpy>=1.24.0`
- `pandas>=2.0.0`
- `scikit-learn>=1.3.0`
- `scipy>=1.10.0`

### `requirements-backend.txt` (7 deps)

- `-r requirements.txt`
- `fastapi>=0.110.0`
- `uvicorn[standard]>=0.27.0`
- `python-dotenv>=1.0.0`
- `pydantic>=2.0.0`
- `langgraph>=0.2.0`
- `google-genai>=1.0.0`

### `product_intelligence/requirement.txt` (3 deps)

- `numpy>=1.26`
- `pandas>=2.0`
- `scikit-learn>=1.4`

---

# 11. Environment Variables

| Variable | Source |
|----------|--------|
| `CORS_ORIGINS` | Referenced in source |
| `DEFAULT_BUDGET` | Referenced in source |
| `DISCOVERY_THRESHOLD` | Referenced in source |
| `GEMINI_API_KEY` | Referenced in source |
| `GEMINI_MODEL` | Referenced in source |
| `MAX_RECOMMENDATIONS` | Referenced in source |
| `VITE_API_BASE_URL` | Referenced in source |

---

# 12. Security Audit

| File | Issue |
|------|-------|
| - `agentic_ai\agent.py` -- merge conflict markers |
| - `agentic_ai\gemini_agent.py` -- merge conflict markers |
| - `agentic_ai\tools.py` -- merge conflict markers |

---

# 13. Tests

**Test files found:** 5

| File | Framework |
|------|-----------|
| `intent\test_intent.py` | unknown |
| `product_intelligence\test\test.py` | unknown |
| `recommendation_ml\tests\test_integration_audit.py` | unknown |
| `recommendation_ml\tests\test_recommendation.py` | pytest |
| `scripts\smoke_test.py` | unknown |

**Test directories:**

- `product_intelligence\test/`
- `recommendation_ml\tests/`

---

# 14. Build Checks

_Skipped (run with `--run-checks` to enable)._
---

# 15. Conflict / Git Audit

**Branch:** `main`
**Ahead of remote:** 0
**Behind remote:** 0

### Working Tree Status

```
?? reports/
?? scripts/repo_audit.py
```

### Merge Conflicts

- `agentic_ai\agent.py`
- `agentic_ai\gemini_agent.py`
- `agentic_ai\tools.py`

---

# 16. Architecture / Dependency Graph

### High-Level Architecture

```text
Module Dependency Graph:

  backend
    v
  agentic_ai

  backend
    v
  customer_intelligence

  backend
    v
  intent

  backend
    v
  product_intelligence

  backend
    v
  recommendation_ml

  recommendation_ml
    v
  data

  scripts
    v
  backend


React frontend
  ├─ POST /api/recommendations
  └─ POST /api/feedback
          │
          ▼
FastAPI backend
  ├─ Agentic AI: supervisor workflow and decision trace
  ├─ Intent: query → structured mission and constraints
  ├─ Customer Intelligence: events → customer digital twin
  ├─ Recommendation ML: hybrid candidate ranking
  ├─ Product Intelligence: condition-aware filtering/scoring
  └─ Bundle Optimizer: affordable multi-product bundle
```

### Module Descriptions

- **agentic_ai**: The `agentic_ai` module is the Agentic AI orchestration layer of RetailMind.
- **backend**: The FastAPI application exposes the single integration path used by the
- **backend_package**: This package makes the repository's existing modules work together:
- **customer_intelligence**: (no README)
- **data**: (no README)
- **frontend**: (no README)
- **intent**: (no README)
- **postman**: (no README)
- **product_intelligence**: An interpretable, condition-aware product recommendation engine built using the RetailRocket dataset.
- **recommendation_ml**: Hybrid recommendation engine for the RetailMind hackathon project. Combines collaborative filtering, content-based simil
- **reports**: (no README)
- **scripts**: (no README)

---

# 17. Potential Problems

## HIGH

- HIGH: Security -- merge conflict markers
- HIGH: Security -- merge conflict markers
- HIGH: Security -- merge conflict markers

## MEDIUM

- MEDIUM: TODO/FIXME in ``agentic_ai\agent.py`
- MEDIUM: TODO/FIXME in ``agentic_ai\agent.py`
- MEDIUM: TODO/FIXME in ``agentic_ai\gemini_agent.py`
- MEDIUM: TODO/FIXME in ``agentic_ai\gemini_agent.py`
- MEDIUM: TODO/FIXME in ``agentic_ai\gemini_agent.py`
- MEDIUM: TODO/FIXME in ``agentic_ai\gemini_agent.py`
- MEDIUM: TODO/FIXME in ``agentic_ai\gemini_agent.py`
- MEDIUM: TODO/FIXME in ``agentic_ai\gemini_agent.py`
- MEDIUM: TODO/FIXME in ``agentic_ai\gemini_agent.py`
- MEDIUM: TODO/FIXME in ``agentic_ai\gemini_agent.py`

## LOW

- LOW: Missing `__init__.py` in `agentic_ai/`
- LOW: Missing `__init__.py` in `scripts/`
- LOW: Missing `__init__.py` in `product_intelligence/`

## INFO

- INFO: Frontend env references port 8000 (FastAPI default)

---

# 18. Project Abstract

### Project Name
**RetailMind — Personalised Retail Agent**

### Problem

_Personalised retail shopping recommendations that are explainable and context-aware._

### Solution

_A full-stack system combining AI agents, intent parsing, customer intelligence, ML recommendations, and product intelligence through a FastAPI backend with a React frontend._

### Target Users

_Retail customers seeking personalised product recommendations._

### Main Features

_Intent-based query parsing, customer profiling, hybrid recommendation engine, bundle optimization, explainable AI agent workflow._

### Architecture

```
React Frontend -> FastAPI Backend -> Agentic AI -> Intent / Customer / Recommendation / Product Intelligence
```

### Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React, Vite |
| Backend | Python, FastAPI |
| AI/Agent | Google Gemini (LLM-based) |
| ML | Custom hybrid recommendation engine |
| Data | JSON files (in-memory) |

### Current Implementation Status

_Based on file presence and code analysis, all major modules are present with source code._

### Known Issues

_See Section 17: Potential Problems._

---

============================================================
AI PROJECT HANDOFF SUMMARY
============================================================

## Project Purpose
RetailMind is a full-stack, explainable shopping-recommendation system for personalised retail.
It connects multiple AI/ML modules through a FastAPI backend and a React frontend.

## Repository Info
- **Path:** `D:\sem_7\cog_hackathon\Personalised_Retail_Agent`
- **Branch:** `main`
- **Commit:** `a60e1c8`
- **Remote:** `https://github.com/gowrichandana24/Personalised_Retail_Agent.git`
- **Files:** 86
- **Folders:** 27
- **Total LOC (approx):** 12,370

## Architecture
```
React Frontend (Vite)
  | HTTP API
FastAPI Backend (backend/main.py)
  | Agentic AI (agentic_ai/) -- supervisor workflow + decision trace
  | Intent (intent/) -- query -> structured mission and constraints
  | Customer Intelligence (customer_intelligence/) -- events -> customer digital twin
  | Recommendation ML (recommendation_ml/) -- hybrid candidate ranking
  | Product Intelligence (product_intelligence/) -- condition-aware filtering/scoring
  +-- Bundle Optimizer
Data: data/catalog.json + data/interactions.json (in-memory)
```

## Repository Structure

- `agentic_ai/ (6 .py)`
- `backend/ (3 .py)`
- `backend_package/`
- `customer_intelligence/ (4 .py)`
- `data/`
- `frontend/ (269 .js/.jsx)`
- `intent/ (7 .py)`
- `postman/`
- `product_intelligence/ (12 .py)`
- `recommendation_ml/ (21 .py)`
- `reports/`
- `scripts/ (2 .py)`

## Important Files

- `backend/main.py` -- FastAPI application entry point [present]
- `backend/service.py` -- Core backend service logic [present]
- `intent/intent_agent.py` -- Intent parsing agent [present]
- `intent/gemini_parser.py` -- Gemini-based intent parser [present]
- `intent/fallback_parser.py` -- Rule-based fallback parser [present]
- `intent/schemas.py` -- Intent data schemas [present]
- `intent/prompts.py` -- LLM prompt templates [present]
- `customer_intelligence/profile.py` -- Customer digital twin builder [present]
- `customer_intelligence/features.py` -- Customer feature extraction [present]
- `customer_intelligence/affinity.py` -- Customer affinity scoring [present]
- `recommendation_ml/engine.py` -- Main recommendation engine [present]
- `recommendation_ml/schemas.py` -- Recommendation data schemas [present]
- `recommendation_ml/config.py` -- Recommendation configuration [present]
- `recommendation_ml/models/collaborative.py` -- Collaborative filtering [present]
- `recommendation_ml/models/content.py` -- Content-based filtering [present]
- `recommendation_ml/models/hybrid.py` -- Hybrid model [present]
- `recommendation_ml/models/popularity.py` -- Popularity-based model [present]
- `recommendation_ml/ranking/discovery.py` -- Discovery ranking [present]
- `recommendation_ml/ranking/diversity.py` -- Diversity ranking [present]
- `recommendation_ml/ranking/constraints.py` -- Ranking constraints [present]
- `product_intelligence/src/product_intelligence/recommender.py` -- Product recommender [present]
- `product_intelligence/src/product_intelligence/scoring.py` -- Product scoring [present]
- `product_intelligence/src/product_intelligence/filtering.py` -- Product filtering [present]
- `product_intelligence/src/product_intelligence/ranking.py` -- Product ranking [present]
- `product_intelligence/src/product_intelligence/condition.py` -- Condition-aware logic [present]
- `product_intelligence/src/product_intelligence/optimization/optimizer.py` -- Bundle optimizer [present]
- `product_intelligence/src/product_intelligence/optimization/bundle.py` -- Bundle logic [present]
- `product_intelligence/src/product_intelligence/optimization/constraints.py` -- Optimization constraints [present]
- `agentic_ai/app.py` -- Agentic AI application [present]
- `agentic_ai/agent.py` -- Agent logic [present]
- `agentic_ai/gemini_agent.py` -- Gemini-powered agent [present]
- `agentic_ai/tools.py` -- Agent tools [present]
- `agentic_ai/state.py` -- Agent state management [present]
- `agentic_ai/config.py` -- Agent configuration [present]
- `frontend/src/main.jsx` -- Frontend entry point [present]
- `frontend/package.json` -- Frontend dependencies [present]
- `frontend/.env.example` -- Environment variable template [present]
- `requirements.txt` -- Root Python dependencies [present]
- `requirements-backend.txt` -- Backend Python dependencies [present]
- `data/catalog.json` -- Product catalog data [present]
- `data/interactions.json` -- Interaction history data [present]
- `scripts/smoke_test.py` -- Smoke test script [present]
- `scripts/run_backend.ps1` -- Backend startup script [present]
- `scripts/run_frontend.ps1` -- Frontend startup script [present]

## Major Classes/Functions

### `agentic_ai\agent.py`
  Functions: extract_mission, fallback_mission_parser, supervisor, profile_node, recommendation_node, ranking_node, discovery_ranking, bundle_node, explanation_node, quality_node, replan, quality_router, final_response, build_agent, run_agent, discovery_score

### `agentic_ai\app.py`
  Classes: RecommendationRequest
  Functions: health_check, recommend

### `agentic_ai\gemini_agent.py`
  Classes: ShoppingMission
  Functions: get_gemini_client, understand_shopping_request

### `agentic_ai\state.py`
  Classes: RetailState

### `agentic_ai\tools.py`
  Functions: get_customer_profile, search_products, get_recommendations, rank_products, create_bundle, explain_recommendation, quality_check

### `backend\main.py`
  Classes: RecommendationRequest, FeedbackRequest, CustomerProfileRequest, AgenticPlanRequest
  Functions: health, modules, catalog, get_recommendations, build_customer_profile, get_agentic_plan, feedback

### `backend\service.py`
  Functions: customer_profile_from_events, decide_next_action, agentic_plan, default_products, recommendation_engine, mission_from_query, profile_from_digital_twin, recommend, record_feedback

### `customer_intelligence\affinity.py`
  Functions: load_item_category_history, enrich_events_with_category, compute_historical_affinity, compute_recent_affinity

### `customer_intelligence\features.py`
  Functions: load_events, build_customer_event_features, build_categorized_interaction_count

### `customer_intelligence\profile.py`
  Functions: build_profile_base, assign_primary_persona, add_behavioural_attributes, add_top_historical_categories, add_top_recent_categories, build_digital_twin, get_customer_profile, assign_evidence_level, assign_evidence_tier, persona

### `demo_recommendation.py`
  Functions: main

### `intent\fallback_parser.py`
  Classes: FallbackIntentParser
  Functions: parse

### `intent\gemini_parser.py`
  Classes: GeminiIntentParser
  Functions: parse

### `intent\intent_agent.py`
  Classes: IntentAgent
  Functions: analyze

### `intent\schemas.py`
  Classes: ShoppingIntent

### `product_intelligence\src\product_intelligence\condition.py`
  Classes: Condition

### `product_intelligence\src\product_intelligence\filtering.py`
  Functions: filter_products

### `product_intelligence\src\product_intelligence\optimization\bundle.py`
  Functions: generate_bundles, filter_bundles_by_budget, calculate_bundle_score

### `product_intelligence\src\product_intelligence\optimization\constraints.py`
  Functions: filter_by_budget, filter_excluded_brands

### `product_intelligence\src\product_intelligence\optimization\optimizer.py`
  Functions: optimize_products

### `product_intelligence\src\product_intelligence\ranking.py`
  Functions: rank_products

### `product_intelligence\src\product_intelligence\recommender.py`
  Classes: ProductIntelligence
  Functions: recommend, explain

### `product_intelligence\src\product_intelligence\scoring.py`
  Functions: minmax_normalize, calculate_budget_fit, calculate_category_match, calculate_semantic_scores, select_weights, calculate_component_scores, calculate_final_score

### `product_intelligence\test\test.py`
  Functions: create_test_catalog, test_condition_creation, test_recommendation_generation, test_category_filtering, test_score_contributions, test_ranking_order, test_strict_budget, test_explanation

### `recommendation_ml\config.py`
  Classes: EventWeights, HybridWeights, RecommendationConfig
  Functions: get, normalize

### `recommendation_ml\data\loader.py`
  Functions: normalize_columns, normalize_id, parse_timestamps, compute_event_strength, load_interactions, load_products, build_user_item_matrix, build_product_metadata_index, time_aware_split

### `recommendation_ml\data\synthetic.py`
  Functions: generate_interactions, generate_test_scenario

### `recommendation_ml\engine.py`
  Classes: RecommendationEngine
  Functions: fit, recommend, rerank_candidates, get_popular_products, get_content_scores, get_collaborative_scores, is_fitted, model_version

### `recommendation_ml\evaluation\metrics.py`
  Functions: precision_at_k, recall_at_k, hit_rate_at_k, ndcg_at_k, catalog_coverage, intra_list_diversity, evaluate_model, compare_models

### `recommendation_ml\models\collaborative.py`
  Classes: CollaborativeModel
  Functions: fit, get_collaborative_scores, get_user_similar_items, is_fitted, n_users, n_items

### `recommendation_ml\models\content.py`
  Classes: ContentModel
  Functions: fit, get_product_vector, build_customer_preference_vector, get_content_scores, score_for_customer, is_fitted, vocabulary_size

### `recommendation_ml\models\hybrid.py`
  Functions: normalize_scores, compute_budget_score, compute_intent_score, compute_preference_score, compute_session_score, hybrid_score_product, hybrid_score_candidates

### `recommendation_ml\models\popularity.py`
  Classes: PopularityModel
  Functions: fit, get_popular_products, recommend_popularity, get_score, get_scores, is_fitted

### `recommendation_ml\ranking\constraints.py`
  Functions: filter_by_budget, filter_by_excluded_brands, filter_by_excluded_categories, filter_by_rating, apply_constraints

### `recommendation_ml\ranking\discovery.py`
  Functions: compute_novelty_score, compute_discovery_score, boost_discovery_candidates, get_discovery_candidates

### `recommendation_ml\ranking\diversity.py`
  Functions: category_diversity_score, brand_diversity_score, mmr_diversify, diversify_recommendations

### `recommendation_ml\schemas.py`
  Classes: Mission, CustomerProfile, ScoreBreakdown, Recommendation, RecommendationResult, Product, Interaction
  Functions: to_dict, from_dict, to_dict, from_dict, to_dict, to_dict, to_dict, to_dict, from_dict, to_dict

### `recommendation_ml\tests\test_recommendation.py`
  Classes: TestSchemas, TestDataLoading, TestSyntheticData, TestPopularityModel, TestContentModel, TestCollaborativeModel, TestHybridScoring, TestConstraints, TestDiversity, TestDiscovery, TestEvaluation, TestColdStart, TestRecommendationEngine, TestEndToEnd
  Functions: sample_products, sample_interactions, sample_mission, sample_profile, engine, test_mission_from_dict, test_mission_to_dict, test_customer_profile_from_dict, test_score_breakdown_to_dict, test_recommendation_to_dict, test_recommendation_result_to_dict, test_normalize_columns, test_normalize_id_numeric, test_normalize_id_string, test_normalize_id_nan, test_load_interactions_from_dataframe, test_load_products_from_dataframe, test_build_user_item_matrix, test_build_product_metadata_index, test_time_aware_split, test_generate_interactions, test_generate_test_scenario, test_fit_and_get_popular, test_empty_fit, test_get_score, test_recommend_popularity_excludes, test_fit, test_get_product_vector, test_get_content_scores, test_build_customer_preference_vector, test_empty_candidates, test_fit, test_get_collaborative_scores, test_cold_start_user, test_empty_fit, test_normalize_scores, test_normalize_empty, test_normalize_equal, test_budget_score, test_intent_score, test_preference_score, test_preference_score_no_profile, test_session_score, test_filter_by_budget, test_filter_by_excluded_brands, test_filter_by_excluded_categories, test_apply_all_constraints, test_empty_candidates, test_category_diversity_new, test_category_diversity_repeat, test_brand_diversity, test_diversify_recommendations, test_novelty_score_new, test_novelty_score_seen, test_discovery_score, test_discovery_score_zero_level, test_boost_discovery_candidates, test_precision_at_k, test_recall_at_k, test_hit_rate, test_ndcg, test_ndcg_empty, test_catalog_coverage, test_intra_list_diversity, test_evaluate_model, test_compare_models, test_unknown_user_returns_results, test_new_user_with_profile, test_fit, test_recommend_basic, test_recommend_has_scores, test_recommend_with_candidates, test_recommend_with_budget_constraint, test_recommend_with_brand_exclusion, test_recommend_empty_candidates, test_rerank_candidates, test_get_popular_products, test_get_content_scores, test_get_collaborative_scores, test_full_pipeline, test_whatif_pipeline, test_diversity_pipeline

### `scripts\repo_audit.py`
  Functions: safe_print, run, safe_read, is_ignored, count_lines, git_info, section_overview, section_tree, section_components, section_important_files, section_python_analysis, section_frontend_analysis, section_backend_analysis, section_database_analysis, section_ai_analysis, section_dependency_analysis, section_env_vars, section_security, section_tests, section_build_checks, section_git_audit, section_architecture, section_problems, section_abstract, section_handoff, main

### `scripts\smoke_test.py`
  Functions: main

## API Endpoints

- GET `/`
- POST `/recommend`
- GET `/api/health`
- GET `/api/modules`
- GET `/api/catalog`
- POST `/api/recommendations`
- POST `/api/customer-profile`
- POST `/api/agentic-plan`
- POST `/api/feedback`

## Data Flow

```
1. User types query in React frontend
2. Frontend sends POST /api/recommendations
3. Backend invokes Agentic AI supervisor
4. Supervisor calls Intent module -> parses query into structured mission
5. Supervisor calls Customer Intelligence -> builds digital twin from events
6. Supervisor calls Recommendation ML -> hybrid candidate ranking
7. Supervisor calls Product Intelligence -> filtering/scoring/bundles
8. Backend returns combined response with explainability trace
9. Frontend renders recommendations with explanations
10. User feedback via POST /api/feedback updates re-ranking
```

## AI/ML Logic

- **Intent Parsing:** Gemini LLM with rule-based fallback parser
- **Customer Intelligence:** Event-driven digital twin with affinity scoring
- **Recommendation Engine:** Hybrid (collaborative + content + popularity + diversity)
- **Product Intelligence:** Condition-aware filtering, scoring, ranking, bundle optimization
- **Agentic AI:** Supervisor workflow with Gemini for decision traces

## Dependencies

### requirements.txt: numpy>=1.24.0, pandas>=2.0.0, scikit-learn>=1.3.0, scipy>=1.10.0
### requirements-backend.txt: -r requirements.txt, fastapi>=0.110.0, uvicorn[standard]>=0.27.0, python-dotenv>=1.0.0, pydantic>=2.0.0, langgraph>=0.2.0, google-genai>=1.0.0

### frontend/package.json
Dependencies: @vitejs/plugin-react, vite, typescript, react, react-dom
DevDependencies: 

## Environment Variables

- `CORS_ORIGINS`
- `DEFAULT_BUDGET`
- `DISCOVERY_THRESHOLD`
- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `MAX_RECOMMENDATIONS`
- `VITE_API_BASE_URL`

## Current Implementation Status

- All major modules have source code present
- Backend entry point (`backend/main.py`) exists
- Frontend has built distribution in `dist/`
- node_modules installed in frontend
- JSON data files present in `data/`
- Smoke test script available
- Postman collection available

## Known Problems

- **3 HIGH issues** -- should fix
- **10 MEDIUM issues** -- recommended to fix
- **3 LOW issues** -- optional improvements

## How to Run
```powershell
# Backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-backend.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install  # if not already done
npm run dev

# Smoke test
.\.venv\Scripts\python.exe scripts\smoke_test.py
```

---
