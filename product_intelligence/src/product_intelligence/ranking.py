import pandas as pd


def rank_products(
    products: pd.DataFrame,
    top_k: int = 10
) -> pd.DataFrame:
    """
    Rank products by final Product Intelligence score.
    """

    if products.empty:
        return products.copy()

    ranked = (
        products
        .sort_values(
            by="final_score",
            ascending=False
        )
        .reset_index(drop=True)
    )

    ranked["rank"] = (
        ranked.index + 1
    )

    return ranked.head(
        top_k
    )