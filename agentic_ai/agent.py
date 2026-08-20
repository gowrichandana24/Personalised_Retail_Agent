"""
RetailMind - Agentic AI Orchestrator
====================================

Member 4: Agentic AI

Flow:

USER
  ↓
Gemini Mission Understanding
  ↓
Supervisor
  ↓
Profile
  ↓
Recommendation
  ↓
Discovery (if required)
  ↓
Ranking
  ↓
Bundle (if required)
  ↓
Explanation
  ↓
Quality Check
  ↓
PASS → Final Response
FAIL → Replan → Recommendation
"""

# ============================================================
# IMPORTS
# ============================================================

from typing import Dict, Any, List
import json
import re

from langgraph.graph import StateGraph, END

try:
    # Package imports used by the integrated FastAPI backend.
    from .state import RetailState
    from .tools import (
        get_customer_profile,
        get_recommendations,
        rank_products,
        create_bundle,
        explain_recommendation,
        quality_check,
    )
    from .gemini_agent import understand_shopping_request
except ImportError:  # pragma: no cover - supports `python agent.py` too.
    from state import RetailState
    from tools import (
        get_customer_profile,
        get_recommendations,
        rank_products,
        create_bundle,
        explain_recommendation,
        quality_check,
    )
    from gemini_agent import understand_shopping_request


# ============================================================
# CONFIG
# ============================================================

DEFAULT_BUDGET = 5000
MAX_REPLAN_ATTEMPTS = 3
MAX_RECOMMENDATIONS = 5


# ============================================================
# 1. GEMINI + FALLBACK INTENT EXTRACTION
# ============================================================

def extract_mission(
    state: RetailState
) -> RetailState:

    query = state.get(
        "user_query",
        ""
    ).strip()

    state.setdefault(
        "agent_trace",
        []
    )

    # --------------------------------------------------------
    # TRY GEMINI
    # --------------------------------------------------------

    try:

        mission = understand_shopping_request(
            query
        )

        mission.setdefault(
            "category",
            "fashion"
        )

        mission.setdefault(
            "occasion",
            "general"
        )

        mission.setdefault(
            "style",
            "casual"
        )

        mission.setdefault(
            "budget",
            DEFAULT_BUDGET
        )

        mission.setdefault(
            "discovery",
            False
        )

        mission.setdefault(
            "requires_bundle",
            False
        )

        mission.setdefault(
            "user_preferences",
            []
        )

        mission.setdefault(
            "exclusions",
            []
        )

        mission.setdefault(
            "reasoning",
            "Mission understood by Gemini."
        )

        state["mission"] = mission

        state["budget"] = mission.get(
            "budget",
            DEFAULT_BUDGET
        )

        state["discovery_mode"] = mission.get(
            "discovery",
            False
        )

        state["agent_trace"].append(
            "Gemini: natural-language shopping mission understood"
        )

        return state

    except Exception as error:

        # ----------------------------------------------------
        # PRINT REAL GEMINI ERROR
        # ----------------------------------------------------

        print()
        print("=" * 60)
        print("[GEMINI ERROR]")
        print(
            "Error type:",
            type(error).__name__
        )
        print(
            "Error message:",
            str(error)
        )
        print("=" * 60)
        print()

        state["agent_trace"].append(
            "Gemini unavailable: deterministic fallback activated"
        )

        # ----------------------------------------------------
        # FALLBACK
        # ----------------------------------------------------

        mission = fallback_mission_parser(
            query
        )

        state["mission"] = mission

        state["budget"] = mission.get(
            "budget",
            DEFAULT_BUDGET
        )

        state["discovery_mode"] = mission.get(
            "discovery",
            False
        )

        return state


# ============================================================
# 2. FALLBACK MISSION PARSER
# ============================================================

def fallback_mission_parser(
    query: str
) -> Dict[str, Any]:

    text = query.lower()

    mission = {

        "category": "fashion",

        "occasion": "general",

        "style": "casual",

        "budget": DEFAULT_BUDGET,

        "discovery": False,

        "requires_bundle": False,

        "user_preferences": [],

        "exclusions": [],

        "reasoning":
            "Fallback rule-based mission extraction.",
    }

    # --------------------------------------------------------
    # CATEGORY
    # --------------------------------------------------------

    if any(
        word in text
        for word in [
            "outfit",
            "complete outfit",
            "complete look",
            "full look",
            "combination",
            "bundle",
            "set",
        ]
    ):

        mission["category"] = "outfit"

    elif any(
        word in text
        for word in [
            "shoe",
            "shoes",
            "sneaker",
            "footwear",
        ]
    ):

        mission["category"] = "footwear"

    elif "shirt" in text:

        mission["category"] = "shirt"

    elif any(
        word in text
        for word in [
            "jeans",
            "denim",
        ]
    ):

        mission["category"] = "jeans"

    elif any(
        word in text
        for word in [
            "tshirt",
            "t-shirt",
            "tee",
        ]
    ):

        mission["category"] = "tshirt"

    elif any(
        word in text
        for word in [
            "pants",
            "trousers",
            "cargo",
        ]
    ):

        mission["category"] = "pants"

    # --------------------------------------------------------
    # OCCASION
    # --------------------------------------------------------

    occasion_map = {

        "college": [
            "college",
            "campus",
            "class",
        ],

        "office": [
            "office",
            "work",
            "meeting",
            "professional",
        ],

        "travel": [
            "travel",
            "trip",
            "vacation",
            "holiday",
        ],

        "party": [
            "party",
            "celebration",
            "event",
        ],

        "wedding": [
            "wedding",
            "marriage",
        ],

        "date": [
            "date",
            "date night",
        ],
    }

    for occasion, keywords in occasion_map.items():

        if any(
            word in text
            for word in keywords
        ):

            mission["occasion"] = occasion

            break

    # --------------------------------------------------------
    # STYLE
    # --------------------------------------------------------

    style_map = {

        "formal": [
            "formal",
            "professional",
        ],

        "streetwear": [
            "streetwear",
            "street",
            "urban",
        ],

        "sportswear": [
            "sports",
            "sport",
            "gym",
            "workout",
            "athletic",
        ],

        "minimal": [
            "minimal",
            "simple",
            "clean",
        ],

        "casual": [
            "casual",
            "comfortable",
            "comfy",
            "everyday",
        ],

        "trendy": [
            "trendy",
            "fashionable",
            "stylish",
        ],
    }

    for style, keywords in style_map.items():

        if any(
            word in text
            for word in keywords
        ):

            mission["style"] = style

            break

    # --------------------------------------------------------
    # DISCOVERY
    # --------------------------------------------------------

    discovery_words = [

        "different",

        "unique",

        "new",

        "surprise",

        "discover",

        "experimental",

        "something else",

        "bored",

        "something unexpected",
    ]

    mission["discovery"] = any(
        word in text
        for word in discovery_words
    )

    # --------------------------------------------------------
    # BUNDLE
    # --------------------------------------------------------

    bundle_words = [

        "outfit",

        "complete outfit",

        "complete look",

        "full look",

        "combination",

        "bundle",

        "set",

        "kit",
    ]

    mission["requires_bundle"] = any(
        word in text
        for word in bundle_words
    )

    # --------------------------------------------------------
    # BUDGET
    # --------------------------------------------------------

    patterns = [

        r"₹\s*(\d+(?:,\d+)?)",

        r"rs\.?\s*(\d+(?:,\d+)?)",

        r"inr\s*(\d+(?:,\d+)?)",

        r"(?:under|below|within|budget)"
        r"\s*(?:₹|rs\.?|inr)?"
        r"\s*(\d+(?:,\d+)?)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            try:

                value = match.groups()[-1]

                mission["budget"] = float(
                    value.replace(",", "")
                )

                break

            except ValueError:

                pass

    return mission


# ============================================================
# 3. SUPERVISOR
# ============================================================

def supervisor(
    state: RetailState
) -> RetailState:

    mission = state.get(
        "mission",
        {}
    )

    actions = []

    # --------------------------------------------------------
    # PERSONALIZATION
    # --------------------------------------------------------

    actions.append(
        "profile"
    )

    # --------------------------------------------------------
    # PRODUCT DISCOVERY
    # --------------------------------------------------------

    actions.append(
        "recommendation"
    )

    # --------------------------------------------------------
    # DISCOVERY MODE
    # --------------------------------------------------------

    if mission.get(
        "discovery",
        False
    ):

        actions.append(
            "discovery"
        )

    # --------------------------------------------------------
    # RANKING
    # --------------------------------------------------------

    actions.append(
        "ranking"
    )

    # --------------------------------------------------------
    # BUNDLE
    # --------------------------------------------------------

    if mission.get(
        "requires_bundle",
        False
    ):

        actions.append(
            "bundle"
        )

    # --------------------------------------------------------
    # EXPLANATION
    # --------------------------------------------------------

    actions.append(
        "explanation"
    )

    # --------------------------------------------------------
    # QUALITY
    # --------------------------------------------------------

    actions.append(
        "quality_check"
    )

    state["selected_actions"] = actions

    state["agent_trace"].append(
        "Supervisor: selected workflow -> "
        + " → ".join(actions)
    )

    return state


# ============================================================
# 4. CUSTOMER PROFILE
# ============================================================

def profile_node(
    state: RetailState
) -> RetailState:

    customer_id = state.get(
        "customer_id",
        "DEMO_USER"
    )

    profile = get_customer_profile(
        customer_id
    )

    state["customer_profile"] = profile

    state["agent_trace"].append(
        "Profile Tool: customer preferences retrieved"
    )

    return state


# ============================================================
# 5. RECOMMENDATION
# ============================================================

def recommendation_node(
    state: RetailState
) -> RetailState:

    customer_id = state.get(
        "customer_id",
        "DEMO_USER"
    )

    mission = state.get(
        "mission",
        {}
    )

    products = get_recommendations(
        customer_id,
        mission
    )

    # --------------------------------------------------------
    # APPLY USER EXCLUSIONS
    # --------------------------------------------------------

    exclusions = [
        str(item).lower()
        for item in mission.get(
            "exclusions",
            []
        )
    ]

    if exclusions:

        filtered_products = []

        for product in products:

            product_text = " ".join(
                [
                    str(
                        product.get(
                            "name",
                            ""
                        )
                    ),

                    str(
                        product.get(
                            "category",
                            ""
                        )
                    ),

                    str(
                        product.get(
                            "style",
                            ""
                        )
                    ),
                ]
            ).lower()

            excluded = any(
                exclusion in product_text
                for exclusion in exclusions
            )

            if not excluded:

                filtered_products.append(
                    product
                )

        products = filtered_products

        state["agent_trace"].append(
            "Recommendation Tool: user exclusions applied"
        )

    state["candidate_products"] = products

    state["agent_trace"].append(
        "Recommendation Tool: "
        f"{len(products)} candidates retrieved"
    )

    return state


# ============================================================
# 6. RANKING
# ============================================================

def ranking_node(
    state: RetailState
) -> RetailState:

    products = state.get(
        "candidate_products",
        []
    )

    mission = state.get(
        "mission",
        {}
    )

    profile = state.get(
        "customer_profile",
        {}
    )

    ranked = rank_products(
        products,
        mission,
        profile
    )

    # --------------------------------------------------------
    # DISCOVERY MODE
    # --------------------------------------------------------

    if mission.get(
        "discovery",
        False
    ):

        ranked = discovery_ranking(
            ranked,
            profile
        )

        state["agent_trace"].append(
            "Discovery Mode: alternative styles prioritized"
        )

    state["ranked_products"] = ranked[
        :MAX_RECOMMENDATIONS
    ]

    state["agent_trace"].append(
        "Ranking Tool: personalized ranking completed"
    )

    return state


# ============================================================
# 7. DISCOVERY RANKING
# ============================================================

def discovery_ranking(
    products: List[Dict[str, Any]],
    profile: Dict[str, Any]
) -> List[Dict[str, Any]]:

    preferred_styles = set(
        profile.get(
            "preferred_styles",
            []
        )
    )

    def discovery_score(
        product: Dict[str, Any]
    ):

        base = float(
            product.get(
                "personalization_score",
                0
            )
        )

        style = product.get(
            "style",
            ""
        )

        # Encourage new styles while retaining
        # personalization.

        if style not in preferred_styles:

            base += 12

        return base

    return sorted(
        products,
        key=discovery_score,
        reverse=True
    )


# ============================================================
# 8. BUNDLE
# ============================================================

def bundle_node(
    state: RetailState
) -> RetailState:

    mission = state.get(
        "mission",
        {}
    )

    # --------------------------------------------------------
    # NO BUNDLE REQUIRED
    # --------------------------------------------------------

    if not mission.get(
        "requires_bundle",
        False
    ):

        state["bundle"] = []

        state["bundle_total"] = 0

        state["agent_trace"].append(
            "Bundle Tool: skipped - bundle not required"
        )

        return state

    # --------------------------------------------------------
    # CREATE BUNDLE
    # --------------------------------------------------------

    products = state.get(
        "ranked_products",
        []
    )

    bundle = create_bundle(
        products,
        mission
    )

    state["bundle"] = bundle

    total = sum(
        float(
            product.get(
                "price",
                0
            )
        )
        for product in bundle
    )

    # IMPORTANT:
    # Store the total in state.

    state["bundle_total"] = total

    state["agent_trace"].append(
        "Bundle Tool: "
        f"{len(bundle)} products selected "
        f"(total ₹{total:.0f})"
    )

    return state


# ============================================================
# 9. EXPLANATION
# ============================================================

def explanation_node(
    state: RetailState
) -> RetailState:

    products = state.get(
        "ranked_products",
        []
    )

    mission = state.get(
        "mission",
        {}
    )

    profile = state.get(
        "customer_profile",
        {}
    )

    explanations = {}

    for product in products:

        product_id = product.get(
            "id",
            product.get(
                "name",
                "product"
            )
        )

        explanations[
            product_id
        ] = explain_recommendation(
            product,
            mission,
            profile
        )

    state["explanations"] = explanations

    state["agent_trace"].append(
        "Explanation Tool: recommendation reasons generated"
    )

    return state


# ============================================================
# 10. QUALITY CHECK
# ============================================================

def quality_node(
    state: RetailState
) -> RetailState:

    products = state.get(
        "ranked_products",
        []
    )

    mission = state.get(
        "mission",
        {}
    )

    # --------------------------------------------------------
    # RUN EXISTING QUALITY CHECK
    # --------------------------------------------------------

    quality = quality_check(
        products,
        mission
    )

    # Make sure we always have a dictionary.

    if not isinstance(
        quality,
        dict
    ):

        quality = {
            "passed": bool(quality)
        }

    # --------------------------------------------------------
    # PRODUCT CHECK
    # --------------------------------------------------------

    if not products:

        quality["passed"] = False

        quality["products_available"] = False

    else:

        quality["products_available"] = True

    # --------------------------------------------------------
    # BUNDLE CHECK
    # --------------------------------------------------------

    if mission.get(
        "requires_bundle",
        False
    ):

        bundle = state.get(
            "bundle",
            []
        )

        if not bundle:

            quality["passed"] = False

            quality["bundle_valid"] = False

        else:

            quality["bundle_valid"] = True

    else:

        quality["bundle_valid"] = True

    # --------------------------------------------------------
    # BUDGET CHECK
    # --------------------------------------------------------

    budget = float(
        mission.get(
            "budget",
            DEFAULT_BUDGET
        )
    )

    ranked_products = state.get(
        "ranked_products",
        []
    )

    budget_violations = [

        product

        for product in ranked_products

        if float(
            product.get(
                "price",
                0
            )
        ) > budget
    ]

    quality["budget_valid"] = (
        len(budget_violations) == 0
    )

    if budget_violations:

        quality["passed"] = False

    # --------------------------------------------------------
    # STORE QUALITY
    # --------------------------------------------------------

    state["quality_result"] = quality

    state["needs_replanning"] = not quality.get(
        "passed",
        False
    )

    if quality.get(
        "passed",
        False
    ):

        state["agent_trace"].append(
            "Quality Check: PASSED"
        )

    else:

        state["agent_trace"].append(
            "Quality Check: FAILED - replanning required"
        )

    return state


# ============================================================
# 11. REPLAN
# ============================================================

def replan(
    state: RetailState
) -> RetailState:

    count = state.get(
        "replan_count",
        0
    )

    count += 1

    state["replan_count"] = count

    mission = dict(
        state.get(
            "mission",
            {}
        )
    )

    # --------------------------------------------------------
    # REPLAN 1
    # --------------------------------------------------------

    if count == 1:

        state["agent_trace"].append(
            "Replan 1: optimizing for direct relevance"
        )

        mission["discovery"] = False

    # --------------------------------------------------------
    # REPLAN 2
    # --------------------------------------------------------

    elif count == 2:

        state["agent_trace"].append(
            "Replan 2: optimizing for budget feasibility"
        )

        mission["discovery"] = False

        # Reduce budget slightly only if there
        # is no explicit user budget.
        #
        # We do NOT overwrite an explicit budget.

    # --------------------------------------------------------
    # REPLAN 3
    # --------------------------------------------------------

    elif count == 3:

        state["agent_trace"].append(
            "Replan 3: returning best feasible result"
        )

        mission["discovery"] = False

    state["mission"] = mission

    state["needs_replanning"] = False

    return state


# ============================================================
# 12. QUALITY ROUTER
# ============================================================

def quality_router(
    state: RetailState
) -> str:

    needs_replanning = state.get(
        "needs_replanning",
        False
    )

    count = state.get(
        "replan_count",
        0
    )

    if (
        needs_replanning
        and count < MAX_REPLAN_ATTEMPTS
    ):

        return "replan"

    return "finish"


# ============================================================
# 13. FINAL RESPONSE
# ============================================================

def final_response(
    state: RetailState
) -> RetailState:

    # --------------------------------------------------------
    # Get final values directly from state.
    # --------------------------------------------------------

    bundle = state.get(
        "bundle",
        []
    )

    # Recalculate as a safety measure.

    bundle_total = sum(
        float(
            product.get(
                "price",
                0
            )
        )
        for product in bundle
    )

    quality = state.get(
        "quality_result",
        {}
    )

    # --------------------------------------------------------
    # FINAL RESPONSE
    # --------------------------------------------------------

    response = {

        "customer_id": state.get(
            "customer_id",
            "DEMO_USER"
        ),

        "query": state.get(
            "user_query",
            ""
        ),

        "mission": state.get(
            "mission",
            {}
        ),

        "recommendations": state.get(
            "ranked_products",
            []
        ),

        "bundle": bundle,

        "bundle_total": bundle_total,

        "explanations": state.get(
            "explanations",
            {}
        ),

        "quality": quality,

        "agent_trace": state.get(
            "agent_trace",
            []
        ),
    }

    state["final_response"] = response

    return state


# ============================================================
# 14. BUILD LANGGRAPH
# ============================================================

def build_agent():

    workflow = StateGraph(
        RetailState
    )

    # --------------------------------------------------------
    # NODES
    # --------------------------------------------------------

    workflow.add_node(
        "intent",
        extract_mission
    )

    workflow.add_node(
        "supervisor",
        supervisor
    )

    workflow.add_node(
        "profile",
        profile_node
    )

    workflow.add_node(
        "recommendation",
        recommendation_node
    )

    workflow.add_node(
        "ranking",
        ranking_node
    )

    workflow.add_node(
        "bundle",
        bundle_node
    )

    workflow.add_node(
        "explanation",
        explanation_node
    )

    workflow.add_node(
        "quality",
        quality_node
    )

    workflow.add_node(
        "replan",
        replan
    )

    workflow.add_node(
        "final",
        final_response
    )

    # --------------------------------------------------------
    # ENTRY
    # --------------------------------------------------------

    workflow.set_entry_point(
        "intent"
    )

    # --------------------------------------------------------
    # MAIN PIPELINE
    # --------------------------------------------------------

    workflow.add_edge(
        "intent",
        "supervisor"
    )

    workflow.add_edge(
        "supervisor",
        "profile"
    )

    workflow.add_edge(
        "profile",
        "recommendation"
    )

    workflow.add_edge(
        "recommendation",
        "ranking"
    )

    workflow.add_edge(
        "ranking",
        "bundle"
    )

    workflow.add_edge(
        "bundle",
        "explanation"
    )

    workflow.add_edge(
        "explanation",
        "quality"
    )

    # --------------------------------------------------------
    # QUALITY ROUTER
    # --------------------------------------------------------

    workflow.add_conditional_edges(

        "quality",

        quality_router,

        {
            "replan": "replan",

            "finish": "final",
        }
    )

    # --------------------------------------------------------
    # REPLAN LOOP
    # --------------------------------------------------------

    workflow.add_edge(
        "replan",
        "recommendation"
    )

    # --------------------------------------------------------
    # END
    # --------------------------------------------------------

    workflow.add_edge(
        "final",
        END
    )

    return workflow.compile()


# ============================================================
# 15. PUBLIC FUNCTION
# ============================================================

def run_agent(
    user_query: str,
    customer_id: str = "DEMO_USER"
) -> Dict[str, Any]:
    """
    Public interface for the Agentic AI system.

    The rest of the team only needs to call:

        run_agent(
            user_query,
            customer_id
        )
    """

    agent = build_agent()

    initial_state: RetailState = {

        "user_query": user_query,

        "customer_id": customer_id,

        "agent_trace": [],

        "replan_count": 0,

        "needs_replanning": False,
    }

    result = agent.invoke(
        initial_state
    )

    return result


# ============================================================
# 16. LOCAL TEST
# ============================================================

if __name__ == "__main__":

    test_query = (
        "I need a casual outfit under ₹3000. "
        "I want something a little different."
    )

    print()
    print("=" * 60)
    print("RETAILMIND AGENTIC AI")
    print("=" * 60)
    print()

    result = run_agent(
        test_query,
        "C1024"
    )

    final = result.get(
        "final_response",
        result
    )

    print(
        json.dumps(
            final,
            indent=2,
            ensure_ascii=False
        )
    )

    print()
    print("=" * 60)
    print("AGENT EXECUTION COMPLETE")
    print("=" * 60)
