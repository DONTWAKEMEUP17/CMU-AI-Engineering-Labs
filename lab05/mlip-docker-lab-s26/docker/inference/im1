FROM python:3.11-slim
WORKDIR /app
COPY docker/inference/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY docker/inference/server.py .
EXPOSE 8081
CMD ["python", "server.py"]
