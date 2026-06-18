"""
LangGraph Conversation Workflow
Main orchestration of the multi-agent conversation flow
"""

from typing import Literal
from langgraph.graph import StateGraph, END

from .states import AgentState
from .nodes import (
    greeting_node,
    gathering_node,
    extraction_node,
    security_analysis_node,
    matching_node,
    presentation_node,
    selection_node,
    handoff_node,
    conversation_node,
)


def should_continue_gathering(state: AgentState) -> Literal["gather_more", "analyze"]:
    """
    Decide whether to continue gathering info or proceed to analysis.
    """
    has_sufficient = state.get("has_sufficient_context", False)
    attempts = state.get("extraction_attempts", 0)

    # If we have enough context, proceed
    if has_sufficient:
        return "analyze"

    # If we've tried too many times, proceed anyway
    if attempts >= 5:
        return "analyze"

    # Otherwise, keep gathering
    return "gather_more"


def should_continue_selecting(state: AgentState) -> Literal["need_selection", "handoff"]:
    """
    Check if user has made a valid selection.
    """
    selected_id = state.get("selected_expert_id")

    if selected_id is not None:
        return "handoff"

    return "need_selection"


def route_by_phase(state: AgentState) -> str:
    """
    Route to appropriate node based on current phase.
    Used for handling incoming messages at different conversation stages.
    """
    phase = state.get("current_phase", "greeting")

    routing = {
        "greeting": "greeting",
        "gathering": "gathering",
        "extracting": "extraction",
        "analyzing": "security_analysis",
        "matching": "matching",
        "presenting": "selection",
        "selecting": "selection",
        "handoff": "handoff",
        "complete": "end"
    }

    return routing.get(phase, "greeting")


def create_chat_workflow() -> StateGraph:
    """
    Create the main conversation workflow graph.

    Flow:
    1. GREETING → First interaction, welcome user
    2. GATHERING → Ask questions, understand problem
    3. EXTRACTION → Convert conversation to structured context
    4. (Loop back to GATHERING if not enough context)
    5. SECURITY_ANALYSIS → Analyze threat with Foundation-Sec
    6. MATCHING → Find experts in Neo4j
    7. PRESENTATION → Present experts to user
    8. SELECTION → Handle user's choice
    9. HANDOFF → Connect user with expert
    """

    # Create the graph
    workflow = StateGraph(AgentState)

    # Add all nodes
    workflow.add_node("greeting", greeting_node)
    workflow.add_node("gathering", gathering_node)
    workflow.add_node("extraction", extraction_node)
    workflow.add_node("security_analysis", security_analysis_node)
    workflow.add_node("matching", matching_node)
    workflow.add_node("presentation", presentation_node)
    workflow.add_node("selection", selection_node)
    workflow.add_node("handoff", handoff_node)

    # Set entry point
    workflow.set_entry_point("greeting")

    # Define edges

    # Greeting → Gathering
    workflow.add_edge("greeting", "gathering")

    # Gathering → Extraction (always extract after gathering)
    workflow.add_edge("gathering", "extraction")

    # Extraction → Conditional (gather more or analyze)
    workflow.add_conditional_edges(
        "extraction",
        should_continue_gathering,
        {
            "gather_more": "gathering",
            "analyze": "security_analysis"
        }
    )

    # Security Analysis → Matching
    workflow.add_edge("security_analysis", "matching")

    # Matching → Presentation
    workflow.add_edge("matching", "presentation")

    # Presentation → Selection (wait for user input)
    workflow.add_edge("presentation", "selection")

    # Selection → Conditional (need selection or handoff)
    workflow.add_conditional_edges(
        "selection",
        should_continue_selecting,
        {
            "need_selection": "selection",
            "handoff": "handoff"
        }
    )

    # Handoff → End
    workflow.add_edge("handoff", END)

    return workflow


class ChatWorkflow:
    """
    Wrapper class for managing chat workflow instances.
    Handles state management and conversation continuity.
    """

    def __init__(self):
        self.workflow = create_chat_workflow()
        self.app = self.workflow.compile()
        self.sessions: dict[str, AgentState] = {}

    def get_initial_state(self, session_id: str, user_message: str) -> AgentState:
        """Create initial state for a new conversation"""
        return {
            "session_id": session_id,
            "messages": [],
            "current_phase": "greeting",
            "user_message": user_message,
            "problem_context": None,
            "security_analysis": None,
            "matched_experts": [],
            "selected_expert_id": None,
            "has_sufficient_context": False,
            "extraction_attempts": 0,
            "is_complete": False,
            "response": ""
        }

    def chat(self, session_id: str, user_message: str) -> dict:
        """
        Process a user message and return a response.
        Runs ONE step of the workflow per call.

        Args:
            session_id: Unique session identifier
            user_message: User's message

        Returns:
            Dict with response and state info
        """

        # Get or create session state
        if session_id in self.sessions:
            state = self.sessions[session_id]
            state["user_message"] = user_message
            # Add user message to history
            state["messages"] = state.get("messages", []) + [
                {"role": "user", "content": user_message}
            ]
        else:
            state = self.get_initial_state(session_id, user_message)

        # Determine which node to run based on phase
        current_phase = state.get("current_phase", "greeting")
        print(f"[WORKFLOW] Session {session_id[:8]}... Phase: {current_phase}")

        # Run ONE step based on current phase
        if current_phase == "greeting":
            # First message - greet and start gathering
            result = greeting_node(state)

        elif current_phase == "gathering":
            # Continue gathering info
            result = gathering_node(state)
            result = extraction_node(result)

            # Check if we have enough context
            # Need: sufficient context AND at least 2 gathering exchanges
            # OR: at least 5 gathering exchanges (fallback to prevent endless loop)
            attempts = result.get("extraction_attempts", 0)
            has_context = result.get("has_sufficient_context", False)

            if (has_context and attempts >= 2) or attempts >= 5:
                # Move to security analysis and expert matching
                print(f"[WORKFLOW] Moving to expert matching (attempts: {attempts}, has_context: {has_context})")
                result = security_analysis_node(result)
                result = matching_node(result)
                result = presentation_node(result)
            else:
                print(f"[WORKFLOW] Continuing gathering (attempts: {attempts}, has_context: {has_context})")

        elif current_phase in ["presenting", "selecting"]:
            # User is selecting an expert
            result = selection_node(state)
            if result.get("selected_expert_id") is not None:
                result = handoff_node(result)

        elif current_phase in ["complete", "conversation"]:
            # Free-form conversation after expert handoff
            # Don't go back to expert matching - just chat
            result = conversation_node(state)

        else:
            # Default: try gathering
            result = gathering_node(state)

        # Store updated state
        self.sessions[session_id] = result
        print(f"[WORKFLOW] New phase: {result.get('current_phase')}")

        # Return response
        # Only include experts when in presenting phase (not after handoff/conversation)
        current_result_phase = result.get("current_phase", "unknown")
        include_experts = current_result_phase == "presenting" and not result.get("is_complete", False)

        return {
            "session_id": session_id,
            "response": result.get("response", "I'm not sure how to respond. Can you tell me more?"),
            "phase": current_result_phase,
            "is_complete": result.get("is_complete", False),
            "experts": result.get("matched_experts") if include_experts else None
        }

    def reset_session(self, session_id: str):
        """Reset a session to start fresh"""
        if session_id in self.sessions:
            del self.sessions[session_id]


# Singleton instance
_chat_workflow: ChatWorkflow | None = None


def get_chat_workflow() -> ChatWorkflow:
    """Get or create chat workflow instance"""
    global _chat_workflow
    if _chat_workflow is None:
        _chat_workflow = ChatWorkflow()
    return _chat_workflow
