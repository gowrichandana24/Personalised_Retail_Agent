from .optimizer import (
    optimize_products,
    optimize_bundles,
    optimize_discovery,
    optimize_what_if,
)


products = [
    {
        "id": 1,
        "name": "Running Shoes",
        "brand": "Nike",
        "category": "shoes",
        "price": 1800,
        "score": 0.95,
        "novelty": 0.7,
        "mission_fit": 0.95,
    },
    {
        "id": 2,
        "name": "Gym T-Shirt",
        "brand": "Adidas",
        "category": "clothing",
        "price": 700,
        "score": 0.90,
        "novelty": 0.8,
        "mission_fit": 0.90,
    },
    {
        "id": 3,
        "name": "Water Bottle",
        "brand": "Milton",
        "category": "accessories",
        "price": 400,
        "score": 0.85,
        "novelty": 0.9,
        "mission_fit": 0.85,
    },
    {
        "id": 4,
        "name": "Gym Bag",
        "brand": "Puma",
        "category": "bags",
        "price": 1200,
        "score": 0.80,
        "novelty": 0.6,
        "mission_fit": 0.80,
    },
    {
        "id": 5,
        "name": "Fitness Watch",
        "brand": "Apple",
        "category": "wearables",
        "price": 3500,
        "score": 0.75,
        "novelty": 0.7,
        "mission_fit": 0.70,
    },
]


print("\n--- PRODUCT OPTIMIZATION ---")

result = optimize_products(
    products,
    budget=3000,
    diversity_limit=3
)

for product in result:
    print(
        product["name"],
        "₹" + str(product["price"]),
        "score=" + str(product["score"])
    )


print("\n--- BUNDLE OPTIMIZATION ---")

bundles = optimize_bundles(
    products,
    budget=3000,
    min_items=2,
    max_items=3,
    top_k=5
)

for bundle in bundles:

    names = [
        product["name"]
        for product in bundle["products"]
    ]

    print(
        names,
        "₹" + str(bundle["price"]),
        "score=" + str(bundle["score"])
    )


print("\n--- DISCOVERY ---")

discovery = optimize_discovery(
    products,
    top_k=3
)

for product in discovery:
    print(
        product["name"],
        "discovery=" +
        str(product["discovery_score"])
    )


print("\n--- WHAT-IF ---")

what_if = optimize_what_if(
    products,
    budget=2000
)

for product in what_if:
    print(
        product["name"],
        "₹" + str(product["price"])
    )