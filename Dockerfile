FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libxml2 \
    libxslt1.1 \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# sentence-transformers removed due to 2GB memory limit on Zeabur. Model loads at runtime if available.

COPY backend/ backend/
COPY frontend/ frontend/
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENV PYTHONPATH=/app/backend
ENV PORT=8080
ENV DATA_DIR=/data

EXPOSE 8080

ENTRYPOINT ["/docker-entrypoint.sh"]
