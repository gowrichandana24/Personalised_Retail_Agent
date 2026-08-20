"""Tests for the Customer Intelligence integration with the backend.

Verifies that:
1. get_digital_twin_for_customer() returns valid profiles
2. The digital twin contains expected fields
3. Cold-start customers get appropriate profiles
4. Known customers get profiles with interaction data
5. profile_from_digital_twin() correctly converts the twin
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.service import get_digital_twin_for_customer, profile_from_digital_twin
from recommendation_ml.schemas import CustomerProfile


class TestGetDigitalTwin:
    """Test get_digital_twin_for_customer function."""

    def test_known_customer_returns_profile(self):
        """seed-1 is in interactions.json and should return a profile."""
        twin = get_digital_twin_for_customer("seed-1")
        assert twin is not None
        assert isinstance(twin, dict)
        assert twin.get("visitorid") == "seed-1"

    def test_profile_has_required_fields(self):
        """The digital twin should have the expected fields."""
        twin = get_digital_twin_for_customer("seed-1")
        required_fields = [
            "visitorid",
            "primary_persona",
            "total_interactions",
            "total_views",
            "total_transactions",
        ]
        for field in required_fields:
            assert field in twin, f"Missing field: {field}"

    def test_known_customer_has_interactions(self):
        """seed-1 has 3 interactions in the dataset."""
        twin = get_digital_twin_for_customer("seed-1")
        assert twin["total_interactions"] >= 1

    def test_unknown_customer_returns_cold_start(self):
        """Unknown customer should get a cold-start profile."""
        twin = get_digital_twin_for_customer("UNKNOWN_CUSTOMER")
        assert twin is not None
        assert twin["visitorid"] == "UNKNOWN_CUSTOMER"
        assert twin["total_interactions"] == 0
        assert twin["primary_persona"] == "New / Unknown"
        assert twin["evidence_tier"] == "Cold / New"

    def test_all_known_customers(self):
        """All 4 seed customers should return profiles."""
        for customer_id in ["seed-1", "seed-2", "seed-3", "seed-4"]:
            twin = get_digital_twin_for_customer(customer_id)
            assert twin is not None
            assert twin["visitorid"] == customer_id


class TestProfileFromDigitalTwin:
    """Test profile_from_digital_twin conversion."""

    def test_conversion_with_real_twin(self):
        """A real digital twin should convert to a valid CustomerProfile."""
        twin = get_digital_twin_for_customer("seed-1")
        profile = profile_from_digital_twin("seed-1", twin)
        assert isinstance(profile, CustomerProfile)
        assert profile.customer_id == "seed-1"

    def test_conversion_with_cold_start_twin(self):
        """A cold-start twin should convert to a valid CustomerProfile."""
        twin = get_digital_twin_for_customer("UNKNOWN_CUSTOMER")
        profile = profile_from_digital_twin("UNKNOWN", twin)
        assert isinstance(profile, CustomerProfile)
        assert profile.customer_id == "UNKNOWN"

    def test_conversion_with_none_twin(self):
        """None twin should produce a default CustomerProfile."""
        profile = profile_from_digital_twin("test", None)
        assert isinstance(profile, CustomerProfile)
        assert profile.customer_id == "test"
        assert profile.total_purchases == 0


class TestEndToEndIntegration:
    """Test the full integration path."""

    def test_recommend_with_real_profile(self):
        """The recommend function should accept a real digital twin."""
        from backend.service import recommend
        twin = get_digital_twin_for_customer("seed-1")
        result = recommend(
            customer_id="seed-1",
            query="I need something for travel",
            digital_twin=twin,
            top_k=3,
        )
        assert result is not None
        assert "recommendations" in result
        assert "customer_profile" in result

    def test_recommend_with_cold_start_profile(self):
        """The recommend function should handle cold-start profiles."""
        from backend.service import recommend
        result = recommend(
            customer_id="NEW_USER",
            query="I need something for a party",
            digital_twin=None,
            top_k=3,
        )
        assert result is not None
        assert "recommendations" in result


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
