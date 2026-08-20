"""FastAPI entry point for the connected RetailMind application."""

from __future__ import annotations

import os
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.service import (
    agentic_plan,
    customer_profile_from_events,
    default_products,
    get_digital_twin_for_customer,
    record_feedback,
    recommend,
)


class RecommendationRequest(BaseModel):
    customer_id: str = "DEMO_USER"
    query: str = Field(min_length=1, max_length=1000)
    customer_profile: dict[str, Any] | None = None
    conversation_context: dict[str, Any] | None = None
    candidate_products: list[dict[str, Any]] | None = None
    top_k: int = Field(default=5, ge=1, le=20)
    budget: float | None = Field(default=None, gt=0)
    discovery_level: float | None = Field(default=None, ge=0, le=1)


class FeedbackRequest(BaseModel):
    customer_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    action: Literal["like", "save", "cart", "skip"]


class CustomerProfileRequest(BaseModel):
    customer_id: str = Field(min_length=1)
    events: list[dict[str, Any]] = Field(min_length=1)
    item_categories: list[dict[str, Any]] = Field(default_factory=list)


class AgenticPlanRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)


app = FastAPI(title="RetailMind API", version="1.1.0")
origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "retailmind-backend",
        "pipeline": [
            "agentic-ai",
            "intent",
            "customer-intelligence",
            "recommendation-ml",
            "product-intelligence",
            "bundle-optimizer",
            "frontend-feedback",
        ],
    }


@app.get("/api/modules")
def modules() -> dict[str, Any]:
    """Return the concrete module-to-backend integration map."""
    return {
        "agentic_ai": "Supervisor plans the auditable workflow.",
        "intent": "Turns the shopping query into structured constraints.",
        "customer_intelligence": "Builds a digital twin from events and categories.",
        "recommendation_ml": "Ranks candidates with hybrid ML signals.",
        "product_intelligence": "Filters, scores and bundles products transparently.",
        "frontend": "Calls recommendations and records feedback through this API.",
    }


@app.get("/api/catalog")
def catalog() -> dict[str, Any]:
    return {"products": default_products()}


@app.get("/api/customer/{customer_id}")
def get_customer_profile(customer_id: str) -> dict[str, Any]:
    """Return the digital twin for a customer from the shared interactions dataset."""
    try:
        return get_digital_twin_for_customer(customer_id)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Failed to load customer profile") from error


@app.post("/api/recommendations")
def get_recommendations(request: RecommendationRequest) -> dict[str, Any]:
    try:
        return recommend(
            customer_id=request.customer_id,
            query=request.query,
            digital_twin=request.customer_profile,
            conversation_context=request.conversation_context,
            candidate_products=request.candidate_products,
            top_k=request.top_k,
            budget=request.budget,
            discovery_level=request.discovery_level,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Recommendation request failed") from error


@app.post("/api/customer-profile")
def build_customer_profile(request: CustomerProfileRequest) -> dict[str, Any]:
    """Build a customer digital twin from raw events and category history."""
    try:
        return customer_profile_from_events(
            customer_id=request.customer_id,
            events=request.events,
            item_categories=request.item_categories,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/api/agentic-plan")
def get_agentic_plan(request: AgenticPlanRequest) -> dict[str, Any]:
    """Expose the Agentic AI supervisor plan for observability clients."""
    return agentic_plan(request.query)


@app.post("/api/feedback")
def feedback(request: FeedbackRequest) -> dict[str, Any]:
    return record_feedback(request.customer_id, request.product_id, request.action)
