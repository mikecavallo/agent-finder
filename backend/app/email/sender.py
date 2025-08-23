import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..config import settings

async def send_email(to_email: str, subject: str, body: str):
    sender_email = settings.sender_email
    sender_password = settings.smtp_password
    smtp_server = settings.smtp_server
    smtp_port = settings.smtp_port

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = to_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Secure the connection
            server.login(settings.smtp_username, sender_password)
            server.sendmail(sender_email, to_email, message.as_string())
        print(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
        return False
