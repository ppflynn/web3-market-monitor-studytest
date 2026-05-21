FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY coin_collector.py config.py ./

CMD ["python", "coin_collector.py"]
