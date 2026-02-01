FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy source code
COPY src/ ./src/

# Create reports directory
RUN mkdir -p reports

# Expose port
EXPOSE 8000

# Start Ollama and FastAPI
CMD ollama serve & sleep 5 && ollama pull llama3.2 && uv run uvicorn wealth_risk_profiler.main:app --host 0.0.0.0 --port 8000