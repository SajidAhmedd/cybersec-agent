"""
Health Check Endpoints
For monitoring and container orchestration
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.postgres import get_db
from app.graph.connection import get_neo4j
from app.config import settings

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "environment": settings.app_env
    }


@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check - verifies all dependencies are available.
    Used by Kubernetes/Docker for readiness probes.
    """
    checks = {
        "postgres": False,
        "neo4j": False,
        "gemini": False
    }

    # Check PostgreSQL
    try:
        db.execute("SELECT 1")
        checks["postgres"] = True
    except Exception as e:
        checks["postgres_error"] = str(e)

    # Check Neo4j
    try:
        neo4j = get_neo4j()
        checks["neo4j"] = neo4j.verify_connectivity()
    except Exception as e:
        checks["neo4j_error"] = str(e)

    # Check Gemini API key is configured
    checks["gemini"] = bool(settings.google_api_key)

    # Overall status
    all_healthy = all([
        checks["postgres"],
        checks["neo4j"],
        checks["gemini"]
    ])

    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks
    }


@router.get("/live")
async def liveness_check():
    """
    Liveness check - basic check that the service is running.
    Used by Kubernetes/Docker for liveness probes.
    """
    return {"status": "alive"}
