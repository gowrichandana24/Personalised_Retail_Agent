def calculate_diversity(products):
    """
    Calculate diversity of a product list
    based on unique categories.
    """

    if not products:
        return 0.0

    categories = {
        product.get("category", "unknown")
        for product in products
    }

    return round(
        len(categories) / len(products),
        4
    )


def diversify_products(products, limit=None):
    """
    Select products while avoiding repeated categories.
    """

    if not products:
        return []

    selected = []
    used_categories = set()

    for product in products:

        category = product.get(
            "category",
            "unknown"
        )

        if category not in used_categories:
            selected.append(product)
            used_categories.add(category)

        if limit and len(selected) >= limit:
            break

    # If we still need more products,
    # fill remaining positions by score.
    if limit and len(selected) < limit:

        selected_ids = {
            product.get("id")
            for product in selected
        }

        for product in products:

            if product.get("id") not in selected_ids:
                selected.append(product)

            if len(selected) >= limit:
                break

    return selected