"""
Presentation Node
Present matched experts to the user with explanations
"""

from app.agents.states import AgentState
from app.agents.prompts.system import SYSTEM_PROMPT
from app.agents.prompts.presentation import PRESENTATION_PROMPT
from app.llm import get_llm


def presentation_node(state: AgentState) -> AgentState:
    """
    Present matched experts to the user.
    Generates personalized explanations for why each expert matches.
    """

    llm = get_llm()

    # Get problem context for personalization
    problem_context = state.get("problem_context", {})
    problem_summary = _format_problem_summary(problem_context)

    # Get matched experts
    matched_experts = state.get("matched_experts", [])

    if not matched_experts:
        response = """I wasn't able to find experts matching your specific situation right now.

This could be because our expert network is still growing. Would you like me to:
1. Try a broader search?
2. Take your contact info and have someone reach out?

Let me know how you'd like to proceed."""

    else:
        # Format experts for presentation
        experts_formatted = _format_experts(matched_experts)

        # Build presentation prompt
        prompt = PRESENTATION_PROMPT.format(
            problem_summary=problem_summary,
            experts=experts_formatted
        )

        # Generate presentation with conversation history
        messages = state.get("messages", [])
        response = llm.chat(
            message="Present these experts to the user based on our conversation.",
            system_prompt=SYSTEM_PROMPT + "\n\n" + prompt,
            history=messages
        )

    # Append to existing messages
    existing_messages = state.get("messages", [])
    new_messages = existing_messages + [
        {"role": "assistant", "content": response}
    ]

    return {
        **state,
        "current_phase": "presenting",
        "response": response,
        "messages": new_messages
    }


def _format_problem_summary(context: dict) -> str:
    """Format problem context as a detailed summary for diagnosis"""
    parts = []

    if context.get("device"):
        parts.append(f"Device: {context['device']}")
    if context.get("platform"):
        parts.append(f"Platform: {context['platform']}")
    if context.get("symptoms"):
        # Include ALL symptoms for proper diagnosis
        parts.append(f"Symptoms: {', '.join(context['symptoms'])}")
    if context.get("timeline"):
        parts.append(f"When it started: {context['timeline']}")
    if context.get("additional_context"):
        parts.append(f"Additional details: {context['additional_context']}")
    if context.get("urgency"):
        parts.append(f"Urgency: {context['urgency']}")
    if context.get("emotional_state"):
        parts.append(f"User state: {context['emotional_state']}")
    if context.get("user_technical_level"):
        parts.append(f"Technical level: {context['user_technical_level']}")

    return "\n".join(parts) if parts else "Security concern"


def _format_experts(matched_experts: list[dict]) -> str:
    """Format matched experts for the presentation prompt"""
    lines = []

    for i, expert_data in enumerate(matched_experts, 1):
        expert = expert_data.get("expert", {})
        match = expert_data.get("match", {})

        if expert.get("is_external"):
            # Only list what we actually know; never invent ratings or rates
            lines.append(f"""
Expert {i} (EXTERNAL - independent freelancer on {expert.get('profile_platform') or 'a freelance platform'}, not affiliated with us; the user reaches them through that platform):
- Name: {expert.get('name', 'Unknown')}
- Title: {expert.get('title', 'Security Freelancer')}
- Skills: {', '.join(expert.get('skills', [])[:5])}
- Match score: {match.get('match_score', 0):.0%}
- Why they match: {', '.join(match.get('match_reasons', []))}
""")
            continue

        if expert.get("is_featured"):
            # No ratings, rates or experience on record; only state what we know
            lines.append(f"""
Expert {i} (FEATURED - present first; reachable directly by WhatsApp or email):
- Name: {expert.get('name', 'Unknown')}
- Title: {expert.get('title', 'Security Expert')}
- About: {expert.get('bio') or 'Cybersecurity specialist'}
- Response time: {expert.get('response_time') or 'Varies'}
- Why they match: {', '.join(match.get('match_reasons', []))}
""")
            continue

        lines.append(f"""
Expert {i}:
- Name: {expert.get('name', 'Unknown')}
- Title: {expert.get('title', 'Security Expert')}
- Experience: {expert.get('years_experience', 'N/A')} years
- Skills: {', '.join(expert.get('skills', [])[:5])}
- Certifications: {', '.join(expert.get('certifications', [])[:3])}
- Rating: {expert.get('rating', 'N/A')}/5 ({expert.get('total_reviews', 0)} reviews)
- Response time: {expert.get('response_time', 'Varies')}
- Rate: ${expert.get('hourly_rate', 'Contact for pricing')}/hour
- Match score: {match.get('match_score', 0):.0%}
- Why they match: {', '.join(match.get('match_reasons', []))}
""")

    return "\n".join(lines)
