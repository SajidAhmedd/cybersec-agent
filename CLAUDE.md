# Claude Code Context - CyberSecAgent

## Project Type
AI-powered cybersecurity expert matching platform (inspired by HeyMaya)

## Core Concept
Users describe security incidents → AI chat gathers info → Diagnoses problem → Matches with experts → Connects via WhatsApp/Email

## Tech Stack
- **Backend:** Python 3.13, FastAPI, Pydantic
- **AI:** Google Gemini 2.0 Flash (conversation), Foundation-Sec-8B (security analysis)
- **Orchestration:** LangGraph (state machine - defined but manually executed)
- **Databases:** Neo4j (graph), PostgreSQL + SQLAlchemy (profiles)
- **Frontend:** Next.js 14, TypeScript, Tailwind CSS, Lucide React
- **Outreach:** Twilio (WhatsApp), SendGrid (Email)

## Key Design Decisions
1. NO OpenAI - use Gemini instead
2. Two-agent system: conversation AI + security AI
3. Graph-based matching (Neo4j) for relationship traversal
4. Calming UX - never alarming, never gives DIY solutions
5. Location-aware matching
6. **Diagnosis before experts** - AI explains what the problem likely is before presenting experts
7. **Post-handoff conversation** - Users can continue chatting after selecting an expert
8. **Question detection** - User questions during gathering are answered, not treated as info

## Important Files

### Backend - Agents
- `app/agents/workflow.py` - Main LangGraph flow & ChatWorkflow class
- `app/agents/states.py` - AgentState TypedDict definition
- `app/agents/nodes/` - Individual workflow nodes:
  - `greeting.py` - Welcome message
  - `gathering.py` - Follow-up questions
  - `extraction.py` - Parse to ProblemContext (includes `_is_question()` detection)
  - `security_analysis.py` - Threat classification
  - `matching.py` - Expert search
  - `presentation.py` - Diagnosis + expert presentation
  - `selection.py` - Handle expert choice
  - `handoff.py` - Connect with expert
  - `conversation.py` - Post-handoff free chat

### Backend - Prompts
- `app/agents/prompts/system.py` - AI personality (calming, professional)
- `app/agents/prompts/gathering.py` - Question-asking prompts with WRONG/RIGHT examples
- `app/agents/prompts/presentation.py` - Two-part prompt: DIAGNOSIS + EXPERT INTRODUCTION

### Backend - Core
- `app/llm/gemini.py` - Gemini client (singleton)
- `app/llm/foundation_sec.py` - Security analysis AI
- `app/graph/search.py` - Neo4j expert matching
- `app/db/postgres.py` - PostgreSQL connection
- `app/main.py` - FastAPI app entry point
- `app/api/chat.py` - Chat API endpoints

### Frontend
- `frontend-next/src/app/page.tsx` - Main chat page with expert popup
- `frontend-next/src/lib/useChat.ts` - Chat state management hook
- `frontend-next/src/components/` - UI components (Header, ChatMessage, ChatInput, ExpertList)

## Conversation Flow (Phases)
```
greeting → gathering ⟲ extraction → security_analysis → matching → presenting → selecting → handoff → conversation
                ↑_________|                                                                              ↓
            (loop if need more info)                                                          (free chat continues)
```

1. **GREETING** - Welcome, calm user
2. **GATHERING** - Ask questions (answers user questions first if they ask)
3. **EXTRACTION** - Convert to structured ProblemContext (Pydantic)
   - Requires: device/platform + 2 of (symptoms, timeline, impact)
   - Questions don't count as extraction attempts
4. **SECURITY_ANALYSIS** - Foundation-Sec threat classification
5. **MATCHING** - Neo4j/PostgreSQL expert search
6. **PRESENTATION** - **Diagnosis first**, then expert introduction
7. **SELECTION** - User picks expert (conversational responses if unclear)
8. **HANDOFF** - Connect user with expert, show contact options
9. **CONVERSATION** - Post-handoff free chat (experts not shown again)

## Environment Variables (.env)
```
GOOGLE_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash
USE_MOCK_LLM=false
DATABASE_URL=postgresql://...
NEO4J_URI=bolt://...
NEO4J_USER=neo4j
NEO4J_PASSWORD=...
```

## Running the Project

### Backend
```bash
cd C:\CyberSecAgent
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd C:\CyberSecAgent\frontend-next
npm run dev
```

Access at: http://localhost:3000

## Recent Updates
- Migrated frontend from Streamlit to Next.js
- Added diagnosis before expert presentation
- Added post-handoff conversation capability
- Added question detection in extraction node
- Added expert selection popup with WhatsApp/Email/Schedule options
- Fixed conversation history preservation across all nodes
- Improved prompts with WRONG vs RIGHT examples for better responses

## Next Steps
- Add user authentication
- Build expert dashboard
- Populate production Neo4j graph
- Add payment integration
- Add real WhatsApp/Email integration in popup
