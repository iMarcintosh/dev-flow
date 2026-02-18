FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Add user to docker group for socket access (GID 998 on host)
# This allows code execution in Docker containers
RUN groupadd -g 998 docker || true && \
    usermod -aG docker root || true

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
