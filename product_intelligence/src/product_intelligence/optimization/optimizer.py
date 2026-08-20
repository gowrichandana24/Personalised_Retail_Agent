from .constraints import (
    filter_by_budget,
    filter_excluded_brands,
)

from .bundle import (
    generate_bundles,
    filter_bundles_by_budget,
    rank_bundles,
)

from .diversity import (
    diversify_products,
)

from .discovery import (
    rank_discovery_products,
)

from .what_if import (
    what_if_optimize,
)


def optimize_products(
    products,
    budget,
    excluded_brands=None,
    diversity_limit=None,
):
    """
    Main product optimization pipeline.

    Steps:
    1. Apply constraints
    2. Rank products
    3. Apply diversity
    """

    candidates = filter_by_budget(
        products,
        budget
    )

    candidates = filter_excluded_brands(
        candidates,
        excluded_brands
    )

    candidates.sort(
        key=lambda product:
        product.get("score", 0),
        reverse=True
    )

    if diversity_limit:
        candidates = diversify_products(
            candidates,
            diversity_limit
        )

    return candidates


def optimize_bundles(
    products,
    budget,
    min_items=2,
    max_items=4,
    top_k=5,
):
    """
    Generate, filter and rank product bundles.
    """

    bundles = generate_bundles(
        products,
        min_items,
        max_items
    )

    valid_bundles = filter_bundles_by_budget(
        bundles,
        budget
    )

    ranked_bundles = rank_bundles(
        valid_bundles,
        budget
    )

    return ranked_bundles[:top_k]


def optimize_discovery(products, top_k=5):
    """
    Return products suitable for discovery.
    """

    ranked = rank_discovery_products(
        products
    )

    return ranked[:top_k]


def optimize_what_if(
    products,
    budget=None,
    excluded_brands=None,
):
    """
    Re-optimize after changed constraints.
    """

    return what_if_optimize(
        products,
        budget,
        excluded_brands
    )