"""
Security Analysis Schema
Output from Foundation-Sec-8B cybersecurity reasoning agent
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class ThreatSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SecurityAnalysis(BaseModel):
    """
    Structured security analysis output from Foundation-Sec-8B.
    Maps user's problem to cybersecurity taxonomy and required expertise.
    """

    # Threat classification
    threat_type: str = Field(
        description="Primary threat category (e.g., 'mobile_compromise', 'ransomware', 'phishing')"
    )

    threat_subcategory: Optional[str] = Field(
        default=None,
        description="More specific threat classification"
    )

    attack_vector: Optional[str] = Field(
        default=None,
        description="Likely attack vector (e.g., 'malware', 'social_engineering', 'credential_theft')"
    )

    # Severity assessment
    severity: ThreatSeverity = Field(
        default=ThreatSeverity.MEDIUM,
        description="Assessed severity of the incident"
    )

    confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Confidence level in the analysis (0-1)"
    )

    # Required expertise
    required_skills: list[str] = Field(
        default_factory=list,
        description="Skills required to handle this incident"
    )

    recommended_services: list[str] = Field(
        default_factory=list,
        description="Types of services recommended (e.g., 'incident_response', 'forensics')"
    )

    # Platform/technology context
    platforms: list[str] = Field(
        default_factory=list,
        description="Relevant platforms (e.g., ['ios', 'mobile'])"
    )

    technologies: list[str] = Field(
        default_factory=list,
        description="Relevant technologies or tools"
    )

    # Additional context for matching
    industry_relevance: list[str] = Field(
        default_factory=list,
        description="Industries where this type of incident is common"
    )

    compliance_relevant: list[str] = Field(
        default_factory=list,
        description="Relevant compliance frameworks (e.g., 'GDPR', 'HIPAA', 'PCI-DSS')"
    )

    # Reasoning (for explainability)
    reasoning: Optional[str] = Field(
        default=None,
        description="Brief explanation of the analysis"
    )

    def get_search_terms(self) -> list[str]:
        """Get all terms relevant for expert search"""
        terms = []
        terms.append(self.threat_type)
        if self.threat_subcategory:
            terms.append(self.threat_subcategory)
        terms.extend(self.required_skills)
        terms.extend(self.platforms)
        terms.extend(self.recommended_services)
        return list(set(terms))

    def get_weighted_skills(self) -> list[tuple[str, float]]:
        """Get skills with weights for Neo4j query"""
        weighted = []
        # Primary skills get higher weight
        for i, skill in enumerate(self.required_skills):
            weight = 1.0 - (i * 0.1)  # Decreasing weight
            weighted.append((skill, max(weight, 0.5)))
        return weighted
