"""Train a ResNet18 classifier on the processed Food-11 dataset, logging to MLflow.

Expects data laid out by ``data.py``: ``root/<split>/<class_name>/*.jpg``
under ``training``, ``validation``, and ``evaluation`` splits.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import mlflow
import mlflow.pytorch
import torch
from torch import nn, optim
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIRS = {
    "processed": REPO_ROOT / "data" / "food11_processed",
    "mini": REPO_ROOT / "data" / "food11_processed_mini",
}

TRACKING_URI = "http://127.0.0.1:5000"
EXPERIMENT_NAME = "food11"

IMAGE_SIZE = 128
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def build_dataloaders(
    data_dir: Path, batch_size: int
) -> tuple[DataLoader, DataLoader, DataLoader, list[str]]:
    transform = transforms.Compose(
        [
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )

    train_ds = datasets.ImageFolder(data_dir / "training", transform=transform)
    val_ds = datasets.ImageFolder(data_dir / "validation", transform=transform)
    test_ds = datasets.ImageFolder(data_dir / "evaluation", transform=transform)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False)

    return train_loader, val_loader, test_loader, train_ds.classes


def build_model(num_classes: int) -> nn.Module:
    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model


def run_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    optimizer: optim.Optimizer | None = None,
) -> tuple[float, float]:
    is_train = optimizer is not None
    model.train(is_train)

    total_loss = 0.0
    correct = 0
    total = 0

    with torch.set_grad_enabled(is_train):
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)

            if is_train:
                optimizer.zero_grad()

            outputs = model(images)
            loss = criterion(outputs, labels)

            if is_train:
                loss.backward()
                optimizer.step()

            total_loss += loss.item() * images.size(0)
            correct += (outputs.argmax(dim=1) == labels).sum().item()
            total += images.size(0)

    return total_loss / total, correct / total


def train(args: argparse.Namespace) -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    data_dir = DATA_DIRS[args.dataset]

    train_loader, val_loader, test_loader, classes = build_dataloaders(data_dir, args.batch_size)
    model = build_model(num_classes=len(classes)).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)

    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)

    with mlflow.start_run():
        mlflow.log_params(
            {
                "model": "resnet18",
                "dataset": args.dataset,
                "epochs": args.epochs,
                "batch_size": args.batch_size,
                "lr": args.lr,
                "num_classes": len(classes),
            }
        )

        for epoch in range(1, args.epochs + 1):
            train_loss, _ = run_epoch(model, train_loader, criterion, device, optimizer)
            val_loss, val_accuracy = run_epoch(model, val_loader, criterion, device)

            mlflow.log_metric("train_loss", train_loss, step=epoch)
            mlflow.log_metric("val_loss", val_loss, step=epoch)
            mlflow.log_metric("val_accuracy", val_accuracy, step=epoch)

            print(
                f"epoch {epoch}/{args.epochs} "
                f"train_loss={train_loss:.4f} val_loss={val_loss:.4f} "
                f"val_accuracy={val_accuracy:.4f}"
            )

        _, test_accuracy = run_epoch(model, test_loader, criterion, device)
        mlflow.log_metric("test_accuracy", test_accuracy)
        print(f"test_accuracy={test_accuracy:.4f}")

        input_example, _ = next(iter(test_loader))
        mlflow.pytorch.log_model(model, "model", input_example=input_example[:1].cpu().numpy())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=DATA_DIRS.keys(), default="mini")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    return parser.parse_args()


def main() -> None:
    train(parse_args())


if __name__ == "__main__":
    main()
