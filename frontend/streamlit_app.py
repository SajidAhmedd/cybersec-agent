"""
CyberSecAgent - Streamlit Chat Interface
User-facing chat interface for the cybersecurity expert matching platform
"""

import streamlit as st
import requests
import uuid
from typing import Optional

# Configuration
API_URL = "http://localhost:8003"

# Page config
st.set_page_config(
    page_title="CyberSecAgent - Security Expert Matching",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    /* Main container */
    .main {
        max-width: 800px;
        margin: 0 auto;
    }

    /* Chat messages */
    .user-message {
        background-color: #e3f2fd;
        color: #1a1a2e !important;
        padding: 15px;
        border-radius: 15px;
        margin: 10px 0;
        margin-left: 20%;
    }

    .assistant-message {
        background-color: #ffffff;
        color: #1a1a2e !important;
        padding: 15px;
        border-radius: 15px;
        margin: 10px 0;
        margin-right: 20%;
        border: 1px solid #e0e0e0;
    }

    .user-message *, .assistant-message * {
        color: #1a1a2e !important;
    }

    /* Expert cards */
    .expert-card {
        background-color: #fff;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* Header */
    .header {
        text-align: center;
        padding: 20px 0;
        border-bottom: 1px solid #e0e0e0;
        margin-bottom: 20px;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Force dark mode text fix */
    .stMarkdown p, .stMarkdown span, .stMarkdown div {
        color: inherit;
    }

    /* Ensure message text is always dark */
    [data-testid="stMarkdownContainer"] .user-message,
    [data-testid="stMarkdownContainer"] .assistant-message {
        color: #1a1a2e !important;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "phase" not in st.session_state:
        st.session_state.phase = "start"
    if "experts" not in st.session_state:
        st.session_state.experts = None
    if "is_complete" not in st.session_state:
        st.session_state.is_complete = False


def start_chat(message: str) -> Optional[dict]:
    """Start a new chat session"""
    try:
        response = requests.post(
            f"{API_URL}/chat/start",
            json={"message": message},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error starting chat: {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to the backend. Make sure the API is running.")
        return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


def continue_chat(session_id: str, message: str) -> Optional[dict]:
    """Continue an existing chat session"""
    try:
        response = requests.post(
            f"{API_URL}/chat/{session_id}",
            json={"message": message},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


def select_expert(session_id: str, expert_id: int) -> Optional[dict]:
    """Select an expert"""
    try:
        response = requests.post(
            f"{API_URL}/chat/{session_id}/select-expert",
            params={"expert_id": expert_id},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


def display_message(role: str, content: str):
    """Display a chat message"""
    if role == "user":
        st.markdown(f'<div class="user-message">🙋 {content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="assistant-message">🔐 {content}</div>', unsafe_allow_html=True)


def display_expert_card(expert_data: dict, index: int):
    """Display an expert card with selection button"""
    expert = expert_data.get("expert", {})
    match = expert_data.get("match", {})

    with st.container():
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"### {index}. {expert.get('name', 'Expert')}")
            st.markdown(f"**{expert.get('title', 'Security Expert')}**")
            st.markdown(f"⭐ {expert.get('rating', 'N/A')}/5 ({expert.get('total_reviews', 0)} reviews)")
            st.markdown(f"⏱️ Response time: {expert.get('response_time', 'Varies')}")
            st.markdown(f"💰 ${expert.get('hourly_rate', 'Contact')}/hour")

            # Match info
            match_score = match.get("match_score", 0)
            st.progress(match_score, text=f"Match: {match_score:.0%}")

            # Skills
            skills = expert.get("skills", [])[:4]
            if skills:
                st.markdown(f"**Skills:** {', '.join(skills)}")

        with col2:
            if st.button(f"Select", key=f"select_{expert.get('id', index)}"):
                return expert.get("id")

    st.divider()
    return None


def main():
    """Main application"""
    init_session_state()

    # Header
    st.markdown("""
    <div class="header">
        <h1>🔐 CyberSecAgent</h1>
        <p>Tell us about your security concern, and we'll connect you with the right expert.</p>
    </div>
    """, unsafe_allow_html=True)

    # Display chat history
    for msg in st.session_state.messages:
        display_message(msg["role"], msg["content"])

    # Display experts if available
    if st.session_state.experts and st.session_state.phase == "presenting":
        st.markdown("### Recommended Experts")

        for i, expert_data in enumerate(st.session_state.experts, 1):
            selected_id = display_expert_card(expert_data, i)

            if selected_id:
                # User selected an expert
                result = select_expert(st.session_state.session_id, selected_id)
                if result:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result.get("response", "Connecting you with the expert...")
                    })
                    st.session_state.phase = result.get("phase", "complete")
                    st.session_state.is_complete = result.get("is_complete", False)
                    st.session_state.experts = None
                    st.rerun()

    # Conversation complete message
    if st.session_state.is_complete:
        st.success("✅ You've been connected with an expert! Check your WhatsApp or email for next steps.")

        if st.button("Start New Conversation"):
            st.session_state.session_id = None
            st.session_state.messages = []
            st.session_state.phase = "start"
            st.session_state.experts = None
            st.session_state.is_complete = False
            st.rerun()

        return

    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Send to API
        if st.session_state.session_id is None:
            # Start new session
            result = start_chat(prompt)
            if result:
                st.session_state.session_id = result.get("session_id")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result.get("response", "")
                })
                st.session_state.phase = result.get("phase", "gathering")
        else:
            # Continue existing session
            result = continue_chat(st.session_state.session_id, prompt)
            if result:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result.get("response", "")
                })
                st.session_state.phase = result.get("phase", "gathering")
                st.session_state.is_complete = result.get("is_complete", False)

                # Store experts if available
                if result.get("experts"):
                    st.session_state.experts = result.get("experts")

        st.rerun()

    # Sidebar with session info
    with st.sidebar:
        st.markdown("### Session Info")
        st.markdown(f"**Session ID:** {st.session_state.session_id or 'Not started'}")
        st.markdown(f"**Phase:** {st.session_state.phase}")
        st.markdown(f"**Messages:** {len(st.session_state.messages)}")

        st.divider()

        if st.button("🔄 Reset Conversation"):
            st.session_state.session_id = None
            st.session_state.messages = []
            st.session_state.phase = "start"
            st.session_state.experts = None
            st.session_state.is_complete = False
            st.rerun()

        st.divider()
        st.markdown("""
        ### How it works
        1. Describe your security concern
        2. Our AI will ask clarifying questions
        3. We'll match you with expert professionals
        4. Choose an expert and get connected
        """)


if __name__ == "__main__":
    main()
