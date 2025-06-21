FROM python:3.11-slim

# Install Chrome and Chromedriver
RUN apt-get update && apt-get install -y \
    chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 5000

# Start the application
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:5000", "--workers", "1", "--timeout", "120"]
