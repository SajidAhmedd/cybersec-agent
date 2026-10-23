# CyberSecAgent

AI-powered platform for matching cybersecurity incidents with expert professionals.

## Overview

CyberSecAgent uses a multi-agent AI system to:
1. **Understand** your security concern through natural conversation
2. **Analyze** the threat using specialized cybersecurity AI
3. **Match** you with the right expert using graph-based search
4. **Connect** you with the expert via WhatsApp or Email

## Architecture

```
User
  ↓
┌─────────────────────────────────────────────────────────┐
│                    STREAMLIT FRONTEND                   │
└─────────────────────────┬───────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                      │
│                      POST /chat                         │
└─────────────────────────┬───────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                 LANGGRAPH ORCHESTRATOR                  │
│   GREETING → GATHERING → ANALYSIS → MATCHING → HANDOFF │
└────────────┬────────────────────────────┬───────────────┘
             ↓                            ↓
┌────────────────────────┐   ┌────────────────────────────┐
│ GROQ / CLAUDE (Convo) │   │ FOUNDATION-SEC (Analysis)  │
│   • Talk to user       │   │ • Threat classification    │
│   • Ask questions      │   │ • Skill mapping            │
│   • Present experts    │   │ • Severity assessment      │
└────────────────────────┘   └────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                       NEO4J                             │
│              Expert Knowledge Graph                     │
│   (Threat)──[:REQUIRES]──>(Skill)──[:HAS_SKILL]──>(Expert)│
└─────────────────────────┬───────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                     POSTGRESQL                          │
│                  Expert Full Profiles                   │
└─────────────────────────────────────────────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python, FastAPI |
| Agent Orchestration | LangGraph |
| Conversation AI | Groq (default) or Anthropic Claude |
| Security AI | Foundation-Sec-8B |
| Graph Database | Neo4j |
| Relational Database | PostgreSQL |
| Frontend | Streamlit |
| Validation | Pydantic |
| Outreach | Twilio (WhatsApp), SendGrid (Email) |

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Groq API key (free) or Anthropic API key (for Claude)

### 1. Clone and Setup

```bash
cd C:\CyberSecAgent

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example env file
copy .env.example .env

# Edit .env and add your API keys:
# - GROQ_API_KEY (required with LLM_PROVIDER=groq, the default)
# - ANTHROPIC_API_KEY (required with LLM_PROVIDER=claude)
# - Twilio credentials (optional, for WhatsApp)
# - SendGrid credentials (optional, for Email)
```

### 3. Start Databases

```bash
# Start PostgreSQL and Neo4j
docker-compose up -d postgres neo4j

# Wait for them to be ready
docker-compose ps
```

### 4. Initialize Databases

```bash
# PostgreSQL - run the init script
docker exec -i cybersec_postgres psql -U postgres -d cybersec_agent < scripts/init_postgres.sql

# Neo4j - open browser at http://localhost:7474
# Login with neo4j/neo4j123
# Run the contents of scripts/init_neo4j.cypher
```

### 5. Run the Backend

```bash
# Run FastAPI server
python -m uvicorn app.main:app --reload --port 8000

# API docs available at http://localhost:8000/docs
```

### 6. Run the Frontend

```bash
# In a new terminal
streamlit run frontend/streamlit_app.py

# Opens at http://localhost:8501
```

## Deployment

See [DEPLOY.md](DEPLOY.md) for a free-tier deployment (Vercel + Render + Neon + Neo4j AuraDB + Groq).

## API Endpoints

### Chat

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat/start` | POST | Start a new chat session |
| `/chat/{session_id}` | POST | Continue a chat session |
| `/chat/{session_id}/state` | GET | Get session state |
| `/chat/{session_id}/select-expert` | POST | Select an expert |

### Experts

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/experts` | GET | List all experts |
| `/experts/{id}` | GET | Get expert details |
| `/experts` | POST | Create new expert |

### Health

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Basic health check |
| `/health/ready` | GET | Readiness check |
| `/health/live` | GET | Liveness check |

## Project Structure

```
CyberSecAgent/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Settings management
│   ├── api/                  # API endpoints
│   │   ├── chat.py
│   │   ├── experts.py
│   │   └── health.py
│   ├── agents/               # LangGraph workflow
│   │   ├── workflow.py      # Main workflow
│   │   ├── states.py        # State definitions
│   │   ├── nodes/           # Workflow nodes
│   │   └── prompts/         # AI prompts
│   ├── llm/                  # LLM clients
│   │   ├── provider.py      # Picks the LLM client
│   │   ├── groq_client.py   # Groq client
│   │   ├── claude.py        # Claude client
│   │   └── foundation_sec.py # Security AI client
│   ├── graph/                # Neo4j integration
│   │   ├── connection.py
│   │   ├── queries.py
│   │   └── search.py
│   ├── db/                   # PostgreSQL integration
│   │   ├── postgres.py
│   │   └── models.py
│   ├── services/             # Business services
│   │   ├── handoff.py
│   │   └── outreach/
│   └── schemas/              # Pydantic models
├── frontend/
│   └── streamlit_app.py     # Chat UI
├── scripts/
│   ├── init_postgres.sql    # DB initialization
│   └── init_neo4j.cypher    # Graph initialization
├── tests/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Configuration

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `LLM_PROVIDER` | `groq` (default) or `claude` |
| `GROQ_API_KEY` | Groq API key (when `LLM_PROVIDER=groq`) |
| `ANTHROPIC_API_KEY` | Anthropic API key (when `LLM_PROVIDER=claude`) |

### Optional Environment Variables

| Variable | Description |
|----------|-------------|
| `POSTGRES_*` | PostgreSQL connection settings |
| `NEO4J_*` | Neo4j connection settings |
| `TWILIO_*` | Twilio credentials for WhatsApp |
| `SENDGRID_*` | SendGrid credentials for Email |

## Development

### Running Tests

```bash
pytest tests/
```

### Code Structure

- **Agents**: LangGraph-based conversation workflow
- **LLM**: Groq or Claude for conversation, Foundation-Sec for security analysis
- **Graph**: Neo4j for relationship-based expert matching
- **Services**: Business logic for handoff and notifications

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request
