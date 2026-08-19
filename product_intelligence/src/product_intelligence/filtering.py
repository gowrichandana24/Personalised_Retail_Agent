import pandas as pd

from .condition import Condition


def filter_products(
    products: pd.DataFrame,
    condition: Condition
) -> pd.DataFrame:
    """
    Apply hard eligibility constraints.

    Products failing these constraints are removed
    before the scoring stage.
    """

    df = products.copy()

    # -------------------------------------------------
    # 1. Availability
    # -------------------------------------------------

    if "available" in df.columns:

        df = df[
            df["available"]
            .fillna(False)
            .astype(bool)
        ]

    # -------------------------------------------------
    # 2. Products with no interaction history
    # -------------------------------------------------

    if "views" in df.columns:

        df = df[
            df["views"].fillna(0) > 0
        ]

    # -------------------------------------------------
    # 3. Category restriction
    # -------------------------------------------------

    if (
        condition.category
        and condition.category != "unknown"
        and "category" in df.columns
    ):

        categories = (
            df["category"]
            .fillna("")
            .astype(str)
            .str.lower()
            .str.strip()
        )

        df = df[
            categories
            == condition.category
        ]

    # -------------------------------------------------
    # 4. Category exclusions
    # -------------------------------------------------

    if (
        condition.exclude_categories
        and "category" in df.columns
    ):

        excluded = {
            category.lower().strip()
            for category
            in condition.exclude_categories
        }

        categories = (
            df["category"]
            .fillna("")
            .astype(str)
            .str.lower()
            .str.strip()
        )

        df = df[
            ~categories.isin(excluded)
        ]

    # -------------------------------------------------
    # 5. Strict budget
    # -------------------------------------------------

    if (
        condition.strict_budget
        and condition.budget is not None
        and "price" in df.columns
    ):

        prices = pd.to_numeric(
            df["price"],
            errors="coerce"
        )

        df = df[
            prices <= condition.budget
        ]

    return (
        df
        .reset_index(drop=True)
    )