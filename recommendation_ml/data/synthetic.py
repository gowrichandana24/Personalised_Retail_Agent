"""Synthetic data generator for testing and development.

Generates realistic retail interaction data for hackathon development
when the actual RetailRocket dataset is not yet available.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


CATEGORIES = [
    "Electronics", "Clothing", "Home & Kitchen", "Sports", "Books",
    "Beauty", "Toys", "Automotive", "Garden", "Health",
]

BRANDS = {
    "Electronics": ["Samsung", "Apple", "Xiaomi", "Sony", "OnePlus"],
    "Clothing": ["Nike", "Adidas", "Zara", "H&M", "Levi's"],
    "Home & Kitchen": ["IKEA", "Prestige", "Milton", "Bajaj", "Philips"],
    "Sports": ["Nike", "Adidas", "Puma", "Reebok", "Yonex"],
    "Books": ["Penguin", "HarperCollins", "Bloomsbury", "RandomHouse", "Scholastic"],
    "Beauty": ["L'Oreal", "Maybelline", "Nivea", "Lakme", "Plum"],
    "Toys": ["Lego", "Funskool", "Hasbro", "Mattel", "Hamleys"],
    "Automotive": ["Mobil", "3M", "Bosch", "Michelin", "Goodyear"],
    "Garden": ["Bosch", "Scotts", "Husqvarna", "Greenworks", "Fiskars"],
    "Health": ["Himalaya", "Dabur", "Vicks", "Johnson", "Abbott"],
}

PRODUCT_TEMPLATES = {
    "Electronics": [
        "{brand} {product} {variant}",
        "{brand} Wireless {product}",
        "{brand} Smart {product} Pro",
    ],
    "Clothing": [
        "{brand} {product} - {variant}",
        "{brand} Premium {product}",
        "{brand} Classic {product}",
    ],
    "Sports": [
        "{brand} {product} for Training",
        "{brand} Pro {product}",
        "{brand} Running {product}",
    ],
}

PRODUCTS_PER_CATEGORY = {
    "Electronics": ["Phone", "Earbuds", "Speaker", "Watch", "Tablet", "Charger", "Case", "Power Bank"],
    "Clothing": ["T-Shirt", "Jeans", "Jacket", "Sneakers", "Dress", "Shirt", "Shorts", "Hoodie"],
    "Home & Kitchen": ["Mixer", "Kettle", "Pressure Cooker", "Fan", "Lamp", "Organizer", "Mat", "Set"],
    "Sports": ["Shoes", "Ball", "Racket", "Mat", "Bottle", "Bag", "Gloves", "Band"],
    "Books": ["Novel", "Guide", "Cookbook", "Manual", "Journal", "Dictionary", "Textbook", "Atlas"],
    "Beauty": ["Cream", "Lotion", "Shampoo", "Lipstick", "Serum", "Mask", "Kit", "Oil"],
    "Toys": ["Building Set", "Action Figure", "Board Game", "Puzzle", "Car", "Doll", "Gun", "Blocks"],
    "Automotive": ["Oil", "Cleaner", "Wiper", "Mat", "Air Freshener", "Cover", "Kit", "Polish"],
    "Garden": ["Mower", "Shears", "Pot", "Soil", "Sprinkler", "Gloves", "Hose", "Light"],
    "Health": ["Vitamins", "Protein", "Bandage", "Thermometer", "Supplement", "Drops", "Powder", "Spray"],
}

VARIANTS = ["Black", "White", "Blue", "Red", "Green", "Large", "Small", "Medium", "Pro", "Lite", "Max"]

PRICES = {
    "Electronics": (500, 25000),
    "Clothing": (200, 3000),
    "Home & Kitchen": (300, 5000),
    "Sports": (200, 4000),
    "Books": (100, 800),
    "Beauty": (100, 1500),
    "Toys": (150, 2000),
    "Automotive": (100, 3000),
    "Garden": (200, 4000),
    "Health": (100, 2000),
}


def _generate_products(n_products: int = 200, seed: int = 42) -> pd.DataFrame:
    """Generate a synthetic product catalogue."""
    rng = random.Random(seed)
    np_rng = np.random.RandomState(seed)

    products = []
    for i in range(n_products):
        category = rng.choice(CATEGORIES)
        brand = rng.choice(BRANDS[category])
        product_name = rng.choice(PRODUCTS_PER_CATEGORY[category])
        template = rng.choice(PRODUCT_TEMPLATES.get(category, ["{brand} {product} {variant}"]))
        variant = rng.choice(VARIANTS)
        title = template.format(brand=brand, product=product_name, variant=variant)

        price_range = PRICES[category]
        price = round(rng.uniform(*price_range), 2)

        rating = round(np_rng.uniform(2.5, 5.0), 1)
        description = f"{title} in {category}. High quality from {brand}. Price: Rs.{price}"

        products.append({
            "product_id": str(1000 + i),
            "title": title,
            "category": category,
            "brand": brand,
            "price": price,
            "description": description,
            "rating": rating,
            "properties": {"color": variant.lower()},
        })

    return pd.DataFrame(products)


def _generate_customer_profile(customer_id: str, rng: random.Random) -> dict:
    """Generate a synthetic customer profile with preferences."""
    pref_categories = rng.sample(CATEGORIES, k=rng.randint(2, 4))
    pref_brands = []
    for cat in pref_categories[:2]:
        pref_brands.extend(rng.sample(BRANDS[cat], k=2))

    category_affinity = {}
    for cat in CATEGORIES:
        if cat in pref_categories:
            category_affinity[cat] = round(rng.uniform(0.5, 1.0), 2)
        else:
            category_affinity[cat] = round(rng.uniform(0.0, 0.3), 2)

    return {
        "customer_id": customer_id,
        "category_affinity": category_affinity,
        "price_sensitivity": round(rng.uniform(0.2, 0.9), 2),
        "preferred_brands": pref_brands,
        "average_spend": round(rng.uniform(500, 3000), 2),
        "recent_categories": pref_categories[:3],
        "recent_products": [],
        "discovery_appetite": round(rng.uniform(0.1, 0.7), 2),
        "total_purchases": rng.randint(2, 30),
        "total_views": rng.randint(10, 100),
        "avg_rating": round(rng.uniform(3.0, 4.8), 1),
    }


def generate_interactions(
    n_customers: int = 100,
    n_products: int = 200,
    n_interactions: int = 2000,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, list[dict]]:
    """Generate synthetic interaction data, product catalogue, and customer profiles.

    Returns:
        Tuple of (interactions_df, products_df, customer_profiles).
    """
    rng = random.Random(seed)
    np_rng = np.random.RandomState(seed)

    products = _generate_products(n_products, seed)

    customer_ids = [str(10000 + i) for i in range(n_customers)]
    customer_profiles = [_generate_customer_profile(cid, rng) for cid in customer_ids]

    product_ids = products["product_id"].tolist()
    product_categories = dict(zip(products["product_id"], products["category"]))
    product_brands = dict(zip(products["product_id"], products["brand"]))

    event_types = ["view", "addtocart", "transaction", "like"]
    event_probs = [0.5, 0.2, 0.15, 0.15]

    interactions = []
    base_time = datetime(2024, 1, 1)

    for customer_id in customer_ids:
        profile = next(p for p in customer_profiles if p["customer_id"] == customer_id)
        pref_cats = set(profile["recent_categories"])
        pref_brands = set(profile["preferred_brands"])

        n_cust_interactions = max(5, int(n_interactions / n_customers * rng.uniform(0.5, 2.0)))

        for _ in range(n_cust_interactions):
            event_type = rng.choices(event_types, weights=event_probs, k=1)[0]

            if rng.random() < 0.7 and pref_cats:
                cat_candidates = [pid for pid in product_ids if product_categories.get(pid) in pref_cats]
                if cat_candidates:
                    product_id = rng.choice(cat_candidates)
                else:
                    product_id = rng.choice(product_ids)
            elif rng.random() < 0.5 and pref_brands:
                brand_candidates = [pid for pid in product_ids if product_brands.get(pid) in pref_brands]
                if brand_candidates:
                    product_id = rng.choice(brand_candidates)
                else:
                    product_id = rng.choice(product_ids)
            else:
                product_id = rng.choice(product_ids)

            days_offset = rng.randint(0, 365)
            hours_offset = rng.randint(0, 23)
            timestamp = base_time + timedelta(days=days_offset, hours=hours_offset)

            interactions.append({
                "customer_id": customer_id,
                "product_id": product_id,
                "event_type": event_type,
                "timestamp": timestamp.isoformat(),
            })

    interactions_df = pd.DataFrame(interactions)

    return interactions_df, products, customer_profiles


def generate_test_scenario() -> dict:
    """Generate a complete test scenario for end-to-end testing.

    Returns a dict with interactions, products, profiles, and a sample mission.
    """
    interactions, products, profiles = generate_interactions(
        n_customers=50,
        n_products=100,
        n_interactions=1000,
        seed=42,
    )

    mission = {
        "goal": "Weekend trip",
        "occasion": "Travel",
        "budget": 5000,
        "preferred_categories": ["Clothing", "Sports", "Electronics"],
        "excluded_brands": [],
        "excluded_categories": [],
        "discovery_level": 0.4,
        "urgency": "medium",
    }

    test_customer = profiles[0]

    return {
        "interactions": interactions,
        "products": products,
        "customer_profiles": profiles,
        "mission": mission,
        "test_customer": test_customer,
    }
