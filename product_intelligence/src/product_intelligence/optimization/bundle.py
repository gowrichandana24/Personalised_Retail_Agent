from itertools import combinations


def generate_bundles(products, min_items=2, max_items=4):
    """
    Generate possible product combinations.
    """

    bundles = []

    max_items = min(max_items, len(products))

    for size in range(min_items, max_items + 1):
        bundles.extend(
            combinations(products, size)
        )

    return bundles


def filter_bundles_by_budget(bundles, budget):
    """
    Keep only bundles whose total price
    is within the user's budget.
    """

    valid_bundles = []

    for bundle in bundles:
        total_price = sum(
            product["price"]
            for product in bundle
        )

        if total_price <= budget:
            valid_bundles.append(bundle)

    return valid_bundles


def calculate_bundle_score(bundle, budget):
    """
    Calculate an initial score for a product bundle.

    The score considers:
    1. Average relevance of products
    2. Budget utilization
    """

    if not bundle:
        return 0

    average_product_score = (
        sum(product.get("score", 0) for product in bundle)
        / len(bundle)
    )

    total_price = sum(
        product["price"]
        for product in bundle
    )

    budget_utilization = total_price / budget

    bundle_score = (
        0.8 * average_product_score
        + 0.2 * budget_utilization
    )

    return round(bundle_score, 4)


if __name__ == "__main__":

    products = [
        {
            "name": "Running Shoes",
            "price": 1800,
            "score": 0.95,
        },
        {
            "name": "Gym T-Shirt",
            "price": 700,
            "score": 0.90,
        },
        {
            "name": "Water Bottle",
            "price": 400,
            "score": 0.85,
        },
        {
            "name": "Gym Bag",
            "price": 1200,
            "score": 0.80,
        },
    ]

    bundles = generate_bundles(products)

    valid_bundles = filter_bundles_by_budget(
        bundles,
        budget=3000
    )

    # THIS is the part you replace
    for bundle in valid_bundles:

        names = [
            product["name"]
            for product in bundle
        ]

        total_price = sum(
            product["price"]
            for product in bundle
        )

        score = calculate_bundle_score(
            bundle,
            budget=3000
        )

        print(
            names,
            "→ ₹",
            total_price,
            "→ score:",
            score
        )