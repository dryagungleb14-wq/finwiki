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

    class Config:
        min_length = 1


class AddAnswerRequest(BaseModel):
    answer: str

    class Config:
        min_length = 1


class AnswerLogResponse(BaseModel):
    id: int
    question_id: int
    text: str
    source: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class QuestionLogResponse(BaseModel):
    id: int
    text: str
    source: Optional[str] = None
    external_id: Optional[str] = None
    created_at: datetime
    answers: List[AnswerLogResponse] = []

    class Config:
        from_attributes = True

