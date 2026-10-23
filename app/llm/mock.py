"""
Mock LLM responses
Used when no provider API key is configured or USE_MOCK_LLM=true
"""

from typing import Type, TypeVar
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)


MOCK_RESPONSES = {
    "greeting": """I understand this is concerning, and I want you to know you're in the right place. Let's figure this out together.

Can you tell me a bit more about what's happening with your iPhone? When did you first notice something was wrong?""",

    "gathering": """Thank you for sharing that. It's helpful to understand the situation better.

A few more questions to help me find the right expert for you:
- Is this your personal phone or a work device?
- Have you noticed any other unusual behavior, like apps you didn't install or messages you didn't send?""",

    "presentation": """Based on what you've described, I found some excellent experts who specialize in exactly this type of situation:

**1. Priya Sharma** - Mobile Security Specialist
She's handled over 50 iPhone compromise cases and is known for explaining things clearly without technical jargon. Her response time is typically within 2 hours.

**2. Alex Chen** - Incident Response Lead
With 12 years of experience and a background in digital forensics, Alex has seen cases like yours many times. He's available right now if you need urgent help.

**3. Sarah Johnson** - Cybersecurity Consultant
Sarah specializes in helping individuals through security incidents. Her clients love her patient, thorough approach.

Which of these experts would you like to connect with?""",

    "handoff": """Great choice! I'm connecting you with them now.

You can reach them via:
- **WhatsApp**: Click to start a chat
- **Email**: Send a message
- **Schedule a call**: Book a convenient time

I've shared a summary of your situation so they'll be prepared to help. You're in good hands!"""
}


def get_mock_response(prompt: str, system_prompt: str = None, history: list = None) -> str:
    """Return appropriate mock response based on context"""
    prompt_lower = prompt.lower()
    history_len = len(history) if history else 0

    # Determine phase based on context
    if history_len == 0:
        return MOCK_RESPONSES["greeting"]
    elif history_len < 4:
        return MOCK_RESPONSES["gathering"]
    elif "expert" in prompt_lower or "presentation" in (system_prompt or "").lower():
        return MOCK_RESPONSES["presentation"]
    elif "handoff" in (system_prompt or "").lower() or "connect" in prompt_lower:
        return MOCK_RESPONSES["handoff"]
    else:
        return MOCK_RESPONSES["gathering"]


def get_mock_structured(response_model: Type[T]) -> T:
    """Return mock structured data for testing"""
    model_name = response_model.__name__

    if model_name == "ProblemContext":
        from app.schemas.problem import ProblemContext, UrgencyLevel, TechnicalLevel, EmotionalState
        return ProblemContext(
            device="iphone",
            platform="ios",
            symptoms=["unusual apps", "battery drain", "strange messages"],
            timeline="2 hours ago",
            impact="personal",
            urgency=UrgencyLevel.HIGH,
            user_technical_level=TechnicalLevel.LOW,
            emotional_state=EmotionalState.ANXIOUS
        )
    elif model_name == "SecurityAnalysis":
        from app.schemas.security import SecurityAnalysis, ThreatSeverity
        return SecurityAnalysis(
            threat_type="mobile_compromise",
            attack_vector="likely_malware",
            severity=ThreatSeverity.HIGH,
            confidence=0.85,
            required_skills=["mobile_security", "ios_forensics", "incident_response"],
            recommended_services=["incident_response", "forensics"],
            platforms=["ios"],
            reasoning="Mock analysis: iPhone compromise with malware indicators"
        )
    else:
        # Try to create with defaults
        return response_model()
