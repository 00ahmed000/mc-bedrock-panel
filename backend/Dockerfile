FROM python:3.12-slim

# This container is mounted onto /var/run/docker.sock (see docker-compose.yml)
# so it can manage the minecraft and sftp containers. That mount is already
# root-equivalent access to the host regardless of which user this process
# runs as, and the ownership-repair logic in app/fsutil.py needs CAP_CHOWN
# to arbitrary UIDs — so it intentionally runs as root rather than pretend
# a USER directive here would meaningfully sandbox it. Keep this service
# reachable only through nginx + the JWT auth layer, never exposed directly.

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health', timeout=3)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
