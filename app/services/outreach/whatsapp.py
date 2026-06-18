"""
WhatsApp Outreach Service
Send notifications to experts via WhatsApp using Twilio
"""

from typing import Optional
from twilio.rest import Client

from app.config import settings


class WhatsAppService:
    """
    Service for sending WhatsApp messages via Twilio.
    Used to notify experts about new client requests.
    """

    def __init__(self):
        self.account_sid = settings.twilio_account_sid
        self.auth_token = settings.twilio_auth_token
        self.from_number = settings.twilio_whatsapp_number

        self._client = None

    @property
    def client(self) -> Optional[Client]:
        """Lazy initialization of Twilio client"""
        if self._client is None and self.account_sid and self.auth_token:
            self._client = Client(self.account_sid, self.auth_token)
        return self._client

    def is_configured(self) -> bool:
        """Check if WhatsApp service is properly configured"""
        return all([
            self.account_sid,
            self.auth_token,
            self.from_number
        ])

    def send_message(self, to_number: str, message: str) -> dict:
        """
        Send a WhatsApp message.

        Args:
            to_number: Recipient's WhatsApp number (with country code)
            message: Message content

        Returns:
            Dict with status and message SID
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "WhatsApp service not configured"
            }

        # Format numbers for WhatsApp
        if not to_number.startswith("whatsapp:"):
            to_number = f"whatsapp:{to_number}"

        try:
            msg = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )

            return {
                "success": True,
                "message_sid": msg.sid,
                "status": msg.status
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def notify_expert(
        self,
        expert_phone: str,
        expert_name: str,
        problem_summary: dict,
        client_info: Optional[dict] = None
    ) -> dict:
        """
        Send a notification to an expert about a new client request.

        Args:
            expert_phone: Expert's WhatsApp number
            expert_name: Expert's name
            problem_summary: Summary of the client's problem
            client_info: Optional client contact info

        Returns:
            Dict with status
        """

        # Build notification message
        message = f"""🔔 *New Client Request*

Hi {expert_name},

A new client needs your help with a security issue:

*Issue Type:* {problem_summary.get('threat_type', 'Security concern')}
*Device:* {problem_summary.get('device', 'Not specified')}
*Urgency:* {problem_summary.get('urgency', 'Medium')}
*Symptoms:* {', '.join(problem_summary.get('symptoms', ['Not specified'])[:3])}

{f"*Timeline:* {problem_summary.get('timeline')}" if problem_summary.get('timeline') else ''}

The client has been matched with you based on your expertise. Please respond as soon as possible.

---
_Sent via CyberSecAgent_
"""

        return self.send_message(expert_phone, message)

    def send_client_intro(
        self,
        client_phone: str,
        expert_name: str,
        expert_title: str
    ) -> dict:
        """
        Send an introduction message to the client.

        Args:
            client_phone: Client's WhatsApp number
            expert_name: Expert's name
            expert_title: Expert's title

        Returns:
            Dict with status
        """

        message = f"""🔐 *CyberSecAgent - Expert Connected*

Great news! You've been connected with *{expert_name}*, {expert_title}.

They've received a summary of your situation and will reach out shortly.

While you wait, here are some general tips:
• Don't click on suspicious links
• Don't share passwords or OTPs
• Document any unusual activity

{expert_name} will guide you through the next steps.

---
_Sent via CyberSecAgent_
"""

        return self.send_message(client_phone, message)


# Singleton instance
_whatsapp_service: Optional[WhatsAppService] = None


def get_whatsapp_service() -> WhatsAppService:
    """Get or create WhatsApp service instance"""
    global _whatsapp_service
    if _whatsapp_service is None:
        _whatsapp_service = WhatsAppService()
    return _whatsapp_service
