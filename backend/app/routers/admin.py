from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from app.database import get_db
from app.models import QAPair, QAPairStatus, Question, Keyword
from app.schemas import QAPairResponse, QAPairPendingResponse, QuestionLogResponse, QAPairUpdate
from app.auth import verify_admin_key

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
async def approve_qa(
    qa_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_admin_key)
):
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
async def reject_qa(
    qa_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_admin_key)
):
    qa_pair = db.query(QAPair).filter(QAPair.id == qa_id).first()
    if not qa_pair:
        raise HTTPException(status_code=404, detail="Q&A не найден")

    if qa_pair.status != QAPairStatus.pending:
        raise HTTPException(status_code=400, detail="Q&A уже обработан")

    qa_pair.status = QAPairStatus.rejected

    db.commit()
    db.refresh(qa_pair)

    return qa_pair


@router.get("/log/questions", response_model=List[QuestionLogResponse])
async def get_recent_questions(limit: int = 50, db: Session = Depends(get_db)):
    questions = db.query(Question).order_by(Question.created_at.desc()).limit(limit).all()
    return questions


@router.get("/qa", response_model=List[QAPairResponse])
async def get_all_qa(
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(QAPair)
    
    if status:
        try:
            status_enum = QAPairStatus(status)
            query = query.filter(QAPair.status == status_enum)
        except ValueError:
            pass
    
    qa_pairs = query.order_by(QAPair.created_at.desc()).limit(limit).all()
    return qa_pairs


@router.put("/qa/{qa_id}", response_model=QAPairResponse)
async def update_qa(
    qa_id: int,
    data: QAPairUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_admin_key)
):
    qa_pair = db.query(QAPair).filter(QAPair.id == qa_id).first()
    if not qa_pair:
        raise HTTPException(status_code=404, detail="Q&A не найден")
    
    if data.question is not None:
        qa_pair.question = data.question
    if data.answer is not None:
        qa_pair.answer = data.answer
    if data.question_processed is not None:
        qa_pair.question_processed = data.question_processed
    if data.answer_processed is not None:
        qa_pair.answer_processed = data.answer_processed
    if data.status is not None:
        try:
            qa_pair.status = QAPairStatus(data.status)
            if data.status == "approved" and qa_pair.approved_at is None:
                qa_pair.approved_at = datetime.utcnow()
        except ValueError:
            raise HTTPException(status_code=400, detail="Неверный статус")
    
    db.commit()
    db.refresh(qa_pair)
    return qa_pair


@router.delete("/qa/{qa_id}")
async def delete_qa(
    qa_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_admin_key)
):
    qa_pair = db.query(QAPair).filter(QAPair.id == qa_id).first()
    if not qa_pair:
        raise HTTPException(status_code=404, detail="Q&A не найден")
    
    db.delete(qa_pair)
    db.commit()
    return {"status": "deleted", "id": qa_id}


