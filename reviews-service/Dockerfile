FROM python:3.11-slim

WORKDIR /app

COPY reviews-service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY common ./common
COPY reviews-service/app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
