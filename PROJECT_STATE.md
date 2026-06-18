# CyberSecAgent - Project State

**Last Updated:** March 17, 2026
**Status:** MVP Complete - Ready for Testing

---

## Project Summary

**What it is:** AI-powered cybersecurity expert matching platform (like HeyMaya but for cybersecurity)

**How it works:**
1. User describes security problem in chat
2. Gemini AI asks clarifying questions (calming, empathetic)
3. Foundation-Sec-8B analyzes the threat
4. Neo4j graph finds matching experts
5. User selects expert → gets connected via WhatsApp/Email

---

## Architecture Decisions Made

| Decision | Choice | Reason |
|----------|--------|--------|
| Conversation AI | Gemini | Avoid OpenAI, good structured output |
| Security AI | Foundation-Sec-8B | Cybersecurity-pretrained model |
| Orchestration | LangGraph | State machine for conversation flow |
| Graph DB | Neo4j | Relationship-based expert matching |
| Relational DB | PostgreSQL | Expert profiles, conversations |
| Backend | FastAPI | Python, async, Pydantic integration |
| Frontend | Streamlit | MVP speed, Python-native |
| Outreach | Twilio + SendGrid | WhatsApp and Email |

---

## What's Built (Complete)

### Core System
- [x] Project structure and dependencies
- [x] Configuration management (.env)
- [x] Pydantic schemas (ProblemContext, SecurityAnalysis, Expert)
- [x] PostgreSQL models and connection
- [x] Neo4j connection and Cypher queries

### LLM Clients
- [x] Gemini client (conversation, extraction, presentation)
- [x] Foundation-Sec-8B client (threat analysis)
- [x] Structured output parsing

### LangGraph Workflow
- [x] State definition (AgentState)
- [x] Greeting node
- [x] Gathering node (ask questions)
- [x] Extraction node (conversation → structured data)
- [x] Security analysis node (Foundation-Sec)
- [x] Matching node (Neo4j search)
- [x] Presentation node (explain experts)
- [x] Selection node (handle user choice)
- [x] Handoff node (notify expert)
- [x] Workflow orchestration

### API Endpoints
- [x] POST /chat/start - Start conversation
- [x] POST /chat/{session_id} - Continue conversation
- [x] GET /chat/{session_id}/state - Get state
- [x] POST /chat/{session_id}/select-expert - Select expert
- [x] GET /experts - List experts
- [x] GET/POST/PUT/DELETE /experts/* - CRUD
- [x] GET /health/* - Health checks

### Frontend
- [x] Streamlit chat interface
- [x] Expert card display
- [x] Session management

### Services
- [x] WhatsApp integration (Twilio)
- [x] Email integration (SendGrid)
- [x] Handoff service

### Infrastructure
- [x] Docker Compose (PostgreSQL, Neo4j)
- [x] Dockerfile
- [x] Database init scripts
- [x] README documentation

---

## What's NOT Built (Future Work)

### High Priority
- [ ] User authentication/accounts
- [ ] Expert dashboard/portal
- [ ] Payment integration
- [ ] Real Foundation-Sec-8B local inference
- [ ] Production Neo4j graph population script
- [ ] Rate limiting

### Medium Priority
- [ ] Expert availability calendar
- [ ] Review/rating system
- [ ] Conversation history persistence
- [ ] Admin dashboard
- [ ] Analytics/metrics

### Low Priority
- [ ] Mobile app (React Native)
- [ ] Multi-language support
- [ ] Video consultation integration
- [ ] Expert verification workflow

---

## File Locations

```
C:\CyberSecAgent\
├── app\main.py                 # FastAPI entry
├── app\config.py               # Settings
├── app\agents\workflow.py      # LangGraph main
├── app\llm\gemini.py           # Gemini client
├── app\llm\foundation_sec.py   # Security AI
├── app\graph\search.py         # Neo4j search
├── app\db\models.py            # PostgreSQL models
├── frontend\streamlit_app.py   # Chat UI
├── scripts\init_postgres.sql   # DB seed
├── scripts\init_neo4j.cypher   # Graph seed
├── .env.example                # Environment template
└── README.md                   # Full docs
```

---

## How to Resume Development

### 1. Quick Start
```bash
cd C:\CyberSecAgent
venv\Scripts\activate
docker-compose up -d
python -m uvicorn app.main:app --reload
# New terminal:
streamlit run frontend/streamlit_app.py
```

### 2. Key Files to Modify

| To change... | Edit this file |
|--------------|----------------|
| AI personality | app\agents\prompts\system.py |
| Conversation flow | app\agents\workflow.py |
| Expert matching logic | app\graph\queries.py |
| Security analysis | app\llm\foundation_sec.py |
| API endpoints | app\api\*.py |
| Frontend UI | frontend\streamlit_app.py |

### 3. Testing the Flow
1. Open http://localhost:8501 (Streamlit)
2. Type: "my iPhone got hacked"
3. Follow the conversation
4. See expert recommendations
5. Select an expert

---

## Environment Variables Needed

```env
# Required
GOOGLE_API_KEY=your_key_here

# Optional (for full functionality)
TWILIO_ACCOUNT_SID=xxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
SENDGRID_API_KEY=xxx
SENDGRID_FROM_EMAIL=noreply@yourdomain.com
```

---

## Conversation Context

This project was built in one session with the following decisions:

1. **Two-agent system**: Gemini (conversation) + Foundation-Sec (security reasoning)
2. **Graph-based matching**: Neo4j for relationship traversal, not just keyword matching
3. **Calming UX**: AI is trained to be empathetic, never alarming, never gives DIY solutions
4. **Location-based**: Matches consider user location for timezone/regional experts
5. **Multi-channel outreach**: WhatsApp + Email for expert notifications

---

## Commands for Common Tasks

```bash
# Start everything
docker-compose up -d && python -m uvicorn app.main:app --reload

# View logs
docker-compose logs -f

# Reset databases
docker-compose down -v && docker-compose up -d

# Run specific test
pytest tests/test_workflow.py -v

# Check API docs
# Open http://localhost:8000/docs
```

---

## Contact / Resume Notes

To resume this project:
1. Read this file
2. Read README.md for setup
3. Key decision: We chose Gemini over OpenAI per user preference
4. The Foundation-Sec model falls back to Gemini if not loaded locally
5. Mock experts are in app\agents\nodes\matching.py for testing

---

*This file was auto-generated to preserve project state for resumption.*
