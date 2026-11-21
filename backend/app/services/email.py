import smtplib
from email.message import EmailMessage
from ..config import settings

def send_email(to: str, subject: str, body: str) -> bool:
    if not settings.smtp_host or not settings.smtp_from: return False
    msg = EmailMessage(); msg["From"] = settings.smtp_from; msg["To"] = to; msg["Subject"] = subject; msg.set_content(body)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
        if settings.smtp_use_tls: server.starttls()
        if settings.smtp_username: server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(msg)
    return True
