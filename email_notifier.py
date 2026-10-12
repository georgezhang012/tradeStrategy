"""
Email Notification Service for Portfolio Alerts
================================================
Sends automated HTML and plain-text email alerts when risk triggers occur:
- Stop-loss breaches
- Take-profit achievements
- 5% Portfolio weight drift rebalancing triggers

Environment Variables (Set locally or in GitHub Repository Secrets):
- SMTP_HOST: default 'smtp.gmail.com'
- SMTP_PORT: default 587
- SMTP_USER: your sender email (e.g., yourname@gmail.com)
- SMTP_PASSWORD: your Gmail App Password (16-character token)
- ALERT_RECIPIENT: email address to receive alerts
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional


class EmailAlertService:
    """Manages email dispatch for portfolio alerts."""

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_pass: Optional[str] = None,
        recipient: Optional[str] = None
    ):
        self.smtp_host = smtp_host or os.environ.get("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(smtp_port or os.environ.get("SMTP_PORT", 587))
        self.smtp_user = smtp_user or os.environ.get("SMTP_USER")
        self.smtp_pass = smtp_pass or os.environ.get("SMTP_PASSWORD")
        self.recipient = recipient or os.environ.get("ALERT_RECIPIENT", self.smtp_user)

    def is_configured(self) -> bool:
        """Returns True if sender credentials and recipient are set."""
        return bool(self.smtp_user and self.smtp_pass and self.recipient)

    def send_alert_email(
        self,
        subject: str,
        report_text: str,
        alerts: list
    ) -> Dict[str, Any]:
        """Sends an HTML + Plain Text alert email to the recipient."""
        if not self.is_configured():
            return {
                "sent": False,
                "reason": "Email service not configured. Set SMTP_USER, SMTP_PASSWORD, and ALERT_RECIPIENT."
            }

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Trading Strategy Monitor <{self.smtp_user}>"
        msg["To"] = self.recipient

        # Plain-text version
        part1 = MIMEText(report_text, "plain")
        msg.attach(part1)

        # HTML formatted version
        html_alerts = "".join([
            f"<li style='margin-bottom: 10px;'><strong>[{a.get('severity', 'INFO')}] {a.get('type')}:</strong><br/>"
            f"{a.get('message')}<br/>"
            f"<span style='color: #d9534f;'><strong>Action:</strong> {a.get('action')}</span></li>"
            for a in alerts
        ])

        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 20px;">
              <h2 style="color: #c92a2a; margin-top: 0;">⚠️ Portfolio Risk Alert — Action Required</h2>
              <p>The automated portfolio monitor detected operational triggers requiring your attention:</p>
              <ul>
                {html_alerts}
              </ul>
              <hr style="border: 0; border-top: 1px solid #ddd; margin: 20px 0;"/>
              <h3>Full Portfolio Status:</h3>
              <pre style="background: #2b2b2b; color: #f8f8f2; padding: 12px; border-radius: 4px; overflow-x: auto;">
{report_text}
              </pre>
            </div>
          </body>
        </html>
        """
        part2 = MIMEText(html_body, "html")
        msg.attach(part2)

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.sendmail(self.smtp_user, self.recipient, msg.as_string())
            return {"sent": True, "recipient": self.recipient}
        except Exception as e:
            return {"sent": False, "error": str(e)}

