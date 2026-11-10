"""Prepare the Food-11 dataset for training.

The raw dump (``data/food11 dataset``) stores images as flat files per split
named ``<class_id>_<index>.jpg``. torchvision's ``ImageFolder`` (and hence a
ResNet trained via transfer learning) instead expects one folder per class:
``root/<split>/<class_name>/*.jpg``.

This script builds two such datasets under ./data:
  - food11_processed:      full dataset, images resized to 128x128
  - food11_processed_mini: same layout, capped at MAX_PER_CLASS_MINI images
                            per class/split, for fast local development
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = REPO_ROOT / "data" / "food11 dataset"
PROCESSED_DIR = REPO_ROOT / "data" / "food11_processed"
PROCESSED_MINI_DIR = REPO_ROOT / "data" / "food11_processed_mini"

IMAGE_SIZE = (128, 128)
SPLITS = ["training", "validation", "evaluation"]
MAX_PER_CLASS_MINI = 100

# Food-11's numeric label -> category name (fixed by the dataset itself).
CLASSES = [
    "Bread",
    "Dairy product",
    "Dessert",
    "Egg",
    "Fried food",
    "Meat",
    "Noodles-Pasta",
    "Rice",
    "Seafood",
    "Soup",
    "Vegetable-Fruit",
]
CLASS_NAMES = dict(enumerate(CLASSES))


def _class_id_from_filename(filename: str) -> int:
    return int(filename.split("_", 1)[0])


def category_from_filename(filename: str) -> str:
    """Return the Food-11 category encoded in an image filename."""
    return CLASSES[_class_id_from_filename(filename)]


def resize_image(img: Image.Image, size: int = 128) -> Image.Image:
    """Return an RGB copy of ``img`` resized to ``size`` square pixels."""
    return img.convert("RGB").resize((size, size), Image.Resampling.BILINEAR)


def _process_split(split: str, out_root: Path, max_per_class: int | None) -> None:
    src_split = RAW_DIR / split
    if not src_split.is_dir():
        raise FileNotFoundError(f"Expected raw split folder at {src_split}")

    counts: dict[int, int] = {}
    for image_path in sorted(src_split.iterdir()):
        if not image_path.is_file():
            continue

        class_id = _class_id_from_filename(image_path.name)
        class_name = category_from_filename(image_path.name)

        seen = counts.get(class_id, 0)
        if max_per_class is not None and seen >= max_per_class:
            continue
        counts[class_id] = seen + 1

        out_dir = out_root / split / class_name
        out_dir.mkdir(parents=True, exist_ok=True)

        with Image.open(image_path) as img:
            img = resize_image(img, IMAGE_SIZE[0])
            img.save(out_dir / image_path.name)


def build_dataset(out_root: Path, max_per_class: int | None) -> None:
    for split in SPLITS:
        _process_split(split, out_root, max_per_class)
    print(f"Wrote dataset to {out_root}")


def main() -> None:
    if PROCESSED_DIR.exists():
        print(f"{PROCESSED_DIR} already exists, skipping full dataset")
    else:
        build_dataset(PROCESSED_DIR, max_per_class=None)

    if PROCESSED_MINI_DIR.exists():
        print(f"{PROCESSED_MINI_DIR} already exists, skipping mini dataset")
    else:
        build_dataset(PROCESSED_MINI_DIR, max_per_class=MAX_PER_CLASS_MINI)


if __name__ == "__main__":
    main()
