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
  ├─ Agentic AI: supervisor workflow and decision trace
  ├─ Intent: query → structured mission and constraints
  ├─ Customer Intelligence: events → customer digital twin
  ├─ Recommendation ML: hybrid candidate ranking
  ├─ Product Intelligence: condition-aware filtering/scoring
  └─ Bundle Optimizer: affordable multi-product bundle
```

## Included modules

| Folder | Connected responsibility |
| --- | --- |
| `agentic_ai/` | Determines the auditable workflow plan. |
| `intent/` | Extracts goal, category, budget, exclusions and discovery needs. |
| `customer_intelligence/` | Builds a customer digital twin from interactions and category history. |
| `recommendation_ml/` | Hybrid personalised ranking and evidence. |
| `product_intelligence/` | Transparent filtering, product scoring and bundle optimization. |
| `backend/` | FastAPI integration layer and API contracts. |
| `frontend/` | React/Vite UI calling the live API. |

## Requirements

- Python 3.10+
- Node.js 20.19+ (or newer) for the Vite frontend

## Start the backend

From the repository root, in PowerShell:

```powershell
.\scripts\run_backend.ps1
```

Or run the commands manually:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-backend.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

To enable Gemini-powered intent understanding, copy
`agentic_ai/.env.example` to `agentic_ai/.env` and set `GEMINI_API_KEY`.
The backend reads that same credential for both the agentic and intent
integrations. Never commit the `.env` file. Without a key, the local intent
parser remains available as a deterministic fallback.

Open `http://127.0.0.1:8000/docs` to see and try the API.

## Start the frontend

Keep the backend running. In a second PowerShell terminal:

```powershell
.\scripts\run_frontend.ps1
```

The UI opens through the Vite URL shown in the terminal, normally
`http://127.0.0.1:5173`. It calls `http://127.0.0.1:8000` by default. For a
deployed backend, copy `frontend/.env.example` to `frontend/.env` and set
`VITE_API_BASE_URL`.

The live backend catalogue and seed interaction data are stored in
`data/catalog.json` and `data/interactions.json`. Replace these files with the
available catalogue/history contract for a deployment; the recommendation
engine will load them at startup rather than using product mappings in code.

## Validate every module

1. Import `postman/RetailMind.postman_collection.json` in Postman.
2. Send the requests in order. Health, module map, agentic plan, customer
   digital twin, end-to-end recommendations, and feedback should all return
   HTTP 200.
3. Run the local smoke test:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_test.py
```

The smoke test creates a customer digital twin, requests recommendations, and
records feedback in the same session.

## Main API routes

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Backend and module health. |
| GET | `/api/modules` | Explicit module integration map. |
| GET | `/api/catalog` | Current demo catalogue. |
| POST | `/api/agentic-plan` | Agentic supervisor trace. |
| POST | `/api/customer-profile` | Raw events and categories → digital twin. |
| POST | `/api/recommendations` | Full recommendation and bundle pipeline. |
| POST | `/api/feedback` | Like/save/cart/skip feedback for re-ranking. |

`backend_package/` is retained from the original repository for historical
reference. Use the root `backend/` folder and `requirements-backend.txt` to
run the connected application.

`POST /api/recommendations` accepts an optional `conversation_context` object.
Pass the previous response's `intent` value on follow-up turns so corrections
such as “actually, I want walking shoes” update the active mission without
losing its product category.
