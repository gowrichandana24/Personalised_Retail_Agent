import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .condition import Condition


# ============================================================
# WEIGHT PROFILES
# ============================================================

WEIGHT_PROFILES = {

    "budget": {
        "category": 0.20,
        "budget": 0.45,
        "semantic": 0.20,
        "quality": 0.10,
        "discovery": 0.05
    },

    "balanced": {
        "category": 0.25,
        "budget": 0.25,
        "semantic": 0.25,
        "quality": 0.15,
        "discovery": 0.10
    },

    "high_discovery": {
        "category": 0.15,
        "budget": 0.15,
        "semantic": 0.30,
        "quality": 0.10,
        "discovery": 0.30
    }
}


# ============================================================
# NORMALIZATION
# ============================================================

def minmax_normalize(
    series: pd.Series
) -> pd.Series:

    values = pd.to_numeric(
        series,
        errors="coerce"
    ).fillna(0)

    minimum = values.min()
    maximum = values.max()

    if maximum == minimum:

        return pd.Series(
            np.ones(
                len(values)
            ),
            index=values.index
        )

    return (
        (values - minimum)
        /
        (maximum - minimum)
    )


# ============================================================
# BUDGET FIT
# ============================================================

def calculate_budget_fit(
    price: float,
    budget: float,
    alpha: float = 3.0
) -> float:

    if budget is None:
        return 0.5

    if pd.isna(price):
        return 0.5

    if budget <= 0:
        return 0.0

    if price <= budget:
        return 1.0

    excess = (
        price - budget
    ) / budget

    return float(
        np.exp(
            -alpha * excess
        )
    )


# ============================================================
# CATEGORY MATCH
# ============================================================

def calculate_category_match(
    category,
    condition_category
) -> float:

    if (
        condition_category is None
        or condition_category == "unknown"
    ):
        return 0.5

    if pd.isna(category):
        return 0.0

    return float(
        str(category)
        .strip()
        .lower()
        ==
        condition_category
        .strip()
        .lower()
    )


# ============================================================
# SEMANTIC / STYLE MATCH
# ============================================================

def calculate_semantic_scores(
    products: pd.DataFrame,
    condition: Condition
) -> np.ndarray:

    if not condition.keywords:

        return np.zeros(
            len(products)
        )

    if "product_text" not in products.columns:

        return np.zeros(
            len(products)
        )

    query = " ".join(
        condition.keywords
    )

    corpus = (
        products["product_text"]
        .fillna("")
        .astype(str)
        .tolist()
    )

    if not any(
        text.strip()
        for text in corpus
    ):

        return np.zeros(
            len(products)
        )

    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english"
    )

    try:

        product_vectors = (
            vectorizer.fit_transform(
                corpus
            )
        )

        query_vector = (
            vectorizer.transform(
                [query]
            )
        )

        scores = cosine_similarity(
            query_vector,
            product_vectors
        )[0]

        return scores

    except ValueError:

        return np.zeros(
            len(products)
        )


# ============================================================
# WEIGHT SELECTION
# ============================================================

def select_weights(
    condition: Condition
) -> dict:

    if condition.discovery_level == "high":

        return WEIGHT_PROFILES[
            "high_discovery"
        ].copy()

    if condition.discovery_level == "low":

        return WEIGHT_PROFILES[
            "budget"
        ].copy()

    return WEIGHT_PROFILES[
        "balanced"
    ].copy()


# ============================================================
# COMPONENT SCORING
# ============================================================

def calculate_component_scores(
    products: pd.DataFrame,
    condition: Condition
) -> pd.DataFrame:

    df = products.copy()

    # --------------------------------------------------------
    # CATEGORY
    # --------------------------------------------------------

    if "category" in df.columns:

        df["category_score"] = df[
            "category"
        ].apply(
            lambda value:
            calculate_category_match(
                value,
                condition.category
            )
        )

    else:

        df["category_score"] = 0.5

    # --------------------------------------------------------
    # SEMANTIC
    # --------------------------------------------------------

    df["semantic_score"] = (
        calculate_semantic_scores(
            df,
            condition
        )
    )

    # --------------------------------------------------------
    # QUALITY
    # --------------------------------------------------------

    if "smoothed_conversion" in df.columns:

        df["quality_score"] = (
            minmax_normalize(
                df[
                    "smoothed_conversion"
                ]
            )
        )

    elif "conversion_rate" in df.columns:

        df["quality_score"] = (
            minmax_normalize(
                df[
                    "conversion_rate"
                ]
            )
        )

    else:

        df["quality_score"] = 0.5

    # --------------------------------------------------------
    # DISCOVERY
    # --------------------------------------------------------

    if "views" in df.columns:

        popularity = (
            minmax_normalize(
                df["views"]
            )
        )

        df["discovery_score"] = (
            1 - popularity
        )

    else:

        df["discovery_score"] = 0.5

    # --------------------------------------------------------
    # BUDGET
    # --------------------------------------------------------

    if (
        "price" in df.columns
        and condition.budget is not None
    ):

        df["budget_score"] = df.apply(

            lambda row:
            calculate_budget_fit(
                row["price"],
                condition.budget
            ),

            axis=1
        )

    else:

        df["budget_score"] = 0.5

    return df


# ============================================================
# FINAL WEIGHTED SCORE
# ============================================================

def calculate_final_score(
    products: pd.DataFrame,
    weights: dict
) -> pd.DataFrame:

    df = products.copy()

    # Contributions
    df["category_contribution"] = (
        df["category_score"]
        * weights["category"]
    )

    df["budget_contribution"] = (
        df["budget_score"]
        * weights["budget"]
    )

    df["semantic_contribution"] = (
        df["semantic_score"]
        * weights["semantic"]
    )

    df["quality_contribution"] = (
        df["quality_score"]
        * weights["quality"]
    )

    df["discovery_contribution"] = (
        df["discovery_score"]
        * weights["discovery"]
    )

    # Transparent weighted sum
    df["final_score"] = (
        df["category_contribution"]
        +
        df["budget_contribution"]
        +
        df["semantic_contribution"]
        +
        df["quality_contribution"]
        +
        df["discovery_contribution"]
    )

    return df