# MLOps Task 0 – Rolling Mean Signal Batch Pipeline

A reproducible MLOps-style batch processing pipeline built in Python as part of the ML Engineering Internship Technical Assessment.

## Features

- Load configuration from `config.yaml`
- Read OHLCV data from `data.csv`
- Validate configuration and dataset
- Compute rolling mean using configurable window size
- Generate binary trading signal
- Write structured metrics to `metrics.json`
- Generate detailed execution logs in `run.log`
- Dockerized for reproducible execution
- Deterministic results using configurable random seed

---

## Project Structure

```
.
├── run.py
├── config.yaml
├── data.csv
├── requirements.txt
├── Dockerfile
├── metrics.json
├── run.log
└── README.md
```

---

## Requirements

- Python 3.9+
- pip

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Run Locally

Execute the project using:

```bash
python run.py \
--input data.csv \
--config config.yaml \
--output metrics.json \
--log-file run.log
```

No file paths are hardcoded. All input and output locations are provided through CLI arguments.

---

## Docker

### Build Image

```bash
docker build -t mlops-task .
```

### Run Container

```bash
docker run --rm mlops-task
```

The Docker image:

- Includes `data.csv` and `config.yaml`
- Executes the pipeline automatically
- Generates `metrics.json`
- Generates `run.log`
- Prints the final metrics JSON to stdout

---

## Configuration

Example `config.yaml`

```yaml
seed: 42
window: 5
version: "v1"
```

---

## Processing Pipeline

1. Load configuration
2. Validate required configuration fields
3. Load dataset
4. Validate CSV structure
5. Compute rolling mean on the `close` column
6. Generate binary signal

```
signal = 1 if close > rolling_mean
signal = 0 otherwise
```

7. Compute execution metrics
8. Save metrics
9. Write execution logs

---

## Example Success Output

```json
{
  "version": "v1",
  "rows_processed": 10000,
  "metric": "signal_rate",
  "value": 0.4983,
  "latency_ms": 14,
  "seed": 42,
  "status": "success"
}
```

---

## Error Output

```json
{
  "version": "v1",
  "status": "error",
  "error_message": "Missing required column: close"
}
```

---

## Validation

The application validates:

- Configuration file exists
- Required config fields
- Input CSV exists
- Valid CSV format
- Dataset is not empty
- Required `close` column exists

Errors are:

- Logged to `run.log`
- Written to `metrics.json`
- Returned with a non-zero exit code

---

## Reproducibility

Deterministic execution is ensured using:

- Configurable random seed
- YAML-based configuration
- No hardcoded file paths
- Consistent rolling mean computation

---

## Logging

The application logs:

- Job start
- Configuration loading
- Dataset validation
- Processing steps
- Metrics summary
- Job completion
- Exceptions (if any)

---

## Tech Stack

- Python
- Pandas
- NumPy
- PyYAML
- Logging
- Docker

---

## Author

**Subodh Kanoujiya**

Computer Science (Artificial Intelligence) Engineer

Interested in:

- Machine Learning
- MLOps
- Generative AI
- AI Automation
