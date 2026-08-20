"""
RetailMind Agentic AI - API Entry Point

Member 4:
Provides a clean API interface for the Agentic AI module.

The frontend/backend team can send a shopping query to:
POST /recommend
"""

from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .agent import run_agent


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="RetailMind Agentic AI",
    description=(
        "Agentic AI orchestration layer for "
        "personalized retail recommendations."
    ),
    version="1.0.0",
)


# ============================================================
# REQUEST MODEL
# ============================================================

class RecommendationRequest(BaseModel):
    """
    Input received from the frontend/backend.
    """

    customer_id: str = "DEMO_USER"
    query: str


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/")
def health_check():
    """
    Check whether the Agentic AI API is running.
    """

    return {
        "status": "online",
        "service": "RetailMind Agentic AI",
        "version": "1.0.0",
    }


# ============================================================
# RECOMMENDATION ENDPOINT
# ============================================================

@app.post("/recommend")
def recommend(request: RecommendationRequest):
    """
    Run the Agentic AI workflow for a shopping request.
    """

    if not request.query.strip():
        raise HTTPException(
            status_code=400,
            detail="Shopping query cannot be empty."
        )

    try:

        result = run_agent(
            user_query=request.query,
            customer_id=request.customer_id
        )

        return {
            "customer_id": request.customer_id,
            "query": request.query,
            "mission": result.get(
                "mission",
                {}
            ),
            "recommendations": result.get(
                "ranked_products",
                []
            ),
            "bundle": result.get(
                "bundle",
                []
            ),
            "explanations": result.get(
                "explanations",
                {}
            ),
            "agent_trace": result.get(
                "agent_trace",
                []
            ),
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Agent execution failed: {str(error)}"
        )


# ============================================================
# LOCAL DEVELOPMENT
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )