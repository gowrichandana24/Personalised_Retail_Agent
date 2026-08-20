from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Condition:
    """
    Structured shopping intent passed to
    the Product Intelligence engine.
    """

    category: Optional[str] = None

    budget: Optional[float] = None

    discovery_level: str = "medium"

    keywords: List[str] = field(
        default_factory=list
    )

    exclude_categories: List[str] = field(
        default_factory=list
    )

    strict_budget: bool = False

    def __post_init__(self):

        # Normalize category
        if self.category is not None:
            self.category = (
                self.category
                .strip()
                .lower()
            )

        # Normalize discovery level
        self.discovery_level = (
            self.discovery_level
            .strip()
            .lower()
        )

        valid_levels = {
            "low",
            "medium",
            "high"
        }

        if self.discovery_level not in valid_levels:
            raise ValueError(
                "discovery_level must be "
                "'low', 'medium', or 'high'"
            )

        # Normalize keywords
        self.keywords = [
            str(keyword).strip().lower()
            for keyword in self.keywords
            if str(keyword).strip()
        ]

        # Normalize exclusions
        self.exclude_categories = [
            str(category).strip().lower()
            for category
            in self.exclude_categories
            if str(category).strip()
        ]

        # Validate budget
        if self.budget is not None:

            if self.budget < 0:
                raise ValueError(
                    "budget cannot be negative"
                )

            self.budget = float(
                self.budget
            )