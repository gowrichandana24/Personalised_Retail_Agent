import re

from .schemas import ShoppingIntent


class FallbackIntentParser:

    def parse(self, message: str) -> ShoppingIntent:

        text = message.lower()

        category = None
        subcategory = None
        occasion = None
        budget = None

        preferences = []
        exclusions = []

        # -------------------------
        # CATEGORY
        # -------------------------

        if "running shoe" in text:
            category = "footwear"
            subcategory = "running shoes"

        elif "shoe" in text or "sneaker" in text:
            category = "footwear"

        elif "laptop" in text:
            category = "electronics"
            subcategory = "laptop"

        elif "phone" in text or "smartphone" in text:
            category = "electronics"
            subcategory = "smartphone"

        elif "dress" in text:
            category = "fashion"
            subcategory = "dress"

        elif "jacket" in text:
            category = "fashion"
            subcategory = "jacket"

        elif "shirt" in text:
            category = "fashion"
            subcategory = "shirt"

        elif "gift" in text:
            category = "gifts"

        # -------------------------
        # OCCASION
        # -------------------------

        if "birthday" in text:
            occasion = "birthday"

        elif "wedding" in text:
            occasion = "wedding"

        elif "college" in text:
            occasion = "college"

        elif "gym" in text:
            occasion = "gym"

        elif "travel" in text or "trip" in text:
            occasion = "travel"

        # -------------------------
        # BUDGET
        # -------------------------

        budget_patterns = [
            r"₹\s?(\d+(?:,\d+)*)",
            r"rs\.?\s?(\d+(?:,\d+)*)",
            r"(\d+(?:\.\d+)?)\s*k"
        ]

        for pattern in budget_patterns:

            match = re.search(pattern, text)

            if match:

                value = match.group(1)
                value = value.replace(",", "")

                budget = float(value)

                if "k" in match.group(0):
                    budget *= 1000

                break

        # -------------------------
        # PREFERENCES
        # -------------------------

        known_preferences = [
            "comfortable",
            "stylish",
            "lightweight",
            "premium",
            "elegant",
            "casual",
            "sporty",
            "minimal",
            "practical",
            "fitness"
        ]

        for preference in known_preferences:

            if preference in text:
                preferences.append(preference)

        # -------------------------
        # EXCLUSIONS
        # -------------------------

        known_exclusions = [
            "flashy",
            "expensive",
            "nike",
            "adidas",
            "puma",
            "reebok"
        ]

        for exclusion in known_exclusions:

            if (
                f"don't want {exclusion}" in text
                or f"do not want {exclusion}" in text
                or f"avoid {exclusion}" in text
                or f"not {exclusion}" in text
            ):
                exclusions.append(exclusion)

        # -------------------------
        # DISCOVERY LEVEL
        # -------------------------

        discovery_level = 0.5

        discovery_phrases = [
            "something different",
            "something new",
            "unique",
            "unusual",
            "surprise me",
            "try something new"
        ]

        if any(
            phrase in text
            for phrase in discovery_phrases
        ):
            discovery_level = 0.8

        familiar_phrases = [
            "something similar",
            "same style",
            "usual",
            "safe choice"
        ]

        if any(
            phrase in text
            for phrase in familiar_phrases
        ):
            discovery_level = 0.2

        # -------------------------
        # URGENCY
        # -------------------------

        urgency = None

        if any(
            word in text
            for word in [
                "urgent",
                "today",
                "immediately",
                "asap"
            ]
        ):
            urgency = "high"

        elif any(
            word in text
            for word in [
                "soon",
                "this week"
            ]
        ):
            urgency = "medium"

        # -------------------------
        # RETURN STRUCTURED INTENT
        # -------------------------

        return ShoppingIntent(
            goal=message,
            category=category,
            subcategory=subcategory,
            occasion=occasion,
            budget=budget,
            preferences=preferences,
            exclusions=exclusions,
            urgency=urgency,
            discovery_level=discovery_level,
            confidence=0.65
        )