"""
Conversation Schemas
State management for the LangGraph conversation workflow
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum

from .problem import ProblemContext
from .security import SecurityAnalysis
from .expert import ExpertRecommendation


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """Single message in the conversation"""

    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Metadata
    agent: Optional[str] = Field(
        default=None,
        description="Which agent generated this message (claude, foundation_sec)"
    )


class ConversationPhase(str, Enum):
    GREETING = "greeting"
    GATHERING = "gathering"
    EXTRACTING = "extracting"
    ANALYZING = "analyzing"
    MATCHING = "matching"
    PRESENTING = "presenting"
    SELECTING = "selecting"
    HANDOFF = "handoff"
    COMPLETE = "complete"


class ConversationState(BaseModel):
    """
    Full conversation state for LangGraph.
    This is the main state object that flows through the workflow.
    """

    # Session info
    session_id: str
    started_at: datetime = Field(default_factory=datetime.utcnow)

    # Current phase
    current_phase: ConversationPhase = Field(default=ConversationPhase.GREETING)

    # Messages
    messages: list[Message] = Field(default_factory=list)

    # Extracted context (from Claude)
    problem_context: Optional[ProblemContext] = None

    # Security analysis (from Foundation-Sec)
    security_analysis: Optional[SecurityAnalysis] = None

    # Expert matching results
    matched_experts: list[ExpertRecommendation] = Field(default_factory=list)

    # User's selection
    selected_expert_id: Optional[int] = None

    # Flags
    has_sufficient_context: bool = Field(default=False)
    is_complete: bool = Field(default=False)

    # Tracking
    questions_asked: list[str] = Field(default_factory=list)
    extraction_attempts: int = Field(default=0)

    def add_message(self, role: MessageRole, content: str, agent: Optional[str] = None):
        """Add a message to the conversation"""
        self.messages.append(Message(
            role=role,
            content=content,
            agent=agent
        ))

    def get_messages_for_llm(self) -> list[dict]:
        """Format messages for LLM input"""
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in self.messages
        ]

    def get_last_user_message(self) -> Optional[str]:
        """Get the most recent user message"""
        for msg in reversed(self.messages):
            if msg.role == MessageRole.USER:
                return msg.content
        return None


class ChatRequest(BaseModel):
    """API request for chat endpoint"""

    session_id: Optional[str] = None
    message: str = Field(min_length=1, max_length=5000)


class ChatResponse(BaseModel):
    """API response from chat endpoint"""

    session_id: str
    response: str
    phase: ConversationPhase

    # Optional: expert recommendations if in presenting phase
    experts: Optional[list[ExpertRecommendation]] = None

    # Flags
    is_complete: bool = Field(default=False)
    requires_selection: bool = Field(default=False)
