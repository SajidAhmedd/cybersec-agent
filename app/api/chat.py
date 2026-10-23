"""
Chat API Endpoints
Main conversation endpoints for the cybersecurity agent
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from app.agents.workflow import get_chat_workflow
from app.api.rate_limit import chat_rate_limit
from app.schemas.conversation import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["Chat"])


class StartChatRequest(BaseModel):
    """Request to start a new chat session"""
    message: str = Field(min_length=1, max_length=5000)


class StartChatResponse(BaseModel):
    """Response when starting a new chat"""
    session_id: str
    response: str
    phase: str


class ContinueChatRequest(BaseModel):
    """Request to continue an existing chat"""
    message: str = Field(min_length=1, max_length=5000)


class ContinueChatResponse(BaseModel):
    """Response for continued chat"""
    session_id: str
    response: str
    phase: str
    is_complete: bool = False
    experts: Optional[list] = None


@router.post("/start", response_model=StartChatResponse, dependencies=[Depends(chat_rate_limit)])
async def start_chat(request: StartChatRequest):
    """
    Start a new chat session.

    This creates a new conversation and returns the initial response
    from the AI assistant.
    """

    # Generate session ID
    session_id = str(uuid.uuid4())

    # Get workflow
    workflow = get_chat_workflow()

    # Process the message
    try:
        result = workflow.chat(session_id, request.message)

        return StartChatResponse(
            session_id=result["session_id"],
            response=result["response"],
            phase=result["phase"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start chat: {str(e)}"
        )


@router.post("/{session_id}", response_model=ContinueChatResponse, dependencies=[Depends(chat_rate_limit)])
async def continue_chat(session_id: str, request: ContinueChatRequest):
    """
    Continue an existing chat session.

    Send a message to an ongoing conversation.
    """

    # Get workflow
    workflow = get_chat_workflow()

    # Check if session exists
    if session_id not in workflow.sessions:
        raise HTTPException(
            status_code=404,
            detail="Session not found. Start a new chat with POST /chat/start"
        )

    # Process the message
    try:
        result = workflow.chat(session_id, request.message)

        return ContinueChatResponse(
            session_id=result["session_id"],
            response=result["response"],
            phase=result["phase"],
            is_complete=result.get("is_complete", False),
            experts=result.get("experts")
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )


@router.get("/{session_id}/state")
async def get_session_state(session_id: str):
    """
    Get the current state of a chat session.

    Useful for debugging and resuming conversations.
    """

    workflow = get_chat_workflow()

    if session_id not in workflow.sessions:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    state = workflow.sessions[session_id]

    return {
        "session_id": session_id,
        "phase": state.get("current_phase"),
        "is_complete": state.get("is_complete", False),
        "message_count": len(state.get("messages", [])),
        "has_problem_context": state.get("problem_context") is not None,
        "has_security_analysis": state.get("security_analysis") is not None,
        "expert_count": len(state.get("matched_experts", []))
    }


@router.delete("/{session_id}")
async def end_session(session_id: str):
    """
    End and delete a chat session.
    """

    workflow = get_chat_workflow()

    if session_id not in workflow.sessions:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    workflow.reset_session(session_id)

    return {"message": "Session ended", "session_id": session_id}


@router.post("/{session_id}/select-expert", dependencies=[Depends(chat_rate_limit)])
async def select_expert(session_id: str, expert_id: int):
    """
    Select an expert from the matched results.

    Used when the frontend handles expert selection separately.
    """

    workflow = get_chat_workflow()

    if session_id not in workflow.sessions:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    state = workflow.sessions[session_id]

    # Verify expert is in matched list
    matched_ids = [e.get("expert", {}).get("id") for e in state.get("matched_experts", [])]

    if expert_id not in matched_ids:
        raise HTTPException(
            status_code=400,
            detail="Expert not in matched results"
        )

    # Update state and trigger handoff
    state["selected_expert_id"] = expert_id
    state["current_phase"] = "handoff"

    # Process handoff
    result = workflow.chat(session_id, f"I'd like to connect with expert {expert_id}")

    return ContinueChatResponse(
        session_id=result["session_id"],
        response=result["response"],
        phase=result["phase"],
        is_complete=result.get("is_complete", False)
    )
