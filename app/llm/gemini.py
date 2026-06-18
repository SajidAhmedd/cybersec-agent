"""
Gemini LLM Client
Handles conversation, context extraction, and expert presentation
Using the new google.genai package
"""

from google import genai
from google.genai import types
from typing import Optional, Type, TypeVar
from pydantic import BaseModel
import json
import re

from app.config import settings

T = TypeVar('T', bound=BaseModel)


# Mock responses for testing without API
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


class GeminiClient:
    """
    Client for Google Gemini API using the new google.genai package.
    Used for:
    - Conversational interactions (greeting, gathering info)
    - Context extraction (conversation -> structured ProblemContext)
    - Expert presentation (explaining why experts match)
    """

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.google_api_key
        self.model_name = model or settings.gemini_model
        self.mock_mode = settings.use_mock_llm
        self.client = None

        print(f"[GEMINI] Initializing - Mock mode: {self.mock_mode}")
        print(f"[GEMINI] Model: {self.model_name}")
        print(f"[GEMINI] API Key present: {bool(self.api_key)}")

        if not self.mock_mode:
            try:
                # Initialize the new genai client
                self.client = genai.Client(api_key=self.api_key)
                print("[GEMINI] Client initialized successfully")
            except Exception as e:
                print(f"[GEMINI] ERROR initializing: {e}")
                self.mock_mode = True
        else:
            print("[MOCK MODE] Gemini client running in mock mode")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[list[dict]] = None
    ) -> str:
        """
        Generate a response from Gemini.

        Args:
            prompt: The user's message or prompt
            system_prompt: Optional system instructions
            history: Optional conversation history

        Returns:
            Generated text response
        """

        # Mock mode - return predefined responses
        if self.mock_mode:
            print("[GEMINI] Using mock response")
            return self._get_mock_response(prompt, system_prompt, history)

        print("[GEMINI] Calling real API...")
        print(f"[GEMINI] Using API key starting with: {self.api_key[:20]}...")
        print(f"[GEMINI] Model: {self.model_name}")

        # Build the full prompt
        full_prompt = ""

        if system_prompt:
            full_prompt += f"System Instructions:\n{system_prompt}\n\n"

        if history:
            full_prompt += "Conversation History:\n"
            for msg in history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                full_prompt += f"{role.capitalize()}: {content}\n"
            full_prompt += "\n"

        full_prompt += f"User: {prompt}\n\nAssistant:"

        # Generate response using new API
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    temperature=settings.gemini_temperature,
                    top_p=0.95,
                    top_k=40,
                    max_output_tokens=2048,
                )
            )
            print("[GEMINI] API call successful")
            return response.text.strip()
        except Exception as e:
            error_str = str(e)
            print(f"[GEMINI] API ERROR: {error_str}")

            # Check for quota exhaustion
            if "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
                print("[GEMINI] WARNING: API quota exhausted! Using mock response.")
                return "I apologize, but I'm experiencing high demand right now. Let me help you with what I know: Based on your concern, I recommend contacting a cybersecurity professional. Please describe your issue in more detail, and I'll do my best to guide you."

            # Fallback to mock on other errors
            return self._get_mock_response(prompt, system_prompt, history)

    def _get_mock_response(self, prompt: str, system_prompt: str = None, history: list = None) -> str:
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

    def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None
    ) -> T:
        """
        Generate a structured response that matches a Pydantic model.

        Args:
            prompt: The prompt/context
            response_model: Pydantic model class to parse response into
            system_prompt: Optional system instructions

        Returns:
            Parsed Pydantic model instance
        """

        # Mock mode - return mock structured data
        if self.mock_mode:
            return self._get_mock_structured(response_model)

        # Get the JSON schema from Pydantic model
        schema = response_model.model_json_schema()

        # Build prompt requesting JSON output
        structured_prompt = f"""
{system_prompt or ''}

{prompt}

You MUST respond with valid JSON that matches this schema:
{json.dumps(schema, indent=2)}

Respond ONLY with the JSON object, no other text.
"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=structured_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,  # Lower temperature for structured output
                    max_output_tokens=2048,
                )
            )
            response_text = response.text.strip()

            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
            if json_match:
                response_text = json_match.group(1)

            # Parse and validate
            data = json.loads(response_text)
            return response_model.model_validate(data)
        except json.JSONDecodeError as e:
            print(f"[GEMINI] Failed to parse JSON response: {e}")
            return self._get_mock_structured(response_model)
        except Exception as e:
            print(f"[GEMINI] Structured generation error: {e}")
            return self._get_mock_structured(response_model)

    def _get_mock_structured(self, response_model: Type[T]) -> T:
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

    def chat(
        self,
        message: str,
        system_prompt: str,
        history: list[dict]
    ) -> str:
        """
        Convenience method for chat interactions.
        Maintains conversation context.
        """
        return self.generate(
            prompt=message,
            system_prompt=system_prompt,
            history=history
        )


# Singleton instance - always recreate for fresh settings
_gemini_client: Optional[GeminiClient] = None


def get_gemini() -> GeminiClient:
    """Get or create Gemini client instance"""
    global _gemini_client
    # Always create fresh client to pick up settings changes
    if _gemini_client is None:
        print("[GEMINI] Creating new GeminiClient instance...")
        _gemini_client = GeminiClient()
    return _gemini_client


def reset_gemini_client():
    """Reset the singleton to force recreation with new settings"""
    global _gemini_client
    _gemini_client = None
    print("[GEMINI] Client reset - will be recreated on next use")
