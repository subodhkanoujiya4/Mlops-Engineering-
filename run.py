#!/usr/bin/env python3
"""
run.py - Minimal MLOps-style batch job.

Loads config from YAML, reads OHLCV data, computes a rolling mean on
`close`, generates a binary trading signal, and writes structured
metrics (metrics.json) plus detailed logs (run.log).

Usage:
    python run.py --input data.csv --config config.yaml --output metrics.json --log-file run.log
"""

import argparse
import json
import logging
import os
import sys
import time

import numpy as np
import pandas as pd
import yaml

REQUIRED_CONFIG_FIELDS = ["seed", "window", "version"]
REQUIRED_COLUMN = "close"


def parse_args():
    parser = argparse.ArgumentParser(description="Rolling-mean signal batch job.")
    parser.add_argument("--input", required=True, help="Path to input OHLCV CSV file.")
    parser.add_argument("--config", required=True, help="Path to YAML config file.")
    parser.add_argument("--output", required=True, help="Path to write metrics JSON.")
    parser.add_argument("--log-file", required=True, help="Path to write run log.")
    return parser.parse_args()


def setup_logging(log_file):
    logger = logging.getLogger("mlops_task")
    logger.setLevel(logging.DEBUG)
    logger.handlers = []  # avoid duplicate handlers if re-invoked

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%dT%H:%M:%S%z"
    )

    file_handler = logging.FileHandler(log_file, mode="w")
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(fmt)
    logger.addHandler(stream_handler)

    return logger


def write_metrics(output_path, payload):
    with open(output_path, "w") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")


def load_and_validate_config(config_path, logger):
    if not os.path.isfile(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        try:
            config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")

    if not isinstance(config, dict):
        raise ValueError("Invalid config structure: expected a YAML mapping/object.")

    missing = [field for field in REQUIRED_CONFIG_FIELDS if field not in config]
    if missing:
        raise ValueError(f"Config missing required field(s): {missing}")

    if not isinstance(config["seed"], int):
        raise ValueError("Config field 'seed' must be an integer.")
    if not isinstance(config["window"], int) or config["window"] < 1:
        raise ValueError("Config field 'window' must be a positive integer.")
    if not isinstance(config["version"], str):
        raise ValueError("Config field 'version' must be a string.")

    logger.info(
        "Config loaded + validated: seed=%s, window=%s, version=%s",
        config["seed"], config["window"], config["version"],
    )
    return config


def load_and_validate_data(input_path, logger):
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if os.path.getsize(input_path) == 0:
        raise ValueError("Input file is empty.")

    try:
        df = pd.read_csv(input_path)
    except pd.errors.EmptyDataError:
        raise ValueError("Input file is empty or contains no columns.")
    except pd.errors.ParserError as e:
        raise ValueError(f"Invalid CSV format: {e}")

    if df.empty:
        raise ValueError("Input file contains no rows.")

    if REQUIRED_COLUMN not in df.columns:
        raise ValueError(f"Missing required column: '{REQUIRED_COLUMN}'")

    if not pd.api.types.is_numeric_dtype(df[REQUIRED_COLUMN]):
        try:
            df[REQUIRED_COLUMN] = pd.to_numeric(df[REQUIRED_COLUMN])
        except (ValueError, TypeError):
            raise ValueError(f"Column '{REQUIRED_COLUMN}' contains non-numeric values.")

    logger.info("Rows loaded: %d", len(df))
    return df


def compute_rolling_mean(df, window, logger):
    # First (window - 1) rows will be NaN; they are excluded from signal
    # computation below. This keeps behavior deterministic and explicit.
    df = df.copy()
    df["rolling_mean"] = df[REQUIRED_COLUMN].rolling(window=window, min_periods=window).mean()
    logger.info("Rolling mean computed with window=%d", window)
    return df


def compute_signal(df, logger):
    df = df.copy()
    df["signal"] = np.where(df[REQUIRED_COLUMN] > df["rolling_mean"], 1, 0)
    # Rows without a full rolling window have no defined signal; exclude them.
    df.loc[df["rolling_mean"].isna(), "signal"] = np.nan
    logger.info("Signal generation complete.")
    return df


def main():
    args = parse_args()
    logger = setup_logging(args.log_file)
    start_time = time.time()
    logger.info("Job start.")

    version = "v1"  # fallback if config fails to load before we know version
    try:
        config = load_and_validate_config(args.config, logger)
        version = config["version"]

        np.random.seed(config["seed"])
        logger.info("Random seed set to %d", config["seed"])

        df = load_and_validate_data(args.input, logger)
        df = compute_rolling_mean(df, config["window"], logger)
        df = compute_signal(df, logger)

        valid_signals = df["signal"].dropna()
        rows_processed = len(df)
        signal_rate = float(valid_signals.mean()) if len(valid_signals) > 0 else 0.0

        latency_ms = int(round((time.time() - start_time) * 1000))

        metrics = {
            "version": version,
            "rows_processed": rows_processed,
            "metric": "signal_rate",
            "value": round(signal_rate, 4),
            "latency_ms": latency_ms,
            "seed": config["seed"],
            "status": "success",
        }

        logger.info(
            "Metrics summary: rows_processed=%d, signal_rate=%.4f, latency_ms=%d",
            rows_processed, signal_rate, latency_ms,
        )

        write_metrics(args.output, metrics)
        logger.info("Job end. status=success")
        print(json.dumps(metrics, indent=2))
        sys.exit(0)

    except Exception as e:
        logger.exception("Job failed: %s", e)
        error_metrics = {
            "version": version,
            "status": "error",
            "error_message": str(e),
        }
        write_metrics(args.output, error_metrics)
        logger.info("Job end. status=error")
        print(json.dumps(error_metrics, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
