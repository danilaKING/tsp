FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

EXPOSE 5000

# Seed DB then start server
CMD ["sh", "-c", "python seed_questions.py && uvicorn main:app --host 0.0.0.0 --port 5000"]
