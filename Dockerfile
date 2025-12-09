
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential     && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./

ENV FLASK_ENV=production
ENV PORT=5000
EXPOSE 5000

CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:5000", "app:app"]
