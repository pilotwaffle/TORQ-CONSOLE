# TORQ Console - Railway Production Dockerfile

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

# Run application with Railway PORT
CMD uvicorn torq_console.ui.railway_app:app --host 0.0.0.0 --port ${PORT}
