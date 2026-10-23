"""
Conversation Persistence
Stores chat sessions and their messages in PostgreSQL
"""

import json

from .postgres import get_db_context
from .models import Conversation, ConversationMessage


def _to_json(value):
    """Make a state value JSON-serializable (e.g. enums inside model dumps)"""
    if value is None:
        return None
    return json.loads(json.dumps(value, default=str))


def save_conversation(state: dict):
    """
    Upsert the conversation row for this session and append any
    messages that have not been stored yet.
    """
    session_id = state.get("session_id")
    if not session_id:
        return

    try:
        with get_db_context() as db:
            conversation = db.query(Conversation).filter_by(session_id=session_id).first()
            if conversation is None:
                conversation = Conversation(session_id=session_id)
                db.add(conversation)
                db.flush()  # assigns conversation.id

            conversation.current_phase = state.get("current_phase")
            conversation.problem_context = _to_json(state.get("problem_context"))
            conversation.security_analysis = _to_json(state.get("security_analysis"))
            conversation.selected_expert_id = state.get("selected_expert_id")
            conversation.is_complete = state.get("is_complete", False)

            # Messages only ever get appended, so store everything past what is saved
            stored_count = db.query(ConversationMessage).filter_by(conversation_id=conversation.id).count()
            for message in state.get("messages", [])[stored_count:]:
                db.add(ConversationMessage(
                    conversation_id=conversation.id,
                    role=message.get("role", "user"),
                    content=message.get("content", "")
                ))
    except Exception as e:
        # Persistence must never break the chat itself
        print(f"[DB] Failed to save conversation {session_id[:8]}...: {e}")
