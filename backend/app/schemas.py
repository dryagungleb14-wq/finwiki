from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class QAPairBase(BaseModel):
    question: str
    answer: str
    submitted_by: Optional[str] = None

class QAPairCreate(QAPairBase):
    pass

class KeywordResponse(BaseModel):
    id: int
    keyword: str

    class Config:
        from_attributes = True

class QAPairResponse(BaseModel):
    id: int
    question: str
    answer: str
    question_processed: Optional[str] = None
    answer_processed: Optional[str] = None
    status: str
    submitted_by: Optional[str] = None
    slack_user: Optional[str] = None
    created_at: datetime
    approved_at: Optional[datetime] = None
    keywords: List[KeywordResponse] = []

    class Config:
        from_attributes = True

class QAPairPendingResponse(BaseModel):
    id: int
    question: str
    answer: str
    question_processed: Optional[str] = None
    answer_processed: Optional[str] = None
    submitted_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class QAPairUnansweredResponse(BaseModel):
    id: int
    question: str
    slack_user: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SearchRequest(BaseModel):
    query: str

class SearchResponse(BaseModel):
    qa_pairs: List[QAPairResponse]

class SlackQuestionRequest(BaseModel):
    question: str
    slack_user: str

class AddAnswerRequest(BaseModel):
    answer: str
