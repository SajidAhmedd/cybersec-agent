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
        # Search wider than we show, so the pinned slots can be filled from real matches
        matches = graph_search.search(
            security_analysis=security_analysis,
            problem_context=problem_context,
            limit=10
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

        featured, external = _get_pinned_candidates()
        matched_experts = order_matches(
            matched_experts, featured, external, security_analysis.required_skills, limit=5
        )

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


def order_matches(
    matched: list[dict],
    featured: list[dict],
    external: list[dict],
    required_skills: list[str],
    limit: int = 5
) -> list[dict]:
    """
    Order the experts shown to the user: featured experts first, then the
    best-matching external freelancer (so a real profile is always offered),
    then the remaining matches by score.

    featured / external are expert profiles used when the graph search did not
    return them for this problem.
    """
    by_id = {m["expert"]["id"]: m for m in matched}

    def as_match(expert: dict) -> dict:
        if expert["id"] in by_id:
            return by_id[expert["id"]]
        skills = [s for s in required_skills if s in expert.get("skills", [])]
        return {
            "expert": expert,
            "match": {
                "expert_id": expert["id"],
                "match_score": 0.9 if expert.get("is_featured") else 0.6,
                "matched_skills": skills,
                "matched_certifications": [],
                "match_reasons": [f"Has skills: {', '.join(skills[:3])}"] if skills else ["General security support"],
            },
        }

    ordered = [as_match(e) for e in featured]

    external_match = next((m for m in matched if m["expert"].get("is_external")), None)
    if external_match is None and external:
        external_match = as_match(external[0])
    if external_match is not None:
        ordered.append(external_match)

    shown = {m["expert"]["id"] for m in ordered}
    ordered += [m for m in matched if m["expert"]["id"] not in shown]
    return ordered[:max(limit, len(featured) + 1)]


def _get_pinned_candidates() -> tuple[list[dict], list[dict]]:
    """Fetch active featured experts and active external freelancers from PostgreSQL"""
    try:
        with get_db_context() as db:
            active = db.query(Expert).filter(Expert.is_active == True)  # noqa: E712
            featured = [e.to_dict() for e in active.filter(Expert.is_featured == True).order_by(Expert.id)]  # noqa: E712
            external = [e.to_dict() for e in active.filter(Expert.is_external == True).order_by(Expert.id)]  # noqa: E712
        return featured, external
    except Exception as e:
        print(f"Failed to fetch pinned experts: {e}")
        return [], []


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
