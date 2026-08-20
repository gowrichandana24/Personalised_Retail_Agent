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
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-backend.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

The backend is then available at `http://127.0.0.1:8000`, with interactive
documentation at `http://127.0.0.1:8000/docs`.

In a second terminal, start the frontend:

```powershell
cd frontend
npm install
npm run dev
```

Vite serves the frontend on `http://127.0.0.1:5173` by default. It is already
included in the backend's CORS allow-list. To use a deployed API, copy
`frontend/.env.example` to `frontend/.env` and change `VITE_API_BASE_URL`.

## API

- `GET /api/health` — verifies the backend and returns the connected pipeline.
- `GET /api/modules` — identifies the role of every connected module.
- `GET /api/catalog` — returns the current product catalogue.
- `POST /api/agentic-plan` — returns the Agentic AI supervisor workflow.
- `POST /api/customer-profile` — turns events/category history into a digital twin.
- `POST /api/recommendations` — runs the full recommendation pipeline.
- `POST /api/feedback` — stores a session feedback signal used in subsequent
  rankings for the same customer.

Example recommendation request:

```json
{
  "customer_id": "42",
  "query": "I need casual shoes under ₹3000",
  "budget": 3000,
  "discovery_level": 0.4,
  "customer_profile": {
    "total_views": 12,
    "total_transactions": 2,
    "top_category_1": "footwear",
    "top_category_affinity_1": 0.9
  },
  "top_k": 5
}
```
