FROM python:3.12-slim

# Install git (required for cloning repos)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Install uv (modern python package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files first for caching
COPY pyproject.toml .
COPY uv.lock .

# Install dependencies using uv
RUN uv sync --frozen

# Copy the rest of the application code
COPY . .

# Expose the default FastAPI port
EXPOSE 8000

# Start the application. If GCP_CREDENTIALS_JSON is provided, write it to a file for ADC.
CMD sh -c 'if [ -n "$GCP_CREDENTIALS_JSON" ]; then echo "$GCP_CREDENTIALS_JSON" > /app/gcp.json && export GOOGLE_APPLICATION_CREDENTIALS=/app/gcp.json; fi && exec uv run uvicorn app.main:app --host 0.0.0.0 --port "${APP_PORT:-8000}"'
