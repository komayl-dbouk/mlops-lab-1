"""Promote a Food-11 model version when it significantly beats the champion."""

from __future__ import annotations

import argparse
import math
import os
from pathlib import Path

import mlflow
from mlflow import MlflowClient

MODEL_NAME = "food11"
ACCURACY_METRIC = "test_accuracy"
REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIRS = {
    "processed": REPO_ROOT / "data" / "food11_processed",
    "mini": REPO_ROOT / "data" / "food11_processed_mini",
}


def test_split_size(dataset: str) -> int:
    """Return the number of files in a processed evaluation split."""
    try:
        evaluation_dir = DATA_DIRS[dataset] / "evaluation"
    except KeyError as exc:
        raise ValueError(f"Unknown dataset recorded on run: {dataset}") from exc

    size = sum(1 for path in evaluation_dir.rglob("*") if path.is_file())
    if size == 0:
        raise ValueError(f"Evaluation split is empty or missing: {evaluation_dir}")
    return size


def run_accuracy(client: MlflowClient, run_id: str) -> float:
    """Read the configured test-accuracy metric from an MLflow run."""
    metrics = client.get_run(run_id).data.metrics
    if ACCURACY_METRIC not in metrics:
        raise ValueError(f"Run {run_id} has no {ACCURACY_METRIC!r} metric")
    return metrics[ACCURACY_METRIC]


def promote(version: str) -> str:
    """Apply the quality gate and return the resulting alias decision."""
    client = MlflowClient()
    candidate = client.get_model_version(MODEL_NAME, version)
    champion = client.get_model_version_by_alias(MODEL_NAME, "champion")

    candidate_run = client.get_run(candidate.run_id)
    candidate_accuracy = run_accuracy(client, candidate.run_id)
    champion_accuracy = run_accuracy(client, champion.run_id)
    n = test_split_size(candidate_run.data.params.get("dataset", "mini"))
    standard_error = math.sqrt(champion_accuracy * (1 - champion_accuracy) / n)
    threshold = champion_accuracy + 2 * standard_error

    if candidate_accuracy >= threshold:
        decision = "champion"
        client.set_registered_model_alias(MODEL_NAME, "champion", version)
    else:
        decision = "challenger"
        client.set_registered_model_alias(MODEL_NAME, "challenger", version)

    tags = {
        "promotion_decision": decision,
        "candidate_accuracy": str(candidate_accuracy),
        "champion_accuracy": str(champion_accuracy),
        "promotion_threshold": str(threshold),
        "test_split_size": str(n),
    }
    for key, value in tags.items():
        client.set_model_version_tag(MODEL_NAME, version, key, value)

    print(
        f"version={version} decision={decision} "
        f"candidate={candidate_accuracy:.4f} champion={champion_accuracy:.4f} "
        f"threshold={threshold:.4f} n={n}"
    )
    return decision


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    mlflow.set_tracking_uri(
        os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
    )
    promote(args.version)


if __name__ == "__main__":
    main()
