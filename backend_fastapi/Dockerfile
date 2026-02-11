# backend_fastapi/Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    gcc \
    curl \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# --- CHANGE START ---
# 1. Install Django dependencies (needed for ORM to work)
COPY backend_core/requirements.txt ./requirements_django.txt
RUN pip install --no-cache-dir -r requirements_django.txt

# 2. Install FastAPI dependencies
COPY backend_fastapi/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# --- CHANGE END ---

# Create directories
RUN mkdir -p src
RUN mkdir -p backend_core

# Copy source code
COPY backend_fastapi/src/ ./src/
COPY backend_core/ ./backend_core/

# Set PYTHONPATH
ENV PYTHONPATH="${PYTHONPATH}:/app/src:/app/backend_core/src"

EXPOSE 8001

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]