"""
RetailMind - Agentic AI Tool Layer
==================================

Member 4: Agentic AI / Orchestration

This file contains the tools used by the Agentic AI.

Current version:
    - Uses mock customer/product data
    - Works independently of other team members
    - Provides clean integration interfaces

Later:
    The mock implementations can be replaced by the actual
    team's database, recommendation model, product catalogue,
    ranking model, etc.

Tools:
    1. get_customer_profile()
    2. search_products()
    3. get_recommendations()
    4. rank_products()
    5. create_bundle()
    6. explain_recommendation()
    7. quality_check()
"""

from typing import Any, Dict, List, Optional
from itertools import combinations


# ============================================================
# MOCK PRODUCT CATALOGUE
# ============================================================

PRODUCT_CATALOGUE: List[Dict[str, Any]] = [
    {
        "id": "P001",
        "name": "Classic Casual Shirt",
        "category": "shirt",
        "style": "casual",
        "price": 1299,
        "rating": 4.4,
    },
    {
        "id": "P002",
        "name": "Straight Fit Jeans",
        "category": "jeans",
        "style": "casual",
        "price": 1799,
        "rating": 4.5,
    },
    {
        "id": "P003",
        "name": "Minimal Sneakers",
        "category": "footwear",
        "style": "casual",
        "price": 2499,
        "rating": 4.6,
    },
    {
        "id": "P004",
        "name": "Oversized Graphic Tee",
        "category": "tshirt",
        "style": "streetwear",
        "price": 899,
        "rating": 4.3,
    },
    {
        "id": "P005",
        "name": "Relaxed Cargo Pants",
        "category": "pants",
        "style": "casual",
        "price": 1599,
        "rating": 4.4,
    },
]


# ============================================================
# 1. CUSTOMER PROFILE TOOL
# ============================================================

def get_customer_profile(
    customer_id: str
) -> Dict[str, Any]:
    """
    Retrieve customer preferences.

    This is currently mock data.

    Integration point:
        Replace this implementation with the team's
        customer-profile/database module.
    """

    return {
        "customer_id": customer_id,

        "preferred_categories": [
            "shirt",
            "jeans",
            "pants",
            "footwear",
        ],

        "preferred_styles": [
            "casual",
            "minimal",
        ],

        "price_sensitivity": 0.65,

        "average_spend": 2100,

        "frequently_purchased": [
            "shirts",
            "jeans",
        ],
    }


# ============================================================
# 2. PRODUCT SEARCH TOOL
# ============================================================

def search_products(
    query: str = "",
    budget: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Search products from the catalogue.

    The current implementation uses the mock catalogue.

    The product catalogue can later be replaced by:
        - SQL database
        - MongoDB
        - vector database
        - product search API
    """

    query = (query or "").lower().strip()

    results = []

    for product in PRODUCT_CATALOGUE:

        searchable_text = " ".join(
            [
                str(product.get("name", "")),
                str(product.get("category", "")),
                str(product.get("style", "")),
            ]
        ).lower()

        # If query is empty, include everything.
        # Otherwise perform simple relevance matching.
        if query and query not in searchable_text:

            query_words = query.split()

            if not any(
                word in searchable_text
                for word in query_words
            ):
                continue

        # Product-level budget filter
        if (
            budget is not None
            and product["price"] > budget
        ):
            continue

        results.append(
            dict(product)
        )

    return results


# ============================================================
# 3. RECOMMENDATION TOOL
# ============================================================

def get_recommendations(
    customer_id: str,
    mission: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Retrieve candidate products for the shopping mission.

    Integration point:
        This function can later call the team's
        recommendation ML model.

    Example future integration:

        return recommend_products(
            customer_id,
            mission
        )
    """

    category = mission.get(
        "category",
        ""
    )

    budget = mission.get(
        "budget"
    )

    style = mission.get(
        "style"
    )

    # For outfit requests we need access to multiple
    # product categories, so we don't restrict the search
    # to the literal word "outfit".
    if category == "outfit":

        candidates = search_products(
            query="",
            budget=budget
        )

    else:

        candidates = search_products(
            query=category,
            budget=budget
        )

    # --------------------------------------------------------
    # Style relevance
    # --------------------------------------------------------

    if style:

        style_matches = [
            product
            for product in candidates
            if product.get("style") == style
        ]

        other_products = [
            product
            for product in candidates
            if product.get("style") != style
        ]

        candidates = (
            style_matches
            + other_products
        )

    return candidates


# ============================================================
# 4. RANKING TOOL
# ============================================================

def rank_products(
    products: List[Dict[str, Any]],
    mission: Dict[str, Any],
    profile: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Rank products using personalization signals.

    Ranking signals:
        - Style match
        - Preferred category
        - Customer preference
        - Product rating
        - Mission relevance
    """

    if not products:
        return []

    profile = profile or {}

    preferred_categories = set(
        profile.get(
            "preferred_categories",
            []
        )
    )

    preferred_styles = set(
        profile.get(
            "preferred_styles",
            []
        )
    )

    mission_style = mission.get(
        "style"
    )

    ranked = []

    for product in products:

        score = 0.0

        # ----------------------------------------------------
        # Product rating
        # ----------------------------------------------------

        rating = float(
            product.get(
                "rating",
                0
            )
        )

        score += rating * 10

        # ----------------------------------------------------
        # Mission style
        # ----------------------------------------------------

        if (
            mission_style
            and product.get("style")
            == mission_style
        ):
            score += 25

        # ----------------------------------------------------
        # Customer preferred style
        # ----------------------------------------------------

        if product.get(
            "style"
        ) in preferred_styles:
            score += 15

        # ----------------------------------------------------
        # Customer preferred category
        # ----------------------------------------------------

        if product.get(
            "category"
        ) in preferred_categories:
            score += 15

        # ----------------------------------------------------
        # Budget compatibility
        # ----------------------------------------------------

        budget = mission.get(
            "budget"
        )

        if (
            budget is not None
            and product.get("price", 0)
            <= budget
        ):
            score += 5

        ranked.append(
            {
                **product,
                "personalization_score": round(
                    score,
                    2
                ),
            }
        )

    ranked.sort(
        key=lambda item: item[
            "personalization_score"
        ],
        reverse=True,
    )

    return ranked


# ============================================================
# PRODUCT ROLE MAPPING
# ============================================================

PRODUCT_ROLES = {
    "shirt": "top",
    "tshirt": "top",
    "top": "top",

    "jeans": "bottom",
    "pants": "bottom",
    "shorts": "bottom",
    "skirt": "bottom",

    "footwear": "footwear",
    "shoes": "footwear",
    "sneakers": "footwear",
}


# ============================================================
# 5. INTELLIGENT BUNDLE TOOL
# ============================================================

def create_bundle(
    products: List[Dict[str, Any]],
    mission: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Build a meaningful bundle under the customer's budget.

    For an outfit request, the system tries to construct:

        TOP + BOTTOM + FOOTWEAR

    If the full combination cannot fit the budget:

        TOP + BOTTOM

    If that is impossible:

        best affordable individual item

    The algorithm evaluates combinations rather than simply
    selecting the highest-priced/highest-ranked product.

    This is important for agentic behaviour because the agent
    can detect a constraint failure and choose another plan.
    """

    if not products:
        return []

    budget = mission.get(
        "budget"
    )

    requires_bundle = mission.get(
        "requires_bundle",
        False
    )

    # --------------------------------------------------------
    # Simple recommendation request
    # --------------------------------------------------------

    if not requires_bundle:

        return products[:1]

    # --------------------------------------------------------
    # Outfit bundle
    # --------------------------------------------------------

    if mission.get(
        "category"
    ) == "outfit":

        # ----------------------------------------------------
        # Find the best product for every role
        # ----------------------------------------------------

        products_by_role: Dict[
            str,
            List[Dict[str, Any]]
        ] = {}

        for product in products:

            category = product.get(
                "category",
                ""
            ).lower()

            role = PRODUCT_ROLES.get(
                category
            )

            if not role:
                continue

            products_by_role.setdefault(
                role,
                []
            ).append(product)

        # ----------------------------------------------------
        # Sort each role by personalization
        # ----------------------------------------------------

        for role in products_by_role:

            products_by_role[role].sort(
                key=lambda product:
                product.get(
                    "personalization_score",
                    0
                ),
                reverse=True,
            )

        # ----------------------------------------------------
        # Generate candidate combinations
        # ----------------------------------------------------

        candidates = []

        role_groups = list(
            products_by_role.values()
        )

        flattened_products = [
            product
            for group in role_groups
            for product in group
        ]

        # Evaluate combinations of 3, 2 and 1 products.
        max_size = min(
            3,
            len(flattened_products)
        )

        for size in range(
            max_size,
            0,
            -1
        ):

            for combo in combinations(
                flattened_products,
                size
            ):

                categories = [
                    product.get(
                        "category"
                    )
                    for product in combo
                ]

                # No duplicate category in one bundle
                if len(categories) != len(
                    set(categories)
                ):
                    continue

                total_price = sum(
                    product.get(
                        "price",
                        0
                    )
                    for product in combo
                )

                # ------------------------------------------------
                # Budget constraint
                # ------------------------------------------------

                if (
                    budget is not None
                    and total_price > budget
                ):
                    continue

                roles = {
                    PRODUCT_ROLES.get(
                        product.get(
                            "category",
                            ""
                        ).lower()
                    )
                    for product in combo
                }

                roles.discard(None)

                personalization = sum(
                    product.get(
                        "personalization_score",
                        0
                    )
                    for product in combo
                )

                # ------------------------------------------------
                # Bundle score
                #
                # Diversity is more important than simply
                # selecting the most expensive products.
                # ------------------------------------------------

                role_score = len(roles) * 100

                personalization_score = (
                    personalization
                )

                budget_efficiency = 0

                if budget and total_price:

                    budget_efficiency = (
                        (budget - total_price)
                        / budget
                    ) * 10

                final_score = (
                    role_score
                    + personalization_score
                    + budget_efficiency
                )

                candidates.append(
                    {
                        "products": list(combo),
                        "score": final_score,
                        "roles": roles,
                        "total": total_price,
                    }
                )

            # If we found valid combinations of the
            # largest possible size, use them.
            if candidates:

                largest_size = max(
                    len(item["products"])
                    for item in candidates
                )

                candidates = [
                    item
                    for item in candidates
                    if len(
                        item["products"]
                    ) == largest_size
                ]

                break

        # ----------------------------------------------------
        # Select best candidate
        # ----------------------------------------------------

        if candidates:

            candidates.sort(
                key=lambda item:
                item["score"],
                reverse=True,
            )

            return candidates[0]["products"]

        return []

    # ========================================================
    # GENERAL BUNDLE
    # ========================================================

    bundle = []

    total_price = 0

    selected_categories = set()

    for product in products:

        category = product.get(
            "category"
        )

        price = product.get(
            "price",
            0
        )

        if category in selected_categories:
            continue

        if (
            budget is not None
            and total_price + price > budget
        ):
            continue

        bundle.append(
            product
        )

        selected_categories.add(
            category
        )

        total_price += price

    return bundle


# ============================================================
# 6. EXPLANATION TOOL
# ============================================================

def explain_recommendation(
    product: Dict[str, Any],
    mission: Dict[str, Any],
    profile: Dict[str, Any],
) -> str:
    """
    Generate a grounded explanation for a recommendation.
    """

    reasons = []

    mission_style = mission.get(
        "style"
    )

    budget = mission.get(
        "budget"
    )

    # --------------------------------------------------------
    # Style
    # --------------------------------------------------------

    if (
        mission_style
        and product.get("style")
        == mission_style
    ):

        reasons.append(
            f"matches your {mission_style} style"
        )

    # --------------------------------------------------------
    # Budget
    # --------------------------------------------------------

    if (
        budget is not None
        and product.get(
            "price",
            0
        ) <= budget
    ):

        reasons.append(
            "fits within your budget"
        )

    # --------------------------------------------------------
    # Preferred category
    # --------------------------------------------------------

    preferred_categories = profile.get(
        "preferred_categories",
        []
    )

    if product.get(
        "category"
    ) in preferred_categories:

        reasons.append(
            "matches your preferred categories"
        )

    # --------------------------------------------------------
    # Rating
    # --------------------------------------------------------

    if product.get(
        "rating",
        0
    ) >= 4.5:

        reasons.append(
            "has a strong customer rating"
        )

    # --------------------------------------------------------
    # Personalization score
    # --------------------------------------------------------

    personalization_score = product.get(
        "personalization_score"
    )

    if (
        personalization_score is not None
        and personalization_score >= 80
    ):

        reasons.append(
            "has a strong personalization match"
        )

    if not reasons:

        reasons.append(
            "matches your current shopping mission"
        )

    return (
        "Recommended because it "
        + ", ".join(reasons)
        + "."
    )


# ============================================================
# 7. QUALITY CHECK TOOL
# ============================================================

def quality_check(
    products: List[Dict[str, Any]],
    mission: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Validate recommendations before returning them.

    Checks:
        1. Products exist
        2. Products are within budget
        3. Results are relevant
        4. Bundle requirements can be satisfied
    """

    budget = mission.get(
        "budget"
    )

    has_products = (
        len(products) > 0
    )

    within_budget = True

    if budget is not None:

        within_budget = all(
            product.get(
                "price",
                0
            ) <= budget
            for product in products
        )

    relevant = has_products

    sufficient_results = (
        len(products) >= 1
    )

    passed = all(
        [
            has_products,
            within_budget,
            relevant,
            sufficient_results,
        ]
    )

    return {
        "has_products": has_products,
        "within_budget": within_budget,
        "relevant": relevant,
        "sufficient_results": sufficient_results,
        "passed": passed,
    }
