from .fallback_parser import FallbackIntentParser
from .schemas import ShoppingIntent


class IntentAgent:

    def __init__(self):

        self.fallback_parser = FallbackIntentParser()
        self.gemini_parser = None

        try:

            from .gemini_parser import GeminiIntentParser

            self.gemini_parser = GeminiIntentParser()

            print("✓ Gemini Intent Parser loaded")

        except Exception as error:

            print("⚠ Gemini unavailable.")
            print(f"Reason: {error}")
            print("✓ Local fallback parser enabled")

    def analyze(self, message: str) -> ShoppingIntent:

        # Try Gemini first
        if self.gemini_parser:

            try:

                result = self.gemini_parser.parse(message)

                print("✓ Intent extracted using Gemini")

                return result

            except Exception as error:

                print("⚠ Gemini failed.")
                print(f"Reason: {error}")
                print("→ Switching to fallback parser")

        # Use local fallback
        result = self.fallback_parser.parse(message)

        print("✓ Intent extracted using local parser")

        return result