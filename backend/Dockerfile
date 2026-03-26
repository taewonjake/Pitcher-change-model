FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.prod.txt /app/backend/requirements.prod.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.prod.txt \
    && pip install --no-cache-dir gunicorn

COPY backend /app/backend

EXPOSE 5000

CMD ["gunicorn", "-w", "2", "-k", "gthread", "-b", "0.0.0.0:5000", "backend.api.app:app", "--timeout", "120"]
