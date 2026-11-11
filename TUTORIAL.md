# CyberSecAgent: A Beginner's Tutorial

This tutorial walks you through the whole code base of CyberSecAgent, file by file and function by function: the Python backend, the databases, the AI parts and the Next.js frontend. By the end you should be able to explain what every part does, why it was written that way, and where you would change it.

You need mid-level Python: functions, classes, imports and `try/except`. You do **not** need to know web frameworks, databases, graph databases, AI libraries, TypeScript or React. Each one is explained when it first appears.

## Contents

1. [How to use this tutorial](#1-how-to-use-this-tutorial)
2. [The big picture](#2-the-big-picture)
3. [Folder map](#3-folder-map)
4. [Python concepts you need](#4-python-concepts-you-need)
5. [The libraries](#5-the-libraries)
6. [Every file and every function](#6-every-file-and-every-function)
7. [One conversation traced from start to finish](#7-one-conversation-traced-from-start-to-finish)
8. [Things to notice](#8-things-to-notice)
9. [Exercises](#9-exercises)
10. [Glossary](#10-glossary)

---

## 1. How to use this tutorial

This tutorial is meant to be read **next to the code**, not on its own.

1. Open the repo folder in VS Code (`File → Open Folder…`).
2. Open `TUTORIAL.md` and press **Ctrl+K V** (Cmd+K V on a Mac). The Markdown preview opens in a side panel, so the tutorial sits on the right and the code on the left.
3. Every link like [app/agents/workflow.py:180-229](app/agents/workflow.py#L180-L229) is clickable. In the preview, clicking it opens that file at those lines. Read the explanation, then look left at the real code.
4. Links to sections of this file (like the contents list above) jump inside the tutorial.

Why read this way? You only really understand code by reading it. The tutorial tells you *what to look for* and *why it's there*; the code shows you *exactly how*. Snippets here are short extracts. The link always takes you to the full version.

This is the biggest of the projects (about 4,500 lines of Python and 1,300 of TypeScript), so take it in pieces. Read sections 2 to 5 first. Section 6 follows the order in which files import each other, so each file comes after the files it depends on. A good plan is one sub-section per sitting.

---

## 2. The big picture

### What the project does

Someone has a security problem: *"My iPhone is acting strange and I think it's been hacked."* They don't know what kind of expert they need, and they're stressed. CyberSecAgent is a chat assistant (called **Maya** in its prompts) that:

1. **Talks** with them calmly and asks one question at a time until it understands the problem.
2. **Extracts** the facts from the chat into a structured record: device, symptoms, timeline, urgency…
3. **Analyses** the threat: what kind of attack, how serious, and which **skills** an expert would need.
4. **Matches** experts by searching a **graph database** (Neo4j) for experts with those skills, platforms and services.
5. **Presents** the best experts as cards, with a short diagnosis.
6. **Hands off**: when the user picks one, it explains how to contact them and (optionally) notifies the expert by WhatsApp or email.

Each step is a separate function, called a **node**, and a library called **LangGraph** decides which node runs next.

### How the pieces fit together

```
                   Browser
                      │
                      ▼
   ┌──────────────────────────────────────────┐
   │  Next.js frontend   (frontend-next/)      │   React page: chat bubbles,
   │  page.tsx ─ useChat.ts ─ api.ts           │   expert cards, contact popup
   └──────────────────────────────────────────┘
                      │  HTTP + JSON   POST /chat/start, POST /chat/{id},
                      ▼                POST /chat/{id}/select-expert
   ┌──────────────────────────────────────────┐
   │  FastAPI backend   (app/main.py)          │
   │   CORS ─ rate limit ─ routes (app/api/)   │
   └──────────────────────────────────────────┘
                      │  ChatWorkflow.chat(session_id, message)
                      ▼
   ┌───────────────────────────────────────────────────────────────────┐
   │  LangGraph workflow  (app/agents/workflow.py)                      │
   │                                                                    │
   │  entry: route_by_phase ──► greeting | extraction | selection |     │
   │                            handoff  | conversation                 │
   │                                                                    │
   │  extraction ─(enough info?)─► analyze_security ─► matching ─►      │
   │      │ no                                          presentation    │
   │      ▼                                                             │
   │  gathering (ask another question)                                  │
   │                                                                    │
   │  selection ─(expert picked?)─► handoff                             │
   └───────────────────────────────────────────────────────────────────┘
        │                    │                     │               │
        ▼                    ▼                     ▼               ▼
   ┌──────────┐      ┌──────────────┐      ┌─────────────┐  ┌──────────────┐
   │ LLM      │      │ Neo4j graph  │      │ PostgreSQL  │  │ Twilio /     │
   │ Groq or  │      │ (Skill)<-    │      │ expert      │  │ SendGrid     │
   │ Claude   │      │ [:HAS_SKILL]-│      │ profiles +  │  │ (off by      │
   │ (app/llm)│      │ (Expert)     │      │ chat logs   │  │  default)    │
   └──────────┘      │ (app/graph)  │      │ (app/db)    │  │(app/services)│
                     └──────────────┘      └─────────────┘  └──────────────┘
```

Three ideas to keep in mind:

- **One graph run per message.** The workflow doesn't loop waiting for the user. Each HTTP request runs the graph from the node for the current *phase* until the assistant has something to say, then stops. The phase is saved, so the next message knows where to continue.
- **Two databases, two jobs.** Neo4j stores *relationships* (expert → skill, expert → platform) and is good at "who has these skills?". PostgreSQL stores full *profiles* (bio, rate, contact details) and chat records. Matching asks Neo4j for IDs, then fetches the profiles from PostgreSQL.
- **It works without keys.** With no LLM key the clients switch to **mock mode** and return canned answers, and if a database is down, matching falls back to three hard-coded sample experts. Great for a demo; it also hides problems ([section 8](#8-things-to-notice)).

---

## 3. Folder map

Every file in the repo, one line each.

```
cybersec-agent/
├── .dockerignore                 files Docker should not copy into the backend image
├── .env.example                  template for your settings and secrets (see section 8 before copying it)
├── .github/workflows/ci.yml      GitHub Actions: backend tests + frontend type-check and build
├── .gitignore                    files git ignores (.env, node_modules, featured_experts.json…)
├── DEPLOY.md                     free hosting guide: Vercel + Render + Neon + Neo4j AuraDB + Groq
├── Dockerfile                    backend container: Python 3.11, requirements, app/ folder, uvicorn
├── LICENSE                       MIT licence
├── README.md                     overview and local setup (still describes the older Streamlit UI)
├── docker-compose.yml            local PostgreSQL + Neo4j (+ backend and a broken frontend service)
├── requirements.txt              backend Python packages
├── requirements-local-model.txt  extra packages to run Foundation-Sec-8B locally (needs a GPU)
├── requirements-streamlit.txt    extra packages for the old Streamlit UI
├── start-all.bat                 Windows: start backend (port 8003) and frontend together
├── start-backend.bat             Windows: start only the backend on port 8003
├── start-frontend.bat            Windows: start only the Next.js frontend
├── app/                          the FastAPI backend package
│   ├── __init__.py               one-line docstring; marks app/ as a package
│   ├── main.py                   creates the FastAPI app, CORS, routers, start-up/shut-down
│   ├── config.py                 every setting in one Settings class, read from env vars / .env
│   ├── agents/
│   │   ├── __init__.py           re-exports create_chat_workflow, ChatWorkflow, AgentState
│   │   ├── states.py             AgentState: the dict passed between nodes
│   │   ├── workflow.py           the LangGraph graph, routing functions, per-session state
│   │   ├── nodes/
│   │   │   ├── __init__.py       re-exports the nine node functions
│   │   │   ├── greeting.py       first reply to a new chat
│   │   │   ├── gathering.py      asks the next follow-up question
│   │   │   ├── extraction.py     chat → structured ProblemContext; decides "enough info?"
│   │   │   ├── security_analysis.py  ProblemContext → SecurityAnalysis (threat, skills)
│   │   │   ├── matching.py       graph search + profiles + featured/external ordering
│   │   │   ├── presentation.py   writes the diagnosis + expert introductions
│   │   │   ├── selection.py      works out which expert the user chose
│   │   │   ├── handoff.py        confirms the choice, contact options, optional notification
│   │   │   └── conversation.py   free chat after the handoff
│   │   └── prompts/
│   │       ├── __init__.py       re-exports five prompt constants
│   │       ├── system.py         Maya's personality and rules; greeting instructions
│   │       ├── gathering.py      gathering, extraction and (unused) sufficiency prompts
│   │       └── presentation.py   presentation, handoff, external handoff, post-handoff prompts
│   ├── api/
│   │   ├── __init__.py           re-exports the three routers
│   │   ├── chat.py               /chat endpoints: start, continue, state, end, select-expert
│   │   ├── experts.py            /experts endpoints: list, get, and admin create/update/delete
│   │   ├── health.py             /health, /health/ready, /health/live
│   │   ├── rate_limit.py         per-IP message limits (in memory)
│   │   └── security.py           X-Admin-Key check for admin endpoints
│   ├── db/
│   │   ├── __init__.py           re-exports engine, sessions and models
│   │   ├── postgres.py           SQLAlchemy engine, sessions, init_db()
│   │   ├── models.py             tables: experts, skills, certifications, reviews, conversations…
│   │   └── conversations.py      saves each chat turn to PostgreSQL
│   ├── graph/
│   │   ├── __init__.py           re-exports the graph classes
│   │   ├── connection.py         Neo4j driver wrapper (handles encrypted AuraDB URIs)
│   │   ├── queries.py            builds the Cypher search query
│   │   └── search.py             runs the search and turns rows into ExpertMatch objects
│   ├── llm/
│   │   ├── __init__.py           re-exports the LLM classes and helpers
│   │   ├── provider.py           picks the Groq or Claude client from LLM_PROVIDER
│   │   ├── groq_client.py        Groq chat + JSON-schema structured output
│   │   ├── claude.py             Anthropic Claude chat + structured output
│   │   ├── foundation_sec.py     security analysis (local Foundation-Sec-8B or the chat LLM)
│   │   ├── mock.py               canned replies and objects for mock mode
│   │   └── structured.py         JSON-extraction helpers (unused by the app)
│   ├── schemas/
│   │   ├── __init__.py           re-exports the main schemas
│   │   ├── problem.py            ProblemContext: what the user told us
│   │   ├── security.py           SecurityAnalysis: what the threat is and needs
│   │   ├── expert.py             Expert, ExpertMatch, ExpertRecommendation, public_expert()
│   │   └── conversation.py       message/phase/state models (mostly unused)
│   └── services/
│       ├── __init__.py           re-exports HandoffService
│       ├── handoff.py            sends expert (and client) notifications
│       └── outreach/
│           ├── __init__.py       re-exports WhatsAppService, EmailService
│           ├── email.py          SendGrid email sending and templates
│           └── whatsapp.py       Twilio WhatsApp sending and templates
├── frontend/
│   └── streamlit_app.py          the old Streamlit chat UI (legacy)
├── frontend-next/                the current Next.js (React + TypeScript) frontend
│   ├── next-env.d.ts             TypeScript types for Next.js (generated, don't edit)
│   ├── next.config.js            Next.js settings (an /api rewrite that the code doesn't use)
│   ├── package.json              JavaScript dependencies and npm scripts
│   ├── package-lock.json         exact installed versions (generated by npm)
│   ├── postcss.config.js         runs Tailwind and Autoprefixer on the CSS
│   ├── start-dev.cmd             Windows helper: npm run dev
│   ├── tailwind.config.ts        Tailwind settings: which files to scan, extra colours
│   ├── tsconfig.json             TypeScript compiler settings, the "@/" import alias
│   └── src/
│       ├── app/
│       │   ├── globals.css       Tailwind layers, scrollbar, typing-dots and popup animations
│       │   ├── layout.tsx        the HTML shell: font, page title, <body>
│       │   └── page.tsx          the one page: welcome screen, chat, expert list, contact popup
│       ├── components/
│       │   ├── index.ts          re-exports the five components
│       │   ├── ChatInput.tsx     the message box and send button
│       │   ├── ChatMessage.tsx   one chat bubble
│       │   ├── ExpertCard.tsx    one expert card
│       │   ├── ExpertList.tsx    grid of expert cards
│       │   └── Header.tsx        logo, phase label, progress dots, New Chat button
│       ├── lib/
│       │   ├── api.ts            fetch() calls to the backend
│       │   └── useChat.ts        React hook holding the chat state
│       └── types/
│           └── index.ts          TypeScript interfaces matching the API's JSON
├── scripts/
│   ├── init_postgres.sql         PostgreSQL tables + 20 skills, 15 certifications, 3 sample experts
│   ├── init_neo4j.cypher         Neo4j constraints + skills, threats, services, platforms, 3 experts
│   ├── seed_databases.py         runs both scripts and syncs the JSON expert files
│   ├── external_experts.json     public freelancer profiles (links only) to list
│   ├── external_experts.example.json  the format for that file
│   └── featured_experts.example.json  the format for featured experts (real file is git-ignored)
└── tests/
    ├── test_handoff.py           3 tests for contact options
    └── test_matching.py          6 tests for ordering, privacy filtering and score scaling
```

---

## 4. Python concepts you need

These are the Python features this code uses beyond "functions, classes, imports, try/except". Each has a one-line recap and a pointer to an example.

**Type hints.** `def get_llm() -> LLMClient:` documents the return type. Python doesn't enforce them, but Pydantic and FastAPI **do** read them to validate data. [app/llm/provider.py:29](app/llm/provider.py#L29).

**`Optional`, `Union`, `X | None`, `list[str]`.** `Optional[str]` means "str or None"; `Union[GroqClient, ClaudeClient]` means "either"; `int | None` is the newer spelling of `Optional[int]`. [app/llm/provider.py:12](app/llm/provider.py#L12), [app/agents/workflow.py:238](app/agents/workflow.py#L238).

**`TypeVar` and generics.** `T = TypeVar('T', bound=BaseModel)` lets `generate_structured(..., response_model: Type[T]) -> T` say "you get back an instance of whichever model class you pass in". [app/llm/groq_client.py:14](app/llm/groq_client.py#L14), [app/llm/groq_client.py:126-131](app/llm/groq_client.py#L126-L131).

**`Literal`.** `-> Literal["analyze", "ask_more"]` means the function returns exactly one of those strings. [app/agents/workflow.py:45](app/agents/workflow.py#L45).

**Enums.** `class UrgencyLevel(str, Enum)` defines a fixed set of allowed values. Inheriting from `str` too makes each member also a plain string, so it turns into JSON nicely. [app/schemas/problem.py:12-16](app/schemas/problem.py#L12-L16).

**`TypedDict`.** A dict type that lists its keys and value types; still a normal dict at runtime. [app/agents/states.py:9-43](app/agents/states.py#L9-L43).

**`@dataclass`.** Writes `__init__` for you from typed fields. [app/graph/queries.py:10-25](app/graph/queries.py#L10-L25).

**`@property`.** A method you read like an attribute: `settings.database_url` runs code. [app/config.py:81-86](app/config.py#L81-L86).

**`@staticmethod`.** A method that doesn't use `self`; it lives in the class only for organisation. [app/llm/groq_client.py:62-78](app/llm/groq_client.py#L62-L78).

**Module-level singletons with `global`.** A module variable starts as `None`; a `get_x()` function creates the object the first time and returns the same one afterwards. Used for the LLM client, Neo4j connection, workflow and services. [app/llm/provider.py:26-38](app/llm/provider.py#L26-L38).

**Module code runs on import.** `settings = Settings()` and the two `print`s at the bottom of [app/config.py:127-131](app/config.py#L127-L131) run the first time anything imports `app.config`. So a bad `.env` crashes *every* import.

**Imports inside functions.** `from transformers import ...` inside `_load_local_model` means the heavy library is only needed if you use that feature. It also avoids *circular imports* (two modules importing each other at the top). [app/llm/foundation_sec.py:77-78](app/llm/foundation_sec.py#L77-L78), [app/llm/foundation_sec.py:131](app/llm/foundation_sec.py#L131).

**Dict unpacking `{**state, "k": v}`.** A new dict copied from `state` with `k` set. Every node returns this. [app/agents/nodes/greeting.py:48-53](app/agents/nodes/greeting.py#L48-L53).

**Context managers and `@contextmanager`.** `with get_db_context() as db:` runs setup, gives you `db`, then always runs cleanup. The `@contextmanager` decorator builds one from a generator: code before `yield` is setup, code after it is cleanup. [app/db/postgres.py:44-58](app/db/postgres.py#L44-L58).

**Generators with `yield`.** A function with `yield` hands out a value and pauses. FastAPI uses this for dependencies: `get_db` yields a session, the route runs, then the `finally` closes it. [app/db/postgres.py:32-41](app/db/postgres.py#L32-L41).

**`async def` / `await`.** An `async` function can pause while waiting for the network and let the server serve someone else. FastAPI routes here are `async def`. The LLM calls inside them are *not* async, which matters ([section 8](#8-things-to-notice)). [app/api/chat.py:44-45](app/api/chat.py#L44-L45).

**`@asynccontextmanager` lifespan.** Code before `yield` runs when the server starts, code after it when it stops. [app/main.py:17-44](app/main.py#L17-L44).

**Lambdas.** Tiny nameless functions: `"groq": lambda: settings.groq_api_key` stores "how to get the key" rather than the key itself. [app/llm/provider.py:20-23](app/llm/provider.py#L20-L23).

**`dict.fromkeys(...)` to de-duplicate in order.** `list(dict.fromkeys(items))` removes duplicates but keeps the first-seen order, unlike `set()`. [app/llm/foundation_sec.py:148](app/llm/foundation_sec.py#L148).

**`next(generator, default)`.** Returns the first item that matches, or `default`. [app/agents/nodes/matching.py:121](app/agents/nodes/matching.py#L121).

**`collections.deque` and `defaultdict`.** A deque is a list that's fast to pop from the left; a defaultdict creates a missing key's value automatically. [app/api/rate_limit.py:17](app/api/rate_limit.py#L17).

**`threading.Lock`.** Makes sure only one thread at a time runs the code inside `with _lock:`. [app/api/rate_limit.py:18](app/api/rate_limit.py#L18), [app/api/rate_limit.py:29](app/api/rate_limit.py#L29).

**f-strings with doubled braces.** In `f"{{ ... }}"` or a template filled by `.format()`, `{{` prints a literal `{`. That's how the prompts contain JSON examples. [app/agents/prompts/gathering.py:67-80](app/agents/prompts/gathering.py#L67-L80).

**Regular expressions.** `re.sub(r"[\s\-/]+", "_", name)` replaces spaces, dashes and slashes with `_`. [app/llm/foundation_sec.py:25-27](app/llm/foundation_sec.py#L25-L27).

### A tiny TypeScript and React primer (for frontend-next/)

- **TypeScript** is JavaScript with type hints, checked before running. `interface Expert { id: number; name: string; bio?: string }` is like a TypedDict; `?` means optional. [frontend-next/src/types/index.ts:30-60](frontend-next/src/types/index.ts#L30-L60).
- **`async`/`await` and `fetch`** work like Python's: `await fetch(url)` waits for an HTTP response. [frontend-next/src/lib/api.ts:29-38](frontend-next/src/lib/api.ts#L29-L38).
- **React components** are functions that return HTML-like **JSX**. `{expert.name}` inserts a value; `{cond && <div/>}` shows the div only if `cond` is true; `list.map(x => <Card/>)` repeats. [frontend-next/src/components/ChatMessage.tsx:10-52](frontend-next/src/components/ChatMessage.tsx#L10-L52).
- **Props** are a component's inputs, like function arguments. [frontend-next/src/components/ExpertList.tsx:7-11](frontend-next/src/components/ExpertList.tsx#L7-L11).
- **State with `useState`.** `const [x, setX] = useState(0)` stores a value React remembers between redraws; calling `setX` redraws the component. [frontend-next/src/lib/useChat.ts:17-26](frontend-next/src/lib/useChat.ts#L17-L26).
- **Hooks** are functions starting with `use`. `useEffect(fn, [deps])` runs `fn` after a redraw when `deps` change; `useCallback` keeps the same function object between redraws; `useRef` holds a value (often a page element) without causing redraws. A *custom hook* (`useChat`) bundles state and functions for reuse.
- **`'use client'`** at the top tells Next.js this file runs in the browser (it uses state and clicks).
- **Tailwind classes** like `px-4 py-2 rounded-xl bg-white` are small CSS utilities written directly on elements: padding, rounded corners, background.

---

## 5. The libraries

### Backend (requirements.txt)

**FastAPI** (`fastapi`). A web framework: you write Python functions and decorate them with a URL; FastAPI reads JSON bodies into Pydantic models, validates them, runs *dependencies* (like rate limits), and turns your return value into JSON. It also generates interactive docs at `/docs`.

```python
from fastapi import FastAPI
app = FastAPI()

@app.get("/hello/{name}")
async def hello(name: str):
    return {"message": f"Hi {name}"}
```
*Why here:* the browser talks to the backend through HTTP endpoints.
*Where:* [app/main.py:48-87](app/main.py#L48-L87), all of [app/api](app/api/chat.py).

**Uvicorn** (`uvicorn[standard]`). The server program that listens on a port and passes requests to FastAPI. `uvicorn app.main:app` means "the `app` variable in `app/main.py`".
*Where:* [Dockerfile:17](Dockerfile#L17), [start-backend.bat:7](start-backend.bat#L7), [app/main.py:102-109](app/main.py#L102-L109).

**Pydantic** (`pydantic`). Describe data as a class with typed fields; Pydantic validates and converts real data, and can describe the class as a **JSON Schema** (`model_json_schema()`), which is how the LLMs are told what JSON to produce.

```python
from pydantic import BaseModel, Field
class Item(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
Item(score=1.5)          # ValidationError: must be <= 1
Item.model_validate_json('{"score": 0.4}')
```
*Where:* every file in [app/schemas](app/schemas/problem.py), the request models in [app/api/chat.py:18-41](app/api/chat.py#L18-L41).

**pydantic-settings** (`pydantic-settings`). Fills a Pydantic class from environment variables and a `.env` file.
*Where:* [app/config.py:6](app/config.py#L6), [app/config.py:115-118](app/config.py#L115-L118).

**python-dotenv** (`python-dotenv`). Reads `.env` files. Never imported directly; pydantic-settings uses it to read `env_file`.

**LangGraph** (`langgraph==0.0.26`). Builds a workflow as a graph of **nodes** (functions) and **edges** (what runs next). A shared **state** dict flows through. *Conditional edges* call a function that returns a label to choose the next node; a *conditional entry point* chooses where to start. `compile()` turns the description into something you can `.invoke(state)`.

```python
from langgraph.graph import StateGraph, END
g = StateGraph(dict)
g.add_node("hi", lambda s: {**s, "reply": "hello"})
g.set_entry_point("hi")
g.add_edge("hi", END)
print(g.compile().invoke({}))
```
*Where:* only [app/agents/workflow.py](app/agents/workflow.py#L69-L149). This is a very early LangGraph version; newer ones changed some method names.

**Anthropic SDK** (`anthropic`). The official Python client for Claude.
*Where:* [app/llm/claude.py](app/llm/claude.py#L56).

**Groq SDK** (`groq`). The official Python client for Groq, a service that runs open models fast with a free tier. Its interface mirrors OpenAI's: `client.chat.completions.create(model=..., messages=[...])`.

```python
import groq
r = groq.Groq(api_key="...").chat.completions.create(
    model="openai/gpt-oss-120b", messages=[{"role": "user", "content": "Hi"}])
print(r.choices[0].message.content)
```
*Where:* [app/llm/groq_client.py](app/llm/groq_client.py#L46).

**Neo4j driver** (`neo4j`) and **certifi** (`certifi`). Neo4j is a **graph database**: data is stored as *nodes* (with labels like `Expert`, `Skill`) and *relationships* between them (`HAS_SKILL`). You query it with **Cypher**, a language that draws patterns with ASCII art:

```cypher
MATCH (e:Expert)-[:HAS_SKILL]->(s:Skill {name: 'mobile_security'})
RETURN e.name
```

"Find experts connected by a `HAS_SKILL` arrow to the `mobile_security` skill." The Python driver sends such queries and returns rows. `certifi` provides a bundle of trusted certificate authorities, used to verify encrypted connections to Neo4j AuraDB.
*Where:* [app/graph/connection.py](app/graph/connection.py#L6-L7), [app/graph/queries.py](app/graph/queries.py#L33-L144), [scripts/init_neo4j.cypher](scripts/init_neo4j.cypher).

**SQLAlchemy** (`sqlalchemy`) and **psycopg2** (`psycopg2-binary`). SQLAlchemy is an **ORM** (object-relational mapper): you describe tables as Python classes and query with Python (`db.query(Expert).filter(Expert.id == 3)`) instead of writing SQL strings. psycopg2 is the low-level driver SQLAlchemy uses to talk to PostgreSQL.

```python
expert = db.query(Expert).filter(Expert.email == "a@b.com").first()
expert.is_active = False
db.commit()
```
*Where:* [app/db](app/db/models.py), [app/api/experts.py](app/api/experts.py).

**asyncpg** (`asyncpg`). An async PostgreSQL driver. **Not used**: it only appears in the unused `async_database_url` property.

**Twilio** (`twilio`) and **SendGrid** (`sendgrid`). Paid services for sending WhatsApp messages and emails from code.
*Where:* [app/services/outreach/whatsapp.py:7](app/services/outreach/whatsapp.py#L7), [app/services/outreach/email.py:7-8](app/services/outreach/email.py#L7-L8). They only send when `OUTREACH_ENABLED=true`.

**httpx** (`httpx`), **tenacity** (`tenacity`), **python-multipart** (`python-multipart`). Not imported by the project. httpx is used *inside* the Groq and Anthropic SDKs; tenacity (retry helpers) and python-multipart (form uploads) are unused.

**pytest** (`pytest`) and **pytest-asyncio** (`pytest-asyncio`). pytest runs `test_*` functions in `tests/`. pytest-asyncio is for async tests; none exist yet.

### Optional extras

**transformers**, **torch**, **accelerate** ([requirements-local-model.txt](requirements-local-model.txt)). Hugging Face's library for running models locally, PyTorch, and a helper that spreads a model across your GPU and CPU. Used only if `USE_LOCAL_SECURITY_MODEL=true`, to run the 8-billion-parameter Foundation-Sec-8B model. *Where:* [app/llm/foundation_sec.py:74-103](app/llm/foundation_sec.py#L74-L103).

**Streamlit** and **requests** ([requirements-streamlit.txt](requirements-streamlit.txt)). For the old Python-only UI in [frontend/streamlit_app.py](frontend/streamlit_app.py).

### Frontend (frontend-next/package.json)

**Next.js** (`next`) is a framework for React apps: it gives you routing by folder (`src/app/page.tsx` is the page at `/`), a dev server (`npm run dev`) and a production build. **React** (`react`, `react-dom`) is the UI library. **lucide-react** provides icons as components (`<Shield size={20} />`).
*Where:* [frontend-next/package.json:11-16](frontend-next/package.json#L11-L16).

**Tailwind CSS** (`tailwindcss`), **PostCSS** (`postcss`) and **Autoprefixer** (`autoprefixer`): Tailwind generates CSS for the utility classes you use; PostCSS runs it; Autoprefixer adds browser-specific prefixes. **TypeScript** (`typescript`) and the `@types/*` packages provide type checking.
*Where:* [frontend-next/package.json:17-25](frontend-next/package.json#L17-L25), [frontend-next/tailwind.config.ts](frontend-next/tailwind.config.ts), [frontend-next/postcss.config.js](frontend-next/postcss.config.js).

---

## 6. Every file and every function

Backend files are in **dependency order**: each appears only after the project files it imports at the top. A few files import others *inside* functions; that's noted where it happens. Then come the database scripts, the frontend, the legacy UI, tests and deployment.

### 6.1 Settings: app/config.py

Imports: no project files.

**`class Settings(BaseSettings)`** [app/config.py:11-118](app/config.py#L11-L118). Every setting with a type and default. pydantic-settings fills each field from an environment variable of the same name (case-insensitive, [line 118](app/config.py#L118)), then from `.env`, then the default. Groups:

- App and deployment: `allowed_origins` (who may call the API from a browser), `admin_api_key`, rate limits ([lines 17-33](app/config.py#L17-L33)). The property **`allowed_origins_list`** [lines 35-37](app/config.py#L35-L37) splits the comma-separated string.
- LLM: `llm_provider` (`groq` or `claude`), keys, models, reasoning "effort", and `use_mock_llm` ([lines 42-68](app/config.py#L42-L68)).
- Databases: PostgreSQL and Neo4j connection details. **`database_url`** [lines 81-86](app/config.py#L81-L86) builds `postgresql://user:password@host:port/db`, plus `?sslmode=require` for hosted databases like Neon. **`async_database_url`** [lines 88-90](app/config.py#L88-L90) is unused.
- Outreach: Twilio, SendGrid and the `outreach_enabled` switch ([lines 102-113](app/config.py#L102-L113)).

**`get_settings()`** [app/config.py:121-123](app/config.py#L121-L123) builds a fresh `Settings` (unused). **`settings = Settings()`** [line 127](app/config.py#L127) is the instance every other file imports. Two debug `print`s follow ([lines 130-131](app/config.py#L130-L131)).

### 6.2 Data shapes: app/schemas/

Imports: within the package only. These Pydantic models are the "contracts" between steps: what the extraction step must produce, what matching needs, what the frontend receives.

#### app/schemas/problem.py

**Enums** [app/schemas/problem.py:12-29](app/schemas/problem.py#L12-L29): `UrgencyLevel` (LOW…CRITICAL), `TechnicalLevel` (low/medium/high), `EmotionalState` (calm…panicked).

**`ProblemContext`** [app/schemas/problem.py:32-137](app/schemas/problem.py#L32-L137). What we know about the user's problem: device, platform, symptoms, timeline, impact, environment, urgency, the user's technical level and emotional state, location, budget, extra context. Each field has a `description`. Those descriptions end up in the JSON Schema sent to the LLM, so they double as instructions.

- **`is_sufficient()`** [lines 113-123](app/schemas/problem.py#L113-L123): "enough to match?" requires device *or* platform, **and** at least two of: two or more symptoms, a timeline, an impact.

```python
has_device_info = bool(self.device or self.platform)
has_symptoms = len(self.symptoms) >= 2
...
return has_device_info and context_details >= 2
```

- **`get_summary()`** [lines 125-137](app/schemas/problem.py#L125-L137): a one-line summary. Unused.

#### app/schemas/security.py

**`ThreatSeverity`** [app/schemas/security.py:11-15](app/schemas/security.py#L11-L15).

**`SecurityAnalysis`** [app/schemas/security.py:18-109](app/schemas/security.py#L18-L109): threat type and subcategory, attack vector, severity, `confidence` (validated to 0–1, [lines 45-50](app/schemas/security.py#L45-L50)), and the three lists matching uses: **`required_skills`**, **`recommended_services`**, **`platforms`**. Only `threat_type` has no default, so it is required. `get_search_terms` and `get_weighted_skills` [lines 91-109](app/schemas/security.py#L91-L109) are unused.

#### app/schemas/expert.py

- **`Expert`** [app/schemas/expert.py:11-58](app/schemas/expert.py#L11-L58): a full profile model. `from_attributes = True` would let it be built from a SQLAlchemy object, but the code uses `to_dict()` instead.
- **`ExpertMatch`** [lines 61-81](app/schemas/expert.py#L61-L81): the search result for one expert: ID, `match_score` (0–1), matched skills and human-readable reasons.
- **`ExpertRecommendation`** [lines 84-104](app/schemas/expert.py#L84-L104): profile + match + explanation + rank. Defined, but the app passes plain dicts with `expert` and `match` keys instead.
- **`PRIVATE_EXPERT_FIELDS`** [line 108](app/schemas/expert.py#L108) and **`public_expert(expert)`** [lines 111-115](app/schemas/expert.py#L111-L115): removes `email`, `phone` and `whatsapp` before sending a profile to the browser, **unless** the expert opted in with `public_contact`. Every endpoint that returns experts uses this, so personal details don't leak.

#### app/schemas/conversation.py and \_\_init\_\_.py

[app/schemas/conversation.py:16-126](app/schemas/conversation.py#L16-L126) defines `MessageRole`, `Message`, `ConversationPhase`, a full `ConversationState` model and `ChatRequest`/`ChatResponse`. These are **leftovers**: the workflow uses the plain `AgentState` dict instead, and `chat.py` imports `ChatRequest`/`ChatResponse` but defines and uses its own models. The phase list is still a handy reference for the phase names. [app/schemas/\_\_init\_\_.py:1-14](app/schemas/__init__.py#L1-L14) re-exports the main classes.

### 6.3 The LLM layer: app/llm/

The workflow needs two kinds of LLM call:

1. **`generate` / `chat`**: free text, for Maya's replies.
2. **`generate_structured`**: an answer that must fit a Pydantic model (`ProblemContext`, `SecurityAnalysis`), so code can use the fields.

Both clients (Groq and Claude) offer these same methods, so the rest of the app doesn't care which one it has. This is *duck typing*: "if it has the right methods, it's good enough".

#### app/llm/mock.py

Imports: schemas, inside a function.

- **`MOCK_RESPONSES`** [app/llm/mock.py:12-44](app/llm/mock.py#L12-L44): canned greeting, gathering, presentation and handoff texts, all about an iPhone.
- **`get_mock_response(prompt, system_prompt, history)`** [lines 47-62](app/llm/mock.py#L47-L62): picks one by history length and keywords.
- **`get_mock_structured(response_model)`** [lines 65-95](app/llm/mock.py#L65-L95): returns a fixed iPhone `ProblemContext` or a fixed "mobile_compromise" `SecurityAnalysis`, or tries `response_model()` with defaults.

*Why?* So you can click through the whole flow with no API key. Note that **real clients also fall back to these** when a structured call fails, which can silently put iPhone data into a real chat ([section 8](#8-things-to-notice)).

#### app/llm/structured.py

**`StructuredOutputParser`** [app/llm/structured.py:14-111](app/llm/structured.py#L14-L111): helpers to pull JSON out of text (code fences, then `{...}`, then `[...]`), parse it into a model, parse safely with a default, and describe a schema in prose. **Not used by the app**; both clients now use their API's built-in structured output instead. It's kept as a useful reference.

#### app/llm/groq_client.py

Imports: `app.config`, `app.llm.mock`.

**`GroqClient.__init__`** [app/llm/groq_client.py:31-49](app/llm/groq_client.py#L31-L49). Reads key and model from settings. No key (or `USE_MOCK_LLM=true`) → `mock_mode = True` ([lines 41-43](app/llm/groq_client.py#L41-L43)); otherwise creates `groq.Groq(...)`.

**`_create(reasoning_effort, **kwargs)`** [lines 51-60](app/llm/groq_client.py#L51-L60). One place for every API call. `reasoning_effort` is only sent to `gpt-oss` models, which "think" before answering; the others reject that parameter.

**`_build_messages(prompt, system_prompt, history)`** [lines 62-78](app/llm/groq_client.py#L62-L78). Chat APIs take a list of messages, each with a `role`: `system` (rules), `user` and `assistant`. This builds: system message → past messages (only user/assistant ones with content) → the new prompt as the last user message.

**`generate(...)`** [lines 80-124](app/llm/groq_client.py#L80-L124). Mock mode returns a canned reply ([lines 99-101](app/llm/groq_client.py#L99-L101)). Otherwise it calls the API. Each kind of failure (bad key, rate limit, other HTTP error, network) is caught **separately** with its own log line, and the user gets a polite `ERROR_MESSAGE` instead of a crash ([lines 110-121](app/llm/groq_client.py#L110-L121)).

**`generate_structured(prompt, response_model, system_prompt)`** [lines 126-176](app/llm/groq_client.py#L126-L176). Asks Groq for JSON that follows the model's schema:

```python
response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": response_model.__name__,
        "schema": response_model.model_json_schema()
    }
}
```

Then it validates the reply with `model_validate_json`. The comment explains that this is "best-effort" (not strict) mode, so the reply can occasionally fail validation; it retries once ([lines 159-174](app/llm/groq_client.py#L159-L174)). If both tries fail, or there's an HTTP error, it returns **mock data** ([line 176](app/llm/groq_client.py#L176)).

**`chat(message, system_prompt, history)`** [lines 178-192](app/llm/groq_client.py#L178-L192): a friendlier name for `generate`, used by the nodes.

#### app/llm/claude.py

Imports: `app.config`, `app.llm.mock`.

Same shape as the Groq client, with Anthropic's API.

- **`FALLBACK_BETA`** [app/llm/claude.py:18](app/llm/claude.py#L18) and **`REFUSAL_MESSAGE`** [lines 20-23](app/llm/claude.py#L20-L23). Cybersecurity talk can sometimes trigger a model's safety refusal. The code opts into a server-side fallback (the comment explains: a refused request is re-run on a recommended fallback model), and if it's still refused, shows a polite message asking the user to describe their problem.
- **`_create(effort, **kwargs)`** [lines 61-70](app/llm/claude.py#L61-L70): every call goes through `client.beta.messages.create` with `max_tokens`, an effort level and the fallback options.
- **`_build_messages(prompt, history)`** [lines 72-84](app/llm/claude.py#L72-L84): Claude takes the system prompt as a separate parameter, not a message, and the first message must come from the user. So leading assistant messages are dropped ([lines 80-82](app/llm/claude.py#L80-L82)).
- **`generate`** [lines 86-135](app/llm/claude.py#L86-L135): like Groq's, plus a refusal check ([lines 130-132](app/llm/claude.py#L130-L132)). A reply is a list of *content blocks*; only the text blocks are joined ([line 135](app/llm/claude.py#L135)).
- **`generate_structured`** [lines 137-185](app/llm/claude.py#L137-L185): uses `client.beta.messages.parse(..., output_format=response_model)`, which constrains the answer to the model's schema and returns an already-parsed object in `parsed_output`. Errors, refusals or no output → mock data.
- **`chat`** [lines 187-201](app/llm/claude.py#L187-L201).

#### app/llm/provider.py

Imports: `app.config`, `app.llm.claude`, `app.llm.groq_client`.

- **`PROVIDERS`** [app/llm/provider.py:14-17](app/llm/provider.py#L14-L17): name → class. Adding a provider is one line here plus one client class.
- **`get_llm()`** [lines 29-38](app/llm/provider.py#L29-L38): the singleton. Creates the client for `LLM_PROVIDER` once and reuses it. An unknown name raises `ValueError`.
- **`reset_llm_client()`** [lines 41-45](app/llm/provider.py#L41-L45): forgets the client (called at start-up).
- **`llm_key_configured()`** [lines 48-51](app/llm/provider.py#L48-L51): used by `/health/ready`.

#### app/graph/connection.py

Imports: `app.config`. (It's here because `foundation_sec.py` uses it.)

**`Neo4jConnection`** [app/graph/connection.py:14-85](app/graph/connection.py#L14-L85).

- **`driver`** property [lines 28-47](app/graph/connection.py#L28-L47): creates the Neo4j driver on first use (*lazy*, so importing the module doesn't need a running database). For encrypted URIs (`neo4j+s://`, used by AuraDB) it rewrites the URI to the plain scheme and passes `encrypted=True` with certifi's certificate bundle ([lines 32-41](app/graph/connection.py#L32-L41)). The comment explains why: Windows doesn't always have the needed root certificate installed.
- **`close`** [lines 49-53](app/graph/connection.py#L49-L53) and **`verify_connectivity`** [lines 55-62](app/graph/connection.py#L55-L62).
- **`session()`** [lines 64-71](app/graph/connection.py#L64-L71): a context manager that always closes the session.
- **`run_query(query, parameters)`** [lines 73-77](app/graph/connection.py#L73-L77): runs Cypher and returns each row as a dict. Parameters (`$name` in the query) are passed separately, never pasted into the string. This prevents *injection*, where user text could change the query.
- **`run_write_query`** [lines 79-85](app/graph/connection.py#L79-L85): runs inside a write transaction.

**`get_neo4j()`** [lines 92-97](app/graph/connection.py#L92-L97) and **`close_neo4j()`** [lines 100-105](app/graph/connection.py#L100-L105): singleton and shutdown.

#### app/llm/foundation_sec.py

Imports: `app.config`; inside functions, `app.graph.connection` and `app.llm.provider`.

The idea: use **Foundation-Sec-8B**, an open model trained for cybersecurity, to classify threats. In practice it needs a large GPU, so by default the **chat LLM** does the analysis with a security-focused system prompt.

- **`SECURITY_SYSTEM_PROMPT`** [app/llm/foundation_sec.py:15-22](app/llm/foundation_sec.py#L15-L22).
- **`_normalize_name(name)`** [lines 25-27](app/llm/foundation_sec.py#L25-L27): `"Mobile Security"` → `"mobile_security"`.
- **`_graph_vocabulary()`** [lines 30-43](app/llm/foundation_sec.py#L30-L43): asks Neo4j for every Skill, Platform and Service name in one Cypher query (`CALL { ... }` runs sub-queries). This is the key trick of the project: the LLM is told the **exact names that exist in the graph**, so its answer can actually match something. Matching uses exact names; an LLM that says "iOS forensic analysis" would match nothing.
- **`FoundationSecClient.__init__`** [lines 58-72](app/llm/foundation_sec.py#L58-L72) and **`_load_local_model`** [lines 74-103](app/llm/foundation_sec.py#L74-L103): loads the model with transformers only if `use_local` is true; on any failure it falls back to the chat LLM.
- **`analyze(problem_context, response_model)`** [lines 105-140](app/llm/foundation_sec.py#L105-L140): builds the prompt with the vocabulary, then either runs the local model and parses its JSON, or calls `get_llm().generate_structured(...)`. Finally it normalises the names.
- **`_normalize_names(analysis)`** [lines 142-149](app/llm/foundation_sec.py#L142-L149): snake_cases and de-duplicates the three matching lists.
- **`_build_analysis_prompt`** [lines 151-191](app/llm/foundation_sec.py#L151-L191): incident details + the "ALLOWED VALUES" block + the JSON shape wanted.
- **`_generate_local`** [lines 193-215](app/llm/foundation_sec.py#L193-L215): tokenises the prompt, generates up to 512 new tokens, decodes, and strips the prompt from the start of the output (local models repeat the input).
- **`_generate_with_llm`** [lines 217-226](app/llm/foundation_sec.py#L217-L226) and **`_parse_structured`** [lines 228-249](app/llm/foundation_sec.py#L228-L249): free-text fallback and JSON parsing for the local model.
- **`get_foundation_sec()`** [lines 256-261](app/llm/foundation_sec.py#L256-L261): singleton.

[app/llm/\_\_init\_\_.py:1-15](app/llm/__init__.py#L1-L15) re-exports these, so nodes write `from app.llm import get_llm`.

### 6.4 Graph search: app/graph/queries.py and search.py

#### app/graph/queries.py

Imports: no project files.

**`ExpertSearchQuery`** [app/graph/queries.py:10-187](app/graph/queries.py#L10-L187), a dataclass holding the search criteria.

**`build_query()`** [lines 27-155](app/graph/queries.py#L27-L155) returns the main Cypher query plus its parameters. Read it step by step; the comments label each step:

1. **Find skills** [lines 49-54](app/graph/queries.py#L49-L54): `UNWIND` turns the list into rows (one per skill name). Each is matched to a `Skill` node by name **or alias** (e.g. `pentest` → `penetration_testing`).
2. **Find experts** [lines 59-61](app/graph/queries.py#L59-L61) who `HAS_SKILL` and are active and available.
3. **Score skills** [lines 66-76](app/graph/queries.py#L66-L76): each matched skill adds its edge `weight` (0.5 if missing) plus 0.05 per year of experience. `collect`, `sum` and `count` then group the rows **per expert** (like SQL's GROUP BY).
4. **Platforms** [lines 81-86](app/graph/queries.py#L81-L86) and 5. **services** [lines 91-97](app/graph/queries.py#L91-L97): `OPTIONAL MATCH` keeps the expert even with no match (like a LEFT JOIN); any match gives +0.15 / +0.1.
6. **Bonuses** [lines 102-120](app/graph/queries.py#L102-L120): same location +0.1; urgent problem and the expert `handles_urgent` +0.15; rating × 0.05.
7. **Total** [lines 125-128](app/graph/queries.py#L125-L128) and 8. **sort and limit** [lines 133-143](app/graph/queries.py#L133-L143).

*Why a graph database for this?* "Experts who have these skills, plus bonus if they also work on this platform and offer this service" is a pattern of connections, and Cypher expresses it directly. In SQL it would be several joins.

**`build_simple_query()`** [lines 157-187](app/graph/queries.py#L157-L187): a fallback that scores by the fraction of required skills each expert has.

#### app/graph/search.py

Imports: schemas, `app.graph.connection`, `app.graph.queries`.

**`ExpertGraphSearch.search(security_analysis, problem_context, limit)`** [app/graph/search.py:23-78](app/graph/search.py#L23-L78). Builds the query from the analysis ([lines 42-49](app/graph/search.py#L42-L49)), runs it, and falls back to the simple query on error ([lines 60-64](app/graph/search.py#L60-L64)). Raw totals like 3.2 aren't percentages, so each score is divided by the best score possible for this problem and capped at 1.0:

```python
match_score=round(min(record.get("match_score", 0.5) / best_score, 1.0), 2),
```

**`best_possible_score(required_skill_count, has_location)`** [lines 80-88](app/graph/search.py#L80-L88): 1.5 per skill (weight 1.0 + 10 years × 0.05) plus 0.65 of bonuses (platform 0.15, service 0.1, urgency 0.15, 5-star rating 0.25), plus 0.1 for location. Tested in [tests/test_matching.py:48-52](tests/test_matching.py#L48-L52).

**`_generate_match_reasons(record)`** [lines 90-106](app/graph/search.py#L90-L106): "Has skills: …", "Experience with: …", "Offers: …". These appear on the cards.

`get_expert_details` and `find_similar_experts` [lines 108-131](app/graph/search.py#L108-L131) are unused examples of other graph queries.

[app/graph/\_\_init\_\_.py:1-10](app/graph/__init__.py#L1-L10) re-exports the classes.

### 6.5 PostgreSQL: app/db/

#### app/db/postgres.py

Imports: `app.config`.

- **`engine`** [app/db/postgres.py:14-19](app/db/postgres.py#L14-L19): SQLAlchemy's connection pool. `pool_pre_ping=True` tests each connection before use, which matters for hosted databases that drop idle connections.
- **`SessionLocal`** [lines 22-26](app/db/postgres.py#L22-L26): a factory for *sessions* (a unit of work: queries plus a pending set of changes).
- **`Base`** [line 29](app/db/postgres.py#L29): unused. The models use their own `Base` in `models.py`.
- **`get_db()`** [lines 32-41](app/db/postgres.py#L32-L41): FastAPI dependency: one session per request, always closed.
- **`get_db_context()`** [lines 44-58](app/db/postgres.py#L44-L58): the same for normal code, plus **commit on success, rollback on error**. *Rollback* undoes all changes since the last commit, so a half-finished update never gets saved.
- **`init_db()`** [lines 61-64](app/db/postgres.py#L61-L64): `create_all` creates any missing tables from the models. Called at start-up.

Creating the engine doesn't connect yet, so the app can start even if PostgreSQL is down; queries just fail later.

#### app/db/models.py

Imports: no project files.

Each class is a table; each `Column` a column.

- **Association tables** [app/db/models.py:17-30](app/db/models.py#L17-L30): `expert_skills` and `expert_certifications` link experts to skills and certifications. An expert has many skills and a skill has many experts, a **many-to-many** relationship, which needs a table in between.
- **`Expert`** [lines 33-129](app/db/models.py#L33-L129): profile columns, plus flags for **external** freelancers (listed by public profile link only, [lines 75-77](app/db/models.py#L75-L77)) and **featured** experts (always listed first, contact details public, [lines 81-82](app/db/models.py#L81-L82)). `relationship(... secondary=expert_skills)` ([lines 94-96](app/db/models.py#L94-L96)) means `expert.skills` gives a list of `Skill` objects without writing the join. **`to_dict()`** [lines 98-129](app/db/models.py#L98-L129) turns a row into a plain dict, including skill names.
- **`Skill`** [lines 132-146](app/db/models.py#L132-L146), **`Certification`** [lines 149-161](app/db/models.py#L149-L161), **`Review`** [lines 164-186](app/db/models.py#L164-L186).
- **`Conversation`** [lines 189-208](app/db/models.py#L189-L208) and **`ConversationMessage`** [lines 211-223](app/db/models.py#L211-L223): a record of each chat.

#### app/db/conversations.py

Imports: `app.db.postgres`, `app.db.models`.

- **`_to_json(value)`** [app/db/conversations.py:12-16](app/db/conversations.py#L12-L16): round-trips through `json.dumps(..., default=str)` so enums and dates become plain JSON.
- **`save_conversation(state)`** [lines 19-52](app/db/conversations.py#L19-L52): an *upsert* (update if it exists, insert if not) of the conversation row ([lines 30-34](app/db/conversations.py#L30-L34)); `db.flush()` sends the insert early so the new row gets its `id`. Then it appends only the messages not yet stored, by counting what's already there ([lines 43-49](app/db/conversations.py#L43-L49)). That works because messages are only ever appended. Any error is logged and swallowed ([lines 50-52](app/db/conversations.py#L50-L52)): *"Persistence must never break the chat itself."*

[app/db/\_\_init\_\_.py:1-12](app/db/__init__.py#L1-L12) re-exports the engine, sessions and four models.

### 6.6 Notifications: app/services/

#### app/services/outreach/email.py and whatsapp.py

Both follow the same pattern: read credentials in `__init__`, create the API client lazily in a `client` property, `is_configured()` checks credentials, one low-level send method that **returns a result dict instead of raising**, and a few templates.

- Email: **`send_email`** [app/services/outreach/email.py:39-86](app/services/outreach/email.py#L39-L86) (success means HTTP 200/201/202); **`notify_expert`** [lines 88-172](app/services/outreach/email.py#L88-L172) builds an HTML email (the CSS braces are doubled `{{ }}` because it's an f-string); **`send_client_confirmation`** [lines 174-243](app/services/outreach/email.py#L174-L243); **`get_email_service`** [lines 250-255](app/services/outreach/email.py#L250-L255).
- WhatsApp: **`send_message`** [app/services/outreach/whatsapp.py:40-78](app/services/outreach/whatsapp.py#L40-L78) adds the `whatsapp:` prefix Twilio requires ([lines 58-59](app/services/outreach/whatsapp.py#L58-L59)); **`notify_expert`** [lines 80-120](app/services/outreach/whatsapp.py#L80-L120) and **`send_client_intro`** [lines 122-157](app/services/outreach/whatsapp.py#L122-L157) use WhatsApp's `*bold*` and `_italic_` formatting; **`get_whatsapp_service`** [lines 164-169](app/services/outreach/whatsapp.py#L164-L169).

[app/services/outreach/\_\_init\_\_.py:1-4](app/services/outreach/__init__.py#L1-L4) re-exports the two classes.

#### app/services/handoff.py

- **`HandoffRequest`** [app/services/handoff.py:13-26](app/services/handoff.py#L13-L26) and **`process_handoff`** [lines 39-112](app/services/handoff.py#L39-L112): notify the expert *and* the client on every configured channel. Unused, since the app never collects the client's contact details.
- **`notify_expert_only(...)`** [lines 114-160](app/services/handoff.py#L114-L160): the one the app uses. WhatsApp if there's a phone, email if there's an email address; collects which channels worked and any errors.
- **`get_handoff_service()`** [lines 167-172](app/services/handoff.py#L167-L172).

[app/services/\_\_init\_\_.py:1-3](app/services/__init__.py#L1-L3) re-exports `HandoffService`.

### 6.7 The agent: state, prompts and nodes

#### app/agents/states.py

**`AgentState`** [app/agents/states.py:9-43](app/agents/states.py#L9-L43): the dict every node reads and returns. The important keys:

| Key | Set by | Meaning |
|---|---|---|
| `messages` | every node that speaks | full chat history as `{"role", "content"}` dicts |
| `current_phase` | every node | where the next message should enter the graph |
| `user_message` | the workflow | the message being processed now |
| `problem_context` | extraction | a `ProblemContext` as a dict |
| `extraction_attempts`, `has_sufficient_context` | extraction | used to decide when to stop asking |
| `security_analysis` | security analysis | a `SecurityAnalysis` as a dict |
| `matched_experts` | matching | list of `{"expert": …, "match": …}` |
| `selected_expert_id` | selection / API | the chosen expert |
| `response` | the node that spoke | the reply to send back |

*Why plain dicts and not Pydantic objects?* LangGraph passes dicts around, and dicts store easily. The nodes convert to models when they need validation (`SecurityAnalysis.model_validate(...)` in matching).

#### app/agents/prompts/

These are long strings, so they live in their own files where they can be edited without touching logic.

- **[app/agents/prompts/system.py](app/agents/prompts/system.py)**: **`SYSTEM_PROMPT`** [lines 6-61](app/agents/prompts/system.py#L6-L61) defines Maya: calm, one question at a time, 2–4 sentences, **never** give technical fixes (her job is to understand and match, not to be the expert). **`GREETING_PROMPT`** [lines 63-76](app/agents/prompts/system.py#L63-L76).
- **[app/agents/prompts/gathering.py](app/agents/prompts/gathering.py)**: **`GATHERING_PROMPT`** [lines 6-57](app/agents/prompts/gathering.py#L6-L57) has `{current_context}` and `{missing_info}` slots and good/bad example answers, because the model kept dodging users' questions. **`EXTRACTION_PROMPT`** [lines 59-83](app/agents/prompts/gathering.py#L59-L83) asks for the `ProblemContext` JSON. **`SUFFICIENCY_CHECK_PROMPT`** [lines 85-106](app/agents/prompts/gathering.py#L85-L106) is unused; `is_sufficient()` does this in code instead.
- **[app/agents/prompts/presentation.py](app/agents/prompts/presentation.py)**: **`PRESENTATION_PROMPT`** [lines 6-60](app/agents/prompts/presentation.py#L6-L60) has two parts, a diagnosis then the experts in the **same order as the cards**, "using ONLY the facts listed". **`HANDOFF_PROMPT`** [lines 62-107](app/agents/prompts/presentation.py#L62-L107). **`EXTERNAL_HANDOFF_PROMPT`** [lines 109-131](app/agents/prompts/presentation.py#L109-L131) must never claim we contacted the freelancer. **`POST_HANDOFF_PROMPT`** [lines 134-174](app/agents/prompts/presentation.py#L134-L174) allows real advice after the handoff. **`EXPLANATION_PROMPT`** [lines 176-197](app/agents/prompts/presentation.py#L176-L197) is unused.

Notice how many rules are about **not inventing facts** ("never invent past cases, ratings or response times"). LLMs tend to fill gaps with plausible fiction, and in a matching service that would mean lying about real people.

[app/agents/prompts/\_\_init\_\_.py:1-11](app/agents/prompts/__init__.py#L1-L11) re-exports five of them.

#### The nodes (app/agents/nodes/)

Every node takes the state and returns a new state. The "talking" nodes all do the same three things: call `llm.chat(...)` with `SYSTEM_PROMPT + "\n\n" + a stage prompt`, append the reply to `messages`, and set `current_phase` and `response`. The workflow has *already* appended the user's message, which is why several nodes pass `messages[:-1]` as history (everything except the current message, which goes in as `message`).

**`greeting_node`** [app/agents/nodes/greeting.py:11-53](app/agents/nodes/greeting.py#L11-L53). Embeds the user's first message in the greeting prompt and sets the phase to `"gathering"`, so the **next** message goes to extraction.

**`gathering_node`** [app/agents/nodes/gathering.py:12-56](app/agents/nodes/gathering.py#L12-L56). Works out what's still missing with **`_get_missing_info`** [lines 59-78](app/agents/nodes/gathering.py#L59-L78), formats what's known with **`_format_context`** [lines 81-96](app/agents/nodes/gathering.py#L81-L96), and asks the LLM for the next question. (`_get_missing_info` checks `urgency`, but `ProblemContext` always has a default urgency, so "how urgent" is never listed as missing after the first extraction.)

**`extraction_node`** [app/agents/nodes/extraction.py:12-62](app/agents/nodes/extraction.py#L12-L62). Formats the whole chat as `User: …` / `Assistant: …` lines (**`_format_conversation`** [lines 86-93](app/agents/nodes/extraction.py#L86-L93)) and asks for a structured `ProblemContext`:

```python
problem_context = llm.generate_structured(
    prompt=prompt,
    response_model=ProblemContext
)
context_dict = problem_context.model_dump()
has_sufficient = problem_context.is_sufficient()
```

Every turn re-extracts from the **whole** conversation, not just the new message, so later answers can correct earlier ones. Then it counts an "attempt", unless the user's message looks like a **question** (**`_is_question`** [lines 65-83](app/agents/nodes/extraction.py#L65-L83)). In that case it doesn't count it and forces "not sufficient", so the gathering node answers the question instead of jumping to matching ([lines 46-53](app/agents/nodes/extraction.py#L46-L53)). `_is_question` checks whether the text *starts with* words like "is", "do", "can", "how". Section 8 shows how that misfires.

**`security_analysis_node`** [app/agents/nodes/security_analysis.py:11-40](app/agents/nodes/security_analysis.py#L11-L40). Calls `get_foundation_sec().analyze(...)`. If that raises, it uses **`_fallback_analysis`** [lines 43-98](app/agents/nodes/security_analysis.py#L43-L98): plain keyword rules ("phone" → `mobile_compromise` + mobile skills; "ransom" in a symptom → `ransomware`…). Several skill names it produces (`endpoint_security`, `server_forensics`, `negotiation`…) don't exist in the Neo4j graph, so they can't match.

**`matching_node`** [app/agents/nodes/matching.py:14-67](app/agents/nodes/matching.py#L14-L67).

1. Turns the dicts back into models and searches the graph for up to 10 experts ([lines 25-36](app/agents/nodes/matching.py#L25-L36)).
2. Fetches their full profiles from PostgreSQL in one query with **`_get_expert_profiles`** [lines 70-84](app/agents/nodes/matching.py#L70-L84) (`Expert.id.in_(ids)` becomes SQL `WHERE id IN (…)`), and pairs each profile with its match ([lines 39-50](app/agents/nodes/matching.py#L39-L50)). An expert found in Neo4j but missing in PostgreSQL is silently skipped.
3. Gets featured and external experts with **`_get_pinned_candidates`** [lines 132-142](app/agents/nodes/matching.py#L132-L142) and orders the list with **`order_matches`**.
4. If anything throws, it uses **`_get_mock_experts`** [lines 145-223](app/agents/nodes/matching.py#L145-L223), three hard-coded profiles ([lines 57-60](app/agents/nodes/matching.py#L57-L60)).

**`order_matches(matched, featured, external, required_skills, limit)`** [lines 87-129](app/agents/nodes/matching.py#L87-L129) is pure logic (no database), which is why it's the most tested function. Order: **featured experts first**, then **one external freelancer** (the best-matched one, or the first in the list), then the rest by score, cut to `limit` but never cutting a pinned slot. The inner **`as_match`** [lines 104-117](app/agents/nodes/matching.py#L104-L117) reuses the real match if the graph found that expert, or builds a simple one (0.9 for featured, 0.6 for external). *Why pin a freelancer?* The seeded network experts are fake, so this guarantees the demo always offers at least one real person to contact.

**`presentation_node`** [app/agents/nodes/presentation.py:12-65](app/agents/nodes/presentation.py#L12-L65). With no matches, a fixed message ([lines 27-34](app/agents/nodes/presentation.py#L27-L34)). Otherwise it fills the presentation prompt with **`_format_problem_summary`** [lines 68-90](app/agents/nodes/presentation.py#L68-L90) and **`_format_experts`** [lines 93-137](app/agents/nodes/presentation.py#L93-L137). Note the three formats: external freelancers get only name, title, skills and match ([lines 101-111](app/agents/nodes/presentation.py#L101-L111)); featured experts get only title and bio, with an explicit "do not add skills, experience…" ([lines 113-121](app/agents/nodes/presentation.py#L113-L121)); only network experts get ratings and rates. The LLM is given **only facts that are true for that kind of expert**, which is the strongest way to stop it inventing others. Phase becomes `"presenting"`.

**`selection_node`** [app/agents/nodes/selection.py:37-106](app/agents/nodes/selection.py#L37-L106). Tries to work out which expert the user meant, typed in the chat:

1. Any part of an expert's name appearing in the message ([lines 51-60](app/agents/nodes/selection.py#L51-L60)).
2. Otherwise a number word via **`_parse_number_selection`** [lines 119-144](app/agents/nodes/selection.py#L119-L144): "first", "one", "2nd", "3"… checked as **substrings** ([lines 133-135](app/agents/nodes/selection.py#L133-L135)).
3. Otherwise the user said something else, so the LLM answers it with **`SELECTION_CONVERSATION_PROMPT`** [lines 11-34](app/agents/nodes/selection.py#L11-L34) and the list from **`_format_experts_summary`** [lines 109-116](app/agents/nodes/selection.py#L109-L116), then asks again. Phase `"selecting"`.

If an expert is found, it sets `selected_expert_id` and phase `"handoff"` **without replying** ([lines 102-106](app/agents/nodes/selection.py#L102-L106)); the graph then goes straight to the handoff node in the same run. Substring matching makes step 2 misfire easily; see [section 8](#8-things-to-notice).

**`handoff_node`** [app/agents/nodes/handoff.py:14-84](app/agents/nodes/handoff.py#L14-L84).

- Finds the selected expert in `matched_experts` ([lines 26-30](app/agents/nodes/handoff.py#L26-L30)).
- External freelancer → `EXTERNAL_HANDOFF_PROMPT` with the profile link; anyone else → `HANDOFF_PROMPT` with contact options ([lines 46-59](app/agents/nodes/handoff.py#L46-L59)).
- **`_build_contact_options`** [lines 87-110](app/agents/nodes/handoff.py#L87-L110): for sample experts (no email, or an `@example.com` address, a domain reserved for examples) it tells the LLM to say plainly there are no real contact details. That stops the assistant offering a fake WhatsApp number.
- Calls **`_notify_expert`** [lines 137-177](app/agents/nodes/handoff.py#L137-L177) for network experts. It builds the notification but only **logs** it unless `OUTREACH_ENABLED=true` ([lines 158-160](app/agents/nodes/handoff.py#L158-L160)).
- Sets phase `"complete"` and `is_complete=True`.

`_format_expert` [lines 113-120](app/agents/nodes/handoff.py#L113-L120), `_format_problem_summary` [lines 123-134](app/agents/nodes/handoff.py#L123-L134) and `_summarize_conversation` [lines 180-184](app/agents/nodes/handoff.py#L180-L184) (the last three user messages joined with `|`) are small formatters.

**`conversation_node`** [app/agents/nodes/conversation.py:12-40](app/agents/nodes/conversation.py#L12-L40). After the handoff: chat with `POST_HANDOFF_PROMPT`, phase `"conversation"`.

[app/agents/nodes/\_\_init\_\_.py:1-21](app/agents/nodes/__init__.py#L1-L21) re-exports all nine.

### 6.8 The graph: app/agents/workflow.py

Imports: `app.agents.states`, `app.db.conversations`, `app.schemas.expert`, all nodes.

**Three routing functions.** They only look at the state and return a label.

- **`route_by_phase(state)`** [app/agents/workflow.py:25-42](app/agents/workflow.py#L25-L42): where a **new message** enters. `greeting` → greeting; `presenting`/`selecting` → selection; `handoff` → handoff; `complete`/`conversation` → conversation; anything else (`gathering`, `extracting`…) → extraction.
- **`ready_for_matching(state)`** [lines 45-59](app/agents/workflow.py#L45-L59): after extraction, go to analysis if the context is sufficient **and** at least 2 attempts were made, **or** after 5 attempts whatever happens (so a vague user isn't asked questions forever).
- **`expert_selected(state)`** [lines 62-66](app/agents/workflow.py#L62-L66): after selection, go to handoff only if an expert was picked.

**`create_chat_workflow()`** [lines 69-149](app/agents/workflow.py#L69-L149). Adds nine nodes ([lines 92-100](app/agents/workflow.py#L92-L100)), then the wiring:

```python
workflow.set_conditional_entry_point(route_by_phase, {...})
workflow.add_edge("greeting", END)
workflow.add_conditional_edges("extraction", ready_for_matching,
                               {"analyze": "analyze_security", "ask_more": "gathering"})
workflow.add_edge("gathering", END)
workflow.add_edge("analyze_security", "matching")
workflow.add_edge("matching", "presentation")
workflow.add_edge("presentation", END)
```

(Condensed; see [lines 103-147](app/agents/workflow.py#L103-L147).) Read it as: *each run starts where the phase says, and stops (`END`) whenever Maya has said something and needs the user's reply.* That's the "one graph run per message" design from section 2, and it's simpler than keeping a graph paused between HTTP requests.

**`class ChatWorkflow`** [lines 152-234](app/agents/workflow.py#L152-L234).

- **`__init__`** [lines 158-161](app/agents/workflow.py#L158-L161): compiles the graph once and makes `self.sessions`, a plain dict from session ID to state. **All live chats are stored in this dict, in memory.**
- **`get_initial_state`** [lines 163-178](app/agents/workflow.py#L163-L178): a fresh state in phase `"greeting"`.
- **`chat(session_id, user_message)`** [lines 180-229](app/agents/workflow.py#L180-L229): the one method the API calls.

```python
if session_id in self.sessions:
    state = dict(self.sessions[session_id])
    state["user_message"] = user_message
else:
    state = self.get_initial_state(session_id, user_message)
state["messages"] = state.get("messages", []) + [{"role": "user", "content": user_message}]
result = self.app.invoke(state)
self.sessions[session_id] = result
save_conversation(result)
```

  (Slightly condensed.) Then it builds the reply dict. Experts are included **only** in the `presenting` phase, and each is passed through `public_expert()` to strip private contact details ([lines 217-229](app/agents/workflow.py#L217-L229)).
- **`reset_session`** [lines 231-234](app/agents/workflow.py#L231-L234).

**`get_chat_workflow()`** [lines 241-246](app/agents/workflow.py#L241-L246): singleton, so every request shares the same `sessions` dict.

[app/agents/\_\_init\_\_.py:1-8](app/agents/__init__.py#L1-L8) re-exports.

### 6.9 The API: app/api/

#### app/api/rate_limit.py

**`chat_rate_limit(request)`** [app/api/rate_limit.py:21-49](app/api/rate_limit.py#L21-L49). A FastAPI dependency. For the client's IP it keeps a deque of request times, drops ones older than a day, counts the last minute, and raises **429 Too Many Requests** over 10 per minute or 100 per day (configurable). *Why?* Each message costs LLM calls, and the free Groq tier has a quota shared by all visitors. The lock matters because FastAPI may handle requests in parallel threads.

#### app/api/security.py

**`require_admin(x_admin_key)`** [app/api/security.py:12-20](app/api/security.py#L12-L20). `Header(default="")` makes FastAPI read the `X-Admin-Key` header (underscores become dashes). No `ADMIN_API_KEY` set → **403**, so the admin endpoints are off by default; wrong key → **401**. `secrets.compare_digest` compares in constant time, so the response time doesn't reveal how much of the key was right.

#### app/api/health.py

- **`GET /health`** [app/api/health.py:18-26](app/api/health.py#L18-L26): always "healthy" if the process runs. Both `""` and `"/"` are registered, so `/health` and `/health/` both work.
- **`GET /health/ready`** [lines 29-68](app/api/health.py#L29-L68): really checks PostgreSQL (`SELECT 1`), Neo4j (`verify_connectivity`) and that an LLM key is set. Useful after deploying ([DEPLOY.md:70-71](DEPLOY.md#L70-L71)).
- **`GET /health/live`** [lines 71-77](app/api/health.py#L71-L77).

#### app/api/chat.py

Imports: `app.agents.workflow`, `app.api.rate_limit`, schemas.

- Request and response models [app/api/chat.py:18-41](app/api/chat.py#L18-L41). `Field(min_length=1, max_length=5000)` rejects empty or huge messages with **422** before any LLM call.
- **`POST /chat/start`** [lines 44-73](app/api/chat.py#L44-L73): makes a random UUID session ID, runs the first turn, returns the greeting. Rate-limited via `dependencies=[Depends(chat_rate_limit)]`.
- **`POST /chat/{session_id}`** [lines 76-110](app/api/chat.py#L76-L110): **404** if the ID isn't in memory ([lines 88-92](app/api/chat.py#L88-L92)), otherwise runs a turn and returns the reply, phase and any experts.
- **`GET /chat/{session_id}/state`** [lines 113-139](app/api/chat.py#L113-L139): a debug summary.
- **`DELETE /chat/{session_id}`** [lines 142-158](app/api/chat.py#L142-L158): forget the session.
- **`POST /chat/{session_id}/select-expert?expert_id=N`** [lines 161-200](app/api/chat.py#L161-L200): what the card buttons call. It checks the ID is one of the matched experts ([lines 180-186](app/api/chat.py#L180-L186)), sets the phase to `"handoff"` directly in the stored state ([lines 189-190](app/api/chat.py#L189-L190)), then runs a turn with a made-up user message ([line 193](app/api/chat.py#L193)). `route_by_phase` sends it straight to the handoff node, skipping the fragile text-based selection.

#### app/api/experts.py

Imports: `app.api.security`, `app.db`, schemas.

- **`GET /experts`** [app/api/experts.py:18-47](app/api/experts.py#L18-L47): paged list (`skip`, `limit` up to 100), optional skill filter with `ilike` (case-insensitive SQL `LIKE`, `%` = any text), contact details stripped.
- **`GET /experts/{expert_id}`** [lines 50-61](app/api/experts.py#L50-L61).
- **`POST`**, **`PUT /{id}`**, **`DELETE /{id}`** [lines 64-140](app/api/experts.py#L64-L140): admin only. Create finds or creates each skill/certification by name; update sets any matching attribute; delete is a **soft delete** (`is_active = False`) so history and references stay valid. These write to PostgreSQL only, not Neo4j ([section 8](#8-things-to-notice)). They accept a plain `dict` body, so there's no validation.
- **`GET /experts/skills/list`** and **`/experts/certifications/list`** [lines 143-169](app/api/experts.py#L143-L169).

[app/api/\_\_init\_\_.py:1-9](app/api/__init__.py#L1-L9) renames each module's `router` for `main.py`.

### 6.10 The application: app/main.py

Imports: `app.config`, `app.api`, `app.db.postgres`, `app.graph.connection`, `app.llm.provider`.

- **`lifespan(app)`** [app/main.py:17-44](app/main.py#L17-L44): at start-up, create the LLM client (logs whether it's in mock mode) and create missing tables (errors only logged, so the API still starts without a database); at shut-down, close Neo4j.
- **`app = FastAPI(...)`** [lines 48-73](app/main.py#L48-L73): the Markdown description appears on `/docs`.
- **CORS** [lines 76-82](app/main.py#L76-L82). Browsers block JavaScript on one site (the Vercel frontend) from reading responses from another (the Render backend) unless the backend lists the frontend's origin. That's what `ALLOWED_ORIGINS` is for ([DEPLOY.md:83-86](DEPLOY.md#L83-L86)).
- **Routers** [lines 85-87](app/main.py#L85-L87) and **`GET /`** [lines 90-99](app/main.py#L90-L99).
- **`if __name__ == "__main__"`** [lines 102-109](app/main.py#L102-L109): `python -m app.main` starts Uvicorn on port 8000.

### 6.11 Database set-up: scripts/

**[scripts/init_postgres.sql](scripts/init_postgres.sql)**: creates the tables ([lines 10-118](scripts/init_postgres.sql#L10-L118)). `IF NOT EXISTS` makes it safe to re-run, and the `ALTER TABLE … ADD COLUMN IF NOT EXISTS` lines ([lines 59-67](scripts/init_postgres.sql#L59-L67)) upgrade older databases. It then inserts 20 skills, 15 certifications and **three sample experts** with `@example.com` emails ([lines 179-247](scripts/init_postgres.sql#L179-L247)), and links them to skills and certifications by email ([lines 250-279](scripts/init_postgres.sql#L250-L279)). `ON CONFLICT DO NOTHING` skips rows that already exist.

**[scripts/init_neo4j.cypher](scripts/init_neo4j.cypher)**: uniqueness *constraints* and indexes ([lines 7-16](scripts/init_neo4j.cypher#L7-L16)); 10 Skill nodes with aliases ([lines 22-50](scripts/init_neo4j.cypher#L22-L50)); Threat nodes and Threat→Skill `REQUIRES` relationships ([lines 56-122](scripts/init_neo4j.cypher#L56-L122)), which **no query uses**; Services and Platforms; and the same three experts with **hard-coded ids 1, 2, 3** ([lines 128-153](scripts/init_neo4j.cypher#L128-L153)) and their `HAS_SKILL {weight, years}`, `WORKS_ON` and `OFFERS` relationships. `MERGE` means "create if it doesn't exist", so this file is re-runnable too.

**[scripts/seed_databases.py](scripts/seed_databases.py)**: runs everything against whatever databases the settings point to (local or hosted).

- [Lines 20-21](scripts/seed_databases.py#L20-L21) add the project root to `sys.path`, so `import app...` works when run as a script.
- **`seed_postgres()`** [lines 29-39](scripts/seed_databases.py#L29-L39): runs the SQL file through a raw database connection.
- **`_cypher_statements(text)`** [lines 42-45](scripts/seed_databases.py#L42-L45) and **`seed_neo4j()`** [lines 48-54](scripts/seed_databases.py#L48-L54): the driver runs one statement at a time, so the file is split on `;` after dropping `//` comment lines.
- **`seed_external_experts()`** [lines 57-163](scripts/seed_databases.py#L57-L163): reads [scripts/external_experts.json](scripts/external_experts.json), skips entries without a name or an `https://` link, drops any skill/platform/service names the graph doesn't know (with a warning), upserts each into PostgreSQL by `profile_url`, then mirrors it into Neo4j with a fixed skill weight of 0.7 (unverified profiles score a bit lower). Freelancers no longer in the file are deactivated in **both** databases.
- **`seed_featured_experts()`** [lines 166-239](scripts/seed_databases.py#L166-L239): same for the git-ignored `featured_experts.json` (format in [scripts/featured_experts.example.json](scripts/featured_experts.example.json)). Featured experts are linked to **every** skill, platform and service, so they match every problem.

This script is the only code that keeps the two databases in step. The PostgreSQL ID it creates is reused as the Neo4j `id`, which is what lets matching join the two.

### 6.12 The Next.js frontend: frontend-next/

The browser side. It doesn't know anything about LLMs or graphs; it sends messages and draws what comes back.

**Configuration.**
- [frontend-next/package.json:5-10](frontend-next/package.json#L5-L10): `npm run dev` (development server on port 3000), `build`, `start`, `lint`.
- [frontend-next/tsconfig.json:20-22](frontend-next/tsconfig.json#L20-L22): the `@/` alias, so `import … from '@/lib/useChat'` means `src/lib/useChat`.
- [frontend-next/next.config.js:4-11](frontend-next/next.config.js#L4-L11): would forward `/api/...` to `localhost:8003`, but nothing calls `/api/...`; `api.ts` calls the backend URL directly.
- [frontend-next/tailwind.config.ts:4-8](frontend-next/tailwind.config.ts#L4-L8): which files Tailwind scans for class names; [lines 9-34](frontend-next/tailwind.config.ts#L9-L34) add `primary-*` and `cyber-*` colours.

**[frontend-next/src/types/index.ts](frontend-next/src/types/index.ts)**: TypeScript shapes for messages, the session, phases ([lines 17-27](frontend-next/src/types/index.ts#L17-L27)), experts and API responses. They mirror the backend's JSON by hand; if the backend changes, these must change too. The phase list has no `'conversation'`, the phase the backend sends after a handoff ([section 8](#8-things-to-notice)).

**[frontend-next/src/lib/api.ts](frontend-next/src/lib/api.ts)**: every HTTP call in one place.
- `API_URL` [line 8](frontend-next/src/lib/api.ts#L8) comes from `NEXT_PUBLIC_API_URL` (the `NEXT_PUBLIC_` prefix is what makes a variable visible to browser code), default `http://localhost:8003`.
- **`ApiError`** [lines 10-15](frontend-next/src/lib/api.ts#L10-L15) keeps the HTTP status; **`handleResponse`** [lines 17-23](frontend-next/src/lib/api.ts#L17-L23) throws on non-2xx and otherwise parses JSON.
- **`chatApi`** [lines 25-100](frontend-next/src/lib/api.ts#L25-L100): `startChat`, `continueChat`, `selectExpert` (expert ID as a query parameter, matching the backend), `getSessionState`, `endSession`, `healthCheck`.

**[frontend-next/src/lib/useChat.ts](frontend-next/src/lib/useChat.ts)**: a custom hook that owns the chat.
- State: the session (ID, messages, phase, completion, experts), `isLoading` and `error` ([lines 17-26](frontend-next/src/lib/useChat.ts#L17-L26)).
- **`addMessage`** [lines 28-40](frontend-next/src/lib/useChat.ts#L28-L40): `setSession(prev => ({...prev, messages: [...prev.messages, message]}))`. The `prev =>` form uses the latest state, which matters when two updates happen quickly.
- **`sendMessage`** [lines 42-108](frontend-next/src/lib/useChat.ts#L42-L108): shows the user's bubble immediately (it feels faster), then either starts a session or continues one. If the backend answers "Session not found" (it restarted and lost its memory), it quietly starts a **new** session with the same message ([lines 79-87](frontend-next/src/lib/useChat.ts#L79-L87)). Experts are kept until the chat is complete.
- **`selectExpert`** [lines 110-145](frontend-next/src/lib/useChat.ts#L110-L145): calls the select endpoint, then adds a "I'd like to connect with …" bubble and the reply, and clears the cards.
- **`resetChat`** [lines 147-159](frontend-next/src/lib/useChat.ts#L147-L159): tells the backend to forget the session and clears everything.

**Components** ([frontend-next/src/components/index.ts](frontend-next/src/components/index.ts) re-exports them):
- **`ChatInput`** [frontend-next/src/components/ChatInput.tsx:13-82](frontend-next/src/components/ChatInput.tsx#L13-L82): a text area; Enter sends, Shift+Enter adds a new line ([lines 29-34](frontend-next/src/components/ChatInput.tsx#L29-L34)); it grows with the text up to 200 px ([lines 56-60](frontend-next/src/components/ChatInput.tsx#L56-L60)).
- **`ChatMessage`** [frontend-next/src/components/ChatMessage.tsx:10-52](frontend-next/src/components/ChatMessage.tsx#L10-L52): one bubble, right-aligned and blue for the user. `whitespace-pre-wrap` keeps the LLM's line breaks. React escapes text automatically, so a reply can't inject HTML.
- **`ExpertList`** [frontend-next/src/components/ExpertList.tsx:13-50](frontend-next/src/components/ExpertList.tsx#L13-L50): a heading and a responsive grid (1, 2 or 3 columns by screen width).
- **`ExpertCard`** [frontend-next/src/components/ExpertCard.tsx:12-179](frontend-next/src/components/ExpertCard.tsx#L12-L179): labels the card by **kind** rather than rank ([lines 21-25](frontend-next/src/components/ExpertCard.tsx#L21-L25)), because pinned cards come first even with lower scores. It shows ratings only for network experts with reviews ([lines 68-78](frontend-next/src/components/ExpertCard.tsx#L68-L78)) and an "External freelancer… not affiliated" notice with a profile link ([lines 82-98](frontend-next/src/components/ExpertCard.tsx#L82-L98)). External links use `rel="noopener noreferrer nofollow"`: the opened page can't control this tab, isn't told where the visitor came from, and search engines don't treat it as an endorsement.
- **`Header`** [frontend-next/src/components/Header.tsx:24-91](frontend-next/src/components/Header.tsx#L24-L91): a label per phase from `phaseLabels` ([lines 11-22](frontend-next/src/components/Header.tsx#L11-L22)), four progress dots worked out from the phase's position in a list ([lines 43-75](frontend-next/src/components/Header.tsx#L43-L75)), and **New Chat**.

**[frontend-next/src/app/layout.tsx](frontend-next/src/app/layout.tsx)**: the HTML shell for every page: the Inter font, the page title and description.

**[frontend-next/src/app/page.tsx](frontend-next/src/app/page.tsx)**: the single page.
- **`hasPlaceholderContact`** [lines 11-13](frontend-next/src/app/page.tsx#L11-L13): the same `@example.com` check as the backend's `_build_contact_options`, so the popup never links to fake details.
- **`handleSelectExpert`** [lines 31-37](frontend-next/src/app/page.tsx#L31-L37): saves the chosen expert's details **before** calling the API, because the list is cleared afterwards, and opens the popup.
- Auto-scroll to the newest message with `useEffect` + `useRef` ([lines 44-47](frontend-next/src/app/page.tsx#L44-L47)).
- Welcome screen with four suggestion buttons when there are no messages ([lines 57-91](frontend-next/src/app/page.tsx#L57-L91)); the chat, the inline expert list and a typing indicator otherwise ([lines 94-129](frontend-next/src/app/page.tsx#L94-L129)).
- **Contact popup** [lines 132-267](frontend-next/src/app/page.tsx#L132-L267): three versions. External → a profile link; network expert with real details → WhatsApp (`wa.me/<digits>`), email (`mailto:`), LinkedIn, website; sample expert → an honest "demo data" note.
- The error box and the input, whose placeholder changes with the stage ([lines 270-292](frontend-next/src/app/page.tsx#L270-L292)).

**[frontend-next/src/app/globals.css](frontend-next/src/app/globals.css)**: the three Tailwind layers, a thin scrollbar, the typing-dots animation ([lines 41-63](frontend-next/src/app/globals.css#L41-L63)) and the popup fade-in ([lines 74-87](frontend-next/src/app/globals.css#L74-L87)).

### 6.13 The legacy Streamlit UI: frontend/streamlit_app.py

[frontend/streamlit_app.py](frontend/streamlit_app.py) was the first UI. It does the same job in one Python file: it keeps the session in `st.session_state` ([lines 91-102](frontend/streamlit_app.py#L91-L102)), calls the same endpoints with `requests` ([lines 105-159](frontend/streamlit_app.py#L105-L159)) and draws expert cards with Select buttons ([lines 170-199](frontend/streamlit_app.py#L170-L199)). It's useful to compare with the React version: Streamlit re-runs the whole script on every click, while React redraws only what changed. Two things are out of date: the hard-coded `API_URL` on port 8003 ([line 12](frontend/streamlit_app.py#L12)), and the completion message promising "Check your WhatsApp or email" ([line 240](frontend/streamlit_app.py#L240)), even though outreach is off and the client's contact details are never collected. It also inserts message text into HTML unescaped ([lines 162-167](frontend/streamlit_app.py#L162-L167)), unlike React.

### 6.14 Tests: tests/

- **[tests/test_handoff.py](tests/test_handoff.py)**: sample experts (`@example.com` or no email) get "None." and no WhatsApp option; a real-looking expert gets both options.
- **[tests/test_matching.py](tests/test_matching.py)**: featured → external → by score ([lines 17-20](tests/test_matching.py#L17-L20)); pinned experts added when the graph missed them; no duplicates; the limit keeps pinned slots; `public_expert` hides contacts unless opted in; and the `best_possible_score` arithmetic.

All of these test **pure functions** (no LLM, no database), which is why CI can run them with nothing else set up. Nothing tests the workflow routing, the API or the selection parsing; [exercise 8](#9-exercises) adds some.

### 6.15 Running and deploying

- **Windows scripts** ([start-all.bat](start-all.bat), [start-backend.bat](start-backend.bat), [start-frontend.bat](start-frontend.bat)): start the backend on **port 8003** and the frontend on 3000. They expect a `venv` folder and Node.js in `C:\Program Files\nodejs`.
- **[Dockerfile](Dockerfile)**: Python 3.11, install requirements, copy only `app/`, start Uvicorn on `$PORT` (set by hosts like Render) or 8000 ([line 17](Dockerfile#L17)). `--proxy-headers --forwarded-allow-ips="*"` makes `request.client.host` the visitor's real IP from the proxy's `X-Forwarded-For` header. Without it, every visitor would share the proxy's IP and one rate-limit bucket.
- **[docker-compose.yml](docker-compose.yml)**: PostgreSQL 16 (the SQL script is mounted into `/docker-entrypoint-initdb.d/`, so it runs automatically on a fresh database, [line 18](docker-compose.yml#L18)), Neo4j 5.17 with the APOC plugin, a backend service, and a Streamlit `frontend` service. The README only starts the two databases with it.
- **[.github/workflows/ci.yml](.github/workflows/ci.yml)**: on every push to `main` and every pull request, it checks that `app.main` imports, runs pytest, type-checks the frontend with `tsc --noEmit` and builds it.
- **[DEPLOY.md](DEPLOY.md)**: step-by-step free hosting: Neon (PostgreSQL), AuraDB (Neo4j), Render (backend from the Dockerfile), Vercel (frontend), seeding the hosted databases from your PC, and connecting CORS. It also lists the demo's limits ([lines 108-113](DEPLOY.md#L108-L113)).

---

## 7. One conversation traced from start to finish

Assume the live set-up: Groq key set, both databases seeded, outreach off. The user opens the site.

**Turn 1. "My phone might be hacked"** (a suggestion button)

1. `sendMessage` shows the bubble, sees no session, and calls `startChat`: [frontend-next/src/lib/useChat.ts:49-57](frontend-next/src/lib/useChat.ts#L49-L57) → [frontend-next/src/lib/api.ts:29-38](frontend-next/src/lib/api.ts#L29-L38).
2. FastAPI: CORS allows the origin; `chat_rate_limit` records the IP; the body is validated; `start_chat` makes a UUID: [app/api/rate_limit.py:21-49](app/api/rate_limit.py#L21-L49) → [app/api/chat.py:44-61](app/api/chat.py#L44-L61).
3. `ChatWorkflow.chat` creates the initial state (phase `greeting`), appends the user message, and invokes the graph: [app/agents/workflow.py:193-208](app/agents/workflow.py#L193-L208).
4. `route_by_phase` → `greeting` → one Groq call; phase becomes `gathering`; `END`: [app/agents/workflow.py:25-42](app/agents/workflow.py#L25-L42) → [app/agents/nodes/greeting.py:37-53](app/agents/nodes/greeting.py#L37-L53) → [app/llm/groq_client.py:105-124](app/llm/groq_client.py#L105-L124).
5. The state is stored in `sessions` and saved to PostgreSQL; the reply goes back: [app/agents/workflow.py:211-212](app/agents/workflow.py#L211-L212) → [app/db/conversations.py:19-49](app/db/conversations.py#L19-L49).

**Turn 2. "It's my iPhone, the battery drains fast and there are apps I didn't install"**

6. `continueChat` → `continue_chat` finds the session → phase `gathering` → `route_by_phase` returns `extraction`: [app/api/chat.py:76-96](app/api/chat.py#L76-L96).
7. `extraction_node` sends the whole chat to `generate_structured(ProblemContext)`. Groq returns JSON matching the schema, for example `device: "iphone"`, `platform: "ios"`, two symptoms, no timeline or impact yet. `is_sufficient()` → only one of three details → **False**. The message doesn't start with a question word, so attempts = 1: [app/agents/nodes/extraction.py:32-53](app/agents/nodes/extraction.py#L32-L53) → [app/llm/groq_client.py:149-166](app/llm/groq_client.py#L149-L166) → [app/schemas/problem.py:113-123](app/schemas/problem.py#L113-L123).
8. `ready_for_matching` → `ask_more` → `gathering_node` asks when it started: [app/agents/workflow.py:45-59](app/agents/workflow.py#L45-L59) → [app/agents/nodes/gathering.py:20-43](app/agents/nodes/gathering.py#L20-L43).

**Turn 3. "Since yesterday. It's my personal phone."**

9. Extraction again (from the whole chat): now with a timeline and impact `"personal"` → sufficient; attempts = 2 → `analyze`: [app/agents/workflow.py:54-56](app/agents/workflow.py#L54-L56).
10. `security_analysis_node` → `FoundationSecClient.analyze`: no local model, so it loads the graph vocabulary from Neo4j, builds the prompt with "ALLOWED VALUES", and asks Groq for a `SecurityAnalysis`. Say it returns `threat_type: "mobile_compromise"`, `required_skills: ["mobile_security", "ios_forensics", "incident_response"]`, `platforms: ["ios"]`, `recommended_services: ["incident_response"]`: [app/agents/nodes/security_analysis.py:17-28](app/agents/nodes/security_analysis.py#L17-L28) → [app/llm/foundation_sec.py:121-140](app/llm/foundation_sec.py#L121-L140).
11. `matching_node` → Cypher search. The sample expert Priya Sharma has all three skills, works on iOS and offers incident response, so she scores highest; her raw total is divided by `best_possible_score(3)` = 5.15: [app/agents/nodes/matching.py:30-36](app/agents/nodes/matching.py#L30-L36) → [app/graph/search.py:52-76](app/graph/search.py#L52-L76) → [app/graph/queries.py:33-144](app/graph/queries.py#L33-L144).
12. Profiles come from PostgreSQL; featured experts (if any) and one external freelancer are pinned in front: [app/agents/nodes/matching.py:39-55](app/agents/nodes/matching.py#L39-L55) → [app/agents/nodes/matching.py:87-129](app/agents/nodes/matching.py#L87-L129).
13. `presentation_node` writes the diagnosis and introductions in card order; phase `presenting`; `END`: [app/agents/nodes/presentation.py:36-65](app/agents/nodes/presentation.py#L36-L65).
14. Because the phase is `presenting`, the response includes the experts, with private contact fields removed: [app/agents/workflow.py:217-229](app/agents/workflow.py#L217-L229) → [app/schemas/expert.py:111-115](app/schemas/expert.py#L111-L115).
15. `useChat` stores them, and `page.tsx` renders the `ExpertList` under the messages: [frontend-next/src/lib/useChat.ts:67-76](frontend-next/src/lib/useChat.ts#L67-L76) → [frontend-next/src/app/page.tsx:101-109](frontend-next/src/app/page.tsx#L101-L109).

That turn made **three** LLM calls (extraction, analysis, presentation) and ran two database searches, so it's the slowest one.

**Turn 4. The user clicks "Connect with Priya"**

16. `handleSelectExpert` saves her details and opens the popup; `selectExpert` calls `POST /chat/{id}/select-expert?expert_id=1`: [frontend-next/src/app/page.tsx:31-37](frontend-next/src/app/page.tsx#L31-L37) → [frontend-next/src/lib/useChat.ts:110-118](frontend-next/src/lib/useChat.ts#L110-L118).
17. The endpoint checks she was matched, sets phase `handoff` and runs a turn: [app/api/chat.py:177-193](app/api/chat.py#L177-L193).
18. `route_by_phase` → `handoff_node`. She isn't external, so `HANDOFF_PROMPT` is used; her email ends in `@example.com`, so the contact options tell the LLM to say she's a sample profile. `_notify_expert` only logs, because outreach is off. Phase `complete`: [app/agents/nodes/handoff.py:54-84](app/agents/nodes/handoff.py#L54-L84) → [app/agents/nodes/handoff.py:87-96](app/agents/nodes/handoff.py#L87-L96) → [app/agents/nodes/handoff.py:158-160](app/agents/nodes/handoff.py#L158-L160).
19. The popup shows the "Sample expert profile" note, and the cards disappear: [frontend-next/src/app/page.tsx:247-257](frontend-next/src/app/page.tsx#L247-L257).

**Turn 5 onwards. "Should I reset my phone?"** → phase `complete` → `conversation_node`, which can now give real advice: [app/agents/nodes/conversation.py:12-40](app/agents/nodes/conversation.py#L12-L40).

---

## 8. Things to notice

Real issues found while reading the code. Items marked *(checked)* were confirmed by running the code.

### Bugs

1. **Copying `.env.example` as it is crashes the backend** *(checked)*. [.env.example:34](.env.example#L34) has a `DATABASE_URL=` line, but `database_url` is a *property* in `Settings`, not a field. pydantic-settings rejects unknown keys in a `.env` file by default, so `import app.config` fails with *"database_url: Extra inputs are not permitted"*. (Checked with a current pydantic-settings; the pinned 2.1.0 has the same default.) Delete that line, or add `extra = "ignore"` to the `Config` class at [app/config.py:115-118](app/config.py#L115-L118). Real environment variables that aren't fields are ignored, so Render and CI are unaffected.

2. **Typed selections pick an expert by accident** *(checked)*. `_parse_number_selection` looks for words as substrings ([app/agents/nodes/selection.py:133-135](app/agents/nodes/selection.py#L133-L135)). *"which **one** is better for my phone"* and *"n**one** of them sound right"* both select expert 1; *"it started **2**4 hours ago"* selects expert 2. The name check has the same problem with short name parts ([lines 57-60](app/agents/nodes/selection.py#L57-L60)). A wrong match goes straight to the handoff. Clicking a card is safe, because it uses the ID directly.

3. **Normal answers are mistaken for questions** *(checked)*. `_is_question` uses `startswith` ([app/agents/nodes/extraction.py:75-77](app/agents/nodes/extraction.py#L75-L77)), so *"**is**sue started yesterday"*, *"**do**wnloaded a movie…"*, *"**can**not open my files"* and *"**how**ever…"* all count as questions. Those turns don't count as attempts and can't trigger matching, so the user gets asked more questions than needed.

4. **A failed structured call becomes fake iPhone data.** If Groq's structured output fails twice or returns an HTTP error (a rate limit, say), `generate_structured` returns `get_mock_structured(...)` ([app/llm/groq_client.py:176](app/llm/groq_client.py#L176); Claude does the same at [app/llm/claude.py:181-183](app/llm/claude.py#L181-L183)). For extraction that's an iPhone with three symptoms, which **passes** `is_sufficient()`. So someone describing ransomware on a server can be matched with mobile experts, and nothing in the logs says why. Returning `None` (and keeping the previous context) would be safer.

5. **The frontend doesn't know the `conversation` phase.** After the handoff, the backend sends `phase: "conversation"` ([app/agents/nodes/conversation.py:37](app/agents/nodes/conversation.py#L37)). It isn't in the TypeScript `ConversationPhase` type ([frontend-next/src/types/index.ts:17-27](frontend-next/src/types/index.ts#L17-L27)) or `phaseLabels` ([frontend-next/src/components/Header.tsx:11-22](frontend-next/src/components/Header.tsx#L11-L22)), so the header's subtitle goes blank and all progress dots turn grey (`indexOf` returns −1). TypeScript can't catch it, because the value comes from JSON at run time.

6. **`docker compose up` (everything) fails.** The `frontend` service builds from `Dockerfile.frontend` ([docker-compose.yml:81](docker-compose.yml#L81)), which doesn't exist. The compose `backend` also gets no LLM key (no `env_file`, [lines 55-63](docker-compose.yml#L55-L63)), so it would silently run in mock mode.

### Design quirks

7. **Sessions live in memory.** `self.sessions` is a dict in one process ([app/agents/workflow.py:161](app/agents/workflow.py#L161)). A restart, a redeploy, or the free Render instance going to sleep loses every chat. The frontend then silently starts a *new* chat with the user's latest message ([frontend-next/src/lib/useChat.ts:79-87](frontend-next/src/lib/useChat.ts#L79-L87)), so Maya suddenly forgets everything. The conversations *are* saved in PostgreSQL but never loaded back. DEPLOY.md documents this ([DEPLOY.md:110-111](DEPLOY.md#L110-L111)).

8. **Slow, blocking work inside `async def` routes.** `start_chat` and `continue_chat` are `async`, but `workflow.chat` makes slow, *synchronous* LLM and database calls ([app/api/chat.py:61](app/api/chat.py#L61), [app/api/chat.py:96](app/api/chat.py#L96)). That blocks the event loop: while one user waits up to ~20 seconds for matching, nobody else's request (not even `/health`) is served. Plain `def` routes would run in FastAPI's thread pool instead.

9. **The two databases can drift apart.** The admin endpoints write only to PostgreSQL ([app/api/experts.py:64-140](app/api/experts.py#L64-L140)), so an expert added through the API never appears in graph search, and a "deleted" one stays active in Neo4j. Only `seed_databases.py` syncs both. The sample experts also depend on PostgreSQL happening to give them IDs 1, 2 and 3 to match the hard-coded Neo4j IDs ([scripts/init_neo4j.cypher:128-153](scripts/init_neo4j.cypher#L128-L153)).

10. **Fallback vocabulary doesn't match the graph.** `_fallback_analysis` uses skill names like `endpoint_security`, `server_forensics`, `negotiation` and `email_security` ([app/agents/nodes/security_analysis.py:59-81](app/agents/nodes/security_analysis.py#L59-L81)) that don't exist as Neo4j Skill nodes ([scripts/init_neo4j.cypher:22-50](scripts/init_neo4j.cypher#L22-L50)). PostgreSQL has 20 skills, Neo4j only 10, so even valid skills from the PostgreSQL list can't match.

11. **Port confusion.** The batch files, the frontend default and the Streamlit app use **8003**; the README, `python -m app.main`, the Dockerfile and docker-compose use **8000**. Following the README and then starting the frontend gives "Failed to send message". Set `NEXT_PUBLIC_API_URL=http://localhost:8000` in `frontend-next/.env.local`, or use the batch files.

12. **Rate-limit memory never shrinks.** `_requests` keeps a key for every IP ever seen ([app/api/rate_limit.py:17](app/api/rate_limit.py#L17)). Old timestamps are dropped, but empty deques stay. Fine for a demo; for real traffic, use a cache that expires keys (such as Redis).

13. **The Threat graph is never used.** The README's diagram shows `(Threat)-[:REQUIRES]->(Skill)`, and the Cypher script creates it ([scripts/init_neo4j.cypher:100-122](scripts/init_neo4j.cypher#L100-L122)), but no query reads it. Skills come only from the LLM's analysis ([exercise 9](#9-exercises)).

14. **The README is out of date.** It still describes Streamlit as the frontend ([README.md:19](README.md#L19), [README.md:61](README.md#L61), [README.md:130-137](README.md#L130-L137)) and has an author-specific `cd C:\CyberSecAgent` ([README.md:76](README.md#L76)).

15. **`.env.example` defaults don't match docker-compose.** The example uses `your_password_here`, the code defaults to `postgres`/`neo4j`, and compose creates `postgres123`/`neo4j123` ([docker-compose.yml:13](docker-compose.yml#L13), [docker-compose.yml:32](docker-compose.yml#L32)). Put the compose passwords in your `.env`.

16. **Settings print on import.** [app/config.py:130-131](app/config.py#L130-L131) prints every time the module is first imported, including in tests and the seed script.

### Unused code

- `async_database_url` and `get_settings` ([app/config.py:88-123](app/config.py#L88-L123)); `secret_key` is never read.
- `Base` in [app/db/postgres.py:29](app/db/postgres.py#L29) (the models use their own).
- `StructuredOutputParser` ([app/llm/structured.py](app/llm/structured.py)).
- `ConversationState`, `Message`, `ChatRequest`, `ChatResponse`, `ExpertRecommendation` and the `Expert` Pydantic model as used types ([app/schemas/conversation.py](app/schemas/conversation.py), [app/schemas/expert.py](app/schemas/expert.py#L11-L104)); `get_summary`, `get_search_terms`, `get_weighted_skills`.
- `get_expert_details`, `find_similar_experts` ([app/graph/search.py:108-131](app/graph/search.py#L108-L131)).
- `HandoffService.process_handoff` and `HandoffRequest` ([app/services/handoff.py:13-112](app/services/handoff.py#L13-L112)).
- `SUFFICIENCY_CHECK_PROMPT` and `EXPLANATION_PROMPT`.
- The `/api` rewrite in [frontend-next/next.config.js](frontend-next/next.config.js#L4-L11); `getSessionState` and `healthCheck` in `api.ts`.
- Packages: `asyncpg`, `tenacity`, `python-multipart`, `pytest-asyncio`.

### Setup gotchas

- **No key = mock mode, silently.** Without `GROQ_API_KEY` the app still "works", with canned iPhone answers. Look for `[MOCK MODE]` in the backend log.
- **Neo4j must be seeded** or matching returns nothing, and you get the hard-coded mock experts if it errors. Run `python scripts/seed_databases.py`.
- **`scripts/external_experts.json` lists real people's public profiles.** Keep it to what DEPLOY.md allows ([DEPLOY.md:101-104](DEPLOY.md#L101-L104)).
- **Foundation-Sec-8B locally** needs roughly 16 GB of GPU memory ([requirements-local-model.txt:2](requirements-local-model.txt#L2)); otherwise leave `USE_LOCAL_SECURITY_MODEL` off.
- **Windows-specific paths** in the batch files (`venv\Scripts\activate`, `C:\Program Files\nodejs`).

---

## 9. Exercises

From easy to advanced. Each says which file to change. Run `python -m pytest tests -q` after each backend change.

1. **Add a suggestion button.** Add "Someone logged into my email" to the welcome screen. *File:* [frontend-next/src/app/page.tsx:72-77](frontend-next/src/app/page.tsx#L72-L77).

2. **Fix the `.env.example` crash.** Remove the `DATABASE_URL` line, or make `Settings` ignore unknown keys. *Files:* [.env.example:33-34](.env.example#L33-L34) or [app/config.py:115-118](app/config.py#L115-L118). Prove it by copying `.env.example` to `.env` and running `python -c "import app.config"`.

3. **Teach the frontend the `conversation` phase.** Add it to the type and give it a label and a dot position. *Files:* [frontend-next/src/types/index.ts:17-27](frontend-next/src/types/index.ts#L17-L27), [frontend-next/src/components/Header.tsx:11-22](frontend-next/src/components/Header.tsx#L11-L22). Run `npx tsc --noEmit` in `frontend-next`.

4. **Whole-word selection.** Make `_parse_number_selection` and the name check match whole words only (hint: `re.search(rf"\b{word}\b", text)`), and require the bare-number rule to be the whole message or "number 2"-style. Add tests in a new `tests/test_selection.py` with the sentences from section 8. *File:* [app/agents/nodes/selection.py:51-67](app/agents/nodes/selection.py#L51-L67).

5. **Fix `_is_question`.** Compare the *first word* (`text.split()[0]`) with the list instead of `startswith`. Add tests. *File:* [app/agents/nodes/extraction.py:65-83](app/agents/nodes/extraction.py#L65-L83).

6. **No fake data on failure.** Make `generate_structured` return `None` when the real API fails (keep mock data for mock mode only), and handle `None` in the extraction node by keeping the previous context. *Files:* [app/llm/groq_client.py:159-176](app/llm/groq_client.py#L159-L176), [app/llm/claude.py:174-185](app/llm/claude.py#L174-L185), [app/agents/nodes/extraction.py:32-43](app/agents/nodes/extraction.py#L32-L43).

7. **Stop blocking the server.** Change the chat routes from `async def` to `def`, then open two browser tabs and check that one slow matching turn no longer freezes the other tab. *File:* [app/api/chat.py:44-110](app/api/chat.py#L44-L110).

8. **Test the workflow without an LLM.** Write tests that build a `ChatWorkflow`, replace `get_llm()` with a fake (for example, monkeypatch `app.agents.nodes.greeting.get_llm`), and check the phase sequence `greeting → gathering → presenting`. *Files:* new `tests/test_workflow.py`; see [app/agents/workflow.py:180-229](app/agents/workflow.py#L180-L229).

9. **Use the Threat graph.** After the analysis, add the skills linked to `threat_type` through `(:Threat)-[:REQUIRES]->(:Skill)` to `required_skills` (weighted by the relationship's `weight`). *Files:* [app/graph/queries.py](app/graph/queries.py#L27-L155) or [app/agents/nodes/matching.py:25-36](app/agents/nodes/matching.py#L25-L36); data in [scripts/init_neo4j.cypher:100-122](scripts/init_neo4j.cypher#L100-L122).

10. **Sessions that survive restarts.** When `session_id` isn't in memory, rebuild the state from the `conversations` and `conversation_messages` tables before giving up. Store the extra state the workflow needs (`extraction_attempts`, `matched_experts`) in a new JSON column. *Files:* [app/agents/workflow.py:193-198](app/agents/workflow.py#L193-L198), [app/db/conversations.py](app/db/conversations.py), [app/db/models.py:189-208](app/db/models.py#L189-L208), [app/api/chat.py:88-92](app/api/chat.py#L88-L92).

---

## 10. Glossary

**Agent / node.** Here, one step of the workflow: a Python function that takes the state and returns an updated state.

**API endpoint / route.** A URL plus HTTP method the backend answers, e.g. `POST /chat/start`.

**Alias (skill).** Another name for the same skill in Neo4j (`pentest` for `penetration_testing`).

**CORS.** A browser rule: a page from one site may only read API responses from another site if that API allows it.

**Cypher.** Neo4j's query language: `MATCH (a)-[:REL]->(b) RETURN a`.

**Dependency (FastAPI).** A function FastAPI runs before a route, e.g. a rate limit, an admin check or a database session.

**Duck typing.** Treating objects as interchangeable if they have the same methods (`GroqClient` and `ClaudeClient`).

**Featured expert.** An expert always shown first, with public contact details (from the git-ignored `featured_experts.json`).

**External freelancer.** A real person listed only by their public profile link; never contacted by the app.

**Graph database.** A database of nodes and relationships, good at "what's connected to what" questions. Here, Neo4j.

**Handoff.** Passing the user to a chosen expert: confirmation, contact options, optional notification.

**JSON Schema.** A JSON description of what a JSON object must look like; generated from a Pydantic model and sent to the LLM.

**JSX.** HTML-like syntax inside JavaScript/TypeScript, used by React.

**LangGraph.** A library for building workflows as graphs of functions sharing a state.

**LLM.** Large language model, e.g. the `gpt-oss` models on Groq, or Claude.

**Mock mode.** Running with canned LLM answers when no API key is set.

**ORM.** Object-relational mapper: tables as classes, rows as objects. Here, SQLAlchemy.

**Phase.** The saved stage of a conversation (`greeting`, `gathering`, `presenting`…) that decides where the next message enters the graph.

**Prompt (system / user).** Instructions to an LLM: the system prompt sets the role and rules, user messages carry the conversation.

**Rate limit.** A cap on requests per time window; exceeding it returns HTTP 429.

**React hook.** A `use…` function that gives a component state or side effects.

**Session.** One chat, identified by a UUID. Also, separately, a database session: one unit of database work.

**Singleton.** A single shared instance created on first use (`get_llm()`, `get_neo4j()`).

**Soft delete.** Marking a row inactive instead of removing it.

**Structured output.** Asking an LLM for JSON that fits a schema, then validating it into an object.

**Tailwind CSS.** Styling with small utility classes written in the HTML.

**Upsert.** Update the row if it exists, insert it if it doesn't.

**UUID.** A random 128-bit ID, practically never repeated; used for session IDs.
