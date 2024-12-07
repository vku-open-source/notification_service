# LCDP Notification Service

A scalable notification service built with Flask and Celery for handling bulk email and SMS notifications.

## Features

- Bulk email notifications using SMTP
- SMS notifications via Vonage API

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Redis
- SMTP server access (e.g., Gmail)
- Vonage API credentials

## Installation

### Using Docker (Recommended)

1. Clone the repository:

```bash
git clone https://github.com/vku-open-source/notification_service.git
cd lcdp_service
```

2. Copy the example environment file and configure your variables:

```bash
cp .env.example .env
```

3. Build and start the services:

```bash
docker-compose up --build
```

### Local Development

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment variables:

```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Start Redis server (required for Celery)

5. Start Celery worker:

```bash
celery -A tasks worker --pool=solo --loglevel=info
```

6. Run the Flask application:

```bash
python app.py
```

## API Endpoints

### Send Batch Notifications

```
POST /api/notifications
```

Request body:

```json
{
  "type": "emergency_alert",
  "title": "Alert Title",
  "content": "Alert content",
  "recipients": [
    {
      "email": "user1@example.com",
      "phone": "84901234567",
      "notification_channels": {
        "email": true,
        "sms": true
      }
    },
    {
      "email": "user2@example.com",
      "phone": "84907654321",
      "notification_channels": {
        "email": true,
        "sms": false
      }
    }
  ]
}
```

Response:

```json
{
  "message": "Notification tasks enqueued successfully!",
  "stats": {
    "email_recipients": 2,
    "sms_recipients": 1
  }
}
```

## Validation Rules

- `type`: Must be "emergency_alert"
- `title`: Required, 1-200 characters
- `content`: Required, 1-1000 characters
- `recipients`: Array of recipient objects with:
  - `email`: Valid email address
  - `phone`: Phone number (will be normalized to international format)
  - `notification_channels`: Configure which channels to use per recipient
    - `email`: boolean
    - `sms`: boolean

## Environment Variables

Key environment variables that need to be configured in `.env`:

```
# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=1

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Vonage Configuration
VONAGE_API_KEY=your-vonage-key
VONAGE_API_SECRET=your-vonage-secret
VONAGE_FROM_NUMBER=your-vonage-number


```

## Project Structure

```
lcdp_service/
├── app.py              # Main Flask application
├── tasks.py            # Celery tasks
├── celery_app.py       # Celery configuration
├── validators.py       # Request validation schemas
├── helper.py           # Utility functions
├── metrics.py          # Prometheus metrics
├── logs/              # Application logs
├── Dockerfile         # Docker configuration
└── docker-compose.yml # Docker Compose configuration
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the terms of the [Apache V2.0](LICENSE)
