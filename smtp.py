import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class SMTP:
    def __init__(self, smtp_url, smtp_port, smtp_email, smtp_password):
        """Initialize using a smtp_url, smtp_port, smtp_email, and smtp_password"""
        assert len(smtp_url) > 0
        assert len(smtp_port) > 0 and smtp_port.isnumeric()
        assert len(smtp_email) > 0
        assert len(smtp_password) > 0

        self.smtp_url = smtp_url
        self.smtp_port = int(smtp_port)
        self.smtp_email = smtp_email
        self.smtp_password = smtp_password

    def send_email(self, from_email, to_email, subject, body):
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = from_email
        message["To"] = to_email

        message.attach(MIMEText(body, "html"))

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.smtp_url, self.smtp_port, context=context) as server:
            server.login(self.smtp_email, self.smtp_password)
            server.sendmail(from_email, to_email, message.as_string())
