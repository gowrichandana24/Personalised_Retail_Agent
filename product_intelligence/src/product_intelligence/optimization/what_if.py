from .constraints import (
    filter_by_budget,
    filter_excluded_brands,
)


def what_if_optimize(
    products,
    budget=None,
    excluded_brands=None,
):
    """
    Re-rank products after the customer
    changes one or more constraints.
    """

    candidates = products

    if budget is not None:
        candidates = filter_by_budget(
            candidates,
            budget
        )

    candidates = filter_excluded_brands(
        candidates,
        excluded_brands
    )

    candidates = sorted(
        candidates,
        key=lambda product:
        product.get("score", 0),
        reverse=True
    )

    return candidates