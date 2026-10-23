"""
Foundation-Sec-8B Client
Cybersecurity-specialized LLM for threat analysis and skill mapping
"""

from typing import Optional, Type, TypeVar
from pydantic import BaseModel
import json
import re

from app.config import settings

T = TypeVar('T', bound=BaseModel)

SECURITY_SYSTEM_PROMPT = """You are a cybersecurity expert with deep knowledge of:
- MITRE ATT&CK framework
- Common attack patterns and TTPs
- Incident response procedures
- Digital forensics
- Various threat types (malware, phishing, ransomware, etc.)

Analyze security incidents and provide structured threat assessments."""


def _normalize_name(name: str) -> str:
    """Normalize a skill/platform/service name to the graph's snake_case form"""
    return re.sub(r"[\s\-/]+", "_", name.strip().lower())


def _graph_vocabulary() -> dict[str, list[str]]:
    """Skill, platform and service names that exist in the Neo4j expert graph"""
    try:
        from app.graph.connection import get_neo4j
        rows = get_neo4j().run_query(
            "CALL { MATCH (s:Skill) RETURN collect(s.name) AS skills } "
            "CALL { MATCH (p:Platform) RETURN collect(p.name) AS platforms } "
            "CALL { MATCH (v:Service) RETURN collect(v.name) AS services } "
            "RETURN skills, platforms, services"
        )
        return dict(rows[0]) if rows else {}
    except Exception as e:
        print(f"Could not load graph vocabulary: {e}")
        return {}


class FoundationSecClient:
    """
    Client for Foundation-Sec-8B model.
    Used for cybersecurity reasoning:
    - Threat classification
    - Attack vector identification
    - Required skills mapping
    - Severity assessment

    Can run locally with transformers or via API.
    """

    def __init__(
        self,
        model_name: str = None,
        use_local: bool = None,
        hf_token: str = None
    ):
        self.model_name = model_name or settings.foundation_sec_model
        self.use_local = use_local if use_local is not None else settings.use_local_security_model
        self.hf_token = hf_token or settings.huggingface_token

        self._model = None
        self._tokenizer = None

        if self.use_local:
            self._load_local_model()

    def _load_local_model(self):
        """Load the model locally using transformers"""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch

            print(f"Loading {self.model_name} locally...")

            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                token=self.hf_token,
                trust_remote_code=True
            )

            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                token=self.hf_token,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True
            )

            print("Model loaded successfully")

        except ImportError:
            print("transformers not installed, falling back to LLM-based security analysis")
            self.use_local = False
        except Exception as e:
            print(f"Failed to load local model: {e}")
            self.use_local = False

    def analyze(
        self,
        problem_context: dict,
        response_model: Type[T] = None
    ) -> T | dict:
        """
        Analyze a cybersecurity problem and return structured analysis.

        Args:
            problem_context: Dictionary with problem details
            response_model: Optional Pydantic model for response

        Returns:
            SecurityAnalysis object or dict
        """

        vocabulary = _graph_vocabulary()
        prompt = self._build_analysis_prompt(problem_context, vocabulary)

        if self.use_local and self._model is not None:
            response = self._generate_local(prompt)
            if not response_model:
                return response
            analysis = self._parse_structured(response, response_model)
        elif response_model:
            # Use the conversational LLM's structured output mode
            from .provider import get_llm
            analysis = get_llm().generate_structured(
                prompt=prompt,
                response_model=response_model,
                system_prompt=SECURITY_SYSTEM_PROMPT
            )
        else:
            return self._generate_with_llm(prompt)

        return self._normalize_names(analysis)

    @staticmethod
    def _normalize_names(analysis: T) -> T:
        """Map skill/platform/service names onto the graph's snake_case names"""
        for field in ("required_skills", "platforms", "recommended_services"):
            values = getattr(analysis, field, None)
            if values:
                setattr(analysis, field, list(dict.fromkeys(_normalize_name(v) for v in values)))
        return analysis

    def _build_analysis_prompt(self, problem_context: dict, vocabulary: dict = None) -> str:
        """Build the analysis prompt for the security model"""

        vocabulary = vocabulary or {}
        allowed = ""
        if vocabulary:
            allowed = f"""
ALLOWED VALUES (expert matching only works with these exact names):
- required_skills (choose at least two): {', '.join(vocabulary.get('skills', []))}
- platforms: {', '.join(vocabulary.get('platforms', []))}
- recommended_services: {', '.join(vocabulary.get('services', []))}
"""

        return f"""You are a cybersecurity expert analyzing a security incident.

INCIDENT DETAILS:
- Device: {problem_context.get('device', 'Unknown')}
- Platform: {problem_context.get('platform', 'Unknown')}
- Symptoms: {', '.join(problem_context.get('symptoms', []))}
- Timeline: {problem_context.get('timeline', 'Unknown')}
- Impact: {problem_context.get('impact', 'Unknown')}
- Environment: {problem_context.get('environment', 'Unknown')}

ANALYSIS REQUIRED:
Based on these details, provide a structured security analysis.
{allowed}
Output the following as valid JSON:
{{
    "threat_type": "primary threat category (e.g., mobile_compromise, ransomware, phishing, data_breach)",
    "threat_subcategory": "more specific classification if applicable",
    "attack_vector": "likely attack method (e.g., malware, social_engineering, credential_theft)",
    "severity": "LOW, MEDIUM, HIGH, or CRITICAL",
    "confidence": 0.0 to 1.0 confidence in this analysis,
    "required_skills": ["list", "of", "required", "expert", "skills"],
    "recommended_services": ["incident_response", "forensics", etc.],
    "platforms": ["relevant", "platforms"],
    "technologies": ["relevant", "technologies"],
    "reasoning": "brief explanation of your analysis"
}}

Respond ONLY with the JSON object."""

    def _generate_local(self, prompt: str) -> str:
        """Generate response using local model"""
        import torch

        inputs = self._tokenizer(prompt, return_tensors="pt").to(self._model.device)

        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.3,
                do_sample=True,
                top_p=0.9,
                pad_token_id=self._tokenizer.eos_token_id
            )

        response = self._tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract just the generated part (after prompt)
        if prompt in response:
            response = response[len(prompt):].strip()

        return response

    def _generate_with_llm(self, prompt: str) -> str:
        """Fallback: Use the conversational LLM with security-focused prompting"""
        from .provider import get_llm

        llm = get_llm()

        return llm.generate(
            prompt=prompt,
            system_prompt=SECURITY_SYSTEM_PROMPT
        )

    def _parse_structured(self, response: str, response_model: Type[T]) -> T:
        """Parse response into Pydantic model"""

        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            response = json_match.group(0)

        try:
            data = json.loads(response)
            return response_model.model_validate(data)
        except json.JSONDecodeError as e:
            # Return a default analysis if parsing fails
            print(f"Failed to parse security analysis: {e}")
            from app.schemas.security import SecurityAnalysis
            return SecurityAnalysis(
                threat_type="unknown",
                severity="MEDIUM",
                required_skills=["incident_response", "security_analysis"],
                recommended_services=["consultation"],
                reasoning="Unable to parse detailed analysis"
            )


# Singleton instance
_foundation_sec_client: Optional[FoundationSecClient] = None


def get_foundation_sec() -> FoundationSecClient:
    """Get or create Foundation-Sec client instance"""
    global _foundation_sec_client
    if _foundation_sec_client is None:
        _foundation_sec_client = FoundationSecClient()
    return _foundation_sec_client
