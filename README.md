# MLOps Task 0 — Rolling-Mean Signal Batch Job

A minimal, reproducible MLOps-style batch job that:

- Loads config from YAML (`seed`, `window`, `version`)
- Reads OHLCV data from CSV
- Computes a rolling mean on `close`
- Generates a binary signal (`1` if `close > rolling_mean`, else `0`)
- Writes structured metrics (`metrics.json`) and detailed logs (`run.log`)
- Runs identically on the host or inside Docker

## Files

| File            | Purpose                                      |
|-----------------|-----------------------------------------------|
| `run.py`        | Main pipeline script                          |
| `config.yaml`   | Run configuration (seed, window, version)     |
| `data.csv`      | Sample OHLCV dataset (10,000 rows)            |
| `requirements.txt` | Python dependencies                       |
| `Dockerfile`    | Container build definition                    |
| `metrics.json`  | Sample output from a successful run           |
| `run.log`       | Sample log from a successful run              |

## Local run

Requires Python 3.9+.

```bash
pip install -r requirements.txt

python run.py \
  --input data.csv \
  --config config.yaml \
  --output metrics.json \
  --log-file run.log
```

The script has no hard-coded paths — all inputs/outputs are passed via CLI flags.

### Exit codes
- `0` — success (metrics written with `"status": "success"`)
- `1` — failure (metrics still written, with `"status": "error"` and an `error_message`)

## Docker

Build:

```bash
docker build -t mlops-task .
```

Run:

```bash
docker run --rm mlops-task
```

This bundles `data.csv` and `config.yaml` into the image, runs the pipeline with the
required CLI, writes `metrics.json` and `run.log` inside the container, and prints the
final metrics JSON to stdout. Exit code is `0` on success, non-zero on failure.

To copy the output files out of the container for inspection:

```bash
docker create --name mlops-tmp mlops-task
docker cp mlops-tmp:/app/metrics.json ./metrics.json
docker cp mlops-tmp:/app/run.log ./run.log
docker rm mlops-tmp
```

## Example `metrics.json` (success)

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

## Example `metrics.json` (error)

```json
{
  "version": "v1",
  "status": "error",
  "error_message": "Missing required column: 'close'"
}
```

## Design notes

- **Reproducibility**: `numpy.random.seed(seed)` is set from config before any processing.
  Rolling mean and signal logic are purely deterministic given the same input/config, so
  repeated runs on the same data produce identical `signal_rate` values.
- **Rolling mean edge case**: the first `window - 1` rows have no full window and are left
  as `NaN` for `rolling_mean`. Their `signal` is also left undefined (`NaN`) and excluded
  from the `signal_rate` calculation, so metrics only reflect rows with a fully defined signal.
- **Validation**: config is checked for required fields/types before use; the dataset is
  checked for existence, non-emptiness, valid CSV structure, and presence of the `close`
  column. Any failure is caught, logged with a full traceback, and reported in `metrics.json`
  with `status: "error"` (the job still exits non-zero and writes both output files).
- **Observability**: `run.log` captures job start, config validation, rows loaded,
  each processing step, the metrics summary, and job end/status — including exceptions.
