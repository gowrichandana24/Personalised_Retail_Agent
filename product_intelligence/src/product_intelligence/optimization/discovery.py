def calculate_discovery_score(product):
    """
    Calculate a simple discovery score.

    Discovery balances:
    - Product relevance
    - Novelty
    - Mission fit
    """

    relevance = product.get(
        "score",
        0
    )

    novelty = product.get(
        "novelty",
        0.5
    )

    mission_fit = product.get(
        "mission_fit",
        relevance
    )

    return round(
        relevance * novelty * mission_fit,
        4
    )


def rank_discovery_products(products):
    """
    Rank products for controlled discovery.
    """

    ranked = []

    for product in products:

        score = calculate_discovery_score(
            product
        )

        result = dict(product)

        result["discovery_score"] = score

        ranked.append(result)

    ranked.sort(
        key=lambda product:
        product["discovery_score"],
        reverse=True
    )

    return ranked