import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from celery import Celery
import os
from vonage import Auth, Vonage
from vonage_sms import SmsMessage, SmsResponse
import logging
from helper import normalize_phone_number
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))  
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

VONAGE_API_KEY = os.getenv("VONAGE_API_KEY")
VONAGE_API_SECRET = os.getenv("VONAGE_API_SECRET")
VONAGE_FROM_NUMBER = os.getenv("VONAGE_FROM_NUMBER")

if not all([VONAGE_API_KEY, VONAGE_API_SECRET]):
    logger.error("Vonage credentials are not properly configured!")

EMAIL_TEMPLATE = EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: ##ff0000 ; }}
        .header {{ background-color: #4CAF50; color: white; padding: 10px; text-align: center; }}
        .content {{ margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="header">
        {title}
    </div>
    <div class="content">
        <p>Dear {recipient_name},</p>
        <p>{content}</p>
        <p>The Team</p>
    </div>
</body>
</html>
"""

SMS_TEMPLATE = "{title}: {content}"

celery = Celery('tasks', broker='redis://localhost:6379/0')

@celery.task
def send_bulk_email_task(users, title, content):
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USERNAME, SMTP_PASSWORD)

            for user in users:
                email = user.get("email")
                recipient_name = user.get("username", "Valued User")
                if email:
                    # Prepare email
                    msg = MIMEMultipart("alternative")
                    msg["Subject"] = title
                    msg["From"] = SMTP_USERNAME
                    msg["To"] = email
                    html_content = EMAIL_TEMPLATE.format(
                        title=title, content=content, recipient_name=recipient_name
                    )
                    msg.attach(MIMEText(html_content, "html"))

                    # Send email
                    smtp.sendmail(SMTP_USERNAME, email, msg.as_string())
                    print(f"Email sent to {email}")
    except Exception as e:
        print(f"Failed to send bulk emails: {e}")

@celery.task(bind=True, max_retries=3)
def send_bulk_sms_task(self, users, title, content):
    try:
        client = Vonage(Auth(
            api_key=VONAGE_API_KEY,
            api_secret=VONAGE_API_SECRET
        ))

        for user in users:
            phone = user.get('phone')
            if not phone:
                continue
                
            # Sử dụng hàm từ helper.py
            normalized_phone = normalize_phone_number(phone)

            try:
                message = SmsMessage(
                    to=normalized_phone,
                    from_=VONAGE_FROM_NUMBER,
                    text=SMS_TEMPLATE.format(title=title, content=content)
                )

                response: SmsResponse = client.sms.send(message)
                
                if response.messages[0].status == "0":
                    print(f"SMS sent successfully to {normalized_phone}")
                else:
                    print(f"Failed to send SMS to {normalized_phone}: {response.messages[0].error_text}")
                    
            except Exception as ve:
                print(f"Error sending SMS to {normalized_phone}: {str(ve)}")
                raise self.retry(exc=ve, countdown=60)

    except Exception as e:
        print(f"Failed to send bulk SMS: {str(e)}")
        raise self.retry(exc=e, countdown=300)


