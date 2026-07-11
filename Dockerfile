FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY *.py ./
RUN mkdir -p /app/data
EXPOSE 8000
# Zaufane proxy: uvicorn czyta zmienną FORWARDED_ALLOW_IPS (ustaw w docker-compose)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
