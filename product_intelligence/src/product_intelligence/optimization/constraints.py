def filter_by_budget(products, budget):
    """
    Keep only products whose individual price
    does not exceed the user's budget.
    """
    return [
        product
        for product in products
        if product["price"] <= budget
    ]


def filter_excluded_brands(products, excluded_brands=None):
    """
    Remove products belonging to brands that
    the user has explicitly excluded.
    """

    if not excluded_brands:
        return products

    excluded = {
        brand.lower()
        for brand in excluded_brands
    }

    return [
        product
        for product in products
        if product.get("brand", "").lower() not in excluded
    ]