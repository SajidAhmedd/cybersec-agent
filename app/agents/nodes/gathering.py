"""
Gathering Node
Ask follow-up questions to understand the problem
"""

from app.agents.states import AgentState
from app.agents.prompts.system import SYSTEM_PROMPT
from app.agents.prompts.gathering import GATHERING_PROMPT
from app.llm import get_gemini


def gathering_node(state: AgentState) -> AgentState:
    """
    Gather more information about the user's problem.
    Ask targeted questions based on what we know and don't know.
    """

    gemini = get_gemini()

    # What do we currently know?
    problem_context = state.get("problem_context") or {}

    # Determine what's missing
    missing_info = _get_missing_info(problem_context)

    # Format current context for prompt
    current_context = _format_context(problem_context) if problem_context else "No context extracted yet"

    # Build the gathering prompt
    prompt = GATHERING_PROMPT.format(
        current_context=current_context,
        missing_info=missing_info
    )

    # Get conversation history
    messages = state.get("messages", [])

    # Generate response
    response = gemini.chat(
        message=state.get("user_message", ""),
        system_prompt=SYSTEM_PROMPT + "\n\n" + prompt,
        history=messages[:-1] if messages else []  # Exclude current message
    )

    # Update state - APPEND to existing messages
    existing_messages = state.get("messages", [])
    new_messages = existing_messages + [
        {"role": "user", "content": state.get("user_message", "")},
        {"role": "assistant", "content": response}
    ]

    return {
        **state,
        "current_phase": "gathering",
        "response": response,
        "messages": new_messages
    }


def _get_missing_info(context: dict) -> str:
    """Determine what information is still needed"""
    missing = []

    if not context.get("device") and not context.get("platform"):
        missing.append("What device or system is affected")

    if not context.get("symptoms"):
        missing.append("What symptoms or issues they're seeing")

    if not context.get("timeline"):
        missing.append("When this started or was noticed")

    if not context.get("urgency"):
        missing.append("How urgent this is for them")

    if not missing:
        return "We have basic information. Clarify any details that would help matching."

    return ", ".join(missing)


def _format_context(context: dict) -> str:
    """Format context for display in prompt"""
    parts = []

    if context.get("device"):
        parts.append(f"Device: {context['device']}")
    if context.get("platform"):
        parts.append(f"Platform: {context['platform']}")
    if context.get("symptoms"):
        parts.append(f"Symptoms: {', '.join(context['symptoms'])}")
    if context.get("timeline"):
        parts.append(f"Timeline: {context['timeline']}")
    if context.get("urgency"):
        parts.append(f"Urgency: {context['urgency']}")

    return "\n".join(parts) if parts else "No context yet"
