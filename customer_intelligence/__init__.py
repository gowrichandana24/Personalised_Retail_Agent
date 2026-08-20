"""Customer intelligence building blocks used by the RetailMind backend."""

from .affinity import (
    compute_historical_affinity,
    compute_recent_affinity,
    enrich_events_with_category,
    load_item_category_history,
)
from .features import build_categorized_interaction_count, build_customer_event_features
from .profile import (
    add_behavioural_attributes,
    assign_primary_persona,
    build_digital_twin,
    build_profile_base,
    get_customer_profile,
)

__all__ = [
    "add_behavioural_attributes",
    "assign_primary_persona",
    "build_categorized_interaction_count",
    "build_customer_event_features",
    "build_digital_twin",
    "build_profile_base",
    "compute_historical_affinity",
    "compute_recent_affinity",
    "enrich_events_with_category",
    "get_customer_profile",
    "load_item_category_history",
]
