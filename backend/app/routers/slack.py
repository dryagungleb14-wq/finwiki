from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import QAPair, QAPairStatus
from app.schemas import QAPairUnansweredResponse, SlackQuestionRequest, AddAnswerRequest, QAPairResponse
from app.services.search_service import search

router = APIRouter(prefix="/api/slack", tags=["slack"])

@router.post("/question", response_model=dict)
async def save_slack_question(request: SlackQuestionRequest, db: Session = Depends(get_db)):
    qa_pair = QAPair(
        question=request.question,
        answer="",
        status=QAPairStatus.unanswered,
        slack_user=request.slack_user
    )
    
    db.add(qa_pair)
    db.commit()
    db.refresh(qa_pair)
    
    return {"id": qa_pair.id, "status": "saved"}

@router.get("/unanswered", response_model=List[QAPairUnansweredResponse])
async def get_unanswered(db: Session = Depends(get_db)):
    qa_pairs = db.query(QAPair).filter(
        QAPair.status == QAPairStatus.unanswered
    ).order_by(QAPair.created_at.desc()).all()
    
    return qa_pairs

@router.post("/qa/{qa_id}/answer", response_model=QAPairResponse)
async def add_answer_to_question(qa_id: int, request: AddAnswerRequest, db: Session = Depends(get_db)):
    qa_pair = db.query(QAPair).filter(QAPair.id == qa_id).first()
    if not qa_pair:
        raise HTTPException(status_code=404, detail="Вопрос не найден")
    
    if qa_pair.status != QAPairStatus.unanswered:
        raise HTTPException(status_code=400, detail="К этому вопросу уже есть ответ")
    
    from app.services.gemini_service import process_qa_pair
    
    processed = process_qa_pair(qa_pair.question, request.answer)
    
    qa_pair.answer = request.answer
    qa_pair.question_processed = processed["question_processed"]
    qa_pair.answer_processed = processed["answer_processed"]
    qa_pair.status = QAPairStatus.approved
    
    from app.models import Keyword
    for keyword_text in processed["keywords"]:
        keyword = Keyword(qa_pair_id=qa_pair.id, keyword=keyword_text)
        db.add(keyword)
    
    db.commit()
    db.refresh(qa_pair)
    
    return qa_pair

@router.get("/search", response_model=dict)
async def search_for_slack(query: str, db: Session = Depends(get_db)):
    results = search(db, query)
    
    if results:
        return {
            "found": True,
            "answer": results[0].answer_processed or results[0].answer
        }
    else:
        return {"found": False}

