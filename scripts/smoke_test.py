"""Quick local validation for the complete RetailMind integration pipeline."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.service import customer_profile_from_events, recommend, record_feedback


def main() -> None:
    profile = customer_profile_from_events(
        customer_id="42",
        events=[
            {"timestamp": 1720000000000, "visitorid": 42, "event": "view", "itemid": 3},
            {"timestamp": 1720001000000, "visitorid": 42, "event": "addtocart", "itemid": 3},
        ],
        item_categories=[
            {"timestamp": 1719990000000, "itemid": 3, "categoryid": 101},
        ],
    )
    result = recommend(
        customer_id="42",
        query="I need casual shoes under ₹3000",
        digital_twin=profile,
        budget=3000,
        top_k=3,
    )
    assert result["recommendations"], "expected at least one recommendation"
    assert "Product Intelligence" in result["pipeline"]

    top_product = result["recommendations"][0]["product_id"]
    feedback = record_feedback("42", top_product, "like")
    assert feedback["status"] == "recorded"

    print("Smoke test passed")
    print("Top product:", top_product)
    print("Pipeline:", " -> ".join(result["pipeline"]))


if __name__ == "__main__":
    main()
