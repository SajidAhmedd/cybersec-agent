"""
Agent State Definition
The state object that flows through the LangGraph workflow
"""

from typing import TypedDict, Optional


class AgentState(TypedDict):
    """
    State for the conversation agent workflow.
    This state is passed between nodes in the LangGraph.
    """

    # Session identification
    session_id: str

    # Conversation
    messages: list[dict]  # Full conversation history (nodes return the updated list)
    current_phase: str

    # User's last message
    user_message: str

    # Extracted problem context (from Claude)
    problem_context: Optional[dict]

    # Security analysis (from Foundation-Sec)
    security_analysis: Optional[dict]

    # Matched experts
    matched_experts: list[dict]

    # Selected expert
    selected_expert_id: Optional[int]

    # Flags
    has_sufficient_context: bool
    extraction_attempts: int
    is_complete: bool

    # Response to send back
    response: str
