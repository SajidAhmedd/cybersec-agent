"""
Matching Node
Find matching experts using Neo4j graph search
"""

from app.agents.states import AgentState
from app.schemas.security import SecurityAnalysis
from app.schemas.problem import ProblemContext
from app.graph import ExpertGraphSearch
from app.db.postgres import get_db_context
from app.db.models import Expert


def matching_node(state: AgentState) -> AgentState:
    """
    Find matching experts based on security analysis.
    Queries Neo4j graph and enriches with PostgreSQL profiles.
    """

    # Get analysis and context
    security_analysis_dict = state.get("security_analysis", {})
    problem_context_dict = state.get("problem_context", {})

    # Convert to schemas
    security_analysis = SecurityAnalysis.model_validate(security_analysis_dict)
    problem_context = ProblemContext.model_validate(problem_context_dict)

    # Search for experts
    try:
        graph_search = ExpertGraphSearch()
        matches = graph_search.search(
            security_analysis=security_analysis,
            problem_context=problem_context,
            limit=5
        )

        # Enrich with PostgreSQL data
        expert_ids = [m.expert_id for m in matches]
        experts = _get_expert_profiles(expert_ids)

        # Combine match data with expert profiles
        matched_experts = []
        for match in matches:
            expert_data = experts.get(match.expert_id)
            if expert_data:
                matched_experts.append({
                    "expert": expert_data,
                    "match": match.model_dump()
                })

    except Exception as e:
        print(f"Matching failed: {e}")
        # Return mock data for development
        matched_experts = _get_mock_experts()

    # Update state
    return {
        **state,
        "matched_experts": matched_experts,
        "current_phase": "matching"
    }


def _get_expert_profiles(expert_ids: list[int]) -> dict:
    """Fetch expert profiles from PostgreSQL"""
    if not expert_ids:
        return {}

    profiles = {}
    try:
        with get_db_context() as db:
            experts = db.query(Expert).filter(Expert.id.in_(expert_ids)).all()
            for expert in experts:
                profiles[expert.id] = expert.to_dict()
    except Exception as e:
        print(f"Failed to fetch profiles: {e}")

    return profiles


def _get_mock_experts() -> list[dict]:
    """Return mock experts for development/testing"""
    return [
        {
            "expert": {
                "id": 1,
                "name": "Priya Sharma",
                "title": "Mobile Security Specialist",
                "bio": "8 years experience in iOS and Android security. Certified GIAC Mobile Device Security Analyst.",
                "skills": ["mobile_security", "ios_forensics", "malware_analysis"],
                "certifications": ["GMOB", "OSCP"],
                "years_experience": 8,
                "rating": 4.9,
                "total_reviews": 47,
                "hourly_rate": 150,
                "currency": "USD",
                "response_time": "2 hours",
                "location": "Mumbai, India",
                "languages": ["English", "Hindi"],
                "availability": True
            },
            "match": {
                "expert_id": 1,
                "match_score": 0.92,
                "matched_skills": ["mobile_security", "ios_forensics"],
                "match_reasons": ["Specializes in mobile security", "iOS forensics expert"]
            }
        },
        {
            "expert": {
                "id": 2,
                "name": "Alex Chen",
                "title": "Incident Response Lead",
                "bio": "Former FBI cyber division. 12 years in digital forensics and incident response.",
                "skills": ["incident_response", "digital_forensics", "malware_analysis"],
                "certifications": ["GCIH", "GCFA", "CISSP"],
                "years_experience": 12,
                "rating": 4.8,
                "total_reviews": 89,
                "hourly_rate": 200,
                "currency": "USD",
                "response_time": "1 hour",
                "location": "San Francisco, USA",
                "languages": ["English", "Mandarin"],
                "availability": True
            },
            "match": {
                "expert_id": 2,
                "match_score": 0.85,
                "matched_skills": ["incident_response", "digital_forensics"],
                "match_reasons": ["Incident response specialist", "Available urgently"]
            }
        },
        {
            "expert": {
                "id": 3,
                "name": "Sarah Johnson",
                "title": "Cybersecurity Consultant",
                "bio": "Helping individuals and small businesses recover from cyber incidents. Patient and thorough approach.",
                "skills": ["security_consulting", "incident_response", "security_awareness"],
                "certifications": ["CISSP", "CISM"],
                "years_experience": 6,
                "rating": 4.95,
                "total_reviews": 34,
                "hourly_rate": 120,
                "currency": "USD",
                "response_time": "4 hours",
                "location": "London, UK",
                "languages": ["English"],
                "availability": True
            },
            "match": {
                "expert_id": 3,
                "match_score": 0.78,
                "matched_skills": ["incident_response", "security_consulting"],
                "match_reasons": ["Great with non-technical clients", "Patient approach"]
            }
        }
    ]
