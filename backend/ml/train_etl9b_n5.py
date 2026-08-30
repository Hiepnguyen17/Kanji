"""Train a 30-class modern Japanese handwriting recognizer from ETL-9B.

The ETL database must be downloaded by the project owner after accepting AIST's
terms. This script reads the original ETL9B-* binary files locally; it never
uploads or republishes their images.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from copy import deepcopy

import numpy as np
import torch
from PIL import Image
from torch import nn
from torch.nn import functional as F
from torch.utils.data import DataLoader, TensorDataset

RECORD_BYTES = 576
IMAGE_BYTES = 504
TARGET_CHARS = [
    "一", "二", "三", "四", "五", "六", "七", "八", "九", "十",
    "百", "千", "円", "年", "時", "分", "半", "月", "火", "水",
    "木", "金", "土", "日", "人", "口", "目", "耳", "手", "足",
]


class KanjiCnn(nn.Module):
    def __init__(self, classes: int):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(64, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(), nn.AdaptiveAvgPool2d(1),
        )
        self.classifier = nn.Sequential(nn.Flatten(), nn.Dropout(0.2), nn.Linear(128, classes))

    def forward(self, value: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.features(value))


def jis0208_to_char(code: int) -> str | None:
    """Decode ETL-9B's two-byte JIS X 0208 label."""
    try:
        return (b"\x1b$B" + code.to_bytes(2, "big") + b"\x1b(B").decode("iso2022_jp")
    except UnicodeDecodeError:
        return None


def normalize_ink(binary: np.ndarray) -> np.ndarray:
    """Crop to ink, preserve aspect ratio, and centre it in a 64×64 square."""
    if binary.mean() > 0.5:
        binary = 1.0 - binary
    points = np.argwhere(binary > 0.5)
    if len(points) == 0:
        return np.zeros((64, 64), dtype=np.float32)
    top, left = points.min(axis=0)
    bottom, right = points.max(axis=0) + 1
    crop = binary[top:bottom, left:right]
    canvas = np.zeros((80, 80), dtype=np.uint8)
    scale = min(64 / crop.shape[0], 64 / crop.shape[1])
    size = (max(1, round(crop.shape[1] * scale)), max(1, round(crop.shape[0] * scale)))
    resized = Image.fromarray((crop * 255).astype(np.uint8)).resize(size, Image.Resampling.LANCZOS)
    x, y = (80 - size[0]) // 2, (80 - size[1]) // 2
    canvas[y:y + size[1], x:x + size[0]] = np.asarray(resized)
    return np.asarray(Image.fromarray(canvas).resize((64, 64), Image.Resampling.LANCZOS), dtype=np.float32) / 255


def load_etl9b(etl_dir: Path) -> tuple[np.ndarray, np.ndarray]:
    target_to_index = {char: index for index, char in enumerate(TARGET_CHARS)}
    images: list[np.ndarray] = []
    labels: list[int] = []
    # AIST has published both ETL9B-1 and ETL9B_1 filename variants.
    def matching_files(directory: Path) -> list[Path]:
        return sorted(
            path for pattern in ("ETL9B-*", "ETL9B_*")
            for path in directory.glob(pattern)
            if path.is_file() and path.suffix == ""
        )

    # Prefer the files placed directly in --etl-dir. Some zip tools create a
    # second nested ETL9B folder; recursive scanning would otherwise duplicate
    # every image and invalidate the validation score.
    files = matching_files(etl_dir)
    if not files:
        files = sorted({path for directory in etl_dir.rglob("*") if directory.is_dir() for path in matching_files(directory)})
    if not files:
        raise FileNotFoundError("ETL9B files were not found in the data directory.")
    for path in files:
        with path.open("rb") as stream:
            record_number = 0
            while record := stream.read(RECORD_BYTES):
                if len(record) != RECORD_BYTES:
                    raise ValueError(f"File ETL bị thiếu dữ liệu: {path}")
                record_number += 1
                if record_number == 1:  # ETL9B has one dummy record at the beginning of every file.
                    continue
                char = jis0208_to_char(int.from_bytes(record[2:4], "big"))
                if char not in target_to_index:
                    continue
                pixels = np.unpackbits(np.frombuffer(record[8:8 + IMAGE_BYTES], dtype=np.uint8))
                images.append(normalize_ink(pixels[: 64 * 63].reshape(63, 64)))
                labels.append(target_to_index[char])
    if not images:
        raise ValueError("No requested N5 labels were found in ETL-9B.")
    counts = np.bincount(labels, minlength=len(TARGET_CHARS))
    missing = [TARGET_CHARS[index] for index, count in enumerate(counts) if count == 0]
    if missing:
        raise ValueError("ETL-9B is missing label codes: " + ", ".join(f"U+{ord(char):04X}" for char in missing))
    print("Samples per label:", ", ".join(f"U+{ord(char):04X}={count}" for char, count in zip(TARGET_CHARS, counts.tolist())))
    return np.stack(images).astype(np.float32), np.asarray(labels, dtype=np.int64)


def stratified_split(labels: np.ndarray, validation_ratio: float = 0.2) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(42)
    train, validation = [], []
    for label in range(len(TARGET_CHARS)):
        indices = np.flatnonzero(labels == label)
        rng.shuffle(indices)
        boundary = max(1, int(len(indices) * (1 - validation_ratio)))
        train.extend(indices[:boundary])
        validation.extend(indices[boundary:])
    return np.asarray(train), np.asarray(validation)


def accuracy(model: nn.Module, loader: DataLoader, device: torch.device) -> float:
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for images, labels in loader:
            prediction = model(images.to(device)).argmax(1).cpu()
            correct += int((prediction == labels).sum())
            total += len(labels)
    return correct / total if total else 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description="Huấn luyện KanjiAI bằng ETL-9B (30 chữ N5).")
    parser.add_argument("--etl-dir", required=True, type=Path, help="Thư mục chứa các file ETL9B-1 đến ETL9B-5")
    parser.add_argument("--epochs", type=int, default=18)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--output", type=Path, default=Path(__file__).parents[1] / "models" / "n5_30_kanji.pt")
    args = parser.parse_args()

    torch.manual_seed(42)
    images, labels = load_etl9b(args.etl_dir)
    train_indices, validation_indices = stratified_split(labels)
    values = torch.from_numpy(images).unsqueeze(1)
    targets = torch.from_numpy(labels)
    train_loader = DataLoader(TensorDataset(values[train_indices], targets[train_indices]), batch_size=args.batch_size, shuffle=True)
    validation_loader = DataLoader(TensorDataset(values[validation_indices], targets[validation_indices]), batch_size=args.batch_size)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = KanjiCnn(len(TARGET_CHARS)).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    loss_fn = nn.CrossEntropyLoss()
    best_accuracy = -1.0
    best_state = None

    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0
        for batch_images, batch_labels in train_loader:
            optimizer.zero_grad()
            loss = loss_fn(model(batch_images.to(device)), batch_labels.to(device))
            loss.backward()
            optimizer.step()
            total_loss += float(loss.detach())
        validation_accuracy = accuracy(model, validation_loader, device)
        if validation_accuracy > best_accuracy:
            best_accuracy = validation_accuracy
            best_state = deepcopy(model.state_dict())
        print(f"Epoch {epoch:02d}/{args.epochs}: loss={total_loss / len(train_loader):.4f}, validation={validation_accuracy:.2%}, best={best_accuracy:.2%}", flush=True)

    model.load_state_dict(best_state)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": model.cpu().state_dict(), "labels": TARGET_CHARS, "input_size": 64, "validation_accuracy": best_accuracy}, args.output)
    args.output.with_suffix(".json").write_text(json.dumps({"labels": TARGET_CHARS, "train_samples": int(len(train_indices)), "validation_samples": int(len(validation_indices)), "validation_accuracy": best_accuracy}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved model: {args.output}")


if __name__ == "__main__":
    main()
