"""Single-model inference entry for EfficientNet-B0."""

from __future__ import annotations

import io
import os
from typing import Any

import torch
from PIL import Image
from torchvision import transforms

try:
    from model_service.config import config
    from model_service.utils.model import create_model
except ImportError:  # pragma: no cover - supports running from model_service directory
    from config import config
    from utils.model import create_model


_MODEL: torch.nn.Module | None = None# 模型实例
_MODEL_PATH: str | None = None# 模型路径缓存


def get_checkpoint_path() -> str:
    return os.path.join(config.save_dir, "efficientnet_b0_flowers102_final.pth")


def get_transform() -> transforms.Compose:
    return transforms.Compose(
        [
            transforms.Resize(config.image_size),
            transforms.CenterCrop(config.image_size),
            transforms.ToTensor(),
            transforms.Normalize(mean=config.mean, std=config.std),
        ]
    )


def load_model(model_path: str | None = None) -> torch.nn.Module:
    global _MODEL, _MODEL_PATH

    resolved_path = os.path.abspath(model_path or get_checkpoint_path())
    if _MODEL is not None and _MODEL_PATH == resolved_path:
        return _MODEL

    if not os.path.exists(resolved_path):
        raise FileNotFoundError(f"Checkpoint not found: {resolved_path}")

    model = create_model("efficientnet_b0")
    state_dict = torch.load(resolved_path, map_location=config.device)
    model.load_state_dict(state_dict)
    model = model.to(config.device)
    model.eval()

    _MODEL = model
    _MODEL_PATH = resolved_path
    return model


def _predict_pil(image: Image.Image, topk: int = 3) -> dict[str, Any]:
    if topk < 1:
        raise ValueError("topk must be greater than 0")

    model = load_model()
    transform = get_transform()
    image_tensor = transform(image).unsqueeze(0).to(config.device)

    with torch.no_grad():
        outputs = model(image_tensor)
        probs = torch.softmax(outputs, dim=1)
        topk_probs, topk_indices = torch.topk(probs, k=topk, dim=1)

    topk_probs = topk_probs[0].cpu().tolist()
    topk_indices = topk_indices[0].cpu().tolist()

    top3 = []
    for idx, prob in zip(topk_indices, topk_probs):
        top3.append(
            {
                "class_id": idx,
                "class_name": config.flower_classes[idx],
                "confidence": prob * 100,
            }
        )

    best_idx = topk_indices[0]
    return {
        "pred_class": best_idx,
        "pred_name": config.flower_classes[best_idx],
        "confidence": topk_probs[0] * 100,
        "top3": top3,
        "model_name": "efficientnet_b0",
        "checkpoint_path": get_checkpoint_path(),
    }

# bytes: 图片字节流
def predict_image_bytes(image_bytes: bytes, topk: int = 3) -> dict[str, Any]:
    with Image.open(io.BytesIO(image_bytes)) as image:
        return _predict_pil(image.convert("RGB"), topk=topk)

# str: 图片路径
def predict_image_path(image_path: str, topk: int = 3) -> dict[str, Any]:
    with Image.open(image_path) as image:
        return _predict_pil(image.convert("RGB"), topk=topk)


def main() -> None:
    image_path = input("Enter image path: ").strip() # 从用户输入获取图片路径
    if not image_path: # 检查路径是否为空
        raise ValueError("Image path cannot be empty.")

    if not os.path.exists(image_path): # 检查图片路径是否存在
        raise FileNotFoundError(f"Image not found: {image_path}")

    result = predict_image_path(image_path, topk=3)

    print(f"Pred class: {result['pred_class']}")
    print(f"Pred name: {result['pred_name']}")
    print(f"Confidence: {result['confidence']:.2f}%")
    print("Top-3:")
    for index, item in enumerate(result["top3"], start=1):
        print(f"{index}. {item['class_name']} ({item['confidence']:.2f}%)")


if __name__ == "__main__":
    main()
