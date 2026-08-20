# RetailMind backend integration

This package makes the repository's existing modules work together:

`frontend -> FastAPI -> Intent Agent -> Customer Digital Twin adapter -> Recommendation ML -> ranked response`

## Install and run

Copy `backend/` and `requirements-backend.txt` into the repository root, then run:

```bash
pip install -r requirements-backend.txt
uvicorn backend.main:app --reload
```

The API is available at `http://127.0.0.1:8000`; interactive documentation is at `/docs`.

## Frontend request

```json
{
  "customer_id": "42",
  "query": "casual shoes under ₹3000",
  "customer_profile": {
    "total_views": 12,
    "total_transactions": 2,
    "top_category_1": "footwear",
    "top_category_affinity_1": 0.9
  },
  "top_k": 5
}
```

POST it to `/api/recommendations`. `candidate_products` is optional; when it is provided it must use `product_id`, `title`, `category`, `price`, and optional `brand`, `rating`, and `description` fields. Without it, the existing sample catalogue is used.

Set `CORS_ORIGINS` to a comma-separated list of your production frontend origins before deployment.
