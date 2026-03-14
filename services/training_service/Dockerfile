FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 8006
CMD ["uvicorn", "services.training_service.main:app", "--host", "0.0.0.0", "--port", "8006"]
