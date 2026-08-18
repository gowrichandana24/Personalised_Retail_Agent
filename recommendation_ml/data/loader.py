"""Data loading and preprocessing for the recommendation ML module.

Supports common retail interaction data with configurable column mappings.
Handles RetailRocket-style datasets and custom CSV/JSON formats.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd

from recommendation_ml.config import EventWeights, RecommendationConfig
from recommendation_ml.schemas import Interaction, Product


DEFAULT_COLUMN_MAP = {
    "visitorid": "customer_id",
    "userid": "customer_id",
    "user_id": "customer_id",
    "customerid": "customer_id",
    "itemid": "product_id",
    "productid": "product_id",
    "product_id": "product_id",
    "item_id": "product_id",
    "event": "event_type",
    "event_type": "event_type",
    "action": "event_type",
    "timestamp": "timestamp",
    "time": "timestamp",
    "eventtime": "timestamp",
    "category": "category",
    "categoryid": "category",
    "category_id": "category",
    "title": "title",
    "name": "title",
    "product_name": "title",
    "brand": "brand",
    "brandname": "brand",
    "brand_name": "brand",
    "price": "price",
    "amount": "price",
    "value": "price",
    "description": "description",
    "desc": "description",
    "product_description": "description",
    "rating": "rating",
    "score": "rating",
}


def normalize_columns(df: pd.DataFrame, column_map: Optional[dict] = None) -> pd.DataFrame:
    """Normalize column names to standard names."""
    if column_map is None:
        column_map = DEFAULT_COLUMN_MAP

    df = df.copy()
    rename_map = {}
    for col in df.columns:
        normalized = col.lower().strip().replace(" ", "_").replace("-", "_")
        if normalized in column_map:
            rename_map[col] = column_map[normalized]
        else:
            rename_map[col] = normalized

    df = df.rename(columns=rename_map)
    return df


def normalize_id(value) -> str:
    """Normalize an identifier to a consistent string format."""
    if pd.isna(value):
        return ""
    s = str(value).strip()
    try:
        return str(int(float(s)))
    except (ValueError, TypeError):
        return hashlib.md5(s.encode()).hexdigest()[:12]


def parse_timestamps(df: pd.DataFrame, timestamp_col: str = "timestamp") -> pd.DataFrame:
    """Parse timestamps to datetime and add derived columns."""
    df = df.copy()
    if timestamp_col not in df.columns:
        df["datetime"] = datetime.now()
        df["days_ago"] = 0.0
        return df

    sample = df[timestamp_col].dropna().head(10)
    if sample.empty:
        df["datetime"] = datetime.now()
        df["days_ago"] = 0.0
        return df

    first_val = sample.iloc[0]
    if isinstance(first_val, (int, float)):
        if first_val > 1e12:
            df["datetime"] = pd.to_datetime(df[timestamp_col], unit="ms", errors="coerce")
        elif first_val > 1e9:
            df["datetime"] = pd.to_datetime(df[timestamp_col], unit="s", errors="coerce")
        else:
            df["datetime"] = pd.to_datetime(df[timestamp_col], unit="s", errors="coerce")
    else:
        df["datetime"] = pd.to_datetime(df[timestamp_col], errors="coerce")

    now = pd.Timestamp.now()
    df["days_ago"] = (now - df["datetime"]).dt.total_seconds() / 86400.0
    df["days_ago"] = df["days_ago"].fillna(365.0)

    return df


def compute_event_strength(
    event_type: str,
    event_weights: EventWeights,
    time_decay_factor: float = 1.0,
) -> float:
    """Compute interaction strength from event type and time decay."""
    base = event_weights.get(event_type)
    return base * time_decay_factor


def load_interactions(
    data: pd.DataFrame | list[dict] | str,
    column_map: Optional[dict] = None,
    event_weights: Optional[EventWeights] = None,
    time_decay_half_life_days: float = 30.0,
) -> pd.DataFrame:
    """Load and preprocess interaction data.

    Args:
        data: DataFrame, list of dicts, or path to CSV/JSON file.
        column_map: Optional custom column name mapping.
        event_weights: Configurable event strength weights.
        time_decay_half_life_days: Half-life for time decay in days.

    Returns:
        Preprocessed DataFrame with normalized columns and interaction strengths.
    """
    if event_weights is None:
        event_weights = EventWeights()

    if isinstance(data, str):
        if data.endswith(".json") or data.endswith(".jsonl"):
            df = pd.read_json(data)
        else:
            df = pd.read_csv(data)
    elif isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        df = data.copy()

    df = normalize_columns(df, column_map)

    required = ["customer_id", "product_id", "event_type"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    df["customer_id"] = df["customer_id"].apply(normalize_id)
    df["product_id"] = df["product_id"].apply(normalize_id)

    df = df[df["customer_id"] != ""]
    df = df[df["product_id"] != ""]

    df = df.drop_duplicates(subset=["customer_id", "product_id", "event_type", "timestamp"], keep="first")

    df = parse_timestamps(df)
    df = df.sort_values("datetime").reset_index(drop=True)

    half_life = time_decay_half_life_days
    decay_rate = np.log(2) / half_life if half_life > 0 else 0.0
    df["time_decay"] = np.exp(-decay_rate * df["days_ago"].clip(lower=0))

    df["strength"] = df.apply(
        lambda row: compute_event_strength(row["event_type"], event_weights, row["time_decay"]),
        axis=1,
    )

    return df


def load_products(
    data: pd.DataFrame | list[dict] | str,
    column_map: Optional[dict] = None,
) -> pd.DataFrame:
    """Load and preprocess product catalogue data.

    Args:
        data: DataFrame, list of dicts, or path to CSV/JSON file.
        column_map: Optional custom column name mapping.

    Returns:
        Preprocessed product DataFrame with normalized IDs.
    """
    if isinstance(data, str):
        if data.endswith(".json") or data.endswith(".jsonl"):
            df = pd.read_json(data)
        else:
            df = pd.read_csv(data)
    elif isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        df = data.copy()

    df = normalize_columns(df, column_map)

    if "product_id" not in df.columns:
        raise ValueError("Product data must contain a product_id column")

    df["product_id"] = df["product_id"].apply(normalize_id)

    for col in ["title", "category", "brand", "description"]:
        if col not in df.columns:
            df[col] = ""
        else:
            df[col] = df[col].fillna("").astype(str)

    for col in ["price", "rating"]:
        if col not in df.columns:
            df[col] = 0.0
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    if "properties" not in df.columns:
        df["properties"] = [{} for _ in range(len(df))]

    df = df.drop_duplicates(subset=["product_id"], keep="first")

    return df


def build_user_item_matrix(interactions: pd.DataFrame) -> pd.DataFrame:
    """Build a user-item interaction matrix from preprocessed interactions.

    Returns a DataFrame with customer_id as index, product_id as columns,
    and aggregated interaction strength as values.
    """
    if interactions.empty:
        return pd.DataFrame()

    agg = interactions.groupby(["customer_id", "product_id"])["strength"].sum().reset_index()
    matrix = agg.pivot_table(
        index="customer_id",
        columns="product_id",
        values="strength",
        fill_value=0.0,
    )
    return matrix


def build_product_metadata_index(products: pd.DataFrame) -> dict:
    """Build a product metadata lookup index."""
    index = {}
    for _, row in products.iterrows():
        index[row["product_id"]] = {
            "title": row.get("title", ""),
            "category": row.get("category", ""),
            "brand": row.get("brand", ""),
            "price": row.get("price", 0.0),
            "description": row.get("description", ""),
            "rating": row.get("rating", 0.0),
            "properties": row.get("properties", {}),
        }
    return index


def time_aware_split(
    interactions: pd.DataFrame,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split interactions chronologically to prevent data leakage.

    Events are sorted by timestamp. The earliest events go to train,
    middle to validation, and latest to test.
    """
    if "datetime" not in interactions.columns:
        interactions = parse_timestamps(interactions)

    sorted_df = interactions.sort_values("datetime").reset_index(drop=True)
    n = len(sorted_df)

    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))

    train = sorted_df.iloc[:train_end].copy()
    val = sorted_df.iloc[train_end:val_end].copy()
    test = sorted_df.iloc[val_end:].copy()

    return train, val, test
