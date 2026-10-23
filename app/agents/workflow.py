"""
LangGraph Conversation Workflow
Main orchestration of the multi-agent conversation flow
"""

from typing import Literal
from langgraph.graph import StateGraph, END

from .states import AgentState
from app.db.conversations import save_conversation
from app.schemas.expert import public_expert
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


def route_by_phase(state: AgentState) -> str:
    """
    Entry router: pick the node that handles the user's message
    based on the conversation's current phase.
    """
    phase = state.get("current_phase", "greeting")

    routing = {
        "greeting": "greeting",
        "presenting": "selection",
        "selecting": "selection",
        "handoff": "handoff",
        "complete": "conversation",
        "conversation": "conversation",
    }

    # gathering / extracting / anything else -> extract what the user just told us
    return routing.get(phase, "extraction")


def ready_for_matching(state: AgentState) -> Literal["analyze", "ask_more"]:
    """
    Decide whether we know enough to analyze the threat and match experts.
    Need sufficient context AND at least 2 gathering exchanges,
    or at least 5 exchanges (fallback to prevent an endless loop).
    """
    attempts = state.get("extraction_attempts", 0)
    has_context = state.get("has_sufficient_context", False)

    if (has_context and attempts >= 2) or attempts >= 5:
        print(f"[WORKFLOW] Moving to expert matching (attempts: {attempts}, has_context: {has_context})")
        return "analyze"

    print(f"[WORKFLOW] Continuing gathering (attempts: {attempts}, has_context: {has_context})")
    return "ask_more"


def expert_selected(state: AgentState) -> Literal["handoff", "wait_for_user"]:
    """Check whether the selection node identified an expert"""
    if state.get("current_phase") == "handoff" and state.get("selected_expert_id") is not None:
        return "handoff"
    return "wait_for_user"


def create_chat_workflow() -> StateGraph:
    """
    Create the conversation workflow graph.

    The graph runs once per user message: it enters at the node for the
    current phase and runs until the assistant needs the user's next reply.

    Flow:
    1. GREETING → First interaction, welcome user
    2. EXTRACTION → Convert the conversation so far to structured context
    3. GATHERING → If context is still missing, ask about it and wait for the answer
    4. SECURITY_ANALYSIS → Analyze threat with Foundation-Sec
    5. MATCHING → Find experts in Neo4j
    6. PRESENTATION → Present experts to user
    7. SELECTION → Handle user's choice
    8. HANDOFF → Connect user with expert
    9. CONVERSATION → Free-form follow-up after the handoff
    """

    # Create the graph
    workflow = StateGraph(AgentState)

    # Add all nodes
    workflow.add_node("greeting", greeting_node)
    workflow.add_node("gathering", gathering_node)
    workflow.add_node("extraction", extraction_node)
    workflow.add_node("analyze_security", security_analysis_node)
    workflow.add_node("matching", matching_node)
    workflow.add_node("presentation", presentation_node)
    workflow.add_node("selection", selection_node)
    workflow.add_node("handoff", handoff_node)
    workflow.add_node("conversation", conversation_node)

    # Each user message enters at the node for the current phase
    workflow.set_conditional_entry_point(
        route_by_phase,
        {
            "greeting": "greeting",
            "extraction": "extraction",
            "selection": "selection",
            "handoff": "handoff",
            "conversation": "conversation",
        }
    )

    # Greeting → wait for the user's answer
    workflow.add_edge("greeting", END)

    # Extraction → analyze, or ask the user for what is still missing
    workflow.add_conditional_edges(
        "extraction",
        ready_for_matching,
        {
            "analyze": "analyze_security",
            "ask_more": "gathering"
        }
    )

    # Gathering → wait for the user's answer
    workflow.add_edge("gathering", END)

    # Security Analysis → Matching → Presentation → wait for the user's choice
    workflow.add_edge("analyze_security", "matching")
    workflow.add_edge("matching", "presentation")
    workflow.add_edge("presentation", END)

    # Selection → handoff, or wait for a clearer choice
    workflow.add_conditional_edges(
        "selection",
        expert_selected,
        {
            "handoff": "handoff",
            "wait_for_user": END
        }
    )

    # Handoff and follow-up conversation → wait for the user
    workflow.add_edge("handoff", END)
    workflow.add_edge("conversation", END)

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
        Runs the workflow graph for one conversation turn.

        Args:
            session_id: Unique session identifier
            user_message: User's message

        Returns:
            Dict with response and state info
        """

        # Get or create session state
        if session_id in self.sessions:
            state = dict(self.sessions[session_id])
            state["user_message"] = user_message
        else:
            state = self.get_initial_state(session_id, user_message)

        # Add user message to history (nodes only append the assistant's reply)
        state["messages"] = state.get("messages", []) + [
            {"role": "user", "content": user_message}
        ]

        print(f"[WORKFLOW] Session {session_id[:8]}... Phase: {state.get('current_phase')}")

        # Run the graph until the assistant needs the user's next reply
        result = self.app.invoke(state)

        # Store updated state (in memory for the live session, in PostgreSQL as a record)
        self.sessions[session_id] = result
        save_conversation(result)
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
            "experts": [
                {**match, "expert": public_expert(match.get("expert", {}))}
                for match in result.get("matched_experts", [])
            ] if include_experts else None
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
