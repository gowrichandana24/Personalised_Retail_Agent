from dotenv import load_dotenv

from intent.intent_agent import IntentAgent


load_dotenv()


agent = IntentAgent()


queries = [

    "I need running shoes under ₹5000 for college. "
    "They should be comfortable but not flashy.",

    "I need a birthday gift for my sister around ₹2000. "
    "She loves fitness and I want something unique.",

    "I'm going on a trip and need something practical "
    "under 3000.",

    "I want something similar to what I usually buy.",

    "I don't want Nike.",

    "Surprise me with something different."
]


for query in queries:

    print("\n" + "=" * 70)

    print("CUSTOMER:")
    print(query)

    print("\nINTENT:")

    result = agent.analyze(query)

    print(result.model_dump_json(indent=2))