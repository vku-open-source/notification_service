"""
Copyright (c) VKU.OneLove.
This source code is licensed under the Apache-2.0 license found in the
LICENSE file in the root directory of this source tree.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from celery import Celery
import os
from vonage import Auth, Vonage
from vonage_sms import SmsMessage, SmsResponse
import logging
from helper import normalize_phone_number
from os import environ
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# SMTP Configuration
SMTP_HOST = environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(environ.get("SMTP_PORT", 587))
SMTP_USERNAME = environ.get("SMTP_USERNAME")
SMTP_PASSWORD = environ.get("SMTP_PASSWORD")

# Vonage Configuration
VONAGE_API_KEY = environ.get("VONAGE_API_KEY")
VONAGE_API_SECRET = environ.get("VONAGE_API_SECRET")
VONAGE_FROM_NUMBER = environ.get("VONAGE_FROM_NUMBER")

if not all([VONAGE_API_KEY, VONAGE_API_SECRET]):
    logger.error("Vonage credentials are not properly configured!")

EMAIL_TEMPLATE = EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #ff0000 ; }}
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

# Celery Configuration
CELERY_BROKER_URL = environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
celery = Celery('tasks', broker=CELERY_BROKER_URL)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def send_email_with_retry(smtp_connection, msg):
    smtp_connection.send_message(msg)

def prepare_email_message(user, title, content):
    msg = MIMEMultipart()
    msg['From'] = SMTP_USERNAME
    msg['To'] = user['email']
    msg['Subject'] = title
    
    html_content = EMAIL_TEMPLATE.format(
        title=title,
        recipient_name=user.get('email', 'Valued Customer'),
        content=content
    )
    
    msg.attach(MIMEText(html_content, 'html'))
    return msg

@celery.task
def send_bulk_email_task(recipients, title, content):
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
            
            for recipient in recipients:
                if recipient.get("email"):
                    msg = prepare_email_message(recipient, title, content)
                    send_email_with_retry(smtp, msg)
                    
    except Exception as e:
        logger.error(f"Email sending failed: {str(e)}")
        raise

@celery.task(bind=True, max_retries=3)
def send_bulk_sms_task(self, recipients, title, content):
    try:
        client = Vonage(Auth(
            api_key=VONAGE_API_KEY,
            api_secret=VONAGE_API_SECRET
        ))

        for recipient in recipients:
            phone = recipient.get('phone')
            if not phone:
                continue
                
            normalized_phone = normalize_phone_number(phone)

            try:
                message = SmsMessage(
                    to=normalized_phone,
                    from_=VONAGE_FROM_NUMBER,
                    text=SMS_TEMPLATE.format(title=title, content=content)
                )

                response: SmsResponse = client.sms.send(message)
                
                if response.messages[0].status == "0":
                    logger.info(f"SMS sent successfully to {normalized_phone}")
                else:
                    logger.error(f"Failed to send SMS to {normalized_phone}: {response.messages[0].error_text}")
                    
            except Exception as ve:
                logger.error(f"Error sending SMS to {normalized_phone}: {str(ve)}")
                raise self.retry(exc=ve, countdown=60)

    except Exception as e:
        logger.error(f"Failed to send bulk SMS: {str(e)}")
        raise self.retry(exc=e, countdown=300)


