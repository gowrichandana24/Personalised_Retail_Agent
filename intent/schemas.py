from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class ShoppingIntent(BaseModel):
    """Structured representation of a customer's shopping mission."""

    goal: str = Field(
        description="What the customer is trying to accomplish."
    )

    category: Optional[str] = Field(
        default=None,
        description="Main product category."
    )

    subcategory: Optional[str] = Field(
        default=None,
        description="Specific product type."
    )

    occasion: Optional[str] = Field(
        default=None,
        description="Context or occasion for the purchase."
    )

    budget: Optional[float] = Field(
        default=None,
        description="Maximum or approximate budget in INR."
    )

    preferences: List[str] = Field(
        default_factory=list,
        description="Things the customer wants."
    )

    exclusions: List[str] = Field(
        default_factory=list,
        description="Things the customer does not want."
    )

    urgency: Optional[Literal["low", "medium", "high"]] = Field(
        default=None,
        description="How urgently the customer needs the product."
    )

    discovery_level: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="How much novelty the customer wants."
    )

    confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Confidence in the extracted intent."
    )