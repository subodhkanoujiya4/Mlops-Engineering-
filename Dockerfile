FROM python:3.9-slim

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and required input files
COPY run.py .
COPY config.yaml .
COPY data.csv .

# Default one-command run: produces metrics.json + run.log inside /app
# and prints the final metrics JSON to stdout.
CMD ["python", "run.py", "--input", "data.csv", "--config", "config.yaml", "--output", "metrics.json", "--log-file", "run.log"]
