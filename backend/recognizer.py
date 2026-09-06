"""Runtime inference for the locally trained 30-character N5 model."""
from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from ml.train_etl9b_n5 import KanjiCnn, normalize_ink

MODEL_PATH = Path(__file__).parent / "models" / "n5_30_kanji.pt"
DAKANJI_DIR = Path(__file__).parent / "models" / "dakanji"
DAKANJI_MODEL_PATH = DAKANJI_DIR / "char_classifier.onnx"
DAKANJI_LABELS_PATH = DAKANJI_DIR / "char_classifier_labels.txt"


@lru_cache(maxsize=1)
def load_model():
    if not MODEL_PATH.exists():
        return None
    checkpoint = torch.load(MODEL_PATH, map_location="cpu", weights_only=False)
    labels = checkpoint["labels"]
    model = KanjiCnn(len(labels))
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    return model, labels, checkpoint.get("validation_accuracy")


@lru_cache(maxsize=1)
def load_dakanji_model():
    """Load the official DaKanji v2 ONNX release when present locally."""
    if not DAKANJI_MODEL_PATH.exists() or not DAKANJI_LABELS_PATH.exists():
        return None
    import onnxruntime as ort

    labels = list(DAKANJI_LABELS_PATH.read_text(encoding="utf-8").strip())
    session = ort.InferenceSession(str(DAKANJI_MODEL_PATH), providers=["CPUExecutionProvider"])
    output_classes = session.get_outputs()[0].shape[-1]
    if len(labels) != output_classes:
        raise ValueError(f"DaKanji labels ({len(labels)}) do not match model output ({output_classes}).")
    return session, labels


def model_status() -> dict:
    dakanji = load_dakanji_model()
    if dakanji:
        _, labels = dakanji
        return {
            "model_status": "ready",
            "model": "DaKanji v2 ONNX",
            "source": "Dariyooo (DaAppLab), MIT",
            "labels": len(labels),
            "validation_accuracy": None,
        }
    loaded = load_model()
    if not loaded:
        return {"model_status": "collecting_samples", "labels": 0, "validation_accuracy": None}
    _, labels, validation_accuracy = loaded
    return {"model_status": "ready", "labels": len(labels), "validation_accuracy": validation_accuracy}


def _crop_ink_for_dakanji(ink: np.ndarray) -> np.ndarray:
    """Return the raw, tight ETL-style glyph frame used by DaKanji.

    DaKanji v2 performs its own grayscale conversion and resizing in the ONNX
    graph.  Padding/resizing it a second time changes the aspect ratio of a
    short character such as 二 and causes kana lookalikes to win.
    """
    rows, columns = np.where(ink > 0)
    if len(rows) == 0:
        return np.zeros((1, 1), dtype=np.float32)
    # Keep a small empty border: a crop that touches the glyph at every edge
    # makes the model interpret the character as taller/denser than it is.
    border = 10
    top = max(0, rows.min() - border)
    bottom = min(ink.shape[0], rows.max() + border + 1)
    left = max(0, columns.min() - border)
    right = min(ink.shape[1], columns.max() + border + 1)
    return ink[top:bottom, left:right]


def _dakanji_predictions(pixels: np.ndarray, top_k: int) -> list[dict]:
    """Run the official ONNX model on its already-rasterized input."""
    dakanji = load_dakanji_model()
    if not dakanji:
        return []
    session, labels = dakanji
    value = np.asarray(pixels, dtype=np.float32)[None, None, :, :]
    probabilities = session.run(None, {session.get_inputs()[0].name: value})[0][0]
    indices = np.argsort(probabilities)[-min(top_k, len(labels)):][::-1]
    return [{"kanji": labels[int(index)], "confidence": round(float(probabilities[index]), 4)} for index in indices]


def recognize_rasterized_strokes(pixels: np.ndarray, top_k: int) -> list[dict]:
    """Recognize white ink on black, square-padded vector stroke rasterization."""
    predictions = _dakanji_predictions(pixels, top_k)
    if predictions:
        return predictions
    image = Image.fromarray(np.asarray(pixels, dtype=np.uint8), mode="L")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return recognize(buffer.getvalue(), top_k)


def recognize_rasterized_png(png: bytes, top_k: int) -> list[dict]:
    """Use a browser-rasterized DaKanji image without thresholding or recropping."""
    image = Image.open(BytesIO(png)).convert("L")
    return recognize_rasterized_strokes(np.asarray(image, dtype=np.float32), top_k)


def recognize(png: bytes, top_k: int) -> list[dict]:
    dakanji = load_dakanji_model()
    if dakanji:
        image = Image.open(BytesIO(png)).convert("L")
        # DaKanji was trained on ETL-style images: black background and white
        # ink in the 0..255 range. The browser canvas is the inverse and also
        # contains pale guide lines, so retain only dark user ink then invert it.
        grayscale = np.asarray(image, dtype=np.uint8)
        ink = (grayscale < 150).astype(np.float32)
        # DaKanji's ONNX graph accepts a raw grayscale image of any size and
        # resizes internally. Keep the cropped glyph raw instead of applying
        # KanjiAI's separate 64x64 normalizer.
        return _dakanji_predictions(_crop_ink_for_dakanji(ink) * 255.0, top_k)
    loaded = load_model()
    if not loaded:
        return []
    model, labels, _ = loaded
    image = Image.open(BytesIO(png)).convert("L")
    # Canvas guide lines are pale; only the dark ink is kept for the classifier.
    ink = (np.asarray(image) < 128).astype(np.float32)
    value = torch.from_numpy(normalize_ink(ink)).unsqueeze(0).unsqueeze(0)
    with torch.no_grad():
        probabilities = torch.softmax(model(value)[0], dim=0)
    confidence, indices = torch.topk(probabilities, min(top_k, len(labels)))
    return [{"kanji": labels[int(index)], "confidence": round(float(score), 4)} for score, index in zip(confidence, indices)]
