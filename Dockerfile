FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY templates/ templates/

RUN mkdir -p /data

ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV DATABASE_PATH=/data/complaints.db

EXPOSE 8080

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} app:app"]