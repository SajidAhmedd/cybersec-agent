"""
Expert Management Endpoints
For managing expert profiles and data
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.postgres import get_db
from app.db.models import Expert, Skill, Certification
from app.schemas.expert import Expert as ExpertSchema

router = APIRouter(prefix="/experts", tags=["Experts"])


@router.get("")
@router.get("/")
async def list_experts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    skill: Optional[str] = None,
    available_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    List all experts with optional filtering.
    """

    query = db.query(Expert)

    if available_only:
        query = query.filter(Expert.availability == True, Expert.is_active == True)

    if skill:
        query = query.join(Expert.skills).filter(Skill.name.ilike(f"%{skill}%"))

    total = query.count()
    experts = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "experts": [e.to_dict() for e in experts]
    }


@router.get("/{expert_id}")
async def get_expert(expert_id: int, db: Session = Depends(get_db)):
    """
    Get a specific expert by ID.
    """

    expert = db.query(Expert).filter(Expert.id == expert_id).first()

    if not expert:
        raise HTTPException(status_code=404, detail="Expert not found")

    return expert.to_dict()


@router.post("")
async def create_expert(expert_data: dict, db: Session = Depends(get_db)):
    """
    Create a new expert profile.
    """

    # Extract skills and certs for separate handling
    skill_names = expert_data.pop("skills", [])
    cert_names = expert_data.pop("certifications", [])

    # Create expert
    expert = Expert(**expert_data)

    # Handle skills
    for skill_name in skill_names:
        skill = db.query(Skill).filter(Skill.name == skill_name).first()
        if not skill:
            skill = Skill(name=skill_name)
            db.add(skill)
        expert.skills.append(skill)

    # Handle certifications
    for cert_name in cert_names:
        cert = db.query(Certification).filter(Certification.name == cert_name).first()
        if not cert:
            cert = Certification(name=cert_name)
            db.add(cert)
        expert.certifications.append(cert)

    db.add(expert)
    db.commit()
    db.refresh(expert)

    return expert.to_dict()


@router.put("/{expert_id}")
async def update_expert(
    expert_id: int,
    expert_data: dict,
    db: Session = Depends(get_db)
):
    """
    Update an existing expert profile.
    """

    expert = db.query(Expert).filter(Expert.id == expert_id).first()

    if not expert:
        raise HTTPException(status_code=404, detail="Expert not found")

    # Update fields
    for key, value in expert_data.items():
        if hasattr(expert, key) and key not in ["id", "created_at"]:
            setattr(expert, key, value)

    db.commit()
    db.refresh(expert)

    return expert.to_dict()


@router.delete("/{expert_id}")
async def delete_expert(expert_id: int, db: Session = Depends(get_db)):
    """
    Soft delete an expert (mark as inactive).
    """

    expert = db.query(Expert).filter(Expert.id == expert_id).first()

    if not expert:
        raise HTTPException(status_code=404, detail="Expert not found")

    expert.is_active = False
    db.commit()

    return {"message": "Expert deactivated", "expert_id": expert_id}


@router.get("/skills/list")
async def list_skills(db: Session = Depends(get_db)):
    """
    List all available skills.
    """

    skills = db.query(Skill).order_by(Skill.name).all()

    return {
        "skills": [{"id": s.id, "name": s.name, "category": s.category} for s in skills]
    }


@router.get("/certifications/list")
async def list_certifications(db: Session = Depends(get_db)):
    """
    List all available certifications.
    """

    certs = db.query(Certification).order_by(Certification.name).all()

    return {
        "certifications": [
            {"id": c.id, "name": c.name, "issuer": c.issuer}
            for c in certs
        ]
    }
