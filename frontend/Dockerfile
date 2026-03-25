FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY frontend/requirements.txt /app/frontend/requirements.txt
RUN pip install --no-cache-dir -r /app/frontend/requirements.txt

COPY frontend /app/frontend

ENV API_URL=http://backend:5000

EXPOSE 8501

CMD ["streamlit", "run", "/app/frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
