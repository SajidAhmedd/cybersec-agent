"""
Handoff Service
Manages the handoff process between clients and experts
"""

from typing import Optional
from dataclasses import dataclass

from .outreach.whatsapp import get_whatsapp_service
from .outreach.email import get_email_service


@dataclass
class HandoffRequest:
    """Data for a handoff request"""
    expert_id: int
    expert_name: str
    expert_email: Optional[str]
    expert_phone: Optional[str]
    expert_title: str

    problem_summary: dict
    conversation_summary: str

    client_email: Optional[str] = None
    client_phone: Optional[str] = None


class HandoffService:
    """
    Service for managing the handoff between clients and experts.
    Coordinates notifications via WhatsApp and Email.
    """

    def __init__(self):
        self.whatsapp = get_whatsapp_service()
        self.email = get_email_service()

    def process_handoff(self, request: HandoffRequest) -> dict:
        """
        Process a complete handoff.

        Sends notifications to:
        1. Expert via WhatsApp and/or Email
        2. Client confirmation (if contact info available)

        Args:
            request: HandoffRequest with all necessary details

        Returns:
            Dict with results of all notifications
        """

        results = {
            "expert_notified": False,
            "client_notified": False,
            "channels_used": [],
            "errors": []
        }

        # Notify expert via WhatsApp
        if request.expert_phone and self.whatsapp.is_configured():
            whatsapp_result = self.whatsapp.notify_expert(
                expert_phone=request.expert_phone,
                expert_name=request.expert_name,
                problem_summary=request.problem_summary
            )

            if whatsapp_result.get("success"):
                results["expert_notified"] = True
                results["channels_used"].append("whatsapp")
            else:
                results["errors"].append(f"WhatsApp: {whatsapp_result.get('error')}")

        # Notify expert via Email
        if request.expert_email and self.email.is_configured():
            email_result = self.email.notify_expert(
                expert_email=request.expert_email,
                expert_name=request.expert_name,
                problem_summary=request.problem_summary,
                conversation_summary=request.conversation_summary
            )

            if email_result.get("success"):
                results["expert_notified"] = True
                results["channels_used"].append("email")
            else:
                results["errors"].append(f"Email: {email_result.get('error')}")

        # Send client confirmation via WhatsApp
        if request.client_phone and self.whatsapp.is_configured():
            client_whatsapp = self.whatsapp.send_client_intro(
                client_phone=request.client_phone,
                expert_name=request.expert_name,
                expert_title=request.expert_title
            )

            if client_whatsapp.get("success"):
                results["client_notified"] = True

        # Send client confirmation via Email
        if request.client_email and self.email.is_configured():
            client_email = self.email.send_client_confirmation(
                client_email=request.client_email,
                expert_name=request.expert_name,
                expert_title=request.expert_title
            )

            if client_email.get("success"):
                results["client_notified"] = True

        return results

    def notify_expert_only(
        self,
        expert_email: Optional[str],
        expert_phone: Optional[str],
        expert_name: str,
        problem_summary: dict,
        conversation_summary: str
    ) -> dict:
        """
        Send notification to expert only.
        Used when client contact info is not available.
        """

        results = {
            "success": False,
            "channels_used": [],
            "errors": []
        }

        # Try WhatsApp first
        if expert_phone and self.whatsapp.is_configured():
            result = self.whatsapp.notify_expert(
                expert_phone=expert_phone,
                expert_name=expert_name,
                problem_summary=problem_summary
            )
            if result.get("success"):
                results["success"] = True
                results["channels_used"].append("whatsapp")
            else:
                results["errors"].append(result.get("error"))

        # Try Email
        if expert_email and self.email.is_configured():
            result = self.email.notify_expert(
                expert_email=expert_email,
                expert_name=expert_name,
                problem_summary=problem_summary,
                conversation_summary=conversation_summary
            )
            if result.get("success"):
                results["success"] = True
                results["channels_used"].append("email")
            else:
                results["errors"].append(result.get("error"))

        return results


# Singleton instance
_handoff_service: Optional[HandoffService] = None


def get_handoff_service() -> HandoffService:
    """Get or create handoff service instance"""
    global _handoff_service
    if _handoff_service is None:
        _handoff_service = HandoffService()
    return _handoff_service
