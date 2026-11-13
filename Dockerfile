FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    SERVICE_MODULE=app.sc01_viajes.main:app \
    SERVICE_PORT=8081

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --upgrade pip && python -m pip install -r requirements.txt

COPY . .
RUN mkdir -p /app/data /app/storage/pasajes

CMD ["sh", "-c", "exec uvicorn ${SERVICE_MODULE} --host 0.0.0.0 --port ${SERVICE_PORT}"]
