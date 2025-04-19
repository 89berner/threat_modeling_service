FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for libmagic
RUN apt-get update && apt-get install -y \
    libmagic1 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV FLASK_APP=app.py

# Expose port
EXPOSE 5000

# Run the application
CMD ["flask", "run", "--host=0.0.0.0", "--port", "5000"]