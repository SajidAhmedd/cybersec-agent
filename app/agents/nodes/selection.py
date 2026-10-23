"""
Selection Node
Handle user's expert selection
"""

import re
from app.agents.states import AgentState
from app.agents.prompts.system import SYSTEM_PROMPT
from app.llm import get_llm

SELECTION_CONVERSATION_PROMPT = """
The user has been shown a list of cybersecurity experts and we're waiting for them to choose one.
But instead of selecting an expert, they said something else (maybe a question, comment, or concern).

THEIR MESSAGE: "{user_message}"

AVAILABLE EXPERTS:
{experts_summary}

Your job:
1. If they asked a question - answer it naturally and helpfully
2. If they have a concern - address it with empathy
3. If they're unsure - help them decide based on their needs
4. After addressing their point, gently ask which expert they'd like to connect with

BE CONVERSATIONAL - respond like ChatGPT or Claude would. Don't be robotic.
Answer their actual question/concern first, then guide them to a selection.

Example - if they ask "why does it matter if it's personal or work?":
"Great question! It matters because work computers often have different security policies and
your IT department might need to be involved. Personal devices give us more flexibility in
how we approach the fix. Based on what you've told me, I think [Expert] would be a great fit
because [reason]. Would you like to connect with them, or would you prefer one of the others?"
"""


def selection_node(state: AgentState) -> AgentState:
    """
    Process user's expert selection.
    Parse their choice and prepare for handoff.
    """

    user_message = state.get("user_message", "")
    user_message_lower = user_message.lower()
    matched_experts = state.get("matched_experts", [])

    selected_expert = None
    selected_id = None

    # Try to match user's selection to an expert
    for expert_data in matched_experts:
        expert = expert_data.get("expert", {})
        expert_name = expert.get("name", "").lower()
        expert_id = expert.get("id")

        # Check if user mentioned this expert's name
        if expert_name and any(part in user_message_lower for part in expert_name.split()):
            selected_expert = expert_data
            selected_id = expert_id
            break

    # Check for number-based selection (1, 2, 3, first, second, etc.)
    if not selected_expert:
        selection_index = _parse_number_selection(user_message_lower)
        if selection_index is not None and 0 <= selection_index < len(matched_experts):
            selected_expert = matched_experts[selection_index]
            selected_id = selected_expert.get("expert", {}).get("id")

    # If still no match, use LLM to respond conversationally
    if not selected_expert:
        llm = get_llm()
        messages = state.get("messages", [])

        # Format experts for the prompt
        experts_summary = _format_experts_summary(matched_experts)

        prompt = SELECTION_CONVERSATION_PROMPT.format(
            user_message=user_message,
            experts_summary=experts_summary
        )

        response = llm.chat(
            message=user_message,
            system_prompt=SYSTEM_PROMPT + "\n\n" + prompt,
            history=messages[:-1] if messages else []  # Exclude current message
        )

        # Append the reply (the workflow already added the user's message)
        existing_messages = state.get("messages", [])
        new_messages = existing_messages + [
            {"role": "assistant", "content": response}
        ]

        return {
            **state,
            "current_phase": "selecting",
            "response": response,
            "messages": new_messages
        }

    # Update state with selection
    return {
        **state,
        "selected_expert_id": selected_id,
        "current_phase": "handoff"
    }


def _format_experts_summary(matched_experts: list) -> str:
    """Format experts for the selection prompt"""
    lines = []
    for i, expert_data in enumerate(matched_experts, 1):
        expert = expert_data.get("expert", {})
        match = expert_data.get("match", {})
        lines.append(f"{i}. {expert.get('name')} - {expert.get('title')} (Match: {match.get('match_score', 0):.0%})")
    return "\n".join(lines)


def _parse_number_selection(text: str) -> int | None:
    """Parse user's number-based selection"""

    # Number words
    word_to_num = {
        "first": 0, "one": 0, "1": 0, "1st": 0,
        "second": 1, "two": 1, "2": 1, "2nd": 1,
        "third": 2, "three": 2, "3": 2, "3rd": 2,
        "fourth": 3, "four": 3, "4": 3, "4th": 3,
        "fifth": 4, "five": 4, "5": 4, "5th": 4,
    }

    text_lower = text.lower()

    for word, index in word_to_num.items():
        if word in text_lower:
            return index

    # Try to find a bare number
    numbers = re.findall(r'\d+', text)
    if numbers:
        num = int(numbers[0])
        if 1 <= num <= 5:
            return num - 1  # Convert to 0-indexed

    return None
