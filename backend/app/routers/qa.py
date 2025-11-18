from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List
import pandas as pd
import io

from app.database import get_db
from app.models import QAPair, Keyword, QAPairStatus
from app.schemas import QAPairCreate, QAPairResponse, SearchRequest, SearchResponse, QAPairPendingResponse
from app.services.gemini_service import process_qa_pair, process_voice_to_text
from app.services.search_service import search

router = APIRouter(prefix="/api", tags=["qa"])

@router.post("/add-qa", response_model=QAPairResponse)
async def add_qa(qa_data: QAPairCreate, db: Session = Depends(get_db)):
    processed = process_qa_pair(qa_data.question, qa_data.answer)
    
    qa_pair = QAPair(
        question=qa_data.question,
        answer=qa_data.answer,
        question_processed=processed["question_processed"],
        answer_processed=processed["answer_processed"],
        submitted_by=qa_data.submitted_by,
        status=QAPairStatus.pending
    )
    
    db.add(qa_pair)
    db.commit()
    db.refresh(qa_pair)
    
    for keyword_text in processed["keywords"]:
        keyword = Keyword(qa_pair_id=qa_pair.id, keyword=keyword_text)
        db.add(keyword)
    
    db.commit()
    db.refresh(qa_pair)
    
    return qa_pair

@router.post("/import-csv")
async def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Поддерживаются только CSV и Excel файлы")
    
    contents = await file.read()
    
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
        
        if 'question' not in df.columns or 'answer' not in df.columns:
            raise HTTPException(status_code=400, detail="Файл должен содержать колонки 'question' и 'answer'")
        
        results = []
        for _, row in df.iterrows():
            question = str(row['question']).strip()
            answer = str(row['answer']).strip()
            
            if not question or not answer:
                continue
            
            processed = process_qa_pair(question, answer)
            
            qa_pair = QAPair(
                question=question,
                answer=answer,
                question_processed=processed["question_processed"],
                answer_processed=processed["answer_processed"],
                submitted_by=row.get('submitted_by', None),
                status=QAPairStatus.pending
            )
            
            db.add(qa_pair)
            db.commit()
            db.refresh(qa_pair)
            
            for keyword_text in processed["keywords"]:
                keyword = Keyword(qa_pair_id=qa_pair.id, keyword=keyword_text)
                db.add(keyword)
            
            db.commit()
            results.append(qa_pair.id)
        
        return {"imported": len(results), "ids": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка обработки файла: {str(e)}")

@router.post("/process-voice")
async def process_voice(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.content_type or not file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="Поддерживаются только аудио файлы")
    
    audio_data = await file.read()
    
    try:
        text = process_voice_to_text(audio_data)
        
        if "ВОПРОС:" in text and "ОТВЕТ:" in text:
            parts = text.split("ОТВЕТ:")
            question = parts[0].replace("ВОПРОС:", "").strip()
            answer = parts[1].strip()
        else:
            lines = text.split('\n')
            question = lines[0] if lines else ""
            answer = '\n'.join(lines[1:]) if len(lines) > 1 else ""
        
        if not question or not answer:
            return {"text": text, "question": None, "answer": None}
        
        processed = process_qa_pair(question, answer)
        
        qa_pair = QAPair(
            question=question,
            answer=answer,
            question_processed=processed["question_processed"],
            answer_processed=processed["answer_processed"],
            status=QAPairStatus.pending
        )
        
        db.add(qa_pair)
        db.commit()
        db.refresh(qa_pair)
        
        for keyword_text in processed["keywords"]:
            keyword = Keyword(qa_pair_id=qa_pair.id, keyword=keyword_text)
            db.add(keyword)
        
        db.commit()
        db.refresh(qa_pair)
        
        return QAPairResponse.from_orm(qa_pair)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка обработки голоса: {str(e)}")

@router.post("/search", response_model=SearchResponse)
async def search_qa(search_request: SearchRequest, db: Session = Depends(get_db)):
    results = search(db, search_request.query)
    return SearchResponse(qa_pairs=results)

