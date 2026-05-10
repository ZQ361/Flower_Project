"""Image recognition endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..dependencies import get_optional_current_user
from ..schemas import PlantInfo, RecognitionResponse, TopPrediction
from ..services.history_service import record_history
from ..services.plant_service import get_plant_detail
from ..services.recognition_service import recognition_service


router = APIRouter(prefix="/recognition", tags=["recognition"])


@router.post("/predict", response_model=RecognitionResponse)
async def predict_flower(
    file: UploadFile = File(...),
    topk: int = Query(default=3, ge=1, le=5),
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
) -> RecognitionResponse:
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        result = recognition_service.predict_bytes(
            image_bytes=image_bytes,
            topk=topk,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - surfaces runtime prediction issues
        raise HTTPException(status_code=400, detail=f"Prediction failed: {exc}") from exc

    plant_item = get_plant_detail(db, result["pred_class"])
    if current_user is not None:
        try:
            record_history(
                db,
                user_id=current_user.id,
                plant_id=plant_item["id"] if plant_item else None,
                image_name=file.filename,
                image_path=None,
                pred_class=result["pred_class"],
                pred_name=result["pred_name"],
                confidence=result["confidence"],
                top3=result["top3"],
                source="web",
            )
        except Exception:
            # History persistence should never block recognition.
            pass

    return RecognitionResponse(
        filename=file.filename,
        model_name=result["model_name"],
        checkpoint_path=result["checkpoint_path"],
        pred_class=result["pred_class"],
        pred_name=result["pred_name"],
        confidence=result["confidence"],
        top3=[TopPrediction(**item) for item in result["top3"]],
        plant=PlantInfo(**plant_item) if plant_item else None,
    )
