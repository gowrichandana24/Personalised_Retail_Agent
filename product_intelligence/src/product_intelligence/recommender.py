import pandas as pd

from .condition import Condition
from .filtering import filter_products
from .scoring import (
    calculate_component_scores,
    calculate_final_score,
    select_weights
)
from .ranking import rank_products


class ProductIntelligence:
    """
    Main Product Intelligence engine.

    Pipeline:

        Condition
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
    """

    def __init__(
        self,
        product_catalog: pd.DataFrame
    ):

        if not isinstance(
            product_catalog,
            pd.DataFrame
        ):

            raise TypeError(
                "product_catalog must "
                "be a pandas DataFrame"
            )

        self.product_catalog = (
            product_catalog.copy()
        )

    def recommend(
        self,
        condition: Condition,
        top_k: int = 10
    ) -> pd.DataFrame:

        # --------------------------------------------
        # STEP 1: HARD FILTERING
        # --------------------------------------------

        eligible = filter_products(
            self.product_catalog,
            condition
        )

        if eligible.empty:

            return pd.DataFrame()

        # --------------------------------------------
        # STEP 2: COMPONENT SCORING
        # --------------------------------------------

        scored = (
            calculate_component_scores(
                eligible,
                condition
            )
        )

        # --------------------------------------------
        # STEP 3: DYNAMIC WEIGHTS
        # --------------------------------------------

        weights = select_weights(
            condition
        )

        # --------------------------------------------
        # STEP 4: TRANSPARENT SCORE
        # --------------------------------------------

        scored = calculate_final_score(
            scored,
            weights
        )

        # --------------------------------------------
        # STEP 5: RANKING
        # --------------------------------------------

        ranked = rank_products(
            scored,
            top_k
        )

        return ranked

    def explain(
        self,
        product: pd.Series,
        condition: Condition
    ) -> dict:
        """
        Generate an exact explanation based on
        score contributions.
        """

        weights = select_weights(
            condition
        )

        contributions = {

            "category_match": float(
                product[
                    "category_contribution"
                ]
            ),

            "budget_fit": float(
                product[
                    "budget_contribution"
                ]
            ),

            "semantic_fit": float(
                product[
                    "semantic_contribution"
                ]
            ),

            "quality": float(
                product[
                    "quality_contribution"
                ]
            ),

            "discovery": float(
                product[
                    "discovery_contribution"
                ]
            )
        }

        return {

            "item_id": str(
                product["itemid"]
            ),

            "final_score": float(
                product["final_score"]
            ),

            "components": {

                "category_match": float(
                    product[
                        "category_score"
                    ]
                ),

                "budget_fit": float(
                    product[
                        "budget_score"
                    ]
                ),

                "semantic_fit": float(
                    product[
                        "semantic_score"
                    ]
                ),

                "quality": float(
                    product[
                        "quality_score"
                    ]
                ),

                "discovery": float(
                    product[
                        "discovery_score"
                    ]
                )
            },

            "weights": weights,

            "contributions":
                contributions
        }