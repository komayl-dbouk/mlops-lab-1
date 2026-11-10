"""Validate a processed Food-11 dataset against its data contract."""

from __future__ import annotations

import argparse
import hashlib
import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image

try:
    from .data import CLASSES, SPLITS
except ImportError:  # Allow execution as a script.
    from data import CLASSES, SPLITS


def report(name: str, passed: bool, detail: str = "") -> bool:
    """Print one contract result and return it for aggregation."""
    suffix = f" - {detail}" if detail else ""
    print(f"{'PASS' if passed else 'FAIL'}: {name}{suffix}")
    return passed


def validate(dataset: Path, min_per_class: int, tau: float) -> bool:
    """Run all data-contract checks against ``dataset``."""
    expected_classes = set(CLASSES)
    split_files: dict[str, dict[str, list[Path]]] = {}

    folder_errors: list[str] = []
    for split in SPLITS:
        split_dir = dataset / split
        actual_classes = (
            {path.name for path in split_dir.iterdir() if path.is_dir()}
            if split_dir.is_dir()
            else set()
        )
        missing = sorted(expected_classes - actual_classes)
        extra = sorted(actual_classes - expected_classes)
        if missing or extra:
            folder_errors.append(f"{split}: missing={missing}, extra={extra}")

        split_files[split] = {
            class_name: sorted(
                path for path in (split_dir / class_name).glob("*") if path.is_file()
            )
            for class_name in CLASSES
        }

    results = [
        report(
            "split class folders",
            not folder_errors,
            "; ".join(folder_errors) if folder_errors else "all splits have 11 classes",
        )
    ]

    invalid_images: list[str] = []
    hashes_by_split: dict[str, set[str]] = defaultdict(set)
    for split, class_files in split_files.items():
        for files in class_files.values():
            for path in files:
                try:
                    content_hash = hashlib.md5(path.read_bytes()).hexdigest()
                    hashes_by_split[split].add(content_hash)
                    with Image.open(path) as image:
                        image.load()
                        if image.mode != "RGB" or image.size != (128, 128):
                            invalid_images.append(
                                f"{path}: mode={image.mode}, size={image.size}"
                            )
                except (OSError, ValueError) as exc:
                    invalid_images.append(f"{path}: {exc}")

    results.append(
        report(
            "image format",
            not invalid_images,
            f"{len(invalid_images)} invalid image(s)" if invalid_images else "all RGB 128x128",
        )
    )

    small_classes = [
        f"{split}/{class_name}={len(files)}"
        for split, class_files in split_files.items()
        for class_name, files in class_files.items()
        if len(files) < min_per_class
    ]
    results.append(
        report(
            "minimum images per class",
            not small_classes,
            ", ".join(small_classes)
            if small_classes
            else f"at least {min_per_class} in every class",
        )
    )

    duplicate_pairs = [
        f"{left}/{right}={len(hashes_by_split[left] & hashes_by_split[right])}"
        for index, left in enumerate(SPLITS)
        for right in SPLITS[index + 1 :]
        if hashes_by_split[left] & hashes_by_split[right]
    ]
    results.append(
        report(
            "no images shared across splits",
            not duplicate_pairs,
            ", ".join(duplicate_pairs) if duplicate_pairs else "no duplicate content",
        )
    )

    training_counts = {
        class_name: len(split_files["training"][class_name]) for class_name in CLASSES
    }
    validation_counts = {
        class_name: len(split_files["validation"][class_name]) for class_name in CLASSES
    }
    training_total = sum(training_counts.values())
    validation_total = sum(validation_counts.values())
    distribution_errors: list[str] = []
    if training_total == 0 or validation_total == 0:
        distribution_errors.append("training or validation split is empty")
    else:
        for class_name in CLASSES:
            difference = abs(
                training_counts[class_name] / training_total
                - validation_counts[class_name] / validation_total
            )
            if difference > tau:
                distribution_errors.append(f"{class_name}={difference:.3f}")

    results.append(
        report(
            "training/validation class balance",
            not distribution_errors,
            ", ".join(distribution_errors)
            if distribution_errors
            else f"all share differences <= {tau}",
        )
    )

    return all(results)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--min-per-class", type=int, default=50)
    parser.add_argument("--tau", type=float, default=0.05)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.min_per_class < 0:
        raise SystemExit("--min-per-class must be non-negative")
    if args.tau < 0:
        raise SystemExit("--tau must be non-negative")
    sys.exit(0 if validate(args.dataset, args.min_per_class, args.tau) else 1)


if __name__ == "__main__":
    main()
