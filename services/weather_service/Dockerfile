FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 8011
CMD ["uvicorn", "services.weather_service.main:app", "--host", "0.0.0.0", "--port", "8011"]
