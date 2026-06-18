"""
Greeting Node
First interaction - welcome user and establish rapport
"""

from app.agents.states import AgentState
from app.agents.prompts.system import SYSTEM_PROMPT, GREETING_PROMPT
from app.llm import get_gemini


def greeting_node(state: AgentState) -> AgentState:
    """
    Handle the initial greeting.
    Welcome the user and start understanding their concern.
    """
    print("[GREETING NODE] Starting greeting_node")

    gemini = get_gemini()
    print(f"[GREETING NODE] Got gemini client - mock_mode: {gemini.mock_mode}")

    # Get user's initial message
    user_message = state.get("user_message", "")
    print(f"[GREETING NODE] User message: {user_message}")

    # Build context for greeting
    full_prompt = f"""
{GREETING_PROMPT}

User's message: "{user_message}"

Generate a warm, brief response that:
1. Acknowledges their concern
2. Reassures them you can help
3. Asks an open question to understand more
"""

    print("[GREETING NODE] Calling gemini.generate()...")
    response = gemini.generate(
        prompt=full_prompt,
        system_prompt=SYSTEM_PROMPT
    )
    print(f"[GREETING NODE] Got response: {response[:100]}...")

    # Append to existing messages (for consistency, even if typically first)
    existing_messages = state.get("messages", [])
    new_messages = existing_messages + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": response}
    ]

    return {
        **state,
        "current_phase": "gathering",
        "response": response,
        "messages": new_messages
    }
