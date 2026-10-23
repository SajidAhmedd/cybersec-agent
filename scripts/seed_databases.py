"""
Seed PostgreSQL and Neo4j with the schema and demo experts.

Uses the same settings as the app (.env or environment variables), so it can
seed hosted databases (e.g. Neon + Neo4j AuraDB) as well as local Docker ones.
Also syncs scripts/external_experts.json (public freelancer profiles, linked
only - see external_experts.example.json for the format).
Everything is idempotent, so running this again is safe.

Usage (from the project root):
    venv\\Scripts\\python.exe scripts\\seed_databases.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.db.postgres import engine  # noqa: E402
from app.graph.connection import get_neo4j  # noqa: E402

SCRIPTS = ROOT / "scripts"


def seed_postgres():
    sql = (SCRIPTS / "init_postgres.sql").read_text(encoding="utf-8")
    connection = engine.raw_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            cursor.execute("SELECT count(*) FROM experts")
            print(f"PostgreSQL seeded - experts: {cursor.fetchone()[0]}")
        connection.commit()
    finally:
        connection.close()


def _cypher_statements(text: str) -> list[str]:
    """Split a .cypher file into statements, dropping // comment lines"""
    lines = [line for line in text.splitlines() if not line.strip().startswith("//")]
    return [stmt.strip() for stmt in "\n".join(lines).split(";") if stmt.strip()]


def seed_neo4j():
    cypher = (SCRIPTS / "init_neo4j.cypher").read_text(encoding="utf-8")
    neo4j = get_neo4j()
    for statement in _cypher_statements(cypher):
        neo4j.run_write_query(statement)
    counts = neo4j.run_query("MATCH (n) RETURN labels(n)[0] AS label, count(*) AS n ORDER BY label")
    print("Neo4j seeded - " + ", ".join(f"{row['label']}: {row['n']}" for row in counts))


def seed_external_experts():
    """
    Sync scripts/external_experts.json (public freelancer profiles, link only)
    into both databases. External experts no longer in the file are deactivated.
    """
    from app.db.postgres import get_db_context
    from app.db.models import Expert, Skill

    path = SCRIPTS / "external_experts.json"
    entries = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    neo4j = get_neo4j()

    valid_skills = {r["name"] for r in neo4j.run_query("MATCH (s:Skill) RETURN s.name AS name")}
    valid_platforms = {r["name"] for r in neo4j.run_query("MATCH (p:Platform) RETURN p.name AS name")}
    valid_services = {r["name"] for r in neo4j.run_query("MATCH (s:Service) RETURN s.name AS name")}

    synced = []  # (expert_id, entry) pairs for the graph step
    with get_db_context() as db:
        for entry in entries:
            url = entry.get("profile_url", "")
            if not entry.get("name") or not url.startswith("https://"):
                print(f"Skipping external expert without a name or https profile_url: {entry}")
                continue

            for field, valid in (("skills", valid_skills), ("platforms", valid_platforms), ("services", valid_services)):
                unknown = [v for v in entry.get(field, []) if v not in valid]
                if unknown:
                    print(f"{entry['name']}: ignoring unknown {field} {unknown} (valid: {sorted(valid)})")
                entry[field] = [v for v in entry.get(field, []) if v in valid]

            expert = db.query(Expert).filter_by(profile_url=url).first()
            if expert is None:
                expert = Expert(profile_url=url)
                db.add(expert)

            expert.name = entry["name"]
            expert.title = entry.get("title") or "Security Freelancer"
            expert.bio = entry.get("bio")
            expert.profile_platform = entry.get("profile_platform")
            expert.location = entry.get("location")
            expert.years_experience = entry.get("years_experience") or 0
            expert.hourly_rate = entry.get("hourly_rate")
            expert.is_external = True
            expert.is_verified = False
            expert.is_active = True
            expert.availability = True
            expert.rating = 0.0
            expert.total_reviews = 0
            expert.skills = db.query(Skill).filter(Skill.name.in_(entry["skills"])).all()
            db.flush()  # assigns expert.id
            synced.append((expert.id, entry))

        synced_ids = [expert_id for expert_id, _ in synced]
        db.query(Expert).filter(
            Expert.is_external == True,  # noqa: E712
            ~Expert.id.in_(synced_ids)
        ).update({"is_active": False}, synchronize_session=False)

    for expert_id, entry in synced:
        neo4j.run_write_query(
            """
            MERGE (e:Expert {id: $id})
            SET e.name = $name, e.title = $title, e.location = $location,
                e.availability = true, e.is_active = true, e.handles_urgent = false,
                e.rating = 0.0, e.is_external = true
            WITH e
            OPTIONAL MATCH (e)-[old:HAS_SKILL|WORKS_ON|OFFERS]->()
            DELETE old
            """,
            {"id": expert_id, "name": entry["name"], "title": entry.get("title"), "location": entry.get("location")}
        )
        # External profiles are unverified and give no per-skill experience, so their
        # skills get a lower fixed weight and no experience bonus (years = 1)
        neo4j.run_write_query(
            """
            MATCH (e:Expert {id: $id})
            UNWIND $skills AS skill_name
            MATCH (s:Skill {name: skill_name})
            MERGE (e)-[r:HAS_SKILL]->(s)
            SET r.weight = 0.7, r.years = 1
            """,
            {"id": expert_id, "skills": entry["skills"]}
        )
        neo4j.run_write_query(
            """
            MATCH (e:Expert {id: $id})
            UNWIND $platforms AS platform_name
            MATCH (p:Platform {name: platform_name})
            MERGE (e)-[:WORKS_ON]->(p)
            """,
            {"id": expert_id, "platforms": entry["platforms"]}
        )
        neo4j.run_write_query(
            """
            MATCH (e:Expert {id: $id})
            UNWIND $services AS service_name
            MATCH (s:Service {name: service_name})
            MERGE (e)-[:OFFERS]->(s)
            """,
            {"id": expert_id, "services": entry["services"]}
        )

    neo4j.run_write_query(
        "MATCH (e:Expert {is_external: true}) WHERE NOT e.id IN $ids SET e.is_active = false",
        {"ids": [expert_id for expert_id, _ in synced]}
    )
    print(f"External experts synced: {len(synced)} active")


if __name__ == "__main__":
    seed_postgres()
    seed_neo4j()
    seed_external_experts()
