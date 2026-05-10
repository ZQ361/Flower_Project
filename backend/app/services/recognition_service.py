"""Recognition service that wraps the fixed EfficientNet-B0 inference entry."""

from __future__ import annotations

from typing import Any

from model_service.inference import predict_image_bytes


class RecognitionService:
    def predict_bytes(
        self,
        image_bytes: bytes,
        topk: int = 3,
    ) -> dict[str, Any]:
        return predict_image_bytes(image_bytes, topk=topk)


recognition_service = RecognitionService()

