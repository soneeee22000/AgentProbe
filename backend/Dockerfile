FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy source code
COPY src/ ./src/
COPY main.py ./

# Create workspace directory for read_file tool
RUN mkdir -p /app/workspace

EXPOSE 8000

CMD ["uvicorn", "agentprobe.infrastructure.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
