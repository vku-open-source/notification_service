from flask import Flask, request, jsonify
from celery_app import make_celery
from tasks import send_bulk_email_task,send_bulk_sms_task
import requests
import os

# Flask app
app = Flask(__name__)

# Celery configuration
app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379/0',
    CELERY_RESULT_BACKEND='redis://localhost:6379/0'
)

celery = make_celery(app)

# Constants
USER_API_ENDPOINT = "http://localhost:1337/api/users"

@app.route('/api/notifications', methods=['POST'])
def handle_notification():
    data = request.get_json()
    print(f"Received payload: {data}")

    # Kiểm tra type
    if data.get("type") != "emergency_alert":
        return jsonify({"message": "No notification sent. Type is not 'emergency_alert'"}), 200

    # Kiểm tra notification channels
    notification_channels = data.get("notification_channels", {"email": True, "sms": False})
    
    # Fetch user data
    try:
        users = requests.get(USER_API_ENDPOINT).json()
    except Exception as e:
        return jsonify({"error": f"Failed to fetch users: {str(e)}"}), 500

    # Chia nhỏ dữ liệu nếu cần 
    batch_size = 50
    user_batches = [users[i:i + batch_size] for i in range(0, len(users), batch_size)]

    # Gửi thông báo email và SMS theo batch và theo kênh được chọn
    for batch in user_batches:
        if notification_channels.get("email"):
            send_bulk_email_task.delay(batch, data["title"], data["content"])
        if notification_channels.get("sms"):
            send_bulk_sms_task.delay(batch, data["title"], data["content"])

    return jsonify({"message": "Notification tasks enqueued successfully!"}), 200

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

if __name__ == '__main__':
    app.run(host="localhost", port=3000)


