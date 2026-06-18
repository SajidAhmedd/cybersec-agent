"""
Security Analysis Node
Use Foundation-Sec-8B to analyze the threat and determine required expertise
"""

from app.agents.states import AgentState
from app.schemas.security import SecurityAnalysis
from app.llm import get_foundation_sec


def security_analysis_node(state: AgentState) -> AgentState:
    """
    Analyze the security incident using Foundation-Sec-8B.
    Classifies threat, determines required skills, and assesses severity.
    """

    foundation_sec = get_foundation_sec()

    # Get problem context
    problem_context = state.get("problem_context", {})

    # Run security analysis
    try:
        analysis = foundation_sec.analyze(
            problem_context=problem_context,
            response_model=SecurityAnalysis
        )
        analysis_dict = analysis.model_dump()

    except Exception as e:
        print(f"Security analysis failed: {e}")
        # Fallback to basic analysis
        analysis_dict = _fallback_analysis(problem_context)

    # Update state
    return {
        **state,
        "security_analysis": analysis_dict,
        "current_phase": "analyzing"
    }


def _fallback_analysis(problem_context: dict) -> dict:
    """
    Fallback analysis when Foundation-Sec fails.
    Uses basic heuristics to determine threat type.
    """

    device = problem_context.get("device", "").lower()
    platform = problem_context.get("platform", "").lower()
    symptoms = problem_context.get("symptoms", [])
    symptoms_lower = [s.lower() for s in symptoms]

    # Basic threat classification
    threat_type = "security_incident"
    required_skills = ["incident_response", "security_analysis"]

    # Device-based classification
    if any(d in device for d in ["phone", "iphone", "android", "mobile"]):
        threat_type = "mobile_compromise"
        required_skills.extend(["mobile_security", "mobile_forensics"])

    elif any(d in device for d in ["laptop", "desktop", "computer", "pc"]):
        threat_type = "endpoint_compromise"
        required_skills.extend(["endpoint_security", "malware_analysis"])

    elif any(d in device for d in ["server", "cloud", "aws", "azure"]):
        threat_type = "server_compromise"
        required_skills.extend(["cloud_security", "server_forensics"])

    # Symptom-based refinement
    if any("ransom" in s for s in symptoms_lower):
        threat_type = "ransomware"
        required_skills.extend(["ransomware_response", "negotiation"])

    elif any("phish" in s for s in symptoms_lower):
        threat_type = "phishing"
        required_skills.extend(["email_security", "social_engineering"])

    elif any("hack" in s for s in symptoms_lower):
        required_skills.append("penetration_testing")

    # Determine urgency from context
    urgency = problem_context.get("urgency", "MEDIUM")
    severity = "HIGH" if urgency in ["HIGH", "CRITICAL"] else "MEDIUM"

    return {
        "threat_type": threat_type,
        "threat_subcategory": None,
        "attack_vector": "unknown",
        "severity": severity,
        "confidence": 0.6,
        "required_skills": list(set(required_skills)),
        "recommended_services": ["incident_response", "consultation"],
        "platforms": [platform] if platform else [],
        "technologies": [],
        "reasoning": "Basic analysis based on reported symptoms"
    }
