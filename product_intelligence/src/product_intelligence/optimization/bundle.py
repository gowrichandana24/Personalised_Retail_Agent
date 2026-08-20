from itertools import combinations


def generate_bundles(products, min_items=2, max_items=4):
    """
    Generate possible product combinations.
    """

    if len(products) < min_items:
        return []

    max_items = min(max_items, len(products))

    bundles = []

    for size in range(min_items, max_items + 1):
        bundles.extend(combinations(products, size))

    return bundles


def get_bundle_price(bundle):
    """
    Calculate the total price of a bundle.
    """

    return sum(
        product.get("price", 0)
        for product in bundle
    )


def filter_bundles_by_budget(bundles, budget):
    """
    Keep only bundles within the customer's budget.
    """

    return [
        bundle
        for bundle in bundles
        if get_bundle_price(bundle) <= budget
    ]


def calculate_diversity_score(bundle):
    """
    Measure how diverse a bundle is based on product categories.

    Higher score means the bundle contains more different categories.
    """

    if not bundle:
        return 0.0

    categories = {
        product.get("category", "unknown")
        for product in bundle
    }

    return len(categories) / len(bundle)


def calculate_complementarity_score(bundle):
    """
    Reward bundles containing different product categories.

    This is a simple baseline complementarity score.
    """

    if not bundle:
        return 0.0

    categories = {
        product.get("category", "unknown")
        for product in bundle
    }

    if len(bundle) == 1:
        return 0.0

    return min(
        len(categories) / len(bundle),
        1.0
    )


def calculate_bundle_score(bundle, budget):
    """
    Calculate the overall score of a bundle.

    Components:
    - Product relevance
    - Budget utilization
    - Diversity
    - Complementarity
    """

    if not bundle or budget <= 0:
        return 0.0

    average_product_score = (
        sum(
            product.get("score", 0)
            for product in bundle
        )
        / len(bundle)
    )

    total_price = get_bundle_price(bundle)

    budget_utilization = total_price / budget

    diversity_score = calculate_diversity_score(bundle)

    complementarity_score = calculate_complementarity_score(bundle)

    final_score = (
        0.55 * average_product_score
        + 0.15 * budget_utilization
        + 0.15 * diversity_score
        + 0.15 * complementarity_score
    )

    return round(final_score, 4)


def rank_bundles(bundles, budget):
    """
    Rank bundles from best to worst.
    """

    scored_bundles = []

    for bundle in bundles:

        score = calculate_bundle_score(
            bundle,
            budget
        )

        scored_bundles.append({
            "products": list(bundle),
            "price": get_bundle_price(bundle),
            "score": score
        })

    scored_bundles.sort(
        key=lambda bundle: bundle["score"],
        reverse=True
    )

    return scored_bundles