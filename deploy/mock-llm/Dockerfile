FROM python:3.13-slim

RUN pip install --no-cache-dir fastapi==0.115.6 uvicorn==0.34.0
WORKDIR /app
COPY deploy/mock-llm/main.py ./main.py
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
