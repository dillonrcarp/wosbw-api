# Dockerfile
FROM python:3.11-slim

# Install Chrome and Chromedriver
RUN apt-get update && apt-get install -y \
    chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Render will route)
EXPOSE 5000

# Start the app with Gunicorn
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:5000", "--workers", "1", "--timeout", "120"]
