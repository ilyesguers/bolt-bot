FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway provides PORT env
ENV PYTHONUNBUFFERED=1
ENV EFOOTBALL_ONLY=true
ENV LOG_LIMIT=500

EXPOSE 8080

CMD ["python", "-m", "src.main"]
