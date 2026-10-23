"""
Conversation Node
Handle free-form conversation after expert handoff is complete
"""

from app.agents.states import AgentState
from app.agents.prompts.system import SYSTEM_PROMPT
from app.agents.prompts.presentation import POST_HANDOFF_PROMPT
from app.llm import get_llm


def conversation_node(state: AgentState) -> AgentState:
    """
    Handle ongoing conversation after expert connection.
    Be helpful and conversational without re-triggering expert matching.
    """

    llm = get_llm()

    user_message = state.get("user_message", "")
    messages = state.get("messages", [])

    # Generate conversational response
    response = llm.chat(
        message=user_message,
        system_prompt=SYSTEM_PROMPT + "\n\n" + POST_HANDOFF_PROMPT,
        history=messages[:-1] if messages else []  # Exclude current message
    )

    # Append the reply (the workflow already added the user's message)
    new_messages = messages + [
        {"role": "assistant", "content": response}
    ]

    return {
        **state,
        "current_phase": "conversation",
        "response": response,
        "messages": new_messages
    }
