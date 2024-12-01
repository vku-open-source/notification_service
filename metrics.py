from prometheus_client import Counter, Histogram
import time

notification_counter = Counter('notifications_total', 'Total notifications sent', ['type', 'channel'])
notification_duration = Histogram('notification_duration_seconds', 'Time spent processing notifications')


