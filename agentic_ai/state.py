from typing import TypedDict, List, Dict, Any


class RetailState(TypedDict, total=False):
    """
    Shared state maintained throughout the RetailMind
    Agentic AI workflow.
    """

    # -------------------------
    # USER INPUT
    # -------------------------
    user_query: str
    customer_id: str

    # -------------------------
    # SHOPPING MISSION
    # -------------------------
    mission: Dict[str, Any]
    budget: float
    discovery_mode: bool

    # -------------------------
    # CUSTOMER INFORMATION
    # -------------------------
    customer_profile: Dict[str, Any]

    # -------------------------
    # PRODUCT PIPELINE
    # -------------------------
    candidate_products: List[Dict[str, Any]]
    ranked_products: List[Dict[str, Any]]
    bundle: List[Dict[str, Any]]

    # -------------------------
    # EXPLANATION
    # -------------------------
    explanations: Dict[str, str]

    # -------------------------
    # AGENT CONTROL
    # -------------------------
    needs_replanning: bool

    # -------------------------
    # AGENT TRACE
    # -------------------------
    agent_trace: List[str]

    # -------------------------
    # FINAL OUTPUT
    # -------------------------
    final_response: str