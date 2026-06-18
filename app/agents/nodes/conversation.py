"""
Conversation Node
Handle free-form conversation after expert handoff is complete
"""

from app.agents.states import AgentState
from app.agents.prompts.system import SYSTEM_PROMPT
from app.agents.prompts.presentation import POST_HANDOFF_PROMPT
from app.llm import get_gemini


def conversation_node(state: AgentState) -> AgentState:
    """
    Handle ongoing conversation after expert connection.
    Be helpful and conversational without re-triggering expert matching.
    """

    gemini = get_gemini()

    user_message = state.get("user_message", "")
    messages = state.get("messages", [])

    # Generate conversational response
    response = gemini.chat(
        message=user_message,
        system_prompt=SYSTEM_PROMPT + "\n\n" + POST_HANDOFF_PROMPT,
        history=messages
    )

    # Append to existing messages
    new_messages = messages + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": response}
    ]

    return {
        **state,
        "current_phase": "conversation",
        "response": response,
        "messages": new_messages
    }
