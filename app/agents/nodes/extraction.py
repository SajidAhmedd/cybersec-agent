"""
Extraction Node
Extract structured problem context from conversation
"""

from app.agents.states import AgentState
from app.agents.prompts.gathering import EXTRACTION_PROMPT
from app.schemas.problem import ProblemContext
from app.llm import get_llm


def extraction_node(state: AgentState) -> AgentState:
    """
    Extract structured problem context from the conversation.
    Uses the LLM to parse conversation into ProblemContext schema.
    """

    llm = get_llm()

    # Check if the user's last message was a question (not providing info)
    user_message = state.get("user_message", "").strip().lower()
    is_user_asking_question = _is_question(user_message)

    # Format conversation for extraction
    messages = state.get("messages", [])
    conversation = _format_conversation(messages)

    # Build extraction prompt
    prompt = EXTRACTION_PROMPT.format(conversation=conversation)

    # Extract structured context
    try:
        problem_context = llm.generate_structured(
            prompt=prompt,
            response_model=ProblemContext
        )
        context_dict = problem_context.model_dump()
        has_sufficient = problem_context.is_sufficient()

    except Exception as e:
        print(f"Extraction failed: {e}")
        context_dict = state.get("problem_context", {})
        has_sufficient = False

    # Track extraction attempts - but DON'T count if user was just asking a question
    current_attempts = state.get("extraction_attempts", 0)
    if not is_user_asking_question:
        attempts = current_attempts + 1
    else:
        attempts = current_attempts
        # If user is asking a question, don't consider context sufficient yet
        has_sufficient = False
        print(f"[EXTRACTION] User asked a question, not counting as info provided")

    # Update state
    return {
        **state,
        "problem_context": context_dict,
        "has_sufficient_context": has_sufficient,
        "extraction_attempts": attempts,
        "current_phase": "extracting"
    }


def _is_question(text: str) -> bool:
    """Check if the user's message is a question rather than providing information"""
    question_starters = [
        'why', 'what', 'how', 'when', 'where', 'who', 'which',
        'can', 'could', 'would', 'should', 'is', 'are', 'do', 'does',
        'will', 'won\'t', 'isn\'t', 'aren\'t', 'don\'t', 'doesn\'t',
        'but why', 'but what', 'but how'
    ]

    # Check if starts with question word
    for starter in question_starters:
        if text.startswith(starter):
            return True

    # Check if ends with question mark
    if text.endswith('?'):
        return True

    return False


def _format_conversation(messages: list[dict]) -> str:
    """Format messages for the extraction prompt"""
    lines = []
    for msg in messages:
        role = msg.get("role", "user").capitalize()
        content = msg.get("content", "")
        lines.append(f"{role}: {content}")
    return "\n".join(lines)
