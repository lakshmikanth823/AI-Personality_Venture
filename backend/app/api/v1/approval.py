from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.app.core.database import get_db
from backend.app.models.user import User, UserRole
from backend.app.models.content import ContentCandidate
from backend.app.api.deps import require_role
from backend.app.services.content_engine import ContentEngine
from backend.app.schemas.content import CandidateGenerateRequest, ApprovalAction

router = APIRouter(prefix="/approval", tags=["approval"])

class CandidateEditRequest(BaseModel):
    new_text: str

@router.get("/candidates")
def list_candidates(
    status: Optional[str] = None,
    current_user: User = Depends(require_role([UserRole.OPERATOR, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    engine = ContentEngine(db)
    return engine.list_candidates(status=status)

@router.post("/candidates/generate")
def generate_candidates(
    payload: CandidateGenerateRequest,
    current_user: User = Depends(require_role([UserRole.OPERATOR, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    engine = ContentEngine(db)
    candidates = engine.generate_candidate_batch(count=payload.count, channel=payload.channel)
    return {"status": "success", "generated_count": len(candidates), "candidates": candidates}

@router.post("/candidates/{candidate_id}/approve")
def approve_candidate(
    candidate_id: str,
    current_user: User = Depends(require_role([UserRole.OPERATOR, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    engine = ContentEngine(db)
    try:
        return engine.approve_and_queue(candidate_id, operator_id=current_user.id)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=409, detail=str(e))

@router.post("/candidates/{candidate_id}/reject")
def reject_candidate(
    candidate_id: str,
    reason: Optional[str] = "Quality or safety mismatch",
    current_user: User = Depends(require_role([UserRole.OPERATOR, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    engine = ContentEngine(db)
    return engine.reject_candidate(candidate_id, operator_id=current_user.id, reason=reason)

@router.post("/candidates/{candidate_id}/edit")
def edit_candidate(
    candidate_id: str,
    payload: CandidateEditRequest,
    current_user: User = Depends(require_role([UserRole.OPERATOR, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    candidate = db.query(ContentCandidate).filter(ContentCandidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    candidate.candidate_text = payload.new_text
    db.commit()
    return {"status": "success", "id": candidate.id, "updated_text": candidate.candidate_text}
