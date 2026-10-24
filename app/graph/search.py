"""
Expert Graph Search
High-level search interface using Neo4j
"""

from typing import Optional
from app.schemas.security import SecurityAnalysis
from app.schemas.problem import ProblemContext
from app.schemas.expert import ExpertMatch
from .connection import get_neo4j
from .queries import ExpertSearchQuery


class ExpertGraphSearch:
    """
    Search for experts in the Neo4j knowledge graph.
    Uses security analysis to find best matches.
    """

    def __init__(self):
        self.neo4j = get_neo4j()

    def search(
        self,
        security_analysis: SecurityAnalysis,
        problem_context: Optional[ProblemContext] = None,
        limit: int = 10
    ) -> list[ExpertMatch]:
        """
        Search for experts based on security analysis.

        Args:
            security_analysis: Output from Foundation-Sec-8B
            problem_context: Optional context for additional filtering
            limit: Maximum number of results

        Returns:
            List of ExpertMatch objects with scores
        """

        # Build query parameters from analysis
        query_builder = ExpertSearchQuery(
            required_skills=security_analysis.required_skills,
            platforms=security_analysis.platforms,
            services=security_analysis.recommended_services,
            location=problem_context.location if problem_context else None,
            urgency=problem_context.urgency.value if problem_context else None,
            limit=limit
        )

        # Try full query first, fall back to simple if needed
        try:
            cypher, params = query_builder.build_query()
            results = self.neo4j.run_query(cypher, params)
            # The full query sums raw points; scale to the best score possible for this problem
            best_score = self.best_possible_score(
                len(security_analysis.required_skills or []),
                has_location=bool(problem_context and problem_context.location)
            )
        except Exception as e:
            print(f"Full query failed, trying simple: {e}")
            cypher, params = query_builder.build_simple_query()
            results = self.neo4j.run_query(cypher, params)
            best_score = 1.0  # already a 0-1 skill coverage ratio

        # Convert to ExpertMatch objects
        matches = []
        for record in results:
            match = ExpertMatch(
                expert_id=record["expert_id"],
                match_score=round(min(record.get("match_score", 0.5) / best_score, 1.0), 2),
                matched_skills=record.get("matched_skills", []),
                matched_certifications=record.get("matched_certifications", []),
                match_reasons=self._generate_match_reasons(record)
            )
            matches.append(match)

        return matches

    @staticmethod
    def best_possible_score(required_skill_count: int, has_location: bool = False) -> float:
        """
        Highest total the full query can give: per matched skill a weight of up to
        1.0 plus 10+ years of experience (0.5), then the platform (0.15), service
        (0.1), urgency (0.15) and 5-star rating (0.25) bonuses, and location (0.1)
        when the user gave one.
        """
        return max(required_skill_count, 1) * 1.5 + 0.65 + (0.1 if has_location else 0)

    def _generate_match_reasons(self, record: dict) -> list[str]:
        """Generate human-readable match reasons"""
        reasons = []

        matched_skills = record.get("matched_skills", [])
        if matched_skills:
            reasons.append(f"Has skills: {', '.join(matched_skills[:3])}")

        matched_platforms = record.get("matched_platforms", [])
        if matched_platforms:
            reasons.append(f"Experience with: {', '.join(matched_platforms)}")

        matched_services = record.get("matched_services", [])
        if matched_services:
            reasons.append(f"Offers: {', '.join(matched_services)}")

        return reasons

    def get_expert_details(self, expert_id: int) -> Optional[dict]:
        """Get full expert node details from Neo4j"""
        query = """
        MATCH (e:Expert {id: $expert_id})
        OPTIONAL MATCH (e)-[:HAS_SKILL]->(s:Skill)
        OPTIONAL MATCH (e)-[:HAS_CERT]->(c:Certification)
        RETURN e, collect(DISTINCT s.name) AS skills, collect(DISTINCT c.name) AS certs
        """
        results = self.neo4j.run_query(query, {"expert_id": expert_id})
        if results:
            return results[0]
        return None

    def find_similar_experts(self, expert_id: int, limit: int = 5) -> list[dict]:
        """Find experts similar to a given expert"""
        query = """
        MATCH (e:Expert {id: $expert_id})-[:HAS_SKILL]->(s:Skill)<-[:HAS_SKILL]-(similar:Expert)
        WHERE similar.id <> $expert_id AND similar.is_active = true
        WITH similar, count(s) AS shared_skills
        RETURN similar.id AS expert_id, similar.name AS name, shared_skills
        ORDER BY shared_skills DESC
        LIMIT $limit
        """
        return self.neo4j.run_query(query, {"expert_id": expert_id, "limit": limit})
