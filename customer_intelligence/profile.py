"""
Customer Intelligence - Customer Profile / Digital Twin

Combines:
- Behavioural features
- Recency/frequency
- Historical affinity
- Recent affinity
- Evidence tier
- Primary persona
- Behavioural attributes
- Compact customer Digital Twin
"""

from __future__ import annotations

import pandas as pd


def build_profile_base(
    customer_features: pd.DataFrame,
    historical_affinity: pd.DataFrame,
    recent_affinity: pd.DataFrame,
    categorized_interactions: pd.DataFrame,
) -> pd.DataFrame:
    """
    Combine validated feature groups into one customer-level
    profile table.
    """

    profile = customer_features.copy()

    # --------------------------------------------------------
    # Historical affinity summary
    # --------------------------------------------------------

    historical_summary = (
        historical_affinity
        .groupby("visitorid")
        .agg(
            num_categories=(
                "categoryid",
                "nunique",
            ),
            total_category_interactions=(
                "interaction_count",
                "sum",
            ),
            max_affinity=(
                "affinity_score",
                "max",
            ),
            avg_affinity=(
                "affinity_score",
                "mean",
            ),
            max_affinity_interactions=(
                "interaction_count",
                "max",
            ),
        )
        .reset_index()
    )

    profile = profile.merge(
        historical_summary,
        on="visitorid",
        how="left",
    )

    # --------------------------------------------------------
    # Recent affinity summary
    # --------------------------------------------------------

    recent_summary = (
        recent_affinity
        .groupby("visitorid")
        .agg(
            recent_num_categories=(
                "categoryid",
                "nunique",
            ),
            max_recent_affinity=(
                "recent_affinity",
                "max",
            ),
            max_recent_score=(
                "recent_score",
                "max",
            ),
        )
        .reset_index()
    )

    profile = profile.merge(
        recent_summary,
        on="visitorid",
        how="left",
    )

    # --------------------------------------------------------
    # Categorized event evidence
    # --------------------------------------------------------

    profile = profile.merge(
        categorized_interactions,
        on="visitorid",
        how="left",
    )

    profile["categorized_interactions"] = (
        profile["categorized_interactions"]
        .fillna(0)
        .astype(int)
    )

    # Category coverage
    profile["category_coverage"] = (
        profile["categorized_interactions"]
        / profile["total_interactions"]
    ).fillna(0)

    # Purchase indicator
    profile["has_purchased"] = (
        profile["total_transactions"] > 0
    ).astype(int)

    # --------------------------------------------------------
    # Profile evidence level
    # --------------------------------------------------------

    def assign_evidence_level(row):
        interactions = row["total_interactions"]

        if interactions <= 1:
            return "Low"
        elif interactions <= 5:
            return "Limited"
        elif interactions <= 20:
            return "Moderate"
        else:
            return "Strong"

    profile["profile_evidence"] = profile.apply(
        assign_evidence_level,
        axis=1,
    )

    # --------------------------------------------------------
    # Final evidence tier
    # --------------------------------------------------------

    def assign_evidence_tier(row):
        interactions = row["total_interactions"]
        purchases = row["total_transactions"]
        carts = row["total_cart_adds"]

        if interactions <= 2 and purchases == 0:
            return "Cold / New"

        elif interactions <= 10 and purchases <= 1:
            return "Developing"

        elif interactions <= 50 or purchases <= 3:
            return "Established"

        else:
            return "Highly Engaged"

    profile["evidence_tier"] = profile.apply(
        assign_evidence_tier,
        axis=1,
    )

    # --------------------------------------------------------
    # Clean missing affinity values
    # --------------------------------------------------------

    affinity_columns = [
        "num_categories",
        "total_category_interactions",
        "max_affinity",
        "avg_affinity",
        "max_affinity_interactions",
        "recent_num_categories",
        "max_recent_affinity",
        "max_recent_score",
    ]

    for column in affinity_columns:
        if column in profile.columns:
            profile[column] = (
                profile[column].fillna(0)
            )

    return profile


def assign_primary_persona(
    profile: pd.DataFrame,
) -> pd.DataFrame:
    """
    Assign one mutually exclusive primary persona.

    Priority:
        Loyal Purchaser
        Repeat Purchaser
        One-Time Purchaser
        Engaged Shopper
        Browser / Explorer
        New / Unknown
    """

    result = profile.copy()

    def persona(row):
        transactions = row["total_transactions"]
        views = row["total_views"]
        carts = row["total_cart_adds"]
        interactions = row["total_interactions"]

        if transactions >= 5:
            return "Loyal Purchaser"

        elif transactions >= 2:
            return "Repeat Purchaser"

        elif transactions == 1:
            return "One-Time Purchaser"

        elif interactions >= 5 or carts >= 1:
            return "Engaged Shopper"

        elif views >= 3:
            return "Browser / Explorer"

        else:
            return "New / Unknown"

    result["primary_persona"] = result.apply(
        persona,
        axis=1,
    )

    return result


def add_behavioural_attributes(
    profile: pd.DataFrame,
) -> pd.DataFrame:
    """
    Add non-exclusive behavioural attributes.
    """

    result = profile.copy()

    result["is_multi_category"] = (
        result["num_categories"] >= 3
    )

    result["is_recently_active"] = (
        result["recency_days"] <= 7
    )

    result["is_highly_active"] = (
        result["total_interactions"] >= 20
    )

    result["is_cart_heavy"] = (
        (result["total_cart_adds"] >= 2)
        &
        (result["total_transactions"] == 0)
    )

    result["is_repeat_purchaser"] = (
        result["total_transactions"] >= 2
    )

    return result


def add_top_historical_categories(
    profile: pd.DataFrame,
    historical_affinity: pd.DataFrame,
    top_n: int = 3,
) -> pd.DataFrame:
    """
    Add top historical category IDs and affinity scores.
    """

    result = profile.copy()

    top = (
        historical_affinity
        .sort_values(
            ["visitorid", "affinity_score"],
            ascending=[True, False],
        )
        .copy()
    )

    top["category_rank"] = (
        top
        .groupby("visitorid")
        .cumcount()
        + 1
    )

    top = top[
        top["category_rank"] <= top_n
    ]

    pivot = top.pivot(
        index="visitorid",
        columns="category_rank",
        values=[
            "categoryid",
            "affinity_score",
        ],
    )

    pivot.columns = [
        (
            f"top_category_{rank}"
            if field == "categoryid"
            else f"top_category_affinity_{rank}"
        )
        for field, rank in pivot.columns
    ]

    pivot = pivot.reset_index()

    result = result.merge(
        pivot,
        on="visitorid",
        how="left",
    )

    return result


def add_top_recent_categories(
    profile: pd.DataFrame,
    recent_affinity: pd.DataFrame,
    top_n: int = 2,
) -> pd.DataFrame:
    """
    Add top recent category IDs and affinity scores.
    """

    result = profile.copy()

    top = (
        recent_affinity
        .sort_values(
            ["visitorid", "recent_affinity"],
            ascending=[True, False],
        )
        .copy()
    )

    top["category_rank"] = (
        top
        .groupby("visitorid")
        .cumcount()
        + 1
    )

    top = top[
        top["category_rank"] <= top_n
    ]

    pivot = top.pivot(
        index="visitorid",
        columns="category_rank",
        values=[
            "categoryid",
            "recent_affinity",
        ],
    )

    pivot.columns = [
        (
            f"recent_category_{rank}"
            if field == "categoryid"
            else f"recent_category_affinity_{rank}"
        )
        for field, rank in pivot.columns
    ]

    pivot = pivot.reset_index()

    result = result.merge(
        pivot,
        on="visitorid",
        how="left",
    )

    return result


def build_digital_twin(
    profile: pd.DataFrame,
    historical_affinity: pd.DataFrame,
    recent_affinity: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build the final compact customer Digital Twin.
    """

    result = profile.copy()

    result = add_top_historical_categories(
        result,
        historical_affinity,
        top_n=3,
    )

    result = add_top_recent_categories(
        result,
        recent_affinity,
        top_n=2,
    )

    # --------------------------------------------------------
    # Category columns
    # --------------------------------------------------------

    category_columns = [
        "top_category_1",
        "top_category_2",
        "top_category_3",
        "recent_category_1",
        "recent_category_2",
    ]

    affinity_columns = [
        "top_category_affinity_1",
        "top_category_affinity_2",
        "top_category_affinity_3",
        "recent_category_affinity_1",
        "recent_category_affinity_2",
    ]

    for column in category_columns:
        if column in result.columns:
            result[column] = result[column].astype("Int64")

    for column in affinity_columns:
        if column in result.columns:
            result[column] = result[column].fillna(0)

    # --------------------------------------------------------
    # Final 29-field profile structure
    # --------------------------------------------------------

    profile_columns = [
        "visitorid",
        "primary_persona",
        "profile_evidence",
        "evidence_tier",
        "total_interactions",
        "total_views",
        "total_cart_adds",
        "total_transactions",
        "unique_products",
        "recency_days",
        "purchase_recency_days",
        "num_categories",
        "max_affinity",
        "max_recent_affinity",
        "has_purchased",
        "is_multi_category",
        "is_recently_active",
        "is_highly_active",
        "is_cart_heavy",
        "top_category_1",
        "top_category_affinity_1",
        "top_category_2",
        "top_category_affinity_2",
        "top_category_3",
        "top_category_affinity_3",
        "recent_category_1",
        "recent_category_affinity_1",
        "recent_category_2",
        "recent_category_affinity_2",
    ]

    existing_columns = [
        column
        for column in profile_columns
        if column in result.columns
    ]

    return result[existing_columns]


def get_customer_profile(
    digital_twin: pd.DataFrame,
    customer_id: int | str,
) -> dict:
    """
    Return one customer's Digital Twin as a dictionary.

    This is the interface Member 1 and Member 4 can use.
    """

    match = digital_twin[
        digital_twin["visitorid"] == customer_id
    ]

    if match.empty:
        raise KeyError(
            f"Customer {customer_id} not found."
        )

    record = match.iloc[0].to_dict()

    # Convert pandas NA to None for JSON compatibility
    cleaned = {}

    for key, value in record.items():

        if pd.isna(value):
            cleaned[key] = None
        else:
            # Convert NumPy scalar types to normal Python types
            if hasattr(value, "item"):
                try:
                    value = value.item()
                except ValueError:
                    pass

            cleaned[key] = value

    return cleaned