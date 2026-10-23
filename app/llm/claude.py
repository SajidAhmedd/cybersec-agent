"""
Claude LLM Client
Handles conversation, context extraction, and expert presentation
Using the Anthropic Python SDK
"""

import anthropic
from typing import Optional, Type, TypeVar
from pydantic import BaseModel

from app.config import settings
from app.llm.mock import get_mock_response, get_mock_structured

T = TypeVar('T', bound=BaseModel)

# Server-side refusal fallback: if Claude's safety classifiers decline a request
# (possible for cybersecurity topics), the API re-runs it on a recommended fallback model.
FALLBACK_BETA = "server-side-fallback-2026-07-01"

REFUSAL_MESSAGE = (
    "I'm sorry, I can't help with that request as phrased. "
    "Could you describe the security problem you're facing so I can connect you with the right expert?"
)

ERROR_MESSAGE = (
    "I apologize, but I'm having trouble responding right now. "
    "Please describe your issue in more detail, and I'll do my best to guide you."
)



class ClaudeClient:
    """
    Client for the Anthropic Claude API.
    Used for:
    - Conversational interactions (greeting, gathering info)
    - Context extraction (conversation -> structured ProblemContext)
    - Expert presentation (explaining why experts match)
    """

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.anthropic_api_key
        self.model_name = model or settings.claude_model
        self.mock_mode = settings.use_mock_llm
        self.client = None

        print(f"[CLAUDE] Initializing - Mock mode: {self.mock_mode}")
        print(f"[CLAUDE] Model: {self.model_name}")
        print(f"[CLAUDE] API Key present: {bool(self.api_key)}")

        if not self.mock_mode and not self.api_key:
            print("[CLAUDE] WARNING: ANTHROPIC_API_KEY not set - falling back to mock mode")
            self.mock_mode = True

        if not self.mock_mode:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            print("[CLAUDE] Client initialized successfully")
        else:
            print("[MOCK MODE] Claude client running in mock mode")

    def _create(self, effort: str, **kwargs):
        """Send a Messages API request with refusal fallback enabled"""
        return self.client.beta.messages.create(
            model=self.model_name,
            max_tokens=16000,
            output_config={"effort": effort},
            betas=[FALLBACK_BETA],
            fallbacks="default",
            **kwargs
        )

    @staticmethod
    def _build_messages(prompt: str, history: Optional[list[dict]]) -> list[dict]:
        """Convert stored conversation history into Messages API format"""
        messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in (history or [])
            if msg.get("role") in ("user", "assistant") and msg.get("content")
        ]
        # The first message must come from the user
        while messages and messages[0]["role"] != "user":
            messages.pop(0)
        messages.append({"role": "user", "content": prompt})
        return messages

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[list[dict]] = None
    ) -> str:
        """
        Generate a response from Claude.

        Args:
            prompt: The user's message or prompt
            system_prompt: Optional system instructions
            history: Optional conversation history

        Returns:
            Generated text response
        """

        # Mock mode - return predefined responses
        if self.mock_mode:
            print("[CLAUDE] Using mock response")
            return get_mock_response(prompt, system_prompt, history)

        print(f"[CLAUDE] Calling API - model: {self.model_name}")

        kwargs = {"messages": self._build_messages(prompt, history)}
        if system_prompt:
            kwargs["system"] = system_prompt

        try:
            response = self._create(effort=settings.claude_effort, **kwargs)
        except anthropic.AuthenticationError:
            print("[CLAUDE] API ERROR: invalid ANTHROPIC_API_KEY")
            return ERROR_MESSAGE
        except anthropic.RateLimitError as e:
            print(f"[CLAUDE] WARNING: rate limited: {e.message}")
            return ERROR_MESSAGE
        except anthropic.APIStatusError as e:
            print(f"[CLAUDE] API ERROR ({e.status_code}): {e.message}")
            return ERROR_MESSAGE
        except anthropic.APIConnectionError as e:
            print(f"[CLAUDE] Connection error: {e}")
            return ERROR_MESSAGE

        if response.stop_reason == "refusal":
            print(f"[CLAUDE] Request refused: {response.stop_details}")
            return REFUSAL_MESSAGE

        print("[CLAUDE] API call successful")
        return "".join(b.text for b in response.content if b.type == "text").strip()

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
            return get_mock_structured(response_model)

        kwargs = {"messages": [{"role": "user", "content": prompt}]}
        if system_prompt:
            kwargs["system"] = system_prompt

        try:
            # Structured outputs: the response is constrained to the model's JSON schema
            response = self.client.beta.messages.parse(
                model=self.model_name,
                max_tokens=16000,
                output_config={"effort": "medium"},
                output_format=response_model,
                betas=[FALLBACK_BETA],
                fallbacks="default",
                **kwargs
            )
        except anthropic.APIStatusError as e:
            print(f"[CLAUDE] Structured generation error ({e.status_code}): {e.message}")
            return get_mock_structured(response_model)
        except anthropic.APIConnectionError as e:
            print(f"[CLAUDE] Connection error: {e}")
            return get_mock_structured(response_model)

        if response.stop_reason == "refusal" or response.parsed_output is None:
            print(f"[CLAUDE] No structured output (stop_reason={response.stop_reason})")
            return get_mock_structured(response_model)

        return response.parsed_output

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

