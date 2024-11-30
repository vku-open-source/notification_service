from tasks import send_bulk_sms_task

users = [
    {"phone": "84522944603", "name": "Test User"}
]

# Gọi task bất đồng bộ
result = send_bulk_sms_task(users, "Alert", "This is a test message. Please ignore.")

