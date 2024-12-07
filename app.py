"""
Copyright (c) VKU.OneLove.
This source code is licensed under the Apache-2.0 license found in the
LICENSE file in the root directory of this source tree.
"""

from flask import Flask, request, jsonify
from prometheus_client import generate_latest
from celery_app import make_celery
from tasks import send_bulk_email_task, send_bulk_sms_task
import requests
from os import environ
from dotenv import load_dotenv
from validators import NotificationSchema
import logging
from logging.handlers import RotatingFileHandler
import os
import redis
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime
# Load environment variables
load_dotenv()

# Flask app
app = Flask(__name__)

# Celery configuration
app.config.update(
    CELERY_BROKER_URL=environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    CELERY_RESULT_BACKEND=environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

celery = make_celery(app)

# Constants from environment
# USER_API_ENDPOINT = environ.get('USER_API_ENDPOINT', 'http://localhost:1337/api/users')

# Setup logging
if not os.path.exists('logs'):
    os.makedirs('logs')
file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

CORS(app, resources={
    r"/api/*": {"origins": ["http://allowed-domain.com"]}
})

@app.route('/api/notifications', methods=['POST'])
@limiter.limit("10 per minute")
def handle_notification():
    # Validate request data
    schema = NotificationSchema()
    data = request.get_json()
    errors = schema.validate(data)
    if errors:
        app.logger.error(f"Validation errors: {errors}")
        return jsonify({"errors": errors}), 400

    app.logger.info(f"Received payload: {data}")

    # Tách recipients theo kênh thông báo
    email_recipients = []
    sms_recipients = []
    
    for recipient in data['recipients']:
        channels = recipient['notification_channels']
        if channels['email']:
            email_recipients.append(recipient)
        if channels['sms']:
            sms_recipients.append(recipient)

    # Gửi email notifications
    if email_recipients:
        send_bulk_email_task.delay(email_recipients, data['title'], data['content'])
        app.logger.info(f"Enqueued email task for {len(email_recipients)} recipients")

    # Gửi SMS notifications
    if sms_recipients:
        send_bulk_sms_task.delay(sms_recipients, data['title'], data['content'])
        app.logger.info(f"Enqueued SMS task for {len(sms_recipients)} recipients")

    return jsonify({
        "message": "Notification tasks enqueued successfully!",
        "stats": {
            "email_recipients": len(email_recipients),
            "sms_recipients": len(sms_recipients)
        }
    }), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Nhận dữ liệu JSON từ yêu cầu
        data = request.get_json()
        
        # In ra dữ liệu để kiểm tra
        print("Received data:", data)
        
        # Xử lý dữ liệu JSON nếu cần 
        
        # Trả về phản hồi thành công
        return jsonify({"status": "success", "message": "Data received"}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "failed", "error": str(e)}), 400

# Thêm error handler
@app.errorhandler(Exception)
def handle_error(error):
    app.logger.error(f'Unhandled exception: {str(error)}')
    return jsonify({
        'error': 'Internal server error',
        'message': str(error)
    }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

def check_redis_connection():
    try:
        redis_client = redis.from_url(app.config['CELERY_BROKER_URL'])
        redis_client.ping()
        return 'ok'
    except Exception as e:
        return f'error: {str(e)}'

def check_celery_status():
    try:
        i = celery.control.inspect()
        if i.active():
            return 'ok'
        return 'no workers available'
    except Exception as e:
        return f'error: {str(e)}'

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

@app.route('/metrics')
def metrics():
    return generate_latest() 

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3000)


