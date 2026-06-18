"""
Email Outreach Service
Send notifications to experts via email using SendGrid
"""

from typing import Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

from app.config import settings


class EmailService:
    """
    Service for sending emails via SendGrid.
    Used to notify experts about new client requests.
    """

    def __init__(self):
        self.api_key = settings.sendgrid_api_key
        self.from_email = settings.sendgrid_from_email

        self._client = None

    @property
    def client(self) -> Optional[SendGridAPIClient]:
        """Lazy initialization of SendGrid client"""
        if self._client is None and self.api_key:
            self._client = SendGridAPIClient(self.api_key)
        return self._client

    def is_configured(self) -> bool:
        """Check if email service is properly configured"""
        return all([
            self.api_key,
            self.from_email
        ])

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_content: Optional[str] = None
    ) -> dict:
        """
        Send an email.

        Args:
            to_email: Recipient's email address
            subject: Email subject
            html_content: HTML email body
            plain_content: Optional plain text body

        Returns:
            Dict with status
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "Email service not configured"
            }

        try:
            message = Mail(
                from_email=Email(self.from_email, "CyberSecAgent"),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )

            if plain_content:
                message.add_content(Content("text/plain", plain_content))

            response = self.client.send(message)

            return {
                "success": response.status_code in [200, 201, 202],
                "status_code": response.status_code
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def notify_expert(
        self,
        expert_email: str,
        expert_name: str,
        problem_summary: dict,
        conversation_summary: Optional[str] = None
    ) -> dict:
        """
        Send a notification email to an expert about a new client request.

        Args:
            expert_email: Expert's email address
            expert_name: Expert's name
            problem_summary: Summary of the client's problem
            conversation_summary: Optional conversation summary

        Returns:
            Dict with status
        """

        subject = f"🔔 New Client Request - {problem_summary.get('threat_type', 'Security Issue')}"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #1a73e8; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .content {{ background-color: #f8f9fa; padding: 20px; border-radius: 0 0 8px 8px; }}
        .detail {{ margin: 10px 0; }}
        .label {{ font-weight: bold; color: #666; }}
        .value {{ color: #333; }}
        .urgency-high {{ color: #d93025; font-weight: bold; }}
        .urgency-medium {{ color: #f9ab00; font-weight: bold; }}
        .urgency-low {{ color: #34a853; font-weight: bold; }}
        .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 New Client Request</h1>
        </div>
        <div class="content">
            <p>Hi {expert_name},</p>
            <p>A new client has been matched with you based on your expertise. Here are the details:</p>

            <div class="detail">
                <span class="label">Issue Type:</span>
                <span class="value">{problem_summary.get('threat_type', 'Security concern')}</span>
            </div>

            <div class="detail">
                <span class="label">Device/Platform:</span>
                <span class="value">{problem_summary.get('device', 'Not specified')} / {problem_summary.get('platform', 'Not specified')}</span>
            </div>

            <div class="detail">
                <span class="label">Urgency:</span>
                <span class="urgency-{problem_summary.get('urgency', 'medium').lower()}">{problem_summary.get('urgency', 'Medium')}</span>
            </div>

            <div class="detail">
                <span class="label">Symptoms:</span>
                <span class="value">{', '.join(problem_summary.get('symptoms', ['Not specified']))}</span>
            </div>

            {f'<div class="detail"><span class="label">Timeline:</span><span class="value">{problem_summary.get("timeline")}</span></div>' if problem_summary.get('timeline') else ''}

            {f'<div class="detail"><span class="label">Conversation Summary:</span><p class="value">{conversation_summary}</p></div>' if conversation_summary else ''}

            <p style="margin-top: 20px;">Please respond to the client as soon as possible. They are expecting your help.</p>

            <div class="footer">
                <p>This notification was sent via CyberSecAgent - Cybersecurity Expert Matching Platform</p>
            </div>
        </div>
    </div>
</body>
</html>
"""

        return self.send_email(expert_email, subject, html_content)

    def send_client_confirmation(
        self,
        client_email: str,
        expert_name: str,
        expert_title: str
    ) -> dict:
        """
        Send a confirmation email to the client.

        Args:
            client_email: Client's email address
            expert_name: Expert's name
            expert_title: Expert's title

        Returns:
            Dict with status
        """

        subject = "✅ Expert Connected - CyberSecAgent"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #34a853; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .content {{ background-color: #f8f9fa; padding: 20px; border-radius: 0 0 8px 8px; }}
        .expert-info {{ background-color: white; padding: 15px; border-radius: 8px; margin: 15px 0; }}
        .tips {{ background-color: #fff3cd; padding: 15px; border-radius: 8px; margin: 15px 0; }}
        .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✅ Expert Connected!</h1>
        </div>
        <div class="content">
            <p>Great news! You've been connected with a cybersecurity expert.</p>

            <div class="expert-info">
                <h3>{expert_name}</h3>
                <p>{expert_title}</p>
                <p>They have received a summary of your situation and will reach out shortly.</p>
            </div>

            <div class="tips">
                <h4>⚠️ While you wait - Security Tips:</h4>
                <ul>
                    <li>Don't click on any suspicious links</li>
                    <li>Don't share passwords or OTPs with anyone</li>
                    <li>Document any unusual activity you notice</li>
                    <li>Avoid making major changes until the expert advises</li>
                </ul>
            </div>

            <p>{expert_name} will guide you through the next steps to resolve your issue.</p>

            <div class="footer">
                <p>This email was sent via CyberSecAgent - Cybersecurity Expert Matching Platform</p>
            </div>
        </div>
    </div>
</body>
</html>
"""

        return self.send_email(client_email, subject, html_content)


# Singleton instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create email service instance"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
