from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import QAPair, QAPairStatus
from app.schemas import QAPairResponse, QAPairPendingResponse

router = APIRouter(prefix="/api", tags=["admin"])

@router.get("/pending", response_model=List[QAPairPendingResponse])
async def get_pending(db: Session = Depends(get_db)):
    qa_pairs = db.query(QAPair).filter(
        QAPair.status == QAPairStatus.pending
    ).order_by(QAPair.created_at.desc()).all()
    
    return qa_pairs

@router.get("/qa/{qa_id}", response_model=QAPairResponse)
async def get_qa(qa_id: int, db: Session = Depends(get_db)):
    qa_pair = db.query(QAPair).filter(QAPair.id == qa_id).first()
    if not qa_pair:
        raise HTTPException(status_code=404, detail="Q&A не найден")
    return qa_pair

@router.post("/approve/{qa_id}", response_model=QAPairResponse)
async def approve_qa(qa_id: int, db: Session = Depends(get_db)):
    qa_pair = db.query(QAPair).filter(QAPair.id == qa_id).first()
    if not qa_pair:
        raise HTTPException(status_code=404, detail="Q&A не найден")
    
    if qa_pair.status != QAPairStatus.pending:
        raise HTTPException(status_code=400, detail="Q&A уже обработан")
    
    qa_pair.status = QAPairStatus.approved
    qa_pair.approved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(qa_pair)
    
    return qa_pair

@router.post("/reject/{qa_id}", response_model=QAPairResponse)
async def reject_qa(qa_id: int, db: Session = Depends(get_db)):
    qa_pair = db.query(QAPair).filter(QAPair.id == qa_id).first()
    if not qa_pair:
        raise HTTPException(status_code=404, detail="Q&A не найден")
    
    if qa_pair.status != QAPairStatus.pending:
        raise HTTPException(status_code=400, detail="Q&A уже обработан")
    
    qa_pair.status = QAPairStatus.rejected
    
    db.commit()
    db.refresh(qa_pair)
    
    return qa_pair

