# EarthTrend backend image
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System packages required by scipy / reportlab wheels are already bundled in
# the manylinux wheels, so only minimal tooling is needed.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app ./app
COPY pytest.ini ./

ENV DATABASE_URL=sqlite:////data/earthtrend.db \
    CACHE_DIR=/data/cache \
    DEMO_DATA_DIR=/data/samples \
    HOST=0.0.0.0 \
    PORT=8000

RUN mkdir -p /data/cache /data/samples

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
