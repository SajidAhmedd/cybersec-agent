"""
CyberSecAgent - Main FastAPI Application
Cybersecurity Expert Matching Platform
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.api import chat_router, experts_router, health_router
from app.db.postgres import init_db
from app.graph.connection import close_neo4j
from app.llm.gemini import get_gemini, reset_gemini_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Runs startup and shutdown logic.
    """
    # Startup
    print(f"Starting {settings.app_name}...")
    print(f"[STARTUP] USE_MOCK_LLM: {settings.use_mock_llm}")
    print(f"[STARTUP] GOOGLE_API_KEY present: {bool(settings.google_api_key)}")

    # Reset and initialize Gemini client
    reset_gemini_client()
    gemini = get_gemini()
    print(f"[STARTUP] Gemini client initialized - mock_mode: {gemini.mock_mode}")

    # Initialize database tables
    try:
        init_db()
        print("Database initialized")
    except Exception as e:
        print(f"Database initialization warning: {e}")

    yield

    # Shutdown
    print("Shutting down...")
    close_neo4j()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
    ## CyberSecAgent API

    AI-powered platform for matching cybersecurity incidents with expert professionals.

    ### Features:
    - **Conversational AI**: Natural language understanding of security incidents
    - **Expert Matching**: Graph-based matching to find the right security expert
    - **Multi-Agent System**: Specialized agents for conversation and security analysis

    ### How it works:
    1. Start a chat session with your security concern
    2. Our AI will ask clarifying questions
    3. We analyze the threat and find matching experts
    4. You choose an expert and get connected

    ### Endpoints:
    - `/chat/*` - Conversation endpoints
    - `/experts/*` - Expert management
    - `/health/*` - Health checks
    """,
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(experts_router)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "description": "Cybersecurity Expert Matching Platform",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
