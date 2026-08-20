import re

from .schemas import ShoppingIntent


class FallbackIntentParser:

    def parse(self, message: str, context: dict | None = None) -> ShoppingIntent:

        # A follow-up correction should replace the earlier mission signals.
        text = re.split(r"\b(?:actually|instead|rather)\b", message.lower())[-1]

        context = context or {}
        category = context.get("category")
        subcategory = None
        occasion = context.get("occasion")
        budget = context.get("budget")

        preferences = []
        exclusions = []

        # -------------------------
        # OCCASION (contextual use-case)
        # -------------------------
        # Detect occasion BEFORE category so contextual keywords
        # like "beach", "party", "formal" are preserved even when
        # no specific product category is mentioned.

        if "beach" in text:
            occasion = "beach"
            preferences.append("outdoor")
            preferences.append("lightweight")

        elif "party" in text:
            occasion = "party"
            preferences.append("stylish")

        elif "college" in text or "campus" in text:
            occasion = "college"

        elif "wedding" in text:
            occasion = "wedding"

        elif "birthday" in text:
            occasion = "birthday"

        elif "gym" in text or "workout" in text:
            occasion = "gym"
            preferences.append("sporty")

        elif "travel" in text or "trip" in text or "vacation" in text:
            occasion = "travel"
            preferences.append("practical")

        elif "office" in text or "work" in text or "professional" in text:
            occasion = "office"

        elif "formal" in text:
            occasion = "formal"
            preferences.append("elegant")

        elif "casual" in text:
            occasion = "casual"

        elif "date" in text:
            occasion = "date"
            preferences.append("stylish")

        elif "festival" in text or "festive" in text:
            occasion = "festival"
            preferences.append("premium")

        # -------------------------
        # CATEGORY (specific product type)
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

        elif "attire" in text or "outfit" in text or "clothing" in text:
            category = "fashion"

        elif "gift" in text:
            category = "gifts"

        # -------------------------
        # BUDGET
        # -------------------------

        budget_patterns = [
            r"₹\s?(\d+(?:,\d+)*)",
            r"rs\.?\s?(\d+(?:,\d+)*)",
            r"(\d+(?:\.\d+)?)\s*k",
            r"(?:under|below|within|max|up\s*to)\s+(\d+(?:,\d+)*)",
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
            "fitness",
            "outdoor",
            "formal",
        ]

        if "walking" in text:
            preferences.append("walking")
        if "everyday" in text or "daily use" in text:
            preferences.append("everyday use")

        for preference in known_preferences:

            if preference in text and preference not in preferences:
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