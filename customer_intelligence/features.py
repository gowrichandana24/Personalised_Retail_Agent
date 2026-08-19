"""
Customer Intelligence - Behavioural Features

Builds customer-level:
- interaction counts
- recency
- frequency
- activity duration
- engagement features
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def load_events(events_path: str | Path) -> pd.DataFrame:
    """
    Load RetailRocket events.csv and create datetime.
    """

    events_path = Path(events_path)

    if not events_path.exists():
        raise FileNotFoundError(
            f"Events file not found: {events_path}"
        )

    events = pd.read_csv(events_path)

    required_columns = {
        "timestamp",
        "visitorid",
        "event",
        "itemid",
        "transactionid",
    }

    missing = required_columns - set(events.columns)

    if missing:
        raise ValueError(
            f"events.csv is missing required columns: "
            f"{sorted(missing)}"
        )

    events["datetime"] = pd.to_datetime(
        events["timestamp"],
        unit="ms"
    )

    return events


def build_customer_event_features(
    events: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build customer-level behavioural features.

    Features:
    - total_interactions
    - total_views
    - total_cart_adds
    - total_transactions
    - unique_products
    - first_activity
    - last_activity
    - last_purchase
    - recency_days
    - purchase_recency_days
    - active_days
    - interactions_per_active_day
    - transactions_per_active_day
    - cart_rate
    - purchase_rate
    """

    required_columns = {
        "visitorid",
        "event",
        "itemid",
        "datetime",
    }

    missing = required_columns - set(events.columns)

    if missing:
        raise ValueError(
            f"Events DataFrame is missing: {sorted(missing)}"
        )

    # --------------------------------------------------------
    # Reference date
    # --------------------------------------------------------

    reference_date = events["datetime"].max()

    # --------------------------------------------------------
    # Fast event-count features
    #
    # Instead of several groupby(lambda...) operations,
    # create indicator columns and aggregate once.
    # --------------------------------------------------------

    event_flags = pd.DataFrame({
        "visitorid": events["visitorid"],
        "total_interactions": 1,
        "total_views": (
            events["event"].eq("view").astype("int8")
        ),
        "total_cart_adds": (
            events["event"].eq("addtocart").astype("int8")
        ),
        "total_transactions": (
            events["event"].eq("transaction").astype("int8")
        ),
    })

    customer_features = (
        event_flags
        .groupby("visitorid", sort=False)
        .sum()
        .reset_index()
    )

    # --------------------------------------------------------
    # Unique products + activity dates
    # --------------------------------------------------------

    activity_features = (
        events
        .groupby("visitorid", sort=False)
        .agg(
            unique_products=("itemid", "nunique"),
            first_activity=("datetime", "min"),
            last_activity=("datetime", "max"),
        )
        .reset_index()
    )

    customer_features = customer_features.merge(
        activity_features,
        on="visitorid",
        how="left",
    )

    # --------------------------------------------------------
    # Last purchase
    # --------------------------------------------------------

    transaction_events = events[
        events["event"].eq("transaction")
    ]

    last_purchase = (
        transaction_events
        .groupby("visitorid", sort=False)["datetime"]
        .max()
        .rename("last_purchase")
        .reset_index()
    )

    customer_features = customer_features.merge(
        last_purchase,
        on="visitorid",
        how="left",
    )

    # --------------------------------------------------------
    # Recency
    # --------------------------------------------------------

    customer_features["recency_days"] = (
        reference_date
        - customer_features["last_activity"]
    ).dt.total_seconds() / (24 * 60 * 60)

    customer_features["purchase_recency_days"] = (
        reference_date
        - customer_features["last_purchase"]
    ).dt.total_seconds() / (24 * 60 * 60)

    # -1 = no recorded purchase
    customer_features["purchase_recency_days"] = (
        customer_features["purchase_recency_days"]
        .fillna(-1)
    )

    # --------------------------------------------------------
    # Active duration
    # --------------------------------------------------------

    customer_features["active_days"] = (
        customer_features["last_activity"]
        - customer_features["first_activity"]
    ).dt.total_seconds() / (24 * 60 * 60)

    # --------------------------------------------------------
    # Frequency-related measures
    # --------------------------------------------------------

    active_days_safe = (
        customer_features["active_days"]
        .clip(lower=1)
    )

    customer_features["interactions_per_active_day"] = (
        customer_features["total_interactions"]
        / active_days_safe
    )

    customer_features["transactions_per_active_day"] = (
        customer_features["total_transactions"]
        / active_days_safe
    )

    # --------------------------------------------------------
    # Engagement ratios
    # --------------------------------------------------------

    views_safe = (
        customer_features["total_views"]
        .replace(0, np.nan)
    )

    customer_features["cart_rate"] = (
        customer_features["total_cart_adds"]
        / views_safe
    ).fillna(0)

    customer_features["purchase_rate"] = (
        customer_features["total_transactions"]
        / views_safe
    ).fillna(0)

    return customer_features


def build_categorized_interaction_count(
    enriched_events: pd.DataFrame,
) -> pd.DataFrame:
    """
    Count customer interactions that have category information.
    """

    categorized = (
        enriched_events
        .dropna(subset=["categoryid"])
        .groupby("visitorid", sort=False)
        .size()
        .rename("categorized_interactions")
        .reset_index()
    )

    return categorized