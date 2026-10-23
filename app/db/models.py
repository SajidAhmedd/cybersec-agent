"""
SQLAlchemy Models for PostgreSQL
Expert profiles and related data
"""

from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean,
    DateTime, ForeignKey, Table, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Many-to-many association tables
expert_skills = Table(
    'expert_skills',
    Base.metadata,
    Column('expert_id', Integer, ForeignKey('experts.id'), primary_key=True),
    Column('skill_id', Integer, ForeignKey('skills.id'), primary_key=True)
)

expert_certifications = Table(
    'expert_certifications',
    Base.metadata,
    Column('expert_id', Integer, ForeignKey('experts.id'), primary_key=True),
    Column('certification_id', Integer, ForeignKey('certifications.id'), primary_key=True),
    Column('year_obtained', Integer, nullable=True)
)


class Expert(Base):
    """Expert profile table"""

    __tablename__ = 'experts'

    id = Column(Integer, primary_key=True, index=True)

    # Basic info
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=True, index=True)  # External profiles have none
    phone = Column(String(50), nullable=True)
    password_hash = Column(String(255), nullable=True)  # If they can login

    # Professional info
    title = Column(String(255), nullable=False)
    bio = Column(Text, nullable=True)
    years_experience = Column(Integer, default=0)
    specializations = Column(JSON, default=list)  # List of specialization strings

    # Service info
    hourly_rate = Column(Float, nullable=True)
    currency = Column(String(10), default='USD')
    availability = Column(Boolean, default=True)
    response_time = Column(String(50), nullable=True)  # e.g., "2 hours"

    # Location
    location = Column(String(255), nullable=True)
    timezone = Column(String(100), nullable=True)
    languages = Column(JSON, default=["English"])

    # Ratings
    rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    total_cases = Column(Integer, default=0)

    # Contact
    whatsapp = Column(String(50), nullable=True)
    linkedin = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)

    # External freelancer profiles (e.g. Upwork) - listed with a link only,
    # not part of the network and never contacted by the platform
    is_external = Column(Boolean, default=False)
    profile_platform = Column(String(50), nullable=True)
    profile_url = Column(String(500), nullable=True)

    # Profile
    profile_image = Column(String(500), nullable=True)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    skills = relationship("Skill", secondary=expert_skills, back_populates="experts")
    certifications = relationship("Certification", secondary=expert_certifications, back_populates="experts")
    reviews = relationship("Review", back_populates="expert")

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "title": self.title,
            "bio": self.bio,
            "years_experience": self.years_experience,
            "skills": [s.name for s in self.skills],
            "certifications": [c.name for c in self.certifications],
            "specializations": self.specializations or [],
            "hourly_rate": self.hourly_rate,
            "currency": self.currency,
            "availability": self.availability,
            "response_time": self.response_time,
            "location": self.location,
            "timezone": self.timezone,
            "languages": self.languages or ["English"],
            "rating": self.rating,
            "total_reviews": self.total_reviews,
            "total_cases": self.total_cases,
            "whatsapp": self.whatsapp,
            "linkedin": self.linkedin,
            "website": self.website,
            "is_external": bool(self.is_external),
            "profile_platform": self.profile_platform,
            "profile_url": self.profile_url,
        }


class Skill(Base):
    """Skills table"""

    __tablename__ = 'skills'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=True)  # e.g., "offensive", "defensive", "compliance"
    description = Column(Text, nullable=True)

    # For rarity scoring (IDF)
    expert_count = Column(Integer, default=0)

    # Relationships
    experts = relationship("Expert", secondary=expert_skills, back_populates="skills")


class Certification(Base):
    """Certifications table"""

    __tablename__ = 'certifications'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    issuer = Column(String(255), nullable=True)  # e.g., "Offensive Security", "(ISC)2"
    description = Column(Text, nullable=True)
    level = Column(String(50), nullable=True)  # e.g., "beginner", "intermediate", "expert"

    # Relationships
    experts = relationship("Expert", secondary=expert_certifications, back_populates="certifications")


class Review(Base):
    """Reviews for experts"""

    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True, index=True)
    expert_id = Column(Integer, ForeignKey('experts.id'), nullable=False)

    # Review content
    rating = Column(Float, nullable=False)  # 1-5
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)

    # Reviewer info (could be linked to a clients table)
    reviewer_name = Column(String(255), nullable=True)
    is_anonymous = Column(Boolean, default=False)

    # Metadata
    case_type = Column(String(100), nullable=True)  # Type of case reviewed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    expert = relationship("Expert", back_populates="reviews")


class Conversation(Base):
    """Store conversation sessions"""

    __tablename__ = 'conversations'

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)

    # State
    current_phase = Column(String(50), default='greeting')
    problem_context = Column(JSON, nullable=True)
    security_analysis = Column(JSON, nullable=True)

    # Outcome
    selected_expert_id = Column(Integer, ForeignKey('experts.id'), nullable=True)
    is_complete = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ConversationMessage(Base):
    """Store conversation messages"""

    __tablename__ = 'conversation_messages'

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False)

    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    agent = Column(String(50), nullable=True)  # 'claude', 'foundation_sec'

    created_at = Column(DateTime(timezone=True), server_default=func.now())
