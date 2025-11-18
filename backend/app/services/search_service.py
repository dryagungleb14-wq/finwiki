from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models import QAPair, Keyword, QAPairStatus
from app.services.gemini_service import semantic_search
from typing import List

def search_by_keywords(db: Session, query: str) -> List[QAPair]:
    query_lower = query.lower()
    words = query_lower.split()
    
    keyword_matches = db.query(Keyword).filter(
        or_(*[Keyword.keyword.ilike(f"%{word}%") for word in words])
    ).all()
    
    qa_pair_ids = list(set([kw.qa_pair_id for kw in keyword_matches]))
    
    if not qa_pair_ids:
        return []
    
    qa_pairs = db.query(QAPair).filter(
        QAPair.id.in_(qa_pair_ids),
        QAPair.status == QAPairStatus.approved
    ).all()
    
    return qa_pairs

def search_full_text(db: Session, query: str) -> List[QAPair]:
    query_lower = query.lower()
    words = query_lower.split()
    
    qa_pairs = db.query(QAPair).filter(
        QAPair.status == QAPairStatus.approved,
        or_(
            *[QAPair.question.ilike(f"%{word}%") for word in words],
            *[QAPair.answer.ilike(f"%{word}%") for word in words],
            *[QAPair.question_processed.ilike(f"%{word}%") for word in words],
            *[QAPair.answer_processed.ilike(f"%{word}%") for word in words]
        )
    ).all()
    
    return qa_pairs

def search_semantic(db: Session, query: str) -> List[QAPair]:
    qa_pairs = db.query(QAPair).filter(
        QAPair.status == QAPairStatus.approved
    ).limit(50).all()
    
    if not qa_pairs:
        return []
    
    qa_list = [
        {
            "id": qa.id,
            "question": qa.question_processed or qa.question,
            "answer": qa.answer_processed or qa.answer,
            "qa_pair": qa
        }
        for qa in qa_pairs
    ]
    
    results = semantic_search(query, qa_list)
    
    return [item["qa_pair"] for item in results]

def search(db: Session, query: str) -> List[QAPair]:
    results = search_by_keywords(db, query)
    
    if not results:
        results = search_full_text(db, query)
    
    if not results:
        results = search_semantic(db, query)
    
    return results[:10]

