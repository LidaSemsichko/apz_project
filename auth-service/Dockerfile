FROM python:3.11-slim

WORKDIR /app

COPY auth-service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY common ./common
COPY auth-service/app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
