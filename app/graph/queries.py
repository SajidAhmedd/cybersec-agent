"""
Cypher Query Builder
Builds dynamic queries for expert search based on security analysis
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ExpertSearchQuery:
    """Builds Cypher queries for expert matching"""

    # Search criteria
    required_skills: list[str]
    platforms: list[str] = None
    services: list[str] = None

    # Filters
    location: Optional[str] = None
    urgency: Optional[str] = None
    max_rate: Optional[float] = None

    # Limits
    limit: int = 10

    def build_query(self) -> tuple[str, dict]:
        """
        Build the main expert search query.
        Returns (cypher_query, parameters)
        """

        query = """
        // =====================================================================
        // EXPERT SEARCH QUERY
        // Find experts matching required skills through graph relationships
        // =====================================================================

        // Input parameters
        WITH $required_skills AS required_skills,
             $platforms AS platforms,
             $services AS services,
             $location AS user_location,
             $urgency AS urgency

        // ---------------------------------------------------------------------
        // STEP 1: Find matching skill nodes
        // ---------------------------------------------------------------------
        UNWIND required_skills AS skill_name

        // Fuzzy match on skill name or aliases
        MATCH (skill:Skill)
        WHERE toLower(skill.name) = toLower(skill_name)
           OR toLower(skill_name) IN [alias IN skill.aliases | toLower(alias)]

        // ---------------------------------------------------------------------
        // STEP 2: Traverse to experts who have these skills
        // ---------------------------------------------------------------------
        MATCH (skill)<-[has_skill:HAS_SKILL]-(expert:Expert)
        WHERE expert.is_active = true
          AND expert.availability = true

        // ---------------------------------------------------------------------
        // STEP 3: Calculate base match score
        // ---------------------------------------------------------------------
        WITH expert, skill, has_skill,
             // Skill weight (from edge, based on IDF)
             COALESCE(has_skill.weight, 0.5) AS skill_weight,
             // Years with this skill adds to score
             COALESCE(has_skill.years, 1) * 0.05 AS experience_bonus

        // Aggregate scores per expert
        WITH expert,
             collect(DISTINCT skill.name) AS matched_skills,
             sum(skill_weight + experience_bonus) AS skill_score,
             count(DISTINCT skill) AS skill_match_count

        // ---------------------------------------------------------------------
        // STEP 4: Optional platform matching
        // ---------------------------------------------------------------------
        OPTIONAL MATCH (expert)-[works_on:WORKS_ON]->(platform:Platform)
        WHERE platform.name IN $platforms

        WITH expert, matched_skills, skill_score, skill_match_count,
             collect(DISTINCT platform.name) AS matched_platforms,
             CASE WHEN count(platform) > 0 THEN 0.15 ELSE 0 END AS platform_bonus

        // ---------------------------------------------------------------------
        // STEP 5: Optional service matching
        // ---------------------------------------------------------------------
        OPTIONAL MATCH (expert)-[offers:OFFERS]->(service:Service)
        WHERE service.name IN $services

        WITH expert, matched_skills, skill_score, skill_match_count,
             matched_platforms, platform_bonus,
             collect(DISTINCT service.name) AS matched_services,
             CASE WHEN count(service) > 0 THEN 0.1 ELSE 0 END AS service_bonus

        // ---------------------------------------------------------------------
        // STEP 6: Apply bonuses
        // ---------------------------------------------------------------------
        WITH expert, matched_skills, matched_platforms, matched_services,
             skill_score, skill_match_count, platform_bonus, service_bonus,

             // Location bonus
             CASE
                WHEN $location IS NOT NULL AND expert.location = $location
                THEN 0.1
                ELSE 0
             END AS location_bonus,

             // Urgency handling bonus
             CASE
                WHEN $urgency IN ['HIGH', 'CRITICAL'] AND expert.handles_urgent = true
                THEN 0.15
                ELSE 0
             END AS urgency_bonus,

             // Rating bonus
             COALESCE(expert.rating, 0) * 0.05 AS rating_bonus

        // ---------------------------------------------------------------------
        // STEP 7: Calculate final score
        // ---------------------------------------------------------------------
        WITH expert, matched_skills, matched_platforms, matched_services,
             skill_match_count,
             (skill_score + platform_bonus + service_bonus +
              location_bonus + urgency_bonus + rating_bonus) AS total_score

        // ---------------------------------------------------------------------
        // STEP 8: Return top experts
        // ---------------------------------------------------------------------
        RETURN
            expert.id AS expert_id,
            expert.name AS name,
            total_score AS match_score,
            matched_skills,
            matched_platforms,
            matched_services,
            skill_match_count

        ORDER BY total_score DESC, skill_match_count DESC
        LIMIT $limit
        """

        parameters = {
            "required_skills": self.required_skills or [],
            "platforms": self.platforms or [],
            "services": self.services or [],
            "location": self.location,
            "urgency": self.urgency,
            "limit": self.limit
        }

        return query, parameters

    def build_simple_query(self) -> tuple[str, dict]:
        """
        Simplified query for when graph is not fully populated.
        Falls back to direct skill matching.
        """

        query = """
        // Simple skill-based expert search
        MATCH (expert:Expert)-[:HAS_SKILL]->(skill:Skill)
        WHERE skill.name IN $required_skills
          AND expert.is_active = true

        WITH expert, collect(skill.name) AS matched_skills, count(skill) AS match_count

        RETURN
            expert.id AS expert_id,
            expert.name AS name,
            toFloat(match_count) / toFloat($skill_count) AS match_score,
            matched_skills

        ORDER BY match_count DESC
        LIMIT $limit
        """

        parameters = {
            "required_skills": self.required_skills or [],
            "skill_count": len(self.required_skills) if self.required_skills else 1,
            "limit": self.limit
        }

        return query, parameters
