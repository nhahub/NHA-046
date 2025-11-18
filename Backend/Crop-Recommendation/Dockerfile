FROM python:3.9-slim

WORKDIR /app

COPY requirements_crop.txt .
RUN pip install --no-cache-dir -r requirements_crop.txt

COPY . .

CMD ["gunicorn", "app_crop:app", "--bind", "0.0.0.0:7860", "--timeout", "120"]
