FROM python:3.12-slim

# ffmpeg for editing, Noto CJK for burned Chinese subtitles / AIGC badge
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY showrunner ./showrunner
COPY scripts ./scripts

# Persistent state lives in volumes: runs/ (productions) and library/ (reusable cast)
VOLUME ["/app/runs", "/app/library", "/app/logs"]

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/healthz')" || exit 1

# Single process by design: gates + job queue are in-memory (do NOT add --workers)
CMD ["uvicorn", "showrunner.server:app", "--host", "0.0.0.0", "--port", "8000"]
