"""
Problem Context Schema
Structured representation of user's cybersecurity problem
Extracted from conversation by Gemini
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum


class UrgencyLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TechnicalLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EmotionalState(str, Enum):
    CALM = "calm"
    CONCERNED = "concerned"
    ANXIOUS = "anxious"
    PANICKED = "panicked"


class ProblemContext(BaseModel):
    """
    Structured representation of the user's cybersecurity problem.
    Extracted from conversation by the Conversational Agent (Gemini).
    """

    # Core problem details
    device: Optional[str] = Field(
        default=None,
        description="Affected device type (e.g., 'iphone', 'laptop', 'server')"
    )

    platform: Optional[str] = Field(
        default=None,
        description="Operating system or platform (e.g., 'ios', 'windows', 'linux', 'aws')"
    )

    symptoms: list[str] = Field(
        default_factory=list,
        description="List of observed symptoms or issues"
    )

    timeline: Optional[str] = Field(
        default=None,
        description="When the issue was first noticed or started"
    )

    # Context
    impact: Optional[str] = Field(
        default=None,
        description="Impact scope: 'personal', 'business', 'both'"
    )

    environment: Optional[str] = Field(
        default=None,
        description="Environment context: 'home', 'office', 'enterprise', 'cloud'"
    )

    # User context
    urgency: UrgencyLevel = Field(
        default=UrgencyLevel.MEDIUM,
        description="How urgent the user needs help"
    )

    user_technical_level: TechnicalLevel = Field(
        default=TechnicalLevel.LOW,
        description="User's technical expertise level"
    )

    emotional_state: EmotionalState = Field(
        default=EmotionalState.CONCERNED,
        description="User's current emotional state"
    )

    # Location & preferences
    location: Optional[str] = Field(
        default=None,
        description="User's location (city, country)"
    )

    preferred_language: str = Field(
        default="English",
        description="User's preferred language for communication"
    )

    budget_mentioned: bool = Field(
        default=False,
        description="Whether user mentioned budget constraints"
    )

    budget_range: Optional[str] = Field(
        default=None,
        description="Budget range if mentioned"
    )

    # Additional context
    additional_context: Optional[str] = Field(
        default=None,
        description="Any other relevant context from conversation"
    )

    def is_sufficient(self) -> bool:
        """Check if we have enough context to proceed with matching"""
        # Require more information before proceeding to expert matching
        has_device_info = bool(self.device or self.platform)
        has_symptoms = len(self.symptoms) >= 2  # At least 2 symptoms
        has_timeline = bool(self.timeline)
        has_impact = bool(self.impact)

        # Need device info + at least 2 of: multiple symptoms, timeline, impact
        context_details = sum([has_symptoms, has_timeline, has_impact])
        return has_device_info and context_details >= 2

    def get_summary(self) -> str:
        """Generate a brief summary of the problem"""
        parts = []
        if self.device:
            parts.append(f"Device: {self.device}")
        if self.platform:
            parts.append(f"Platform: {self.platform}")
        if self.symptoms:
            parts.append(f"Symptoms: {', '.join(self.symptoms[:3])}")
        if self.timeline:
            parts.append(f"Timeline: {self.timeline}")
        parts.append(f"Urgency: {self.urgency.value}")
        return " | ".join(parts)
