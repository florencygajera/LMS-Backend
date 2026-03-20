FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 8010
CMD ["uvicorn", "services.ml_service.main:app", "--host", "0.0.0.0", "--port", "8010"]
