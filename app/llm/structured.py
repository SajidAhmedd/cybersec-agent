"""
Structured Output Utilities
Helpers for parsing LLM responses into structured data
"""

import json
import re
from typing import Type, TypeVar
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)


class StructuredOutputParser:
    """
    Utility class for parsing LLM outputs into structured Pydantic models.
    Handles various output formats and edge cases.
    """

    @staticmethod
    def extract_json(text: str) -> str:
        """
        Extract JSON from text that may contain markdown or other formatting.
        """

        # Try to find JSON in markdown code blocks
        code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if code_block_match:
            return code_block_match.group(1).strip()

        # Try to find a JSON object
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            return json_match.group(0)

        # Try to find a JSON array
        array_match = re.search(r'\[[\s\S]*\]', text)
        if array_match:
            return array_match.group(0)

        # Return original text if no JSON found
        return text.strip()

    @staticmethod
    def parse(text: str, model: Type[T]) -> T:
        """
        Parse text into a Pydantic model.

        Args:
            text: Raw text from LLM
            model: Pydantic model class

        Returns:
            Parsed model instance
        """

        json_str = StructuredOutputParser.extract_json(text)

        try:
            data = json.loads(json_str)
            return model.model_validate(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON: {e}\nText: {json_str}")
        except Exception as e:
            raise ValueError(f"Failed to validate model: {e}\nData: {json_str}")

    @staticmethod
    def safe_parse(text: str, model: Type[T], default: T = None) -> T:
        """
        Safely parse text, returning default on failure.

        Args:
            text: Raw text from LLM
            model: Pydantic model class
            default: Default value if parsing fails

        Returns:
            Parsed model instance or default
        """

        try:
            return StructuredOutputParser.parse(text, model)
        except Exception as e:
            print(f"Parse warning: {e}")
            return default

    @staticmethod
    def format_for_prompt(model: Type[BaseModel]) -> str:
        """
        Generate a prompt-friendly description of a Pydantic model's schema.
        """

        schema = model.model_json_schema()

        lines = ["Expected JSON format:", "{"]

        properties = schema.get("properties", {})
        required = schema.get("required", [])

        for name, prop in properties.items():
            prop_type = prop.get("type", "any")
            description = prop.get("description", "")
            is_required = name in required

            req_marker = "*" if is_required else ""
            lines.append(f'  "{name}"{req_marker}: {prop_type}  // {description}')

        lines.append("}")
        lines.append("\n* = required field")

        return "\n".join(lines)
