from .constraints import (
    filter_by_budget,
    filter_excluded_brands,
)


def optimize_products(
    products,
    budget,
    excluded_brands=None,
):
    """
    Main entry point for the optimization module.
    """

    # Apply budget constraint
    candidates = filter_by_budget(
        products,
        budget,
    )

    # Apply brand constraint
    candidates = filter_excluded_brands(
        candidates,
        excluded_brands,
    )

    # Rank candidates by recommendation score
    candidates.sort(
        key=lambda product: product.get("score", 0),
        reverse=True,
    )

    return candidates


if __name__ == "__main__":

    products = [
        {
            "id": 1,
            "name": "Running Shoes",
            "brand": "Nike",
            "category": "shoes",
            "price": 1800,
            "score": 0.95
        },
        {
            "id": 2,
            "name": "Gym T-Shirt",
            "brand": "Adidas",
            "category": "clothing",
            "price": 700,
            "score": 0.90
        },
        {
            "id": 3,
            "name": "Water Bottle",
            "brand": "Milton",
            "category": "accessories",
            "price": 400,
            "score": 0.85
        },
        {
            "id": 4,
            "name": "Fitness Watch",
            "brand": "Apple",
            "category": "wearables",
            "price": 3500,
            "score": 0.80
        }
    ]

    result = optimize_products(
        products,
        budget=3000
    )

    for product in result:
        print(
            product["name"],
            product["price"],
            product["score"]
        )