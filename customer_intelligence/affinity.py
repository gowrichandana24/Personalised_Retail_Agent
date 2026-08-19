"""
Customer Intelligence - Category Affinity

Contains the validated logic for:
- Combining item property files
- Item -> category mapping
- Time-aware event enrichment
- Historical category affinity
- Recent/time-decayed category affinity
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


EVENT_WEIGHTS = {
    "view": 1.0,
    "addtocart": 3.0,
    "transaction": 5.0,
}


def load_item_category_history(
    part1_path: str | Path,
    part2_path: str | Path,
) -> pd.DataFrame:
    """
    Load both RetailRocket item-property files and retain
    categoryid property records.
    """

    part1_path = Path(part1_path)
    part2_path = Path(part2_path)

    if not part1_path.exists():
        raise FileNotFoundError(part1_path)

    if not part2_path.exists():
        raise FileNotFoundError(part2_path)

    part1 = pd.read_csv(part1_path)
    part2 = pd.read_csv(part2_path)

    required_columns = {
        "timestamp",
        "itemid",
        "property",
        "value",
    }

    for name, df in {
        "part1": part1,
        "part2": part2,
    }.items():

        missing = required_columns - set(df.columns)

        if missing:
            raise ValueError(
                f"{name} missing columns: {sorted(missing)}"
            )

    item_categories = pd.concat(
        [
            part1[
                part1["property"] == "categoryid"
            ],
            part2[
                part2["property"] == "categoryid"
            ],
        ],
        ignore_index=True,
    )

    item_categories = item_categories.rename(
        columns={"value": "categoryid"}
    )

    item_categories = item_categories[
        ["timestamp", "itemid", "categoryid"]
    ].copy()

    item_categories["timestamp"] = pd.to_datetime(
        item_categories["timestamp"],
        unit="ms",
    )

    # Same item/category at the same timestamp is redundant.
    item_categories = (
        item_categories
        .drop_duplicates(
            subset=[
                "itemid",
                "categoryid",
                "timestamp",
            ]
        )
        .sort_values(
            ["timestamp", "itemid"]
        )
        .reset_index(drop=True)
    )

    return item_categories


def enrich_events_with_category(
    events: pd.DataFrame,
    item_categories: pd.DataFrame,
) -> pd.DataFrame:
    """
    Map each customer event to the latest category assignment
    for that item at or before the event timestamp.
    """

    required_events = {
        "datetime",
        "visitorid",
        "event",
        "itemid",
        "transactionid",
    }

    missing = required_events - set(events.columns)

    if missing:
        raise ValueError(
            f"Events missing columns: {sorted(missing)}"
        )

    required_categories = {
        "timestamp",
        "itemid",
        "categoryid",
    }

    missing = required_categories - set(
        item_categories.columns
    )

    if missing:
        raise ValueError(
            f"Item categories missing: {sorted(missing)}"
        )

    events_for_merge = events[
        [
            "datetime",
            "visitorid",
            "event",
            "itemid",
            "transactionid",
        ]
    ].copy()

    category_history = item_categories[
        [
            "timestamp",
            "itemid",
            "categoryid",
        ]
    ].copy()

    # merge_asof requires the time keys to be globally sorted.
    events_for_merge = (
        events_for_merge
        .sort_values(
            ["datetime", "itemid"]
        )
        .reset_index(drop=True)
    )

    category_history = (
        category_history
        .sort_values(
            ["timestamp", "itemid"]
        )
        .reset_index(drop=True)
    )

    enriched_events = pd.merge_asof(
        events_for_merge,
        category_history,
        left_on="datetime",
        right_on="timestamp",
        by="itemid",
        direction="backward",
    )

    enriched_events = enriched_events.drop(
        columns=["timestamp"]
    )

    enriched_events = (
        enriched_events
        .sort_values(
            ["visitorid", "datetime"]
        )
        .reset_index(drop=True)
    )

    return enriched_events


def compute_historical_affinity(
    enriched_events: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compute historical customer-category affinity.

    Weights:
        view       = 1
        addtocart  = 3
        transaction = 5
    """

    affinity_events = enriched_events.dropna(
        subset=["categoryid"]
    ).copy()

    affinity_events["categoryid"] = (
        affinity_events["categoryid"].astype(int)
    )

    affinity_events["interaction_weight"] = (
        affinity_events["event"]
        .map(EVENT_WEIGHTS)
        .fillna(0)
    )

    # Customer-category weighted score
    affinity = (
        affinity_events
        .groupby(
            ["visitorid", "categoryid"]
        )["interaction_weight"]
        .sum()
        .reset_index()
    )

    # Total weighted score for each customer
    affinity["customer_total_score"] = (
        affinity
        .groupby("visitorid")[
            "interaction_weight"
        ]
        .transform("sum")
    )

    # Relative affinity
    affinity["affinity_score"] = (
        affinity["interaction_weight"]
        / affinity["customer_total_score"]
    )

    # Interaction evidence
    interaction_counts = (
        affinity_events
        .groupby(
            ["visitorid", "categoryid"]
        )
        .size()
        .rename("interaction_count")
        .reset_index()
    )

    affinity = affinity.merge(
        interaction_counts,
        on=["visitorid", "categoryid"],
        how="left",
    )

    affinity["customer_interaction_count"] = (
        affinity
        .groupby("visitorid")[
            "interaction_count"
        ]
        .transform("sum")
    )

    affinity["evidence_ratio"] = (
        affinity["interaction_count"]
        / affinity["customer_interaction_count"]
    )

    affinity["num_categories"] = (
        affinity
        .groupby("visitorid")[
            "categoryid"
        ]
        .transform("nunique")
    )

    affinity = (
        affinity
        .sort_values(
            ["visitorid", "affinity_score"],
            ascending=[True, False],
        )
        .reset_index(drop=True)
    )

    return affinity


def compute_recent_affinity(
    enriched_events: pd.DataFrame,
    half_life_days: float = 30.0,
) -> pd.DataFrame:
    """
    Compute time-decayed customer-category affinity.

    The validated logic uses:
        time_decay =
            exp(-ln(2) * age_days / half_life_days)

    Default half-life = 30 days.
    """

    recent_events = enriched_events.dropna(
        subset=["categoryid"]
    ).copy()

    recent_events["categoryid"] = (
        recent_events["categoryid"].astype(int)
    )

    recent_events["event_weight"] = (
        recent_events["event"]
        .map(EVENT_WEIGHTS)
        .fillna(0)
    )

    reference_date = enriched_events[
        "datetime"
    ].max()

    recent_events["age_days"] = (
        reference_date
        - recent_events["datetime"]
    ).dt.total_seconds() / (24 * 60 * 60)

    recent_events["time_decay"] = np.exp(
        -np.log(2)
        * recent_events["age_days"]
        / half_life_days
    )

    recent_events["decayed_weight"] = (
        recent_events["event_weight"]
        * recent_events["time_decay"]
    )

    recent_scores = (
        recent_events
        .groupby(
            ["visitorid", "categoryid"]
        )["decayed_weight"]
        .sum()
        .reset_index(
            name="recent_score"
        )
    )

    recent_scores["customer_recent_total"] = (
        recent_scores
        .groupby("visitorid")[
            "recent_score"
        ]
        .transform("sum")
    )

    recent_scores["recent_affinity"] = (
        recent_scores["recent_score"]
        / recent_scores["customer_recent_total"]
    )

    recent_scores = (
        recent_scores
        .sort_values(
            ["visitorid", "recent_affinity"],
            ascending=[True, False],
        )
        .reset_index(drop=True)
    )

    return recent_scores