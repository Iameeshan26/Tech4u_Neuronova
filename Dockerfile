FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for geopandas and other libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the API port
EXPOSE 8000

# Default command (will be overridden in docker-compose for the worker)
CMD ["python", "app/api.py"]
