# Use minimal Python base image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install dependencies first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV FLASK_APP=src.app
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=production

# Expose the default Flask port
EXPOSE 5000

# Start with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "src.app:app"]

