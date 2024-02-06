from dataclasses import dataclass
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from uuid import uuid4


@dataclass
class Email:
    from_name: str
    from_email: str
    to_name: str
    to_email: str
    subject: str
    body: str


@dataclass
class SMTPOptions:
    host: str
    port: int
    username: str
    password: str


class SMTP:
    smtp_options: SMTPOptions

    def __init__(self, smtp_options: SMTPOptions):
        self.smtp_options = smtp_options

    def send_email(self, email: Email):
        message = MIMEMultipart("alternative")
        message["Subject"] = email.subject
        message["From"] = f"{email.from_name} <{email.from_email}>"

        if (len(email.to_name) > 0):
            message["To"] = f"{email.to_name} <{email.to_email}>"
        else:
            message["To"] = email.to_email

        try:
            message_id = f"<{uuid4()}@{email.from_email.split('@')[1]}>"
        except IndexError:
            # this should never happen with a valid email address,
            # but we let the SMTP server handle it instead of raising it here
            message_id = f"<{uuid4()}@{email.from_email}>"

        message["Message-ID"] = message_id
        message["MIME-Version"] = "1.0"

        message.attach(MIMEText(email.body, "html"))

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.smtp_options.host, self.smtp_options.port, context=context) as server:
            server.login(self.smtp_options.username,
                         self.smtp_options.password)
            server.sendmail(email.from_email, email.to_email,
                            message.as_string())
