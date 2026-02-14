# TORQ Console - Railway Production Dockerfile
# Multi-stage build for optimal image size and security

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONDISABLEBYTECODE=1
ENV PIPNOcachedir=1
ENV PIPDISABLEPIPVERSIONCHECK=1
ENV TORQCONSOLEPRODUCTION=true
ENV TORQDISABLELOCALLM=true
ENV TORQDISABLEGPU=true

# Set working directory
WORKDIR /app

# Install system dependencies  
RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements-railway.txt .

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements-railway.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1001 torq && chown -R torq:torq /app
USER torq

# Expose port
EXPOSE 8080

# Run application
CMD ["python", "-m", "torq_console.ui.railway_main", "--host", "0.0.0.0", "--port", "8080"]
