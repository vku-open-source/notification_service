#  Copyright (c) VKU.OneLove.
#  This source code is licensed under the Apache-2.0 license found in the
#  LICENSE file in the root directory of this source tree.

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 3000

# Command to run the application
CMD ["python", "app.py"] 