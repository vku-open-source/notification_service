"""
Copyright (c) VKU.OneLove.
This source code is licensed under the Apache-2.0 license found in the
LICENSE file in the root directory of this source tree.
"""

from prometheus_client import Counter, Histogram
import time

notification_counter = Counter('notifications_total', 'Total notifications sent', ['type', 'channel'])
notification_duration = Histogram('notification_duration_seconds', 'Time spent processing notifications')


