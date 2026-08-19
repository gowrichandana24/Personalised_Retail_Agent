"""FastAPI entry point consumed by the web or mobile frontend."""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.service import recommend


class RecommendationRequest(BaseModel):
    customer_id: str = "DEMO_USER"
    query: str = Field(min_length=1, max_length=1000)
    customer_profile: dict[str, Any] | None = None
    candidate_products: list[dict[str, Any]] | None = None
    top_k: int = Field(default=5, ge=1, le=20)


app = FastAPI(title="RetailMind API", version="1.0.0")
origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "retailmind-backend"}


@app.post("/api/recommendations")
def get_recommendations(request: RecommendationRequest) -> dict[str, Any]:
    try:
        return recommend(
            customer_id=request.customer_id,
            query=request.query,
            digital_twin=request.customer_profile,
            candidate_products=request.candidate_products,
            top_k=request.top_k,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Recommendation request failed") from error
