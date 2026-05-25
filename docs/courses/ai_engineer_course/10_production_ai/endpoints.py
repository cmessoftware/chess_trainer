from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/ai-course", tags=["ai-course"])


@router.post("/analyze_game")
def analyze_game() -> dict[str, str]:
    return {"status": "stub"}


@router.post("/predict_move_quality")
def predict_move_quality() -> dict[str, str]:
    return {"status": "stub"}


@router.post("/explain_position")
def explain_position() -> dict[str, str]:
    return {"status": "stub"}
