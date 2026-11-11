# OpenGen Multi-Modal Generation Framework Dockerfile
FROM python:3.11-slim

# Set non-interactive debian frontend
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install system dependencies (LibreOffice for PDF rendering, tesseract for OCR, libgl for opencv/PIL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libreoffice-writer \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project specification & install dependencies
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Copy source tree
COPY src/ /app/src/
COPY app/ /app/app/

# Create runtime directories
RUN mkdir -p /app/data/uploads /app/data/outputs /app/cache

EXPOSE 8000

# Default command runs the REST API and MCP stdio
CMD ["uvicorn", "opengen.api:app", "--host", "0.0.0.0", "--port", "8000"]
