"""
Handoff Node
Complete the connection between user and expert
"""

from app.agents.states import AgentState
from app.agents.prompts.system import SYSTEM_PROMPT
from app.agents.prompts.presentation import HANDOFF_PROMPT, EXTERNAL_HANDOFF_PROMPT
from app.config import settings
from app.llm import get_llm
from app.services.handoff import get_handoff_service


def handoff_node(state: AgentState) -> AgentState:
    """
    Handle the handoff to the selected expert.
    Generate confirmation message and trigger notifications.
    """

    llm = get_llm()

    # Get selected expert
    selected_id = state.get("selected_expert_id")
    matched_experts = state.get("matched_experts", [])

    selected_expert = None
    for expert_data in matched_experts:
        if expert_data.get("expert", {}).get("id") == selected_id:
            selected_expert = expert_data
            break

    if not selected_expert:
        response = "I'm sorry, I couldn't find that expert. Let me show you the options again."
        return {
            **state,
            "current_phase": "presenting",
            "response": response
        }

    expert = selected_expert.get("expert", {})
    problem_context = state.get("problem_context", {})

    # Format problem summary
    problem_summary = _format_problem_summary(problem_context)

    if expert.get("is_external"):
        # External freelancer: point the user to their public profile; nobody is notified
        prompt = EXTERNAL_HANDOFF_PROMPT.format(
            expert=_format_expert(expert),
            problem_summary=problem_summary,
            platform=expert.get("profile_platform") or "a freelance platform",
            profile_url=expert.get("profile_url", "")
        )
    else:
        prompt = HANDOFF_PROMPT.format(
            expert=_format_expert(expert),
            problem_summary=problem_summary,
            contact_options=_build_contact_options(expert)
        )

    # Generate handoff message with conversation history
    messages = state.get("messages", [])
    response = llm.chat(
        message=f"The user selected {expert.get('name')}. Complete the handoff.",
        system_prompt=SYSTEM_PROMPT + "\n\n" + prompt,
        history=messages
    )

    # Trigger expert notification (network experts only)
    if not expert.get("is_external"):
        _notify_expert(expert, problem_context, state.get("security_analysis") or {}, messages)

    # Append to existing messages
    new_messages = messages + [
        {"role": "assistant", "content": response}
    ]

    return {
        **state,
        "current_phase": "complete",
        "is_complete": True,
        "response": response,
        "messages": new_messages
    }


def _build_contact_options(expert: dict) -> str:
    """Build contact options string for the expert"""
    options = []

    if expert.get("whatsapp"):
        options.append(f"- WhatsApp: Click to chat with {expert.get('name')}")
    else:
        options.append("- WhatsApp: Available upon confirmation")

    if expert.get("email"):
        options.append(f"- Email: Send a message to {expert.get('name')}")
    else:
        options.append("- Email: Available upon confirmation")

    options.append("- Schedule a call: Book a convenient time slot")

    return "\n".join(options)


def _format_expert(expert: dict) -> str:
    """Format expert info for the prompt"""
    return f"""
Name: {expert.get('name', 'Expert')}
Title: {expert.get('title', 'Security Specialist')}
Response time: {expert.get('response_time', 'Varies')}
Rating: {expert.get('rating', 'N/A')}/5
"""


def _format_problem_summary(context: dict) -> str:
    """Format problem context as a brief summary"""
    parts = []

    if context.get("device"):
        parts.append(f"Device: {context['device']}")
    if context.get("symptoms"):
        parts.append(f"Issue: {', '.join(context['symptoms'][:2])}")
    if context.get("urgency"):
        parts.append(f"Urgency: {context['urgency']}")

    return " | ".join(parts) if parts else "Security concern"


def _notify_expert(expert: dict, problem_context: dict, security_analysis: dict, messages: list[dict]):
    """
    Notify the expert about the new client via WhatsApp and/or Email.
    Only sends when OUTREACH_ENABLED=true and Twilio/SendGrid are configured.
    """

    # Build notification content
    notification = {
        "expert_id": expert.get("id"),
        "expert_name": expert.get("name"),
        "expert_contact": expert.get("whatsapp") or expert.get("email"),
        "problem_summary": {
            "threat_type": security_analysis.get("threat_type"),
            "device": problem_context.get("device"),
            "symptoms": problem_context.get("symptoms", []),
            "urgency": problem_context.get("urgency"),
            "timeline": problem_context.get("timeline")
        },
        "conversation_summary": _summarize_conversation(messages)
    }

    if not settings.outreach_enabled:
        print(f"[NOTIFICATION] Outreach disabled - would notify expert {notification['expert_name']} (id {notification['expert_id']})")
        return

    try:
        result = get_handoff_service().notify_expert_only(
            expert_email=expert.get("email"),
            expert_phone=expert.get("whatsapp") or expert.get("phone"),
            expert_name=expert.get("name", "Expert"),
            problem_summary=notification["problem_summary"],
            conversation_summary=notification["conversation_summary"]
        )
    except Exception as e:
        print(f"[NOTIFICATION] Failed to notify expert {notification['expert_id']}: {e}")
        return

    if result["success"]:
        print(f"[NOTIFICATION] Notified expert {notification['expert_id']} via {', '.join(result['channels_used'])}")
    else:
        print(f"[NOTIFICATION] Expert {notification['expert_id']} not notified: {result['errors'] or 'no outreach channel configured'}")


def _summarize_conversation(messages: list[dict]) -> str:
    """Create a brief summary of the conversation for the expert"""
    # In production, could use LLM to summarize
    user_messages = [m["content"] for m in messages if m.get("role") == "user"]
    return " | ".join(user_messages[-3:]) if user_messages else "Client conversation available"
