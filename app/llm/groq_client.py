"""
Groq LLM Client
Handles conversation, context extraction, and expert presentation
Using the Groq Python SDK (free tier, rate-limited)
"""

import groq
from pydantic import BaseModel, ValidationError
from typing import Optional, Type, TypeVar

from app.config import settings
from app.llm.mock import get_mock_response, get_mock_structured

T = TypeVar('T', bound=BaseModel)

ERROR_MESSAGE = (
    "I apologize, but I'm having trouble responding right now. "
    "Please describe your issue in more detail, and I'll do my best to guide you."
)


class GroqClient:
    """
    Client for the Groq API.
    Used for:
    - Conversational interactions (greeting, gathering info)
    - Context extraction (conversation -> structured ProblemContext)
    - Expert presentation (explaining why experts match)
    """

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.groq_api_key
        self.model_name = model or settings.groq_model
        self.mock_mode = settings.use_mock_llm
        self.client = None

        print(f"[GROQ] Initializing - Mock mode: {self.mock_mode}")
        print(f"[GROQ] Model: {self.model_name}")
        print(f"[GROQ] API Key present: {bool(self.api_key)}")

        if not self.mock_mode and not self.api_key:
            print("[GROQ] WARNING: GROQ_API_KEY not set - falling back to mock mode")
            self.mock_mode = True

        if not self.mock_mode:
            self.client = groq.Groq(api_key=self.api_key)
            print("[GROQ] Client initialized successfully")
        else:
            print("[MOCK MODE] Groq client running in mock mode")

    def _create(self, reasoning_effort: str, **kwargs):
        """Send a chat completion request"""
        # reasoning_effort is only accepted by the reasoning (gpt-oss) models
        if "gpt-oss" in self.model_name:
            kwargs["reasoning_effort"] = reasoning_effort
        return self.client.chat.completions.create(
            model=self.model_name,
            max_completion_tokens=8192,
            **kwargs
        )

    @staticmethod
    def _build_messages(
        prompt: str,
        system_prompt: Optional[str],
        history: Optional[list[dict]]
    ) -> list[dict]:
        """Convert stored conversation history into chat completion format"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages += [
            {"role": msg["role"], "content": msg["content"]}
            for msg in (history or [])
            if msg.get("role") in ("user", "assistant") and msg.get("content")
        ]
        messages.append({"role": "user", "content": prompt})
        return messages

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[list[dict]] = None
    ) -> str:
        """
        Generate a response from Groq.

        Args:
            prompt: The user's message or prompt
            system_prompt: Optional system instructions
            history: Optional conversation history

        Returns:
            Generated text response
        """

        # Mock mode - return predefined responses
        if self.mock_mode:
            print("[GROQ] Using mock response")
            return get_mock_response(prompt, system_prompt, history)

        print(f"[GROQ] Calling API - model: {self.model_name}")

        try:
            response = self._create(
                reasoning_effort=settings.groq_reasoning_effort,
                messages=self._build_messages(prompt, system_prompt, history)
            )
        except groq.AuthenticationError:
            print("[GROQ] API ERROR: invalid GROQ_API_KEY")
            return ERROR_MESSAGE
        except groq.RateLimitError as e:
            print(f"[GROQ] WARNING: rate limited (free tier limit reached?): {e.message}")
            return ERROR_MESSAGE
        except groq.APIStatusError as e:
            print(f"[GROQ] API ERROR ({e.status_code}): {e.message}")
            return ERROR_MESSAGE
        except groq.APIConnectionError as e:
            print(f"[GROQ] Connection error: {e}")
            return ERROR_MESSAGE

        print("[GROQ] API call successful")
        return (response.choices[0].message.content or "").strip()

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

        # Best-effort JSON schema mode (strict mode would require every field to be required)
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": response_model.__name__,
                "schema": response_model.model_json_schema()
            }
        }
        messages = self._build_messages(prompt, system_prompt, None)

        # Best-effort output occasionally fails schema validation - retry once
        for attempt in range(2):
            try:
                response = self._create(
                    reasoning_effort="medium",
                    messages=messages,
                    response_format=response_format
                )
                return response_model.model_validate_json(response.choices[0].message.content or "")
            except (groq.BadRequestError, ValidationError) as e:
                print(f"[GROQ] Structured output attempt {attempt + 1} failed: {e}")
            except groq.APIStatusError as e:
                print(f"[GROQ] Structured generation error ({e.status_code}): {e.message}")
                break
            except groq.APIConnectionError as e:
                print(f"[GROQ] Connection error: {e}")
                break

        return get_mock_structured(response_model)

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
